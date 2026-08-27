"""Explorateur du modèle Random Forest entraîné (page `/ml`).

Contrairement à une première version qui ré-entraînait un RandomForest à
chaque appel, l'interface utilise désormais le modèle SAUVEGARDÉ
(`config.ML_MODEL_PATH`, ex. `backend/model/ml_model.joblib`) :

- on charge le payload entraîné (modèle, classes, features, métriques) ;
- on ré-évalue le modèle sur le jeu de test (même split stratifié seed 42)
  pour afficher accuracy / F1 / précision / rappel / log-loss ;
- on affiche les importances de features et la prédiction pour le profil
  étudiant du formulaire.

`explorer(profil)` : renvoie le rapport complet ; lève `RuntimeError` si
aucun modèle n'est entraîné.
"""

import time

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

from services import ml_features, ml_service


def _metriques_test(model, x_test, y_test) -> dict:
    """Calcule les métriques du modèle sur le jeu de test."""
    y_pred = model.predict(x_test)
    proba_test = model.predict_proba(x_test)
    ll = None
    try:
        ll = round(float(log_loss(y_test, proba_test, labels=model.classes_)), 4)
    except ValueError:
        ll = None
    return {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "log_loss": ll,
        "precision_macro": round(
            float(precision_score(y_test, y_pred, average="macro", zero_division=0)), 4
        ),
        "recall_macro": round(
            float(recall_score(y_test, y_pred, average="macro", zero_division=0)), 4
        ),
        "f1_macro": round(float(f1_score(y_test, y_pred, average="macro", zero_division=0)), 4),
    }


def explorer(profil: dict | None = None) -> dict:
    """Analyse du modèle entraîné sauvegardé, sans ré-entraînement."""
    payload = ml_service._load_payload()  # RuntimeError si aucun modèle
    model = payload["model"]
    feature_names = payload.get("feature_names") or ml_features.feature_names()

    df = ml_service.load_dataset()
    x = ml_features.df_to_features(df)
    y = df[ml_service.CIBLE].astype(str)
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y
    )

    debut = time.perf_counter()
    metriques = _metriques_test(model, x_test, y_test)
    duree = round(time.perf_counter() - debut, 3)

    importances = [
        {"feature": name, "importance": round(float(imp), 4)}
        for name, imp in sorted(
            zip(feature_names, model.feature_importances_), key=lambda t: t[1], reverse=True
        )
    ]

    prediction = None
    if profil:
        vecteur = ml_features.profil_to_vector(profil)
        probas = model.predict_proba([vecteur])[0]
        idx = int(np.argmax(probas))
        prediction = {
            "parcours": str(model.classes_[idx]),
            "confidence": round(float(probas[idx]), 4),
            "probabilities": {
                str(classe): round(float(prob), 4)
                for classe, prob in zip(model.classes_, probas)
            },
        }

    return {
        "train": {
            "n_samples": int(len(df)),
            "n_features": len(feature_names),
            "n_classes": int(len(model.classes_)),
            "train_size": int(len(x_train)),
            "test_size": int(len(x_test)),
            "duree_s": duree,
        },
        "modele": {
            "nom": payload.get("model_name"),
            "accuracy_test": payload.get("accuracy_test"),
            "trained_at": payload.get("trained_at"),
            "dataset_path": payload.get("dataset_path"),
        },
        "metriques": metriques,
        "feature_importances": importances[:25],
        "prediction": prediction,
    }
