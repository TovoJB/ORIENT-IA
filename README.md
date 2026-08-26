# Hackathon AI Agent — Clinique AI

Agent intelligent modulaire (LLM Gemini + Machine Learning) pour hackathon.

Stack: **Python / FastAPI / scikit-learn / Gemini API** · **Next.js (React) / square-ui chat template**.

> **Nouveau ici ? Lis la documentation : [`docs/`](docs/README.md)**
> Elle explique l'architecture pour débutants et contient des tutoriels pas à pas.

## Démarrage rapide avec PONY

Le projet embarque un lanceur nommé **PONY** qui vérifie, installe, teste et lance tout :

```bash
./scripts/pony.sh            # Linux / macOS — pipeline complet: check → setup → install → train → test → run
./pony check                 # vérifie l'environnement (python, node, .env)
./pony test                  # lance TOUS les tests (backend + frontend)
./pony resetdb               # supprime la base SQLite (clinique.db), recréée au redémarrage
./pony run                   # démarre backend (:8000) + frontend (:3000)
```

**Windows** : utilisez la version PowerShell équivalente :

```powershell
.\pony.cmd                   # raccourci (contourne la restriction PowerShell)
.\scripts\pony.ps1 test      # ou directement
```

`./pony` est un raccourci de `./scripts/pony.sh`. Tapez `./pony help` (ou `.\pony.cmd help`) pour la liste des commandes.

## Documentation

| Où | Quoi |
| -- | ---- |
| [`docs/`](docs/README.md) | Sommaire de la doc (lecture pour débutants) |
| [`docs/architecture/`](docs/architecture/) | Comment marchent le backend et le frontend |
| [`docs/tutorials/setup_gemini.md`](docs/tutorials/setup_gemini.md) | Activer l'IA Gemini (à faire en premier) |
| [`docs/tutorials/add_ml_model.md`](docs/tutorials/add_ml_model.md) | Utiliser son propre modèle ML |
| [`docs/tutorials/create_feature.md`](docs/tutorials/create_feature.md) | Ajouter une fonctionnalité de bout en bout |
| [`docs/tutorials/implementation_example.md`](docs/tutorials/implementation_example.md) | Exemple complet commenté : fichiers à créer, ordre, formes des fonctions, jusqu'au test |

## Tests

| Partie | Outil | Commande |
| ------ | ----- | -------- |
| Backend | pytest | `cd backend && ./.venv/bin/python -m pytest` |
| Frontend | vitest | `cd frontend && npm test` |
| Qualité frontend | eslint + build | `cd frontend && npm run lint && npm run build` |

Le plus simple : `./pony test` fait tout d'un coup.

## Arborescence

```
cliniqueExam/
├── scripts/
│   ├── pony.sh                   # PONY: lanceur Linux/macOS (check / install / test / run)
│   └── pony.ps1                  # PONY: lanceur Windows (PowerShell)
├── pony.cmd                      # Raccourci Windows -> scripts/pony.ps1
├── docs/                         # Documentation + tutoriels (voir tableau ci-dessus)
├── backend/                     # API FastAPI (clean architecture)
│   ├── main.py                  # Entrypoint FastAPI + CORS + /health (avec état de la base)
│   ├── config.py                # Chargement des variables d'environnement (.env)
│   ├── requirements.txt         # Dépendances runtime
│   ├── requirements-dev.txt     # Dépendances de test (pytest)
│   ├── .env / .env.example      # GEMINI_API_KEY, DB_PATH (jamais hardcodés)
│   ├── tests/                   # Tests pytest (api, ml, llm, rag, sqlite)
│   ├── api/
│   │   ├── routes.py            # POST /chat, POST /predict
│   │   └── schemas.py           # Modèles Pydantic (requêtes/réponses)
│   ├── domain/
│   │   └── entities.py          # Entités métier (Message, Conversation, PredictionResult)
│   ├── services/
│   │   ├── llm_service.py       # ask_gemini() — appel à Google Gemini
│   │   ├── ml_service.py        # train() / predict() — RandomForest
│   │   └── rag_service.py       # RAG minimal (TF-IDF + cosine similarity)
│   ├── repositories/
│   │   ├── base.py              # Contrat commun (interface)
│   │   ├── sqlite_repository.py # Conversations persistées dans SQLite (clinique.db)
│   │   ├── in_memory_repository.py  # Alternative en mémoire
│   │   └── conversation_repository.py  # Choix de l'implémentation selon DB_PATH
│   ├── evaluation/
│   │   └── evaluate.py          # Smoke test du LLM
│   ├── utils/
│   │   └── helpers.py           # generate_id() etc.
│   └── rag_documents.txt        # Base de connaissances RAG (à remplir)
└── frontend/                    # Next.js (React), chat inspiré de square-ui
    ├── package.json             # + scripts: dev / build / lint / test
    ├── .env.example             # NEXT_PUBLIC_API_URL
    ├── lib/api.ts               # Client HTTP vers le backend (/chat, /predict) + tests
    ├── store/chat-store.ts      # État global (Zustand)
    ├── app/page.tsx             # Layout chat (sidebar + zone de chat)
    └── components/chat/         # ChatMain, ChatInputBox, ChatMessage...
```

## Rôle de chaque dossier (backend)

| Dossier       | Responsabilité                                                  |
| ------------- | --------------------------------------------------------------- |
| `api/`        | Couche HTTP : routes FastAPI, schémas de validation (Pydantic). |
| `services/`   | Logique applicative : LLM, ML, RAG. Aucune logique HTTP ici.    |
| `domain/`     | Entités métier pures (dataclasses), indépendantes de tout cadre. |
| `repositories`| Accès aux données. **SQLite par défaut** (`clinique.db`), remplaçable (mémoire, autres DB) via `DB_PATH`. |
| `evaluation/` | Tests manuels / smoke tests de vos services.                    |
| `utils/`      | Helpers réutilisables.                                          |

Flux : **route → service → repository**, les services ne dépendent que du domain.
Les conversations sont persistées dans `backend/clinique.db` (SQLite) : elles survivent aux redémarrages.

## Backend

Le plus simple : `./pony run-api` (installe les dépendances automatiquement). À la main :

```bash
cd backend
python3 -m venv .venv
./.venv/bin/pip install -r requirements-dev.txt   # runtime + tests

# Configurer la clé API Gemini (voir docs/tutorials/setup_gemini.md)
cp .env.example .env
#   -> éditer .env et mettre GEMINI_API_KEY=votre_cle

# (optionnel) entraîner le modèle ML
./.venv/bin/python -m services.ml_service

# Lancer le serveur
./.venv/bin/uvicorn main:app --reload --port 8000
```

API dispo sur http://localhost:8000 — docs interactives : http://localhost:8000/docs

- `POST /chat` `{"message": "...", "history": []}` → `{reply, conversation_id}`
- `POST /predict` `{"features": [5.1, 3.5, 1.4, 0.2]}` → `{prediction, class_name, probabilities}`
- `GET /health`

Obtention de la clé Gemini : https://aistudio.google.com/apikey

## Frontend

```bash
cd frontend
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev                  # -> http://localhost:3000
```

Le chat appelle `POST /chat` (Gemini). Le bouton **ML Predict** appelle `POST /predict`.

## Adapter à un autre use case (hackathon)

1. **LLM** : modifiez `services/llm_service.py` (modèle, `system_instruction`).
2. **ML** : changez le dataset dans `services/ml_service.py::train()`, adaptez le nombre de `features`.
3. **RAG** : remplissez `rag_documents.txt` avec votre base de connaissances.
4. **Logique** : ajoutez un service + une route + un schéma, rien d'autre ne change.
   (Voir l'exemple commenté : `docs/tutorials/implementation_example.md`)
5. **Persistance** : par défaut SQLite (`backend/clinique.db`, configurable via `DB_PATH`).
   Pour une autre base, ajoutez un repository qui respecte `repositories/base.py`.
```
