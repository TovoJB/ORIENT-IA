import pytest

from services import ml_rf_explorer, ml_service


def test_explorer_structure():
    result = ml_rf_explorer.explorer()
    assert result["train"]["n_samples"] >= ml_service.MIN_SAMPLES
    assert result["train"]["n_features"] > 0
    assert result["train"]["duree_s"] >= 0
    assert {"accuracy", "log_loss", "precision_macro", "recall_macro", "f1_macro"} <= set(
        result["metriques"]
    )
    assert result["feature_importances"], "importances non vides"
    assert all("feature" in f and "importance" in f for f in result["feature_importances"])
    assert result["modele"]["nom"] in ("rf", "lr")
    assert result["prediction"] is None  # pas de profil fourni


def test_explorer_aucun_profil_pas_de_prediction():
    result = ml_rf_explorer.explorer(None)
    assert result["prediction"] is None


def test_explorer_prediction():
    profil = {
        "serie_bac": "s",
        "matiere_mathematiques": "1",
        "matiere_informatique": "1",
        "competence_programmation": "1",
        "prerequis_bases_algo": "1",
        "metier_vise": "data_scientist",
    }
    result = ml_rf_explorer.explorer(profil)
    prediction = result["prediction"]
    assert prediction is not None
    assert isinstance(prediction["parcours"], str) and prediction["parcours"]
    assert prediction["confidence"] > 0
    assert prediction["probabilities"]
    assert abs(sum(prediction["probabilities"].values()) - 1.0) < 1e-6


def test_explorer_metriques_valides():
    result = ml_rf_explorer.explorer()
    metriques = result["metriques"]
    for key in ("accuracy", "precision_macro", "recall_macro", "f1_macro"):
        assert 0 <= metriques[key] <= 1


def test_explorer_sans_modele(monkeypatch):
    def _raise():
        raise RuntimeError("Aucun modèle entraîné.")

    monkeypatch.setattr(ml_service, "_load_payload", _raise)
    with pytest.raises(RuntimeError):
        ml_rf_explorer.explorer()
