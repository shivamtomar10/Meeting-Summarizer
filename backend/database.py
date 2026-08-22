"""
Lightweight persistence layer.

Stores each processed meeting (transcript + summary + decisions + action
items) in a local SQLite database so past meetings can be listed and
retrieved without re-processing audio. Uses only Python's built-in `sqlite3`
— no extra dependency, keeping the project's package footprint minimal per
the submission guidelines.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "meetings.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meetings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    filename      TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    transcript    TEXT NOT NULL,
    summary       TEXT NOT NULL,
    key_decisions TEXT NOT NULL,   -- JSON-encoded list[str]
    action_items  TEXT NOT NULL    -- JSON-encoded list[dict]
);
"""


@contextmanager
def _connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create the meetings table if it doesn't already exist. Call on startup."""
    with _connection() as conn:
        conn.execute(SCHEMA)


def save_meeting(
    filename: str,
    transcript: str,
    summary: str,
    key_decisions: list,
    action_items: list,
) -> int:
    """Persist a processed meeting record. Returns the new record's id."""
    with _connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO meetings (filename, created_at, transcript, summary, key_decisions, action_items)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                filename,
                datetime.now(timezone.utc).isoformat(),
                transcript,
                summary,
                json.dumps(key_decisions),
                json.dumps(action_items),
            ),
        )
        return cursor.lastrowid


def list_meetings() -> list:
    """Return a lightweight list of all stored meetings (no full transcript), newest first."""
    with _connection() as conn:
        rows = conn.execute(
            "SELECT id, filename, created_at, summary FROM meetings ORDER BY id DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def get_meeting(meeting_id: int) -> Optional[dict]:
    """Return the full record for a single meeting, or None if not found."""
    with _connection() as conn:
        row = conn.execute(
            "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
        ).fetchone()
        if row is None:
            return None
        record = dict(row)
        record["key_decisions"] = json.loads(record["key_decisions"])
        record["action_items"] = json.loads(record["action_items"])
        return record