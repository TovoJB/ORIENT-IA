from config import config
from services.ml_service import predict, train


def test_train_and_predict_roundtrip():
    result = train()
    assert "accuracy" in result

    prediction = predict([5.1, 3.5, 1.4, 0.2])
    assert prediction["prediction"] in (0, 1, 2)
    assert len(prediction["probabilities"]) == 3


def test_predict_without_model_raises(monkeypatch):
    monkeypatch.setattr(config, "ML_MODEL_PATH", "does_not_exist.joblib")
    try:
        predict([1.0, 2.0, 3.0, 4.0])
    except RuntimeError:
        return
    raise AssertionError("predict() should raise RuntimeError without a model")
