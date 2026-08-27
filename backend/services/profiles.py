"""Stockage du profil utilisateur en cours de construction (par session).

Le profil se remplit au fil de la conversation (outil enregistrer_profil).
Persisté en JSON dans SQLite : table `profiles`.
"""

import json
import sqlite3
import time

from config import config


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS profiles (
            session_id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            updated_at REAL NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def get_profile(session_id: str) -> dict:
    conn = _connect()
    row = conn.execute(
        "SELECT data FROM profiles WHERE session_id = ?", (session_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return {}
    return json.loads(row[0])


def set_profile(session_id: str, data: dict) -> dict:
    conn = _connect()
    conn.execute(
        "INSERT OR REPLACE INTO profiles (session_id, data, updated_at) VALUES (?, ?, ?)",
        (session_id, json.dumps(data, ensure_ascii=False), time.time()),
    )
    conn.commit()
    conn.close()
    return data


def merge_profile(session_id: str, updates: dict) -> dict:
    """Fusionne les champs `updates` dans le profil de la session."""
    profil = get_profile(session_id)
    profil.update(updates)
    return set_profile(session_id, profil)
