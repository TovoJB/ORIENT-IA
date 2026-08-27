"""Machine Learning ORIENT'IA -- démarche scientifique (Phase 2 du sujet).

- baseline simple (classe majoritaire) pour comparer,
- comparaison d'au moins 2 modèles : RandomForest vs LogisticRegression,
- split train/test stratifié,
- métriques sérieuses : accuracy, log-loss, rapport de classification,
  matrice de confusion,
- analyse d'erreurs et de biais (fournie via `rapport_biais` et les notebooks).

Règle de robustesse : si le jeu de données est trop petit (< MIN_SAMPLES),
`train()` lève NotEnoughDataError et l'agent bascule en mode règles seules.
Le modèle est intégré à l'agent comme outil (`predict`), pas dans un notebook.
"""

import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    log_loss,
)
from sklearn.model_selection import train_test_split

from config import config
from services import ml_features

MIN_SAMPLES = 30
CIBLE = "parcours_choisi"


class NotEnoughDataError(RuntimeError):
    """Levée quand le jeu de données est trop petit pour un entraînement sérieux."""


def load_dataset(path: str | None = None) -> pd.DataFrame:
    path = path or config.DATASET_PATH
    if not Path(path).exists():
        raise FileNotFoundError(f"Jeu de données introuvable : {path}")
    return pd.read_csv(path, encoding="utf-8")


def _impute(x: np.ndarray) -> np.ndarray:
    return SimpleImputer(strategy="median").fit_transform(x)


def train(path: str | None = None) -> dict:
    """Entraîne RF + LR, compare à la baseline, sauvegarde le meilleur modèle.

    Retourne un rapport complet (métriques par modèle + modèle retenu).
    """
    df = load_dataset(path)
    if len(df) < MIN_SAMPLES:
        raise NotEnoughDataError(
            f"{len(df)} lignes < seuil de {MIN_SAMPLES} : entraînement refusé. "
            "Le système reste en mode règles seules."
        )

    X = ml_features.df_to_features(df)
    y = df[CIBLE].astype(str)

    x_train, x_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    baseline = DummyClassifier(strategy="most_frequent")
    baseline.fit(x_train, y_train)

    rf = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
    rf.fit(x_train, y_train)

    lr = LogisticRegression(max_iter=3000, random_state=42)
    lr.fit(_impute(x_train), y_train)

    report = _build_report(rf, lr, baseline, x_test, y_test)

    # Modèle retenu : meilleure accuracy hors baseline
    best_name = max(
        [m for m in ("rf", "lr")],
        key=lambda name: report[name]["accuracy"],
    )
    best_model = {"rf": rf, "lr": lr}[best_name]

    payload = {
        "model": best_model,
        "model_name": best_name,
        "classes": sorted(rf.classes_.tolist()),
        "feature_names": ml_features.feature_names(),
        "report": report,
        "n_samples": int(len(df)),
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_path": str(Path(path or config.DATASET_PATH).name),
    }
    joblib.dump(payload, config.ML_MODEL_PATH)

    return _public_report(payload)


def _build_report(rf, lr, baseline, x_test, y_test) -> dict:
    models = {
        "baseline": (baseline, x_test),
        "rf": (rf, x_test),
        "lr": (lr, _impute(x_test)),
    }
    report: dict[str, dict] = {}
    for name, (model, x_test_prepared) in models.items():
        y_pred = model.predict(x_test_prepared)
        proba = getattr(model, "predict_proba", None)
        ll = float("nan")
        if proba is not None and len(model.classes_) > 1:
            try:
                ll = log_loss(y_test, proba(x_test_prepared), labels=model.classes_)
            except ValueError:
                ll = float("nan")
        report[name] = {
            "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
            "log_loss": round(float(ll), 4) if not np.isnan(ll) else None,
            "classification_report": classification_report(
                y_test, y_pred, zero_division=0
            ),
            "confusion_matrix": confusion_matrix(
                y_test, y_pred, labels=sorted(model.classes_)
            ).tolist(),
        }
    return report


def _public_report(payload: dict) -> dict:
    return {
        "message": "Modèle entraîné et sauvegardé.",
        "model_choisi": payload["model_name"],
        "n_samples": payload["n_samples"],
        "classes": payload["classes"],
        "metriques": {
            name: {
                "accuracy": metrics["accuracy"],
                "log_loss": metrics["log_loss"],
            }
            for name, metrics in payload["report"].items()
        },
        "model_path": config.ML_MODEL_PATH,
    }


def modele_existe() -> bool:
    return Path(config.ML_MODEL_PATH).exists()


def _load_payload() -> dict:
    if not modele_existe():
        raise RuntimeError("Aucun modèle entraîné.")
    return joblib.load(config.ML_MODEL_PATH)


def predict(profil: dict) -> dict:
    """Outil ML appelable par l'agent : probabilités pour tous les parcours."""
    if not modele_existe():
        raise RuntimeError(
            "Aucun modèle entraîné. Lancez d'abord: ./pony train "
            "(nécessite un jeu de données d'au moins 30 profils)."
        )
    payload = _load_payload()
    vector = ml_features.profil_to_vector(profil)
    probabilities = payload["model"].predict_proba([vector])[0]
    idx = int(np.argmax(probabilities))
    return {
        "parcours": payload["classes"][idx],
        "probabilities": {
            classe: round(float(prob), 4)
            for classe, prob in zip(payload["model"].classes_, probabilities)
        },
        "confidence": round(float(probabilities[idx]), 4),
        "model": payload["model_name"],
    }


if __name__ == "__main__":
    print(train())
