"""
Query History & API Module (storage half)
--------------------------------------------
Logs every query, its retrieved sources, and the generated response to
SQLite -- enough for a prototype's auditable trail. Swap for PostgreSQL
in production by pointing SQLAlchemy at a Postgres URL instead; the
schema stays identical.
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS query_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    query TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources TEXT NOT NULL,
    grounded INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
"""


@contextmanager
def _conn():
    conn = sqlite3.connect(settings.sqlite_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _conn() as conn:
        conn.execute(SCHEMA)


def log_query(session_id: str, query: str, answer: str, sources: list[dict], grounded: bool):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO query_history (session_id, query, answer, sources, grounded, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                session_id,
                query,
                answer,
                json.dumps(sources),
                int(grounded),
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def get_history(session_id: str, limit: int = 50) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM query_history WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
