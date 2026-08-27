from config import config
from services import llm_service


def test_ask_gemini_without_key_returns_error(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    reply = llm_service.ask_gemini("hello")
    assert "Erreur" in reply


def test_ask_gemini_catches_api_error(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "fake-key")

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        @property
        def models(self):
            raise RuntimeError("API indisponible (simulation)")

    monkeypatch.setattr(llm_service, "_get_client", lambda: _FakeClient())
    reply = llm_service.ask_gemini("hello")
    assert "Erreur Gemini" in reply


def test_gemini_disponible(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    assert llm_service.gemini_disponible() is False
    monkeypatch.setattr(config, "GEMINI_API_KEY", "x")
    assert llm_service.gemini_disponible() is True
