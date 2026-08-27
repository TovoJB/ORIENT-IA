import pandas as pd
import pytest

from config import config
from services import ml_features, ml_service


def test_train_requires_min_samples(tmp_path, monkeypatch):
    small = tmp_path / "small.csv"
    pd.DataFrame(
        {"parcours_choisi": ["isaia", "iggia", "iggia", "isaia"]}
    ).to_csv(small, index=False)
    monkeypatch.setattr(config, "DATASET_PATH", str(small))
    with pytest.raises(ml_service.NotEnoughDataError):
        ml_service.train()


def test_train_and_predict(monkeypatch):
    monkeypatch.setattr(config, "ML_MODEL_PATH", "/tmp/orientia_test_model2.joblib")
    report = ml_service.train()
    assert report["model_choisi"] in ("rf", "lr")
    assert "metriques" in report
    assert report["metriques"]["baseline"]["accuracy"] <= report["metriques"]["rf"]["accuracy"]

    profil = {
        "serie_bac": "s",
        "environnement": "bureau",
        "note_mathematiques": "16",
        "note_spc": "15",
        "note_svt": "12",
        "note_francais": "11",
        "note_malagasy": "12",
        "note_langue_vivante": "11",
        "note_hg": "10",
        "note_philosophie": "10",
        "note_ses": "",
        "moyenne_generale": "4",
        "mention_diplome": "3",
        "matiere_mathematiques": "1",
        "matiere_informatique": "1",
        "competence_programmation": "1",
        "competence_logique": "1",
        "interet_technologie": "1",
        "interet_science": "1",
        "prerequis_bases_algo": "1",
        "prerequis_maths_avancees": "1",
        "metier_vise": "data_scientist",
    }
    result = ml_service.predict(profil)
    assert result["parcours"] == "isaia"
    assert result["probabilities"], "probabilités non vides"


def test_predict_without_model(monkeypatch):
    monkeypatch.setattr(config, "ML_MODEL_PATH", "does_not_exist.joblib")
    with pytest.raises(RuntimeError):
        ml_service.predict({"serie_bac": "s"})


def test_features_sparse_profil():
    """Un profil partiel (beaucoup de colonnes absentes) doit produire un vecteur."""
    vector = ml_features.profil_to_vector({"serie_bac": "ose"})
    assert len(vector) == len(ml_features.feature_names())
