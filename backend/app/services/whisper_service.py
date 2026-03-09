import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

# Lazy-loaded model; None until first successful load.
_model = None

# Cached availability flag (set on first check, avoids repeated import attempts).
_whisper_available: bool | None = None


def _ensure_ffmpeg_binary() -> None:
    """Ensure an ffmpeg binary is discoverable for whisper."""
    if shutil.which("ffmpeg"):
        return

    try:
        import imageio_ffmpeg

        ffmpeg_path = Path(imageio_ffmpeg.get_ffmpeg_exe())
        shim_dir = Path(tempfile.gettempdir()) / "iaca-ffmpeg-bin"
        shim_dir.mkdir(parents=True, exist_ok=True)
        shim_path = shim_dir / "ffmpeg"

        if not shim_path.exists():
            try:
                shim_path.symlink_to(ffmpeg_path)
            except OSError:
                shutil.copy2(ffmpeg_path, shim_path)
            shim_path.chmod(0o755)

        current_path = os.environ.get("PATH", "")
        shim_dir_str = str(shim_dir)
        if shim_dir_str not in current_path.split(os.pathsep):
            os.environ["PATH"] = (
                f"{shim_dir_str}{os.pathsep}{current_path}" if current_path else shim_dir_str
            )
    except Exception as exc:
        logger.warning(f"FFmpeg indisponible pour Whisper: {exc}")


def check_disponible() -> bool:
    """Return True if the whisper module and model can be loaded."""
    global _whisper_available
    if _whisper_available is not None:
        return _whisper_available
    _ensure_ffmpeg_binary()
    try:
        import whisper  # noqa: F401
        _whisper_available = True
    except ModuleNotFoundError:
        logger.warning(
            "Module 'whisper' introuvable. "
            "Installez-le avec: pip install openai-whisper  "
            "(torch sera installé automatiquement)."
        )
        _whisper_available = False
    return _whisper_available


def _get_model():
    global _model
    if _model is None:
        if not check_disponible():
            raise RuntimeError(
                "Whisper non disponible — installez openai-whisper: "
                "pip install openai-whisper"
            )
        import whisper
        logger.info(f"Chargement modèle Whisper '{settings.whisper_model}'…")
        _model = whisper.load_model(settings.whisper_model)
        logger.info("Modèle Whisper chargé.")
    return _model


async def transcrire(audio_bytes: bytes, language: str = "fr") -> str:
    """Transcribe audio bytes to text using Whisper.

    Raises RuntimeError with a clear message if whisper is not installed,
    so the WS handler can forward a JSON error without dropping the session.
    """
    if not check_disponible():
        raise RuntimeError(
            "Transcription audio indisponible: module whisper manquant. "
            "Installez-le avec: pip install openai-whisper"
        )
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        result = await asyncio.to_thread(_transcrire_sync, tmp_path, language)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return result


def _transcrire_sync(file_path: str, language: str) -> str:
    model = _get_model()
    result = model.transcribe(file_path, language=language)
    return result["text"].strip()


async def transcrire_fichier(file_path: str, language: str = "fr") -> str:
    """Transcribe an audio file to text."""
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    if not check_disponible():
        raise RuntimeError(
            "Transcription audio indisponible: module whisper manquant. "
            "Installez-le avec: pip install openai-whisper"
        )
    return await asyncio.to_thread(_transcrire_sync, file_path, language)
