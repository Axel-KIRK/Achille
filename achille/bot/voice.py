"""
Achille — Voice Transcription
Transcription via OpenAI Whisper API.
"""
import os
from pathlib import Path
from openai import OpenAI


def _get_client() -> OpenAI:
    """Create OpenAI client on demand (reads current env var)."""
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise ValueError("OPENAI_API_KEY not set")
    return OpenAI(api_key=key)


async def transcribe(audio_path: Path) -> str:
    """Transcrit un fichier audio via Whisper API."""
    try:
        client = _get_client()
        with open(audio_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="fr",
            )
        return response.text
    except Exception as e:
        print(f"[whisper error] {type(e).__name__}: {e}")
        return ""
