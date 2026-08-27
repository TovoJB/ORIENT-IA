import pytest

from config import config

# Tests : base SQLite temporaire (jamais backend/clinique.db) + modèle entraîné.
# Le singleton de repository est construit à l'import de main, donc DB_PATH
# doit être fixé ici, au niveau module, avant tout import des tests.
TEST_DB_PATH = "/tmp/orientia_test_clinique.db"
TEST_MODEL_PATH = "/tmp/orientia_test_model.joblib"

config.DB_PATH = TEST_DB_PATH
config.ML_MODEL_PATH = TEST_MODEL_PATH

import services.ml_service as ml_service  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_inspection():
    """Chaque test part avec le mode inspection désactivé."""
    from services.inspection import state

    state.mode = False
    state.force_prolog = False
    yield
    state.mode = False
    state.force_prolog = False


@pytest.fixture(scope="session", autouse=True)
def trained_model():
    """Entraîne le modèle ML sur le jeu synthétique pour les tests qui en ont besoin."""
    ml_service.train()
    yield
    import os

    for path in (TEST_DB_PATH, TEST_MODEL_PATH):
        if os.path.exists(path):
            os.remove(path)
