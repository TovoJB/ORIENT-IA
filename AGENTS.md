# AGENTS.md — Contexte du projet

Agent intelligent de hackathon (chat IA + prédiction ML) pour une clinique.
Stack : **FastAPI (Python) + Google Gemini + scikit-learn + SQLite** · **Next.js (React, template square-ui)**.

## Démarrage rapide

```bash
./pony                  # pipeline complet: check → setup → install → train → test → run
./pony check            # vérifie python, node, .env
./pony test             # pytest + eslint + vitest + build
./pony resetdb          # supprime backend/clinique.db (recréée au redémarrage)
./pony run              # backend :8000 + frontend :3000 (Ctrl+C arrête tout)
./pony help             # liste des commandes
```

- Windows : équivalent PowerShell `.\pony.cmd` (→ `scripts/pony.ps1`).
- `pony` est un symlink vers `scripts/pony.sh`.

## Commands de test

| Partie | Commande |
| ------ | -------- |
| Backend | `cd backend && ./.venv/bin/python -m pytest` (15 tests) |
| Frontend | `cd frontend && npm test` (vitest) |
| Qualité frontend | `cd frontend && npm run lint && npm run build` |

Ne jamais lancer les tests à la main : utiliser `./pony test`.

## Architecture (clean architecture, backend d'abord)

Flux : **route → service → repository → domain**. Un étage n'appelle que son voisin.

```
backend/
├── main.py                  # Entrypoint FastAPI + CORS + GET /health (état DB)
├── config.py                # Lit .env (clé Gemini, DB_PATH, modèle...)
├── api/
│   ├── routes.py            # POST /chat, POST /predict
│   └── schemas.py           # Modèles Pydantic (validation auto)
├── services/
│   ├── llm_service.py       # ask_gemini(prompt) — Gemini (SDK google-genai)
│   ├── ml_service.py        # train() / predict() — RandomForest (iris)
│   └── rag_service.py       # RAG : TF-IDF + cosine similarity
├── domain/entities.py       # dataclasses : Message, Conversation, PredictionResult
├── repositories/
│   ├── base.py              # Interface ConversationRepository
│   ├── sqlite_repository.py # Persistance SQLite (clinique.db) — par défaut
│   ├── in_memory_repository.py
│   └── conversation_repository.py  # Fabrique selon config.DB_PATH
├── evaluation/evaluate.py   # Smoke test LLM
├── utils/helpers.py         # generate_id()
├── conftest.py              # pytest : DB en :memory: + modèle ML temp
└── tests/                   # test_api, test_ml, test_llm, test_rag, test_sqlite_repository
```

```
frontend/                    # Next.js 16 (voir frontend/AGENTS.md: API breaking)
├── lib/api.ts               # SEUL point de contact avec le backend (fetch)
├── store/chat-store.ts      # Zustand (sidebar)
├── components/chat/         # ChatMain (orchestrateur), ChatInputBox, ChatMessage, ...
└── app/page.tsx             # Layout chat
```

## Règles de code

- **Jamais de secret en dur.** Tout passe par `backend/.env` → `config.py` (`GEMINI_API_KEY`, `DB_PATH`).
- **Nouvelle logique métier = nouveau fichier dans `services/`.** Route = ajout dans `api/routes.py`, format = ajout dans `api/schemas.py`.
- **Le frontend ne parle au backend QUE via `frontend/lib/api.ts`.**
- **Toute fonctionnalité = un test.** Backend : simuler le LLM avec `monkeypatch`, la DB avec `:memory:`. Frontend : `mockFetchOnce` dans `lib/api.test.ts`.
- Noms explicites, fonctions courtes, docstrings. UI et commentaires en français. Pas d'emojis sauf demande explicite.
- SQLite : les tables (`conversations`, `messages`) sont créées automatiquement par `sqlite_repository.py`.

## Modifier le projet

Voir la doc complète : `docs/` — notamment :
- `docs/tutorials/create_chat_feature.md` (ordre de création : entités → repositories → services → schemas → routes → tests → frontend)
- `docs/tutorials/implementation_example.md` (exemple complet `/summarize`)
- `docs/architecture/backend_structure.md` et `frontend_structure.md`

## Pièges connus

- `pkill -f` peut se tuer lui-même : utiliser les patterns `[u]vicorn`, `[n]ext dev`.
- Le bannière "PONY" dans `pony.sh` est un heredoc : son terminateur `EOF` ne doit pas avoir d'espace en fin de ligne.
- Les tests backend ne doivent jamais créer `backend/clinique.db` (conftest bascule sur `:memory:`).
