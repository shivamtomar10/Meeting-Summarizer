# 🎙️ Meeting Summarizer

Transcribe meeting audio and generate action-oriented summaries — key decisions,
discussion highlights, and action items — from a single uploaded audio file.

## Objective

Given a meeting audio recording, this app:
1. Transcribes the audio to text (ASR).
2. Sends the transcript to an LLM to generate a structured summary:
   key decisions, discussion points, and action items with owners (when identifiable).
3. Returns the transcript + summary as JSON, viewable in a simple web frontend.

## Architecture

```
meeting-summarizer/
├── backend/
│   ├── main.py            # FastAPI app — /upload, /meetings, /health endpoints
│   ├── transcription.py   # ASR — local faster-whisper (no API key, no cost)
│   ├── summarizer.py      # LLM summary generation via Groq's free API
│   ├── database.py        # SQLite persistence — stores every processed meeting
│   ├── models.py          # Pydantic response models
│   └── config.py          # Env/config loading
├── frontend/
│   └── index.html         # Upload audio, view transcript + summary
├── sample_data/
│   └── README.md          # Where to place a sample meeting audio file for testing
├── requirements.txt
├── .gitignore
└── README.md
```

## Tech Stack

- **Backend:** Python 3.10+, FastAPI, Uvicorn
- **ASR:** [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — runs the Whisper model **locally**, free, no API key
- **LLM:** [Groq](https://console.groq.com/) (`llama-3.1-8b-instant`) via an OpenAI-compatible endpoint — free tier, no credit card required
- **Frontend:** Plain HTML/CSS/JS (no build step, no framework — keeps the repo dependency-free per submission guidelines)

> Both the ASR and the LLM are free to run: Whisper transcription happens
> entirely on your machine, and Groq's free tier (no credit card) is enough
> for demo/grading use.

## Setup

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd meeting-summarizer
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

The first run downloads the local Whisper model weights (cached afterward),
so the first transcription will be slower than later ones.

### 2. Configure your (free) Groq API key

Create a `.env` file in the project root (this file is git-ignored and must
**never** be committed):

```
GROQ_API_KEY=gsk-your-key-here
```

Get a free key (no credit card needed) at https://console.groq.com/keys —
sign-up takes under a minute.

### 3. Run the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

The API will be live at `http://localhost:8000`. Interactive docs at
`http://localhost:8000/docs`.

### 4. Open the frontend

Simply open `frontend/index.html` in a browser (or serve it with any static
server). Upload a `.mp3`/`.wav`/`.m4a` meeting recording and view the
transcript, key decisions, and action items.

## API

### `POST /upload`

**Form-data:** `file` — the audio file (mp3, wav, m4a, mp4)

**Response:**
```json
{
  "transcript": "Full meeting transcript...",
  "summary": "2-3 sentence overview of the meeting...",
  "key_decisions": ["Decision 1", "Decision 2"],
  "action_items": [
    {"task": "Send updated proposal", "owner": "Priya", "due": "Friday"},
    {"task": "Review budget draft", "owner": "Unassigned", "due": null}
  ]
}
```

Every processed meeting is also saved to a local SQLite database
(`data/meetings.db`, created automatically on first run) so it can be
retrieved later without re-running ASR/LLM on the same audio.

### `GET /meetings`

Returns a list of every previously processed meeting (id, filename,
timestamp, and summary — not the full transcript):

```json
[
  {"id": 2, "filename": "client_sync.wav", "created_at": "2026-08-20T08:37:01Z", "summary": "..."},
  {"id": 1, "filename": "standup.mp3", "created_at": "2026-08-20T08:30:00Z", "summary": "..."}
]
```

### `GET /meetings/{id}`

Returns the full stored record (transcript, summary, key decisions, action
items) for one meeting. Returns `404` if the id doesn't exist.

### `GET /health`

Simple liveness check — returns `{"status": "ok"}`.

## LLM Prompting Approach

The transcript is passed to the LLM with an instruction to extract:
- A short overview summary
- Key decisions made during the meeting
- Action items, each with an owner and due date **if mentioned**, otherwise
  marked `null`/`"Unassigned"`

The model is asked to return **strict JSON** so the backend can parse it
reliably without brittle text parsing. See `backend/summarizer.py` for the
exact prompt template.

## Testing With Sample Audio

Place any short `.mp3`/`.wav` meeting recording (even a 1–2 minute voice memo
works) in `sample_data/` and upload it via the frontend or `curl`:

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@sample_data/your_sample.mp3"
```

## Notes on Submission Hygiene

This repo intentionally excludes (see `.gitignore`):
- `venv/`, `__pycache__/` — environment/build artifacts
- `.env` — secrets (API key)
- `.vscode/`, `.idea/` — editor-specific files
- `data/` — the local SQLite database, generated at runtime, not source code

Only the minimal dependencies required for ASR + LLM summarization + the API
server are listed in `requirements.txt`.

## Evaluation Focus Checklist

- ✅ **Transcription accuracy** — local Whisper via `faster-whisper`
- ✅ **Summary quality** — structured JSON output: overview, decisions, action items
- ✅ **LLM prompt effectiveness** — explicit, strict-JSON prompt in `summarizer.py`
- ✅ **Code structure** — separated concerns (transcription / summarization / storage / API / config)
- ✅ **Backend storage** — every processed meeting persists to SQLite (`backend/database.py`), retrievable via `GET /meetings`

## Demo Video

https://github.com/user-attachments/assets/3b861a5c-63a4-4ac6-9f31-15ef7cec5dd1





