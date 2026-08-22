"""
LLM-based summary generation.

Sends the meeting transcript to an LLM (via Groq's free-tier API) and asks
for a strict-JSON response containing an overview summary, key decisions,
and action items. Strict JSON output avoids brittle regex/text parsing of
free-form model output.

Groq exposes an OpenAI-compatible endpoint, so we reuse the `openai` Python
client and just point it at Groq's base URL — no separate SDK needed.
"""

import json
from openai import OpenAI
from . import config

_client: OpenAI | None = None

SYSTEM_PROMPT = """You are an expert meeting-notes assistant. You read raw \
meeting transcripts and extract a clear, action-oriented summary.

Respond with ONLY valid JSON (no markdown fences, no extra text) matching \
exactly this schema:

{
  "summary": "2-3 sentence high-level overview of the meeting",
  "key_decisions": ["decision 1", "decision 2", ...],
  "action_items": [
    {"task": "...", "owner": "name or 'Unassigned'", "due": "date/deadline or null"}
  ]
}

Rules:
- Only include decisions that were explicitly made, not general discussion.
- Only include action items that were explicitly assigned or clearly implied as next steps.
- If no owner is mentioned for a task, set "owner" to "Unassigned".
- If no due date is mentioned, set "due" to null.
- Keep the summary concise and factual — do not invent information not in the transcript.
"""

USER_PROMPT_TEMPLATE = (
    "Summarize this meeting transcript into key decisions and action items.\n\n"
    "Transcript:\n{transcript}"
)


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        config.require_api_key()
        # Groq's API is OpenAI-compatible — same client, different base_url.
        _client = OpenAI(
            api_key=config.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
    return _client


def generate_summary(transcript: str) -> dict:
    """
    Generate a structured summary from a meeting transcript.

    Args:
        transcript: The full meeting transcript text.

    Returns:
        A dict with keys: summary (str), key_decisions (list[str]),
        action_items (list[dict]).
    """
    client = _get_client()

    response = client.chat.completions.create(
        model=config.SUMMARY_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(transcript=transcript)},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"LLM returned non-JSON output. Response was: {raw[:200]!r}"
        ) from exc

    # Defensive defaults in case the model omits a field.
    data.setdefault("summary", "")
    data.setdefault("key_decisions", [])
    data.setdefault("action_items", [])

    return data