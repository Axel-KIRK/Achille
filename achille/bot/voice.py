"""
Achille — Voice Transcription
Transcription via OpenAI Whisper API.
"""
from pathlib import Path
from openai import OpenAI
from config.settings import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


async def transcribe(audio_path: Path) -> str:
    """Transcrit un fichier audio via Whisper API."""
    try:
        with open(audio_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="fr",
            )
        return response.text
    except Exception as e:
        print(f"[whisper error] {e}")
        return ""
