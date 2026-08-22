"""
Meeting Summarizer — FastAPI backend.

Endpoints:
    POST /upload        — upload meeting audio, get transcript + summary + action items
    GET  /meetings      — list all past meetings
    GET  /meetings/{id} — fetch one meeting's full record
    GET  /health        — liveness check
"""

import os
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import config, database
from .transcription import transcribe_audio
from .summarizer import generate_summary
from .models import MeetingSummaryResponse, MeetingListItem, HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure the SQLite database and table exist before serving requests."""
    database.init_db()
    yield


app = FastAPI(
    title="Meeting Summarizer API",
    description="Transcribe meeting audio and generate action-oriented summaries.",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the local frontend (opened as a file:// page or a static server) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm"}


@app.get("/health", response_model=HealthResponse)
def health() -> dict:
    return {"status": "ok"}


@app.post("/upload", response_model=MeetingSummaryResponse)
async def upload_meeting_audio(file: UploadFile = File(...)) -> dict:
    """
    Accepts a meeting audio file, transcribes it, and returns a structured
    summary with key decisions and action items.
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    contents = await file.read()
    if len(contents) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 25MB limit.")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Whisper's API needs a file path/handle, so write to a temp file.
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        transcript = transcribe_audio(tmp_path)
        if not transcript:
            raise HTTPException(status_code=422, detail="Transcription returned no text.")

        summary_data = generate_summary(transcript)

        # Persist the processed meeting so it can be listed/retrieved later
        # without re-running ASR + LLM on the same audio.
        meeting_id = database.save_meeting(
            filename=file.filename or "unknown",
            transcript=transcript,
            summary=summary_data["summary"],
            key_decisions=summary_data["key_decisions"],
            action_items=summary_data["action_items"],
        )
        record = database.get_meeting(meeting_id)

        return record
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 — surface a clean error to the client
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}") from exc
    finally:
        os.unlink(tmp_path)


@app.get("/meetings", response_model=list[MeetingListItem])
def get_meetings() -> list:
    """List all previously processed meetings, newest first (summary only, no full transcript)."""
    return database.list_meetings()


@app.get("/meetings/{meeting_id}", response_model=MeetingSummaryResponse)
def get_meeting_detail(meeting_id: int) -> dict:
    """Fetch the full stored record — transcript, summary, decisions, action items — for one meeting."""
    record = database.get_meeting(meeting_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No meeting found with id {meeting_id}")
    return record