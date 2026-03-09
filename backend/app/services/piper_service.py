import asyncio
import tempfile
from pathlib import Path

from app.config import settings


async def synthetiser(texte: str) -> bytes:
    """Synthesize text to speech using Piper TTS. Returns WAV audio bytes."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        process = await asyncio.create_subprocess_exec(
            "piper",
            "--model", settings.piper_voice,
            "--output_file", tmp_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate(input=texte.encode())
        if process.returncode != 0:
            raise RuntimeError(f"Piper TTS error: {stderr.decode()}")
        return Path(tmp_path).read_bytes()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


async def synthetiser_fichier(texte: str, output_path: str) -> str:
    """Synthesize text to speech and save to file."""
    audio_bytes = await synthetiser(texte)
    Path(output_path).write_bytes(audio_bytes)
    return output_path


async def check_disponible() -> bool:
    """Check if Piper TTS is installed and accessible."""
    try:
        process = await asyncio.create_subprocess_exec(
            "piper", "--help",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()
        return process.returncode == 0
    except FileNotFoundError:
        return False
