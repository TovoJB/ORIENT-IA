from config import config
from services import llm_service


def test_ask_gemini_without_key_returns_error(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    reply = llm_service.ask_gemini("hello")
    assert "Erreur" in reply


def test_ask_gemini_with_bad_key_returns_error(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "invalid-key")
    reply = llm_service.ask_gemini("hello")
    assert "Erreur Gemini" in reply
