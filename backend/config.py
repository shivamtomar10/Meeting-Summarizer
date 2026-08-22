"""
Configuration loading for the Meeting Summarizer backend.

Reads settings from environment variables (via a local .env file during
development).

ASR runs 100% locally via faster-whisper (no API key, no cost).
Summarization uses Groq's free-tier API (OpenAI-compatible, no cost within
free-tier limits) — get a free key at https://console.groq.com/keys.
Never hard-code API keys — set GROQ_API_KEY in your .env.
"""

import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Local ASR model size (faster-whisper). Options: tiny, base, small, medium,
# large-v3 — bigger = more accurate but slower/more RAM. "base" is a good
# default for CPU-only machines.
ASR_MODEL = os.getenv("ASR_MODEL", "base")

# Groq chat model used for summarization. Groq deprecated llama-3.1-8b-instant
# (shut down Aug 16, 2026); openai/gpt-oss-20b is Groq's recommended free-tier
# replacement — same speed/cost tier. Check https://console.groq.com/docs/models
# if this ever 404s again, since Groq's free-tier lineup changes periodically.
SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", "openai/gpt-oss-20b")

# Max upload size (bytes).
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def require_api_key() -> None:
    """Raise a clear error early if no Groq API key is configured."""
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Create a .env file in the project "
            "root with: GROQ_API_KEY=gsk-your-key-here\n"
            "Get a free key (no credit card) at https://console.groq.com/keys"
        )