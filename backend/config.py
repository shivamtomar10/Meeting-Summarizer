"""
Configuration loading for the Meeting Summarizer backend.

Reads settings from environment variables (via a local .env file during
development). Never hard-code API keys — set OPENAI_API_KEY in your .env.
"""

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Model configuration — override via env vars if you want to swap models.
ASR_MODEL = os.getenv("ASR_MODEL", "whisper-1")
SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", "gpt-4o-mini")

# Max upload size (bytes) — OpenAI Whisper API caps individual files at 25MB.
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def require_api_key() -> None:
    """Raise a clear error early if no API key is configured."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Create a .env file in the project "
            "root with: OPENAI_API_KEY=sk-your-key-here"
        )
