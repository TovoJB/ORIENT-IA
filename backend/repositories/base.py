from abc import ABC, abstractmethod

from domain.entities import Conversation


class ConversationRepository(ABC):
    """Contrat commun : le reste du code dépend de cette interface,
    pas d'une implémentation précise (mémoire ou SQLite)."""

    @abstractmethod
    def create(self) -> Conversation:
        ...

    @abstractmethod
    def get(self, conversation_id: str) -> Conversation | None:
        ...

    @abstractmethod
    def add_message(
        self, conversation_id: str | None, role: str, content: str
    ) -> Conversation:
        ...

    @abstractmethod
    def health_check(self) -> bool:
        ...
