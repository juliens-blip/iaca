import asyncio
import json
import sqlite3
from collections.abc import AsyncGenerator
from pathlib import Path

import httpx

from app.config import settings

_DB_PATH = (
    Path(settings.database_url.replace("sqlite:///", "", 1))
    if settings.database_url.startswith("sqlite:///")
    else None
)


def _rag_context(question: str, max_results: int = 3) -> str:
    """Fetch the most relevant flashcard Q/A pairs from the local DB as context."""
    if _DB_PATH is None or not _DB_PATH.exists():
        return ""
    try:
        words = [w.lower() for w in question.split() if len(w) > 4]
        if not words:
            return ""
        conn = sqlite3.connect(str(_DB_PATH))
        placeholders = " OR ".join(["LOWER(question) LIKE ?" for _ in words[:5]])
        params = [f"%{w}%" for w in words[:5]]
        rows = conn.execute(
            f"SELECT question, reponse FROM flashcards WHERE {placeholders} LIMIT ?",
            params + [max_results],
        ).fetchall()
        conn.close()
        if not rows:
            return ""
        snippets = [f"Q: {r[0]}\nR: {r[1][:200]}" for r in rows]
        return "Fiches de cours pertinentes:\n" + "\n\n".join(snippets)
    except Exception:
        return ""

SYSTEM_PROMPT = """Tu es un professeur de droit public pour concours administratifs (INSP/IRA). Réponds en 2-3 phrases courtes en français. Sois factuel et précis. Termine par une courte question de relance."""

# Preferred models in order of priority (lightest first for low-RAM machines)
PREFERRED_MODELS = ["qwen2:0.5b", "phi3:mini", "tinyllama", "mistral:latest"]

# Token limits per model to control response length and TTS compatibility
MODEL_TOKEN_LIMITS: dict[str, int] = {
    "qwen2:0.5b": 200,
    "tinyllama": 200,
    "phi3:mini": 250,
    "mistral:latest": 300,
}


async def _get_best_model() -> str:
    """Find the best available model from preferred list."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            tags_resp = await client.get(f"{settings.ollama_host}/api/tags")
            if tags_resp.status_code == 200:
                available = [m["name"] for m in tags_resp.json().get("models", [])]
                for model in PREFERRED_MODELS:
                    if model in available:
                        return model
                # Fallback: use first available model
                if available:
                    return available[0]
    except (httpx.ConnectError, httpx.TimeoutException):
        raise RuntimeError("Ollama non accessible. Lancez: ollama serve")
    raise RuntimeError(f"Aucun modele disponible. Lancez: ollama pull qwen2:0.5b")


def _format_size(size_in_bytes: int | None) -> str:
    """Format model size in GB with one decimal place."""
    if not isinstance(size_in_bytes, int) or size_in_bytes <= 0:
        return "N/A"
    return f"{size_in_bytes / (1024 ** 3):.1f}GB"


async def list_models() -> list[dict[str, str]]:
    """List Ollama models with a human-readable size."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            tags_resp = await client.get(f"{settings.ollama_host}/api/tags")
            tags_resp.raise_for_status()
            raw_models = tags_resp.json().get("models", [])
            return [
                {
                    "name": model.get("name", ""),
                    "size": _format_size(model.get("size")),
                }
                for model in raw_models
                if model.get("name")
            ]
    except (httpx.ConnectError, httpx.TimeoutException):
        raise RuntimeError("Ollama non accessible. Lancez: ollama serve")
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Erreur Ollama HTTP {e.response.status_code}: {e.response.text[:200]}")


async def chat(message: str, historique: list[dict] | None = None, model: str | None = None) -> str:
    """Send a message to Ollama and get a response, enriched with RAG context."""
    if model is None:
        model = await _get_best_model()

    num_predict = MODEL_TOKEN_LIMITS.get(model, 250)

    # RAG only on first turn (no history yet) or when history is short
    rag = ""
    if not historique or len(historique) <= 2:
        rag = await asyncio.to_thread(_rag_context, message)
    system = SYSTEM_PROMPT if not rag else f"{SYSTEM_PROMPT}\n\nContexte cours:\n{rag}"

    messages = [{"role": "system", "content": system}]
    if historique:
        messages.extend(historique)
    messages.append({"role": "user", "content": message})

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{settings.ollama_host}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,
                        "num_predict": num_predict,
                        "repeat_penalty": 1.3,
                        "top_p": 0.9,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Erreur Ollama HTTP {e.response.status_code}: {e.response.text[:200]}")
    except httpx.TimeoutException:
        raise RuntimeError(f"Ollama timeout (>90s) avec {model}. Memoire insuffisante ou modele trop lourd.")


async def chat_stream(
    message: str,
    historique: list[dict] | None = None,
    model: str | None = None,
) -> AsyncGenerator[str, None]:
    """Yield tokens one by one from Ollama streaming API."""
    if model is None:
        model = await _get_best_model()

    num_predict = MODEL_TOKEN_LIMITS.get(model, 250)

    rag = ""
    if not historique or len(historique) <= 2:
        rag = await asyncio.to_thread(_rag_context, message)
    system = SYSTEM_PROMPT if not rag else f"{SYSTEM_PROMPT}\n\nContexte cours:\n{rag}"

    messages = [{"role": "system", "content": system}]
    if historique:
        messages.extend(historique)
    messages.append({"role": "user", "content": message})

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{settings.ollama_host}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": 0.4,
                        "num_predict": num_predict,
                        "repeat_penalty": 1.3,
                        "top_p": 0.9,
                    },
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if chunk.get("done"):
                        return
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Erreur Ollama HTTP {e.response.status_code}: {e.response.text[:200]}")
    except httpx.TimeoutException:
        raise RuntimeError(f"Ollama timeout (>120s) avec {model}.")


async def evaluer_reponse(question: str, reponse_attendue: str, reponse_etudiant: str, model: str | None = None) -> str:
    """Evaluate a student's answer against the expected answer and provide pedagogical feedback."""
    prompt = f"""Compare la réponse de l'étudiant à la réponse attendue.

Question: {question}
Réponse attendue: {reponse_attendue}
Réponse de l'étudiant: {reponse_etudiant}

Donne un feedback pédagogique: ce qui est correct, ce qui manque, et une note sur 5.
Sois encourageant mais précis."""
    return await chat(prompt, model=model)


async def interroger_sur_document(contenu: str, question: str) -> str:
    """Ask Ollama a question about a specific document content."""
    prompt = f"""Voici un extrait de document de cours:

{contenu[:3000]}

Question de l'étudiant: {question}

Réponds de manière pédagogique en te basant sur le document."""

    return await chat(prompt)


async def check_disponible() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_host}/api/tags")
            return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False
