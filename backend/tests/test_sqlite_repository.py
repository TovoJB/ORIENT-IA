import pytest

from repositories.sqlite_repository import SQLiteConversationRepository


@pytest.fixture
def repo():
    return SQLiteConversationRepository(":memory:")


def test_create_and_get(repo):
    conversation = repo.create()
    assert conversation.id
    assert repo.get(conversation.id) is not None


def test_add_message_creates_conversation_when_missing(repo):
    conversation = repo.add_message(None, "user", "Bonjour")
    assert conversation.id
    got = repo.get(conversation.id)
    assert got is not None
    assert len(got.messages) == 1
    assert got.messages[0].role == "user"
    assert got.messages[0].content == "Bonjour"


def test_add_message_appends_to_existing_conversation(repo):
    conversation = repo.add_message(None, "user", "Bonjour")
    repo.add_message(conversation.id, "assistant", "Salut !")
    got = repo.get(conversation.id)
    assert len(got.messages) == 2
    assert got.messages[1].role == "assistant"


def test_health_check(repo):
    assert repo.health_check() is True
