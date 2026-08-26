import sqlite3
from datetime import datetime

from domain.entities import Conversation, Message
from repositories.base import ConversationRepository
from utils.helpers import generate_id


class SQLiteConversationRepository(ConversationRepository):
    """Conversations persistées dans une base SQLite (fichier clinique.db).

    Les données survivent au redémarrage du serveur.
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
            """
        )
        self._conn.commit()

    def _conversation_exists(self, conversation_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        return row is not None

    def create(self) -> Conversation:
        conversation = Conversation(id=generate_id())
        self._conn.execute(
            "INSERT INTO conversations (id, created_at) VALUES (?, ?)",
            (conversation.id, datetime.now().isoformat()),
        )
        self._conn.commit()
        return conversation

    def get(self, conversation_id: str) -> Conversation | None:
        row = self._conn.execute(
            "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if row is None:
            return None
        messages = [
            Message(
                role=m["role"],
                content=m["content"],
                timestamp=datetime.fromisoformat(m["timestamp"]),
            )
            for m in self._conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY id",
                (conversation_id,),
            )
        ]
        return Conversation(id=row["id"], messages=messages)

    def add_message(
        self, conversation_id: str | None, role: str, content: str
    ) -> Conversation:
        conversation_id = conversation_id or generate_id()
        if not self._conversation_exists(conversation_id):
            self._conn.execute(
                "INSERT INTO conversations (id, created_at) VALUES (?, ?)",
                (conversation_id, datetime.now().isoformat()),
            )
        self._conn.execute(
            "INSERT INTO messages (conversation_id, role, content, timestamp) "
            "VALUES (?, ?, ?, ?)",
            (conversation_id, role, content, datetime.now().isoformat()),
        )
        self._conn.commit()
        return Conversation(id=conversation_id)

    def health_check(self) -> bool:
        try:
            self._conn.execute("SELECT 1").fetchone()
            return True
        except sqlite3.Error:
            return False
