"""
ASR (Automatic Speech Recognition) integration.

Uses the OpenAI Whisper API to transcribe meeting audio to text. Swap this
module out for Azure Speech or Google Speech-to-Text if preferred — the rest
of the app only depends on `transcribe_audio(file_path) -> str`.
"""

import os

from openai import OpenAI
from . import config

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        config.require_api_key()
        _client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _client


# Map file extensions to MIME types expected by the Whisper API.
_MIME_TYPES = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".mp4": "video/mp4",
    ".mpeg": "audio/mpeg",
    ".mpga": "audio/mpeg",
    ".webm": "audio/webm",
}


def transcribe_audio(file_path: str) -> str:
    if config.OPENAI_API_KEY == 'sk-mock-key':
        import time; time.sleep(2)
        return 'This is a mock transcript. Alice: We discussed the Q4 roadmap and decided to launch the new feature next month. Bob: I will prepare the slide deck by Friday.'
    """
    Transcribe an audio file to plain text using OpenAI's Whisper API.

    Args:
        file_path: Path to a local audio file (mp3, wav, m4a, mp4, etc.)

    Returns:
        The full transcript as a string.
    """
    client = _get_client()
    ext = os.path.splitext(file_path)[1].lower()
    mime_type = _MIME_TYPES.get(ext, "application/octet-stream")
    filename = os.path.basename(file_path)

    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model=config.ASR_MODEL,
            file=(filename, audio_file, mime_type),
        )

    return transcript.text.strip()
