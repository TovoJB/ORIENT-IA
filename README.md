# ORIENT'IA — Assistant d'orientation pédagogique (ISPM)

**ORIENT'IA** est un assistant IA d'orientation qui recommande un **parcours d'études
parmi les 16 parcours de l'ISPM (Madagascar)** répartis en 5 catégories. Il combine
quatre briques qui communiquent :

- **Règles Prolog** (`SWI-Prolog` + fallback Python) : filtrage des parcours non éligibles
  (série de bac, prérequis) et score de compatibilité.
- **Machine Learning** (`scikit-learn`) : RandomForest + LogisticRegression entraînés sur
  les données synthétiques, avec comparaison scientifique et étude des biais.
- **Agent conversationnel Gemini** : 6 outils, RAG sourcé avec citations, formulaire guidé
  à choix multiples et politiques de refus éthique/sécurité.
- **Traçabilité** : chaque étape (outil, refus, recherche, prédiction) est journalisée
  dans SQLite (`clinique.db`).

Stack : **Python / FastAPI / scikit-learn / Google Gemini / SQLite / SWI-Prolog (pyswip)** ·
**Next.js (React)**.

---

## 1. Livrables de l'exercice

Ce projet répond à l'exercice avec **deux supports complémentaires** :

| Livrable | Support | Où le trouver |
| -------- | ------- | ------------- |
| **Vidéo de démonstration (5 min)** | Les cas demandés par l'exercice y sont montrés en action | `⏳ chemin à compléter` (vidéo externe au dépôt) |
| **README** (ce document) | Explique le reste : emplacement de la base synthétique, architecture du projet, lanceur PONY, évaluation | `README.md` |
| **Photo du lanceur PONY** | Capture d'écran du pipeline qui vérifie, installe, teste et lance tout | `data/photo/` |

La vidéo montre les **cas demandés** en situation réelle ; ce document décrit la
structure et la méthodologie qui rendent ces cas possibles.

---

## 2. Où se trouve la base de données synthétisée ?

La base synthétique est dans **`data/synthetique/`** :

```
data/synthetique/
├── dataset_orientia_synthetique.csv   # 400 profils (260 étudiants + 140 professionnels)
├── generate_synthetic_data.py         # script de génération reproductible
└── README.md                          # méthodologie complète (règles, distributions, cohérence)
```

| Fichier | Contenu |
| ------- | ------- |
| `dataset_orientia_synthetique.csv` | **400 profils anonymisés** (`rep_synth_XXXX`) : série de bac, notes par matière, mention, matières/compétences/intérêts, métier visé, prérequis, parcours choisi, satisfaction, `referait_choix` |
| `generate_synthetic_data.py` | Génération **documentée et reproductible** (seed fixe), conforme aux critères réels de l'ISPM |
| `README.md` | Méthodologie : éligibilité des séries, distributions gaussiennes par série, boost d'affinité, profilage multi-hot, scores composites, modèle de satisfaction |

**Pourquoi ces données ?** Le ML exige **≥ 30 profils** ; le dataset en fournit 400,
statistiquement cohérents avec les règles académiques ISPM (séries autorisées par
parcours, corrélation notes → compétences, satisfaction corrélée à la cohérence du
profil).

---

## 3. Architecture du projet

Flux : **route → service → repository → domain**. Un étage n'appelle que son voisin
(clean architecture, backend d'abord).

![Architecture d'ORIENT'IA — boucle de collecte progressive](data/photo/boucle_collecte_progressive_orientia.png)

```
cliniqueExam/
├── scripts/                   # PONY : pony.sh (Linux/macOS) + pony.ps1 (Windows)
├── pony / pony.cmd            # raccourcis vers le lanceur
├── data/
│   ├── mapping_taxonomie_orientia.md    # 16 parcours / 5 catégories (référence)
│   ├── synthetique/                    # ⭐ base synthétique (voir section 2)
│   ├── sources/                        # corpus RAG (6 documents) + registre_sources.csv
│   ├── enquete/ & sondage/             # questionnaire + registre de collecte
│   └── photo/                          # 📸 photos (lanceur PONY, schéma de collecte)
├── backend/                   # API FastAPI
│   ├── main.py                # entrypoint + CORS + /health (état DB)
│   ├── config.py              # .env (GEMINI_API_KEY, DB_PATH, DATASET_PATH, ...)
│   ├── api/routes.py          # /chat /orienter /predict /comparer /prerequis /inspection /traces /moteurs
│   ├── api/schemas.py         # modèles Pydantic
│   ├── services/
│   │   ├── chat_service.py        # agent Gemini + 6 outils + politiques de refus
│   │   ├── questionnaire.py       # formulaire guidé à choix multiples
│   │   ├── orientation_service.py # hybridation : Prolog filtre → ML choisit → fusion 60/40
│   │   ├── prolog_service.py      # règles SWI-Prolog (pyswip) + trace des requêtes
│   │   ├── rules_fallback.py      # miroir Python des 16 parcours (fallback automatique)
│   │   ├── ml_service.py          # train() RF + LR + baseline, predict(profil)
│   │   ├── ml_features.py         # profil → vecteur de features (tolérant)
│   │   ├── rag_service.py         # RAG v2 : embeddings gemini/tfidf + citations
│   │   ├── llm_service.py         # Google Gemini (SDK google-genai)
│   │   ├── profiles.py / traces.py# profil de session + observabilité
│   │   └── inspection.py          # mode inspection (force_prolog, raisonnement en direct)
│   ├── repositories/          # base (interface) + sqlite + in_memory + fabrique
│   ├── knowledge_base/orientia_rules.pl  # base Prolog (16 parcours, contraintes, scores)
│   ├── evaluation/            # test_suite.json (34 cas) + run_evaluation.py → rapport
│   ├── notebooks/             # exploration, comparaison RF/LR, étude des biais (livrables)
│   └── tests/                 # 70 tests pytest
└── frontend/                  # Next.js (React)
    ├── lib/api.ts             # SEUL point de contact avec le backend
    ├── store/chat-store.ts    # Zustand (profil + historique en temps réel)
    └── components/chat/       # ChatMain, ChatSidebar, InspectionPanel...
```

### Pipeline de recommandation

1. **Prolog** élimine les parcours non éligibles (série de bac, prérequis) et calcule un
   score de compatibilité (matières / compétences / intérêts / métier).
2. **ML** fournit les probabilités de chaque parcours (RandomForest, si entraîné).
3. **Fusion** (`orientation_service`) : **60% proba ML + 40% score règles**.
4. **Explication** : motifs + description sourcée (RAG) ; blocages listés.
5. **Traçabilité** : chaque étape journalisée dans `traces` (SQLite).

### Dialogue d'orientation

Le chat combine l'agent Gemini et un **formulaire guidé à choix multiples** :
- Message libre (y compris le premier) → Gemini extrait le profil, pose les questions
  manquantes, puis recommande quand le profil est suffisant.
- Clic sur une option → réponse **prédéfinie sans Gemini** (`questionnaire.reponse_predictive`).
- La réponse contient `question`, `recommendation` et `profil` (mis à jour à chaque tour).

### Mode inspection

Quand le mode est actif, `/orienter` et `/chat` renvoient un bloc `inspection` :
filtrage Prolog (raisons de blocage), scores/motifs des règles, probabilités RandomForest,
détail de la fusion 60/40 et requêtes Prolog réellement exécutées. `force_prolog` oblige
SWI-Prolog sans repli silencieux.

---

## 4. Le lanceur PONY

PONY vérifie, installe, entraîne, teste et lance tout le projet en une commande.

![Lancement du pipeline PONY](data/photo/Capture%20d%E2%80%99%C3%A9cran%20du%202026-08-27%2015-17-53.png)

```bash
./pony                    # pipeline complet : check → setup → install → train → test → run
./pony check              # vérifie python, node, .env
./pony train              # entraîne RF + LR sur data/synthetique/ (≥30 profils requis)
./pony test               # pytest (70 tests) + eslint + vitest + build
./pony eval               # évaluation 34 cas : RAG + ML (+ --llm pour la fidélité LLM)
./pony resetdb            # supprime backend/clinique.db (recréée au redémarrage)
./pony run                # backend :8000 + frontend :3000
```

**Windows** : `.\pony.cmd` (→ `scripts/pony.ps1`). `pony` est un symlink vers `scripts/pony.sh`.

---

## 5. Évaluation (34 cas exigés par le sujet)

`./pony eval` exécute le jeu `backend/evaluation/test_suite.json` (**34 cas**
catégorisés) et écrit `backend/evaluation/rapport_evaluation.json`.

Répartition des 34 cas :

| Catégorie | Cas | Catégorie | Cas |
| --------- | --- | --------- | --- |
| Factuelles | 7 | Infos absentes | 4 |
| Comparaisons | 4 | Ambiguës | 3 |
| Recommandations ML | 5 | Sécurité / injection | 3 |
| Multi-sources | 4 | Biais | 2 |
| Refus de profilage | 2 | | |

Dernières mesures (voir `backend/evaluation/rapport_evaluation.json`) :

- **RAG** : précision top-1 **0.67**, top-3 **1.0** (15 cas évalués).
- **ML** : précision top-1 **1.0** sur les 5 cas de recommandation.

### Évaluation du modèle RandomForest (livrable ML)

Les figures d'évaluation du modèle (entraîné sur les 400 profils synthétiques)
sont générées par le notebook `backend/notebooks/01_exploration_et_modeles.ipynb`
et déposées dans `backend/notebooks/figures/`. Analyse complète dans
[`RAPPORT_01_exploration_et_modeles.md`](backend/notebooks/RAPPORT_01_exploration_et_modeles.md).

![Distribution des profils](backend/notebooks/figures/distributions_profils.png)
*Répartition des 400 profils par parcours, sexe et série de bac.*

![Comparaison des modèles](backend/notebooks/figures/comparaison_modeles.png)
*RF vs LogisticRegression : accuracy (↑) et log-loss (↓), baseline en pointillés
(accuracy ≈ 0.075 → ≈ 0.80–0.83).*

![Matrice de confusion (RF)](backend/notebooks/figures/matrice_confusion.png)
*Heatmap brute + normalisée : diagonale dominante, quelques classes fragiles
(`aee`, `emii`) liées à de faibles effectifs.*

![F1 par parcours](backend/notebooks/figures/f1_par_parcours.png)
*Précision / rappel / F1 par parcours — weighted F1 ≈ 0.81, plusieurs parcours à 1.00.*

![Importance des features (RF)](backend/notebooks/figures/importance_features.png)
*Top 20 des importances Gini : dominées par les notes et scores composites.*

![Analyse de biais (RF)](backend/notebooks/figures/analyse_biais.png)
*Accuracy par groupe (famille de bac, série, type, sexe) : les écarts proviennent
des notes corrélées à la série, d'où le rééquilibrage du jeu synthétique.*

**Éthique & sécurité** : le système refuse les critères discriminatoires, le profilage
psychologique et les injections, et rappelle que la recommandation *n'est pas une décision
officielle d'admission*. Ces refus sont testés dans `evaluation/test_suite.json`.

---

## 6. Démarrage rapide

```bash
./pony            # tout-en-un : vérif → install → train → test → run
```

À la main :

```bash
# Backend
cd backend
python3 -m venv .venv && ./.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env                 # puis éditer .env (GEMINI_API_KEY)
./.venv/bin/uvicorn main:app --reload --port 8000

# Frontend (autre terminal)
cd frontend
cp .env.example .env.local            # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install && npm run dev            # -> http://localhost:3000
```

API dispo sur http://localhost:8000 — docs interactives : http://localhost:8000/docs
Obtention de la clé Gemini : https://aistudio.google.com/apikey

---

## 7. Documentation & tests

| Sujet | Où |
| ----- | -- |
| Sommaire de la doc (débutants) | [`docs/README.md`](docs/README.md) |
| Architecture backend / frontend | [`docs/architecture/`](docs/architecture/) |
| Activer Gemini, ML, ajouter une feature | [`docs/tutorials/`](docs/tutorials/) |
| Méthodologie de la base synthétique | [`data/synthetique/README.md`](data/synthetique/README.md) |
| Notations ML, comparaison RF/LR, biais | [`backend/notebooks/RAPPORT_01_exploration_et_modeles.md`](backend/notebooks/RAPPORT_01_exploration_et_modeles.md) |

**Tests** : le plus simple est `./pony test` (pytest backend **70 tests** + vitest + lint + build).
