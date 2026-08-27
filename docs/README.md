# Documentation du projet Clinique AI

Bienvenue ! Cette documentation est écrite pour **tout le monde** : tu n'as besoin ni de connaître l'architecture, ni le "Clean Code", ni le projet pour t'en sortir. Chaque guide part de zéro et explique chaque étape.

## Démarrer rapidement avec PONY

Le plus simple pour tout lancer (vérification, installation, tests, serveurs) :

```bash
./scripts/pony.sh        # Linux / macOS
.\pony.cmd               # Windows (ou .\scripts\pony.ps1)
./pony test              # lance tous les tests
./pony eval              # évaluation 34 cas (RAG + ML ; --llm pour le LLM)
./pony resetdb           # supprime la base SQLite (clinique.db)
./pony run               # démarre backend + frontend
```

`pony` est un raccourci vers `scripts/pony.sh` (voir `docs/architecture/` pour comprendre le projet).
La version Windows équivalente est `scripts/pony.ps1` (PowerShell) et le raccourci `pony.cmd`.

## La documentation

| Chemin | Contenu | Pour qui ? |
| ------ | ------- | ---------- |
| [`architecture/backend_structure.md`](architecture/backend_structure.md) | Comment fonctionne le backend, couche par couche (avec une analogie simple). | Tout le monde |
| [`architecture/frontend_structure.md`](architecture/frontend_structure.md) | Comment fonctionne le frontend Next.js, composant par composant. | Tout le monde |
| [`tutorials/setup_gemini.md`](tutorials/setup_gemini.md) | Obtenir sa clé Google Gemini et l'activer. | À faire en premier |
| [`tutorials/add_ml_model.md`](tutorials/add_ml_model.md) | Remplacer le modèle ML par le sien. | Devs ML |
| [`tutorials/create_feature.md`](tutorials/create_feature.md) | Ajouter une fonctionnalité complète (guide pas à pas). | Devs |
| [`tutorials/create_chat_feature.md`](tutorials/create_chat_feature.md) | **Comment le chat a été construit** : entités → base SQLite (avec vérification du modèle) → services → API → tests → frontend, étape par étape. | Devs |
| [`tutorials/implementation_example.md`](tutorials/implementation_example.md) | **Exemple commenté de bout en bout** : quels fichiers créer, dans quel ordre, la forme des fonctions, jusqu'au test. | Devs |

## Comment sont organisés les tests

Il y a **deux familles de tests**, une par partie du projet :

| Partie | Outil | Dossier | Comment lancer |
| ------ | ----- | ------- | -------------- |
| Backend (Python) | `pytest` | `backend/tests/` | `cd backend && .venv/bin/python -m pytest` |
| Frontend (React) | `vitest` | `frontend/lib/*.test.ts` | `cd frontend && npm test` |
| Qualité frontend | `eslint` + build TypeScript | — | `cd frontend && npm run lint` puis `npm run build` |

**Le plus simple : ne jamais lancer tout ça à la main.** Utilise `./pony test` qui fait tout d'un coup, ou `./pony` pour la chaîne complète (vérif → install → train → test → run).

## Guide de lecture rapide (5 minutes)

1. Lis [`architecture/backend_structure.md`](architecture/backend_structure.md) → tu comprends les couches (API → service → repository).
2. Lis [`architecture/frontend_structure.md`](architecture/frontend_structure.md) → tu comprends l'interface.
3. Fais [`tutorials/setup_gemini.md`](tutorials/setup_gemini.md) → tu actives l'IA.
4. Quand tu veux changer un comportement, suis [`tutorials/create_feature.md`](tutorials/create_feature.md).
5. Pour un **exemple complet commenté** du début à la fin : [`tutorials/create_chat_feature.md`](tutorials/create_chat_feature.md) (le chat) ou [`tutorials/implementation_example.md`](tutorials/implementation_example.md) (le résumé).
