from config import config
from repositories.base import ConversationRepository
from repositories.in_memory_repository import InMemoryConversationRepository
from repositories.sqlite_repository import SQLiteConversationRepository


def build_repository() -> ConversationRepository:
    """Choisit le stockage selon la configuration :
    - une base SQLite si DB_PATH est défini (défaut),
    - sinon un stockage en mémoire.
    """
    if config.DB_PATH:
        return SQLiteConversationRepository(config.DB_PATH)
    return InMemoryConversationRepository()


conversation_repository = build_repository()
