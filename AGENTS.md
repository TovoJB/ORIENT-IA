# AGENTS.md — Contexte du projet

Projet de hackathon : **ORIENT'IA**, assistant IA d'orientation pédagogique ISPM
(Madagascar) qui recommande un parcours d'études parmi 16 parcours (5 catégories).

Système à 3 briques qui communiquent : **données tracées** (SQLite + registres),
**ML** (RandomForest + LogisticRegression, comparaison scientifique), **agent
conversationnel** (Gemini + 6 outils + RAG avec citations). Les exigences du sujet
(traçabilité, évaluation 34 cas, éthique/sécurité) sont documentées dans `docs/`.

Livrables d'évaluation (sujet) :
- `backend/evaluation/test_suite.json` (34 cas, hors-ligne) + `run_evaluation.py` → `./pony eval`.
- `backend/evaluation/jeu_evaluation.csv` (32 cas, 9 catégories obligatoires) + `eval_jeu_api.py`
  → banc de test EN LIGNE : injecte chaque question via `/chat` et écrit
  `jeu_evaluation_resultats.csv` (question, réponse attendue, réponse obtenue, verdict SUCCÈS/ÉCHEC).
  Commande : `./pony evaljeu` (ou `python -m evaluation.eval_jeu_api --ids TC-XX` pour relancer
  des cas, fusion avec les résultats existants).

Stack : **FastAPI (Python) + Google Gemini + scikit-learn + SQLite + SWI-Prolog (pyswip)** · **Next.js (React)**.

## Démarrage rapide

```bash
./pony                  # pipeline complet: check → setup → install → train → test → run
./pony check            # vérifie python, node, .env
./pony train            # entraîne RF+LR sur data/synthetique/ (≥30 profils requis)
./pony test             # pytest + eslint + vitest + build
./pony eval             # évaluation 34 cas : RAG + ML (+ --llm pour fidélité LLM)
./pony resetdb          # supprime backend/clinique.db (recréée au redémarrage)
./pony run              # backend :8000 + frontend :3000
```

- Windows : `.\pony.cmd` (→ `scripts/pony.ps1`).
- `pony` est un symlink vers `scripts/pony.sh`.

## Commands de test

| Partie | Commande |
| ------ | -------- |
| Backend | `cd backend && ./.venv/bin/python -m pytest` (51 tests) |
| Frontend | `cd frontend && npm test` (vitest) |
| Qualité frontend | `cd frontend && npm run lint && npm run build` |
| Évaluation | `cd backend && ./.venv/bin/python -m evaluation.run_evaluation` |

Ne jamais lancer les tests à la main : utiliser `./pony test`.

## Architecture (clean architecture, backend d'abord)

Flux : **route → service → repository → domain**. Un étage n'appelle que son voisin.

```
backend/
├── main.py                  # FastAPI + CORS + /health (état DB)
├── config.py                # .env (GEMINI_API_KEY, DB_PATH, DATASET_PATH, RAG_EMBEDDING, SWIPL_BIN_DIR)
├── api/
│   ├── routes.py            # /chat /predict /orienter /comparer /prerequis /sources /traces /moteurs /inspection
│   └── schemas.py           # Pydantic (validation auto)
├── services/
│   ├── chat_service.py      # Agent : Gemini + function calling, 6 outils, politiques de refus
│   ├── questionnaire.py     # FORMULAIRE GUIDÉ : questions à choix multiples, réponses prédéfinies
│   ├── inspection.py        # état mode + force_prolog (raisonnement temps réel)
│   ├── llm_service.py       # ask_gemini / generate_with_tools (SDK google-genai)
│   ├── orientation_service.py# HYBRIDATION : Prolog filtre → ML choisit → fusion 60/40 + explication
│   ├── prolog_service.py    # Règles (pyswip) avec fallback Python automatique
│   ├── rules_fallback.py    # Miroir Python des règles Prolog (16 parcours)
│   ├── ml_service.py        # train() RF+LR+baseline, métriques ; predict(profil)
│   ├── ml_features.py       # profil → vecteur features (NaN + indicateurs, tolérant)
│   ├── rag_service.py       # RAG v2 : corpus data/sources, embeddings gemini/tfidf, citations
│   ├── profiles.py          # profil construit au fil du dialogue (SQLite)
│   └── traces.py            # observabilité : chaque étape journalisée (SQLite)
├── repositories/
│   ├── base.py              # interface ConversationRepository
│   ├── sqlite_repository.py # persistance SQLite (clinique.db)
│   ├── in_memory_repository.py
│   └── conversation_repository.py  # fabrique selon config.DB_PATH
├── knowledge_base/orientia_rules.pl   # base Prolog (16 parcours, contraintes, scores)
├── evaluation/
│   ├── test_suite.json      # 34 cas catégorisés (factuelles, ML, injection, biais, profilage...)
│   ├── run_evaluation.py    # mesures RAG / ML / fidélité LLM → rapport_evaluation.json
├── notebooks/               # exploration, comparaison modèles, biais (livrables)
├── conftest.py              # pytest : DB temporaire + modèle entraîné
└── tests/                   # test_api, ml, prolog, orientation, chat, rag, llm, sqlite
```

```
data/
├── mapping_taxonomie_orientia.md   # 16 parcours / 5 catégories (référence)
├── sources/                        # corpus RAG documenté + registre_sources.csv
├── enquete/                        # questionnaire + registre de collecte (à remplir)
├── synthetique/                    # génération documentée + dataset (400 profils)
└── dataset_orientia_squelette.csv  # référence de la forme du profil
```

```
frontend/                    # Next.js 16 (voir frontend/AGENTS.md: API breaking)
├── lib/api.ts               # SEUL point de contact avec le backend (/chat, /orienter, /inspection)
├── store/chat-store.ts      # Zustand + profil/trancript en temps réel (sidebar)
├── components/chat/         # ChatMain, ChatSidebar (profil+historique), InspectionPanel...
└── app/page.tsx             # Layout chat
```

## Dialogue d'orientation (agent + formulaire, à connaître)

Le chat COMBINE un agent Gemini et un formulaire guidé à choix multiples :

1. **Message libre** (y compris le premier, ex: "j'ai un bac série C...") → TOUJOURS
   Gemini (`chat_service.chat_turn`) : il EXTRAIT les infos du profil
   (`enregistrer_profil`), pose les questions manquantes via `poser_question`
   (formulaire à choix multiples dans le frontend) ou en texte libre, puis
   `recommander_parcours` quand le profil est suffisant.
2. **Clic sur une option** (`POST /chat` avec `answer: {champ, valeur}`) → réponse
   PRÉDÉFINIE sans Gemini (`questionnaire.reponse_predictive`) : question suivante
   ou recommandation.
3. La réponse contient `question` (payload choix multiples), `recommendation`
   (structurée) et `profil` (collecté, mis à jour à chaque tour). La sidebar
   affiche en temps réel le profil de l'étudiant + l'historique.
4. Observabilité : traces `chat:llm`, `chat:reponse_formulaire`, `outil:*`.

## Mode inspection (étude du raisonnement)

- `services/inspection.py` : état global `mode` + `force_prolog`.
- `GET/POST /inspection` : lire/activer depuis l'interface (toggles dans la sidebar).
- `force_prolog` = désactive TEMPORAIREMENT `rules_fallback` et force SWI-Prolog
  (pyswip) exclusivement ; sans SWI-Prolog → `PrologUnavailable` remontée dans
  `inspection.erreur_prolog` (jamais de repli silencieux dans ce mode).
- SWI-Prolog est installé via conda (`/home/<user>/miniconda3/envs/swipl/bin`) ;
  `prolog_service._ensure_swipl_on_path` l'ajoute au PATH (config `SWIPL_BIN_DIR`).
  Si `USING_SWIPL` est vrai, `moteur()` = "swipl" et le fallback n'est pas utilisé
  (sauf mode force_prolog off → le fallback sert de base au score miroir).
- Quand `mode` est actif, `/orienter` et `/chat` renvoient un bloc `inspection`
  : filtrage Prolog (avec raisons de blocage), scores/motifs des règles,
  probabilités RandomForest, détail de la fusion 60/40 et les requêtes Prolog
  réellement exécutées (`prolog_service.derniere_trace`).
- Le panneau « Inspection » du frontend (`components/chat/inspection-panel.tsx`)
  affiche ces étapes en temps réel sous la recommandation.

## Pipeline de recommandation (à connaître)

1. **Prolog** (`prolog_service`) élimine les parcours non éligibles (série de bac,
   prérequis) et calcule un score de compatibilité (matières/compétences/intérêts/métier).
2. **ML** (`ml_service.predict`) fournit des probabilités (si entraîné, ≥30 profils).
3. **Fusion** (`orientation_service.recommander`) : 60% proba_ML + 40% score règles.
4. **Explication** : motifs + description sourcée (RAG) ; blocages listés.
5. **Traçabilité** : chaque étape (outil, refus, recherche, prédiction) dans `traces`.

## Règles de code

- **Jamais de secret en dur.** Tout passe par `backend/.env` → `config.py`.
- **Nouvelle logique métier = nouveau fichier dans `services/`.** Route = ajout dans `api/routes.py`, format = ajout dans `api/schemas.py`.
- **Le frontend ne parle au backend QUE via `frontend/lib/api.ts`.**
- **Toute fonctionnalité = un test.** Backend : simuler le LLM (monkeypatch) et la DB (temp file). Frontend : `mockFetchOnce`.
- Noms explicites, fonctions courtes, docstrings. UI et commentaires en français.
- **Éthique** : refus des critères discriminatoires, du profilage psychologique, des injections ; disclaimer "pas une décision officielle d'admission". Ces refus sont testés dans `evaluation/test_suite.json`.
- SQLite : tables créées automatiquement (`conversations`, `messages`, `profiles`, `traces`, `rag_chunks`).

## Modifier le projet

Voir `docs/` : `tutorials/create_chat_feature.md` (ordre de création), `tutorials/implementation_example.md`, `architecture/backend_structure.md`, `frontend_structure.md`.

## Pièges connus

- `pkill -f` peut se tuer lui-même : utiliser `[u]vicorn`, `[n]ext dev`.
- Le heredoc "PONY" dans `pony.sh` : son terminateur `EOF` ne doit pas avoir d'espace en fin de ligne.
- Les tests ne doivent jamais créer `backend/clinique.db` ni dépendre du modèle iris (conftest bascule sur une DB temp + entraîne le modèle ORIENT'IA).
- Le moteur d'embeddings Gemini peut échouer (clé/quota) : `rag_service` bascule automatiquement sur TF-IDF. Ne jamais lever d'exception en production.
- La boucle outils Gemini nécessite l'API **chats** (function calling automatique) : ne pas réimplémenter la boucle manuelle (`thought_signature`).
- **pyswip** : les faits assertés (`_profil_facts`) ne doivent PAS se terminer par un point (assertz ajoute `(fait).`) ; les prédicats assertés (`serie_bac/2`, `possede/2`, `prefere/2`, `interet/2`, `vise/2`) doivent être déclarés `:- dynamic` dans `orientia_rules.pl` ; on ne retracte jamais une règle statique (`parcours_possibles/2`).
- SWI-Prolog : si `swipl` n'est pas sur le PATH du serveur, configurer `SWIPL_BIN_DIR` (ou compter sur `_ensure_swipl_on_path` pour l'env conda).
