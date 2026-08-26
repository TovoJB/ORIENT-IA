import joblib
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from config import config


def train() -> dict:
    """Train a RandomForest classifier on the iris dataset and persist it."""
    data = load_iris()
    x_train, x_test, y_train, y_test = train_test_split(
        data.data, data.target, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(x_train, y_train)
    accuracy = model.score(x_test, y_test)

    joblib.dump(
        {"model": model, "classes": list(data.target_names)},
        config.ML_MODEL_PATH,
    )
    return {
        "message": "Modèle entraîné et sauvegardé.",
        "accuracy": round(float(accuracy), 4),
        "model_path": config.ML_MODEL_PATH,
    }


def predict(features: list[float]) -> dict:
    """Predict a class from a feature vector using the persisted model."""
    try:
        payload = joblib.load(config.ML_MODEL_PATH)
    except FileNotFoundError:
        raise RuntimeError(
            "Aucun modèle trouvé. Lancez d'abord l'entraînement: python -m services.ml_service"
        )

    model = payload["model"]
    classes = payload["classes"]

    prediction = int(model.predict([features])[0])
    probabilities = [float(p) for p in model.predict_proba([features])[0]]

    return {
        "prediction": prediction,
        "class_name": classes[prediction],
        "probabilities": probabilities,
    }


if __name__ == "__main__":
    print(train())
