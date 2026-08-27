# Architecture du backend (expliquée simplement)

> Objectif de ce document : comprendre comment le backend est organisé **sans aucun prérequis**.
> C'est la partie Python/FastAPI du projet.

## 1. L'idée en une phrase

Le backend est une **usine** : il reçoit une demande de l'extérieur (le frontend), il la transforme, et il renvoie une réponse. Le code est rangé en **étages** pour que chaque étage fasse **une seule chose** et qu'on puisse changer un étage sans casser les autres.

### L'analogie du restaurant

Imaginons un restaurant :

| Étage | Rôle | Dans le projet |
| ----- | ---- | -------------- |
| **La salle** (le client commande) | reçoit la commande, note, vérifie que c'est lisible | `api/` (les routes HTTP) |
| **La cuisine** (les recettes) | fait réellement le plat | `services/` (le LLM, le ML, le RAG) |
| **Le garde-manger** (les ingrédients) | stocke les données | `repositories/` (les conversations) |
| **La recette sur papier** (la définition d'un plat) | la définition de ce qu'est une donnée | `domain/` (les entités) |

La règle d'or : **la salle ne cuisine pas, la cuisine ne commande pas**. Chaque étage parle seulement à son voisin.

## 2. L'arborescence du backend

```
backend/
├── main.py                       # LE point d'entrée : crée l'app FastAPI
├── config.py                     # lit les variables du fichier .env
├── requirements.txt              # liste des dépendances Python
├── conftest.py                   # prépare l'environnement des tests
├── tests/                        # les tests pytest
│   ├── test_api.py               #   /health, /orienter, /predict, /traces...
│   ├── test_ml_service.py        #   train/predict, features, seuil de données
│   ├── test_prolog_service.py    #   règles, parcours possibles, prérequis
│   ├── test_orientation_service.py  # hybridation + explication
│   ├── test_chat_service.py      #   outils de l'agent, refus sans clé
│   ├── test_rag_service.py       #   corpus + citations
│   ├── test_llm_service.py       #   gestion d'erreur Gemini
│   └── test_sqlite_repository.py #   persistance
├── api/                          # ÉTAGE 1 : la salle du restaurant
│   ├── routes.py                 #   /chat /predict /orienter /comparer /prerequis /sources /traces /moteurs
│   └── schemas.py                #   vérifie ce que le client envoie/reçoit
├── services/                     # ÉTAGE 2 : la cuisine
│   ├── chat_service.py           #   l'agent (Gemini + outils + refus)
│   ├── orientation_service.py    #   hybridation Prolog → ML → fusion 60/40
│   ├── prolog_service.py         #   moteur de règles (pyswip + fallback)
│   ├── rules_fallback.py         #   miroir Python des règles Prolog
│   ├── ml_service.py             #   entraîne (RF + LR) / prédit
│   ├── ml_features.py            #   profil → vecteur de features
│   ├── rag_service.py            #   RAG : embeddings + base vectorielle + citations
│   ├── llm_service.py            #   appelle Google Gemini
│   ├── profiles.py               #   profil de session (construit au fil du dialogue)
│   └── traces.py                 #   observabilité (chaque étape journalisée)
├── knowledge_base/               # la base de règles Prolog
│   └── orientia_rules.pl
├── domain/                       # ÉTAGE 4 : les définitions de données
│   └── entities.py               #   Message, Conversation, PredictionResult
├── repositories/                 # ÉTAGE 3 : le garde-manger
│   ├── base.py                   #   le "contrat"
│   ├── sqlite_repository.py      #   stockage SQLite (clinique.db)
│   ├── in_memory_repository.py   #   alternative en mémoire
│   └── conversation_repository.py#   choisit l'implémentation selon la config
├── evaluation/                   # évaluation exigée par le sujet
│   ├── test_suite.json           #   34 cas catégorisés
│   └── run_evaluation.py         #   mesures RAG / ML / fidélité LLM
├── notebooks/                    # livrables ML (exploration, comparaison, biais)
└── utils/                        # petites fonctions réutilisables
```

## 3. Le trajet d'une requête (exemple : `/chat`)

Quand le frontend envoie `{"message": "Bonjour"}` à l'URL `POST /chat`, voici ce qui se passe **dans l'ordre** :

```
frontend (React)
   │  requête HTTP
   ▼
main.py ──────────────► démarre l'app, inclut les routes
   │
   ▼
api/routes.py  (1) reçoit la requête
   │            (2) confie le travail à un service
   ▼
services/llm_service.py  (3) appelle Google Gemini
   │
   ▼
api/routes.py  (4) demande au repository de sauvegarder la conversation
   │
   ▼
repositories/conversation_repository.py  (5) range les messages en mémoire
   │
   ▼
api/routes.py  (6) renvoie la réponse au frontend
```

Chaque étape est **petite et lisible** : si une étape casse, on sait exactement où regarder.

## 4. Les fichiers, un par un

### `main.py` — le point d'entrée

```python
app = FastAPI(...)            # crée l'application
app.add_middleware(CORSMiddleware, ...)   # autorise le frontend (port 3000) à appeler l'API
app.include_router(router)    # branche les routes définies dans api/routes.py

@app.get("/health")           # petit contrôle : "l'API est-elle vivante ?"
def health():
    return {"status": "ok"}
```

### `config.py` — les réglages

Lit le fichier `.env` (dans lequel on met les secrets comme la clé API Gemini) et expose les valeurs dans un objet `config` :

```python
config.GEMINI_API_KEY   # la clé Gemini
config.GEMINI_MODEL     # le modèle à utiliser (ex: gemini-2.0-flash)
config.DB_PATH          # le chemin de la base SQLite (ex: backend/clinique.db)
```

**Règle importante** : aucune clé, aucun secret n'est écrit en dur dans le code. Tout passe par `.env` → `config.py`.

### `api/routes.py` — la salle du restaurant

Définit **ce que le client peut demander**. Deux routes principales :

| Route | Méthode | Rôle |
| ----- | ------- | ---- |
| `/chat` | POST | prendre le message, appeler Gemini, renvoyer la réponse |
| `/predict` | POST | prendre des nombres (features), appeler le ML, renvoyer la prédiction |

La route `/chat` :
1. récupère les textes utiles dans la base RAG (`retriever.retrieve(...)`),
2. construit un "prompt" lisible par l'IA,
3. appelle `llm_service.ask_gemini(...)`,
4. sauvegarde le message et la réponse dans le repository,
5. renvoie `{reply, conversation_id}`.

### `api/schemas.py` — le contrôleur d'entrée

Vérifie que ce que le client envoie a **la bonne forme**. Par exemple, un `ChatRequest` doit avoir un champ `message` non vide. Si ce n'est pas le cas, FastAPI renvoie une erreur `422` automatiquement (sans qu'on ait rien à coder).

### `services/` — la cuisine

Chaque fichier fait un métier précis :

| Fichier | Métier |
| ------- | ------ |
| `llm_service.py` | `ask_gemini(prompt)` → appelle l'IA de Google et renvoie son texte |
| `ml_service.py` | `train()` entraîne le modèle, `predict(features)` prédit |
| `rag_service.py` | recherche dans des textes (base de connaissances) les passages les plus proches d'une question |

### `domain/entities.py` — les définitions de données

Des petites classes Python simples (des `dataclass`) qui décrivent le métier du projet : un `Message` a un rôle (`user` ou `assistant`), un contenu et une date. Les services travaillent avec ces objets, jamais avec des choses "au hasard".

### `repositories/` — le garde-manger (avec SQLite !)

Le projet stocke désormais les conversations dans une **vraie base SQLite**
(fichier `backend/clinique.db`) : les messages **survivent au redémarrage** du serveur.
La couche se décompose en 4 fichiers :

| Fichier | Rôle |
| ------- | ---- |
| `base.py` | le **contrat** : la liste des méthodes que toute implémentation doit avoir (`create`, `get`, `add_message`, `health_check`) |
| `sqlite_repository.py` | l'implémentation par défaut : enregistre tout dans SQLite |
| `in_memory_repository.py` | une alternative en mémoire (utile pour des tests rapides) |
| `conversation_repository.py` | la **fabrique** : choisit l'implémentation selon `DB_PATH` dans la config |

Pour passer en mémoire (au lieu de SQLite) : `DB_PATH=` dans `.env` (vide).
Pour changer de base de données un jour (PostgreSQL, Redis...) : on écrit un nouveau fichier
`xxx_repository.py` qui respecte le contrat de `base.py`, et le reste du code **ne change pas**.

### `utils/helpers.py` — la boîte à outils

Petites fonctions génériques comme `generate_id()` qui fabrique un identifiant unique.

## 5. Les tests du backend

Les tests sont dans `backend/tests/`. Ils s'assurent que le backend fonctionne sans avoir besoin de lancer le serveur ni de payer des appels Gemini.

| Fichier de test | Ce qu'il vérifie |
| --------------- | ---------------- |
| `test_api.py` | `/health` répond, `/predict` renvoie une prédiction, `/chat` appelle bien le service LLM |
| `test_ml_service.py` | `train()` produit un modèle, `predict()` fonctionne dessus |
| `test_llm_service.py` | `ask_gemini()` gère proprement le cas "pas de clé API" |
| `test_rag_service.py` | le RAG retrouve le bon texte |
| `test_sqlite_repository.py` | les conversations se créent, se lisent et se complètent en SQLite |

> Détail pratique : le LLM est **simulé** dans les tests (`monkeypatch`). On ne tape pas sur l'API Gemini à chaque test, c'est gratuit et instantané.
> La base SQLite est aussi **simulée** (une base en mémoire `:memory:`) pour que les tests
> ne créent pas de fichier sur ta machine. C'est `conftest.py` qui fait ce réglage.

### Comment lancer les tests backend

```bash
cd backend
./.venv/bin/python -m pytest          # lance TOUS les tests
./.venv/bin/python -m pytest -q       # version plus courte
./.venv/bin/python -m pytest tests/test_api.py   # un seul fichier
```

Si tu vois `11 passed`, tout est bon.

### Le fichier `conftest.py`

Il prépare le terrain avant chaque série de tests : il entraîne un petit modèle dans un dossier temporaire pour que les tests ne dépendent pas de l'état de ta machine.

## 6. Lancer le backend seul

```bash
cd backend
./.venv/bin/uvicorn main:app --reload --port 8000
```

- L'API répond sur `http://localhost:8000`
- La documentation interactive (où tu peux tester chaque route avec un bouton) : `http://localhost:8000/docs`

## 7. Recette : comment lire un nouveau fichier backend

Quand on arrive dans un fichier backend inconnu, pose-toi ces questions dans l'ordre :

1. **C'est dans quel dossier ?** → routes = "la salle", services = "la cuisine", domain = "définitions", repositories = "stockage".
2. **Que fait la fonction principale ?** → lis son nom (`ask_gemini`, `predict`, `chat`...), il dit tout.
3. **Qui l'appelle ?** → la route appelle un service, le service appelle un autre service ou une bibliothèque.
4. **Que renvoie-t-elle ?** → regarde le schéma Pydantic correspondant dans `api/schemas.py`.

C'est tout. Chaque fonction doit tenir en quelques lignes et se lire comme une phrase.

---

👉 Maintenant que tu connais le backend, passe à la partie suivante selon ton besoin :
- [`frontend_structure.md`](frontend_structure.md) → comprendre l'interface
- [`../tutorials/create_feature.md`](../tutorials/create_feature.md) → ajouter une fonctionnalité
