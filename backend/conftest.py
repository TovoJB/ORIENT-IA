import pytest

from config import config

# Les tests ne doivent ni créer ni dépendre du vrai fichier clinique.db :
# on bascule sur une base SQLite en mémoire.
config.DB_PATH = ":memory:"

from services.ml_service import train  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def trained_model(tmp_path_factory):
    """Train a model in a temp file so tests never depend on the repo state."""
    model_path = tmp_path_factory.mktemp("ml") / "model.joblib"
    config.ML_MODEL_PATH = str(model_path)
    train()
    return model_path
