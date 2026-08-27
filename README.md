# ORIENT'IA — Assistant d'orientation pédagogique (ISPM)

Agent IA qui recommande un parcours d'études parmi **16 parcours ISPM** (5 catégories),
en combinant **règles Prolog** (contraintes), **Machine Learning** (RandomForest /
LogisticRegression) et un **agent conversationnel Gemini** (RAG sourcé, 5 outils, traçabilité).

Stack: **Python / FastAPI / scikit-learn / Gemini API / SQLite / Prolog (pyswip)** · **Next.js (React) / square-ui chat template**.

> **Nouveau ici ? Lis la documentation : [`docs/`](docs/README.md)**
> Elle explique l'architecture pour débutants et contient des tutoriels pas à pas.

## Démarrage rapide avec PONY

Le projet embarque un lanceur nommé **PONY** qui vérifie, installe, teste et lance tout :

```bash
./scripts/pony.sh            # Linux / macOS — pipeline complet: check → setup → install → train → test → run
./pony check                 # vérifie l'environnement (python, node, .env)
./pony train                 # entraîne RF+LR sur les données synthétiques (≥30 profils requis)
./pony test                  # lance TOUS les tests (backend + frontend)
./pony eval                  # évaluation 34 cas : RAG + ML (ajoutez --llm pour la fidélité LLM)
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
│   ├── pony.sh                   # PONY: lanceur Linux/macOS (check / install / train / test / eval / run)
│   └── pony.ps1                  # PONY: lanceur Windows (PowerShell)
├── pony.cmd                      # Raccourci Windows -> scripts/pony.ps1
├── docs/                         # Documentation + tutoriels (voir tableau ci-dessus)
├── data/
│   ├── mapping_taxonomie_orientia.md   # 16 parcours / 5 catégories (référence)
│   ├── sources/                  # Corpus RAG documenté + registre_sources.csv
│   ├── enquete/                  # Questionnaire + registre de collecte (à remplir)
│   ├── synthetique/              # Génération documentée + dataset (400 profils)
│   └── dataset_orientia_squelette.csv  # Forme du profil
├── backend/                     # API FastAPI (clean architecture)
│   ├── main.py                  # Entrypoint FastAPI + CORS + /health
│   ├── config.py                # .env (GEMINI_API_KEY, DB_PATH, DATASET_PATH, RAG_EMBEDDING)
│   ├── requirements.txt / requirements-dev.txt
│   ├── .env / .env.example      # secrets jamais commités
│   ├── tests/                   # 40 tests pytest (api, ml, prolog, orientation, chat, rag, llm, sqlite)
│   ├── api/
│   │   ├── routes.py            # /chat /predict /orienter /comparer /prerequis /sources /traces /moteurs
│   │   └── schemas.py           # Modèles Pydantic
│   ├── services/
│   │   ├── chat_service.py      # Agent : Gemini + 5 outils + refus (éthique/sécurité)
│   │   ├── orientation_service.py  # Hybridation Prolog→ML→fusion 60/40 + explication
│   │   ├── prolog_service.py / rules_fallback.py  # Règles (pyswip + fallback Python)
│   │   ├── ml_service.py / ml_features.py         # RF+LR, baseline, métriques
│   │   ├── rag_service.py       # RAG v2 : embeddings (gemini/tfidf) + citations
│   │   ├── llm_service.py       # Gemini (ask_gemini + function calling)
│   │   ├── profiles.py / traces.py                # profil de session + observabilité
│   │   └── rules_fallback.py
│   ├── repositories/            # base + sqlite + in_memory + fabrique
│   ├── knowledge_base/orientia_rules.pl   # Base Prolog (16 parcours)
│   ├── evaluation/
│   │   ├── test_suite.json      # 34 cas catégorisés (incl. sécurité/biais)
│   │   └── run_evaluation.py    # mesures RAG/ML/LLM → rapport_evaluation.json
│   ├── notebooks/               # livrables ML (exploration, comparaison, biais)
│   ├── utils/helpers.py
│   └── rag_documents.txt
└── frontend/                    # Next.js (React), chat square-ui
    ├── lib/api.ts               # SEUL point de contact backend (/chat, /orienter)
    ├── store/chat-store.ts      # Zustand
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

- `POST /chat` `{"message": "...", "history": []}` → `{reply, conversation_id, tools_used}` (agent avec outils)
- `POST /orienter` `{"profil": {...}}` → recommandation classée (Prolog filtre + ML choisit + explication)
- `POST /predict` `{"profil": {...}}` → probabilités du modèle ML
- `POST /comparer` / `POST /prerequis` → comparaison / vérification de prérequis
- `GET/POST /inspection` → mode inspection (raisonnement Prolog + probabilités ML en temps réel)
- `GET /sources` → registre des sources du corpus · `GET /traces` → observabilité
- `GET /moteurs` → état des moteurs (règles, embeddings, ML) · `GET /health`

Obtention de la clé Gemini : https://aistudio.google.com/apikey

## Frontend

```bash
cd frontend
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev                  # -> http://localhost:3000
```

Le chat est un **formulaire guidé** : il pose des questions à **choix multiples**
(prédéfinies, sans appel Gemini), construit le profil, puis affiche la
**recommandation** (Prolog + ML) avec explications. Gemini n'est appelé que si
nécessaire (question libre après la recommandation).

## Évaluer le système (sujet)

```bash
./pony eval               # RAG + ML hors-ligne (34 cas)
./pony eval --llm         # + fidélité des réponses LLM (appels Gemini)
cat backend/evaluation/rapport_evaluation.json
```

## Adapter à un autre use case (hackathon)

1. **LLM** : modifiez `services/chat_service.py` (SYSTEM_PROMPT, outils) et `llm_service.py`.
2. **ML** : changez le dataset dans `config.py::DATASET_PATH` (ou `data/synthetique/`),
   la cible dans `ml_service.py`, les features dans `ml_features.py`.
3. **Règles** : éditez `knowledge_base/orientia_rules.pl` + `services/rules_fallback.py` (miroir).
4. **RAG** : remplissez `data/sources/*.md` + `registre_sources.csv`.
5. **Logique** : ajoutez un service + une route + un schéma (voir `docs/tutorials/implementation_example.md`).
6. **Persistance** : SQLite par défaut (`DB_PATH`) ; autre base = un repository respectant `repositories/base.py`.
