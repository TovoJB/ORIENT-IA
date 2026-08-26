# Tutoriel : utiliser ton propre modèle de Machine Learning

> Objectif : remplacer le modèle d'exemple (RandomForest sur les iris) par **ton** modèle,
> adapté à **ton** problème (ex: prédire un diagnostic, un prix, un risque...).

## Rappel : où est le code ML ?

Tout est dans **`backend/services/ml_service.py`**. Deux fonctions seulement :

| Fonction | Rôle |
| -------- | ---- |
| `train()` | entraîne un modèle sur des données et le sauvegarde sur le disque |
| `predict(features)` | charge le modèle sauvegardé et prédit pour de nouvelles données |

Le fichier actuel est un **exemple volontairement simple** : il utilise le dataset `iris`
(des fleurs, 4 mesures → 3 espèces). Ton travail : remplacer les données d'exemple par les tiennes.

## Étape 1 — Comprendre le format des données

Ton modèle a besoin de deux choses :

1. **`X` (les entrées)** : un tableau de nombres. Chaque ligne = un exemple, chaque colonne = une caractéristique.
   Exemple : `[poids, âge, tension, température]` = 4 caractéristiques par patient.
2. **`y` (la sortie à prédire)** : pour chaque ligne de `X`, la réponse connue.
   Exemple : `0` = pas malade, `1` = malade. Ou bien `"chat"`, `"chien"`, `"oiseau"`.

> Si tes données sont dans un fichier **CSV**, la librairie `pandas` (déjà installée) est ton amie :
> `import pandas as pd` puis `df = pd.read_csv("mon_fichier.csv")`.

## Étape 2 — Adapter la fonction `train()`

Ouvre `backend/services/ml_service.py`. Voici le squelette actuel :

```python
def train() -> dict:
    data = load_iris()                        # ← 1. charge TON jeu de données
    x_train, x_test, y_train, y_test = train_test_split(
        data.data, data.target, test_size=0.2, random_state=42
    )                                          # ← 2. sépare: 80% entraîne, 20% vérifie

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(x_train, y_train)                # ← 3. entraîne le modèle
    accuracy = model.score(x_test, y_test)     # ← 4. mesure la justesse

    joblib.dump({"model": model, "classes": [...]}, config.ML_MODEL_PATH)
    return {"accuracy": accuracy, ...}
```

### Cas A — tu as un fichier CSV

```python
import pandas as pd

def train() -> dict:
    df = pd.read_csv("mes_donnees.csv")                    # tes données
    x = df.drop(columns=["cible"]).values                  # toutes les colonnes SAUF la cible
    y = df["cible"].values                                 # la colonne à prédire

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42
    )
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(x_train, y_train)

    classes = sorted(set(y))
    joblib.dump({"model": model, "classes": classes}, config.ML_MODEL_PATH)
    return {"message": "Modèle entraîné !", "accuracy": round(float(model.score(x_test, y_test)), 4)}
```

### Cas B — ton problème est une prédiction de chiffre (régression)

Remplacer le classifieur par un régresseur :

```python
from sklearn.ensemble import RandomForestRegressor

model = RandomForestRegressor(n_estimators=100, random_state=42)
```

⚠️ Attention : `predict()` plus bas doit alors **ne pas renvoyer `class_name`** (il n'y a pas de classes en régression). Vois l'étape 3.

### Cas C — tu veux changer d'algorithme

Le format est identique, seul le modèle change. Exemples :

```python
from sklearn.linear_model import LogisticRegression
model = LogisticRegression(max_iter=1000)

from sklearn.svm import SVC
model = SVC(probability=True)
```

## Étape 3 — Adapter la fonction `predict()`

La fonction actuelle renvoie trois choses : `prediction`, `class_name`, `probabilities`.

- Si tu gardes un **classifieur** : rien à changer (renomme juste les classes dans `train()`).
- Si tu fais de la **régression** (prédire un nombre) :

```python
def predict(features: list[float]) -> dict:
    try:
        payload = joblib.load(config.ML_MODEL_PATH)
    except FileNotFoundError:
        raise RuntimeError("Aucun modèle trouvé. Lance d'abord: ./pony train")
    model = payload["model"]
    value = float(model.predict([features])[0])
    return {"prediction": value}
```

Pense à adapter le schéma de réponse dans **`backend/api/schemas.py`** :

```python
class PredictResponse(BaseModel):
    prediction: float   # au lieu de prediction: int + class_name + probabilities
```

## Étape 4 — (optionnel) la RAG, ta base de connaissances

Le chat répond déjà, mais il ne connaît que ce que Gemini sait. Pour qu'il réponde **avec TES infos**
(horaires, tarifs, procédures...), remplis le fichier **`backend/rag_documents.txt`** :

```
Notre clinique est ouverte de 8h à 18h du lundi au vendredi.
Une consultation pédiatrie coûte 40 euros.
La cardiologie est disponible le mardi.
```

Chaque ligne = un fait. Au prochain démarrage, le backend retrouve automatiquement
les lignes proches de la question et les donne à l'IA. Rien à coder.

## Étape 5 — Tester

```bash
./pony train        # réentraîne avec TON modèle
./pony test         # vérifie que les tests passent toujours
./pony run          # lance le projet
```

Dans le chat, clique sur **ML Predict** : tu verras la prédiction de ton modèle.

## Les tests ML existants

`backend/tests/test_ml_service.py` vérifie que `train()` + `predict()` fonctionnent.
Si tu changes le modèle, tu devras peut-être ajuster ces tests :

```python
def test_predict_without_model_raises(monkeypatch):   # ce test reste valable
    ...
```

Pour lancer seulement les tests ML :

```bash
cd backend
./.venv/bin/python -m pytest tests/test_ml_service.py -q
```

## Checklist avant le hackathon

- [ ] Mes données sont dans un CSV (ou un tableau de nombres).
- [ ] `train()` charge mes données et sauvegarde le modèle.
- [ ] `predict()` renvoie ce que le frontend attend.
- [ ] `./pony test` passe au vert.
- [ ] Le bouton **ML Predict** affiche ma prédiction.

👉 Pour toute autre fonctionnalité (nouvelle route, nouveau bouton), suis
[`create_feature.md`](create_feature.md).
