from fastapi.testclient import TestClient

from api.routes import llm_service
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_predict_returns_prediction():
    response = client.post("/predict", json={"features": [5.1, 3.5, 1.4, 0.2]})
    assert response.status_code == 200
    data = response.json()
    assert {"prediction", "class_name", "probabilities"} <= set(data)


def test_predict_rejects_empty_features():
    response = client.post("/predict", json={"features": []})
    assert response.status_code == 422


def test_chat_uses_llm_service(monkeypatch):
    monkeypatch.setattr(
        llm_service, "ask_gemini", lambda *args, **kwargs: "Réponse de test"
    )
    response = client.post("/chat", json={"message": "bonjour", "history": []})
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "Réponse de test"
    assert data["conversation_id"]


def test_chat_requires_message():
    response = client.post("/chat", json={"history": []})
    assert response.status_code == 422
