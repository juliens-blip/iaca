import asyncio
import base64
import json
import logging
import random
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.flashcard import Flashcard
from app.security import verify_ws_token
from app.services import ollama_service, whisper_service, piper_service

logger = logging.getLogger(__name__)
router = APIRouter()

SUMMARY_PREFIX = "[Résumé précédent:]"
MAX_EXCHANGES_BEFORE_SUMMARY = 10
SUMMARY_SOURCE_MESSAGES = 6
SUMMARY_TRUNCATE_CHARS = 50
RECENT_MESSAGES_TO_KEEP = 4


def _build_history_summary(messages: list[dict]) -> str:
    """Create a compact text summary from the oldest messages."""
    snippets: list[str] = []
    for message in messages[:SUMMARY_SOURCE_MESSAGES]:
        content = message.get("content", "")
        compact = " ".join(str(content).split())
        snippets.append(compact[:SUMMARY_TRUNCATE_CHARS])
    return f"{SUMMARY_PREFIX} {' | '.join(snippets)}"


def _compact_history(messages: list[dict]) -> list[dict]:
    """Keep recent messages and summarize older ones when history grows too much."""
    max_messages = MAX_EXCHANGES_BEFORE_SUMMARY * 2
    if len(messages) <= max_messages:
        return messages
    summary_message = {"role": "system", "content": _build_history_summary(messages)}
    return [summary_message] + messages[-RECENT_MESSAGES_TO_KEEP:]


async def _pick_random_flashcard(db: AsyncSession, matiere_id: int | None = None) -> Flashcard:
    """Pick a random flashcard, preferring due ones."""
    query = select(Flashcard)
    if matiere_id:
        query = query.filter(Flashcard.matiere_id == matiere_id)
    result = await db.execute(
        query.filter(Flashcard.prochaine_revision <= datetime.now(timezone.utc))
    )
    due = result.scalars().all()
    if not due:
        result = await db.execute(query)
        due = result.scalars().all()
    if not due:
        raise HTTPException(404, "Aucune flashcard disponible")
    return random.choice(due)


@router.get("/flashcard-random")
async def get_random_flashcard(matiere_id: int | None = None, db: AsyncSession = Depends(get_db)):
    """Return a random flashcard, preferring those due for revision."""
    card = await _pick_random_flashcard(db, matiere_id)
    return {
        "id": card.id,
        "question": card.question,
        "reponse": card.reponse,
        "matiere_id": card.matiere_id,
    }


@router.websocket("/ws")
async def vocal_chat(websocket: WebSocket, token: str | None = None, model: str | None = None):
    """WebSocket endpoint for vocal chat with the AI professor.

    Protocol:
    - Client sends: {"type": "audio", "data": "<base64 audio>"} or {"type": "text", "message": "..."}
    - Server responds: {"type": "text", "message": "..."} then {"type": "audio", "data": "<base64 wav>"}
    - Server sends: {"type": "ping"} every 30s as heartbeat
    - Server sends: {"type": "error", "message": "..."} on errors

    Auth (when API_AUTH_TOKEN is set):
    - Pass token as query param: ?token=<token>
    - Or pass Authorization: Bearer <token> header
    """
    auth_header = websocket.headers.get("Authorization")
    if not await verify_ws_token(token, auth_header):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    historique: list[dict] = []
    # Quiz mode state: when set, the next user message is treated as a quiz answer
    quiz_pending_card: dict | None = None  # {"id", "question", "reponse"}

    async def heartbeat():
        """Send periodic pings to keep connection alive."""
        try:
            while True:
                await asyncio.sleep(30)
                await websocket.send_json({"type": "ping"})
        except Exception:
            pass

    heartbeat_task = asyncio.create_task(heartbeat())

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "JSON invalide"})
                continue

            # Get user message (either from audio transcription or direct text)
            if data.get("type") == "audio":
                try:
                    audio_bytes = base64.b64decode(data["data"])
                    user_message = await whisper_service.transcrire(audio_bytes)
                    await websocket.send_json({
                        "type": "transcription",
                        "message": user_message,
                    })
                except RuntimeError as e:
                    # Whisper not installed or model error — recoverable, keep session alive
                    logger.warning(f"Transcription indisponible: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                        "recoverable": True,
                    })
                    continue
                except Exception as e:
                    logger.error(f"Erreur transcription Whisper: {e}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Erreur transcription: {str(e)}",
                        "recoverable": True,
                    })
                    continue
            elif data.get("type") == "text":
                user_message = data.get("message", "")
                if not user_message:
                    await websocket.send_json({"type": "error", "message": "Message vide"})
                    continue
            elif data.get("type") == "pong":
                continue
            elif data.get("type") == "start_quiz":
                # Start a quiz round: fetch a random flashcard and send the question
                try:
                    async for db in get_db():
                        card = await _pick_random_flashcard(db, data.get("matiere_id"))
                        quiz_pending_card = {
                            "id": card.id,
                            "question": card.question,
                            "reponse": card.reponse,
                        }
                        await websocket.send_json({
                            "type": "quiz_question",
                            "flashcard_id": card.id,
                            "question": card.question,
                        })
                        break
                except HTTPException as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": e.detail,
                        "recoverable": True,
                    })
                except Exception as e:
                    logger.error(f"Erreur start_quiz: {e}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Erreur quiz: {str(e)}",
                        "recoverable": True,
                    })
                continue
            elif data.get("type") == "quiz_answer":
                # Evaluate the student's answer against the pending flashcard
                if not quiz_pending_card:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Aucune question en cours. Envoyez start_quiz d'abord.",
                        "recoverable": True,
                    })
                    continue
                student_answer = data.get("message", "")
                if not student_answer:
                    await websocket.send_json({"type": "error", "message": "Réponse vide"})
                    continue
                try:
                    feedback = await ollama_service.evaluer_reponse(
                        quiz_pending_card["question"],
                        quiz_pending_card["reponse"],
                        student_answer,
                        model=model,
                    )
                    await websocket.send_json({
                        "type": "quiz_feedback",
                        "flashcard_id": quiz_pending_card["id"],
                        "feedback": feedback,
                    })
                except Exception as e:
                    logger.error(f"Erreur évaluation quiz: {e}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Erreur évaluation: {str(e)}",
                        "recoverable": True,
                    })
                finally:
                    quiz_pending_card = None
                continue
            else:
                await websocket.send_json({"type": "error", "message": "Type invalide"})
                continue

            # Get AI response from Ollama via streaming
            try:
                full_response = ""
                sentence_buffer = ""
                sentence_index = 0

                async for token in ollama_service.chat_stream(user_message, historique, model=model):
                    full_response += token
                    sentence_buffer += token
                    # Send each token to the frontend
                    await websocket.send_json({"type": "text_chunk", "token": token})

                    # Detect end of sentence for incremental TTS
                    if any(sentence_buffer.rstrip().endswith(p) for p in [".", "!", "?"]):
                        clean = sentence_buffer.strip()
                        if len(clean) > 10:
                            try:
                                audio_bytes = await piper_service.synthetiser(clean[:280])
                                await websocket.send_json({
                                    "type": "audio_chunk",
                                    "data": base64.b64encode(audio_bytes).decode(),
                                    "index": sentence_index,
                                })
                                sentence_index += 1
                            except Exception as e:
                                logger.warning(f"TTS chunk error: {e}")
                            sentence_buffer = ""

                # Send full text once streaming is done
                await websocket.send_json({"type": "text_done", "message": full_response})

                # TTS for the last buffered sentence if not already sent
                if sentence_buffer.strip() and len(sentence_buffer.strip()) > 10:
                    try:
                        audio_bytes = await piper_service.synthetiser(sentence_buffer.strip()[:280])
                        await websocket.send_json({
                            "type": "audio_chunk",
                            "data": base64.b64encode(audio_bytes).decode(),
                            "index": sentence_index,
                        })
                    except Exception:
                        pass
                await websocket.send_json({"type": "audio_done"})

            except WebSocketDisconnect:
                raise
            except Exception as e:
                logger.error(f"Erreur Ollama chat: {e}", exc_info=True)
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Erreur LLM: {str(e)}",
                        "recoverable": True,
                    })
                except Exception:
                    pass
                continue

            # Update history after streaming is complete
            historique.append({"role": "user", "content": user_message})
            historique.append({"role": "assistant", "content": full_response})
            historique = _compact_history(historique)

    except WebSocketDisconnect:
        logger.info("Client WebSocket deconnecte")
    except RuntimeError as e:
        if "not connected" in str(e).lower() or "close message" in str(e).lower():
            logger.info("Client WebSocket déconnecté pendant traitement")
        else:
            logger.error(f"Erreur WebSocket vocal: {type(e).__name__}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Erreur WebSocket vocal: {type(e).__name__}: {e}", exc_info=True)
    finally:
        heartbeat_task.cancel()


@router.get("/status")
async def vocal_status():
    """Check availability of vocal services."""
    ollama_ok = await ollama_service.check_disponible()
    piper_ok = await piper_service.check_disponible()
    whisper_ok = whisper_service.check_disponible()
    model = None
    if ollama_ok:
        try:
            model = await ollama_service._get_best_model()
        except Exception:
            pass
    return {
        "ollama": ollama_ok,
        "piper": piper_ok,
        "whisper": whisper_ok,
        "model": model,
    }


@router.get("/models")
async def vocal_models():
    """List available Ollama models and currently active model."""
    try:
        models = await ollama_service.list_models()
        active = await ollama_service._get_best_model() if models else None
        return {"models": models, "active": active}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
