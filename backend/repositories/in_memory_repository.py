from domain.entities import Conversation, Message
from repositories.base import ConversationRepository
from utils.helpers import generate_id


class InMemoryConversationRepository(ConversationRepository):
    """Stockage en mémoire (perdu à l'arrêt du serveur).
    Utile pour les tests ou un démarrage ultra-rapide."""

    def __init__(self) -> None:
        self._store: dict[str, Conversation] = {}

    def create(self) -> Conversation:
        conversation = Conversation(id=generate_id())
        self._store[conversation.id] = conversation
        return conversation

    def get(self, conversation_id: str) -> Conversation | None:
        return self._store.get(conversation_id)

    def add_message(
        self, conversation_id: str | None, role: str, content: str
    ) -> Conversation:
        conversation = self.get(conversation_id) if conversation_id else None
        if conversation is None:
            conversation = self.create()
        conversation.messages.append(Message(role=role, content=content))
        return conversation

    def health_check(self) -> bool:
        return True
