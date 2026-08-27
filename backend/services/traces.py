"""Traçabilité (observabilité) : chaque étape du système est journalisée.

Exigence du sujet : le système doit être *observable*. Chaque étape
(question RAG, filtrage Prolog, prédiction ML, refus, tour de chat) écrit
une entrée horodatée dans la table `traces` de SQLite, consultable via
GET /traces/{id} et GET /traces?session_id=...
"""

import json
import sqlite3
import time

from config import config


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS traces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            step TEXT NOT NULL,
            detail TEXT,
            created_at REAL NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def trace(step: str, session_id: str | None, detail: dict | None = None) -> int:
    """Journalise une étape et renvoie son identifiant."""
    conn = _connect()
    cursor = conn.execute(
        "INSERT INTO traces (session_id, step, detail, created_at) VALUES (?, ?, ?, ?)",
        (session_id, step, json.dumps(detail, ensure_ascii=False, default=str),
         time.time()),
    )
    conn.commit()
    trace_id = int(cursor.lastrowid)
    conn.close()
    return trace_id


def get_trace(trace_id: int) -> dict | None:
    conn = _connect()
    row = conn.execute(
        "SELECT id, session_id, step, detail, created_at FROM traces WHERE id = ?",
        (trace_id,),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return {
        "id": row[0],
        "session_id": row[1],
        "step": row[2],
        "detail": json.loads(row[3]) if row[3] else None,
        "created_at": row[4],
    }


def list_traces(session_id: str | None = None, limit: int = 200) -> list[dict]:
    conn = _connect()
    if session_id:
        rows = conn.execute(
            "SELECT id, session_id, step, detail, created_at FROM traces "
            "WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, session_id, step, detail, created_at FROM traces "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "session_id": row[1],
            "step": row[2],
            "detail": json.loads(row[3]) if row[3] else None,
            "created_at": row[4],
        }
        for row in rows
    ]
