# Tutoriel : activer Google Gemini

> Objectif : faire parler ton agent avec l'IA de Google (le chat ne répondra pas "Erreur Gemini" mais de vraies réponses).

## Pourquoi c'est nécessaire ?

Le projet utilise Google Gemini comme moteur d'IA. Pour l'utiliser, Google exige une **clé API** (comme un badge d'accès). Cette clé est **personnelle et secrète** : c'est pour ça qu'on ne l'écrit jamais dans le code, mais dans un fichier `.env`.

## Étape 1 — Créer la clé API (2 minutes)

1. Connecte-toi avec un compte Google sur : **https://aistudio.google.com/apikey**
2. Clique sur **"Create API key"** (créer une clé).
3. Choisis un projet (ou laisse le projet par défaut).
4. Copie la clé affichée (elle ressemble à : `AIzaSy...`).

> La version gratuite (Free tier) suffit largement pour un hackathon.

## Étape 2 — Mettre la clé dans le projet

1. Ouvre le fichier **`backend/.env`** (s'il n'existe pas, copie d'abord `.env.example` en `.env`).
2. Remplace `your_api_key_here` par ta vraie clé :

```env
GEMINI_API_KEY=AIzaSyTA0K3z3kJ_taMaCléRéelle_123456
GEMINI_MODEL=gemini-2.0-flash
```

3. Enregistre le fichier.

> Le fichier `.env` ne doit **jamais** être partagé ni mis sur GitHub (il est déjà dans `.gitignore`).

## Étape 3 — Vérifier que ça marche

Deux façons :

**Méthode A — via PONY :**

```bash
./pony check        # doit afficher "GEMINI_API_KEY configurée"
```

**Méthode B — test manuel (sans lancer le serveur) :**

```bash
cd backend
./.venv/bin/python -c "from services import llm_service; print(llm_service.ask_gemini('Bonjour, réponds en une phrase'))"
```

Tu dois voir une réponse de l'IA (pas un message "Erreur").

## Étape 4 — Tester dans le chat

```bash
./pony run          # démarre backend + frontend
```

Ouvre **http://localhost:3000** et envoie un message : l'IA doit répondre.

## Problèmes fréquents

| Symptôme | Cause | Solution |
| -------- | ----- | -------- |
| `Erreur Gemini: ...API key not valid` | clé fausse ou incomplète | recopie la clé sans espaces |
| `Erreur: GEMINI_API_KEY manquante` | `.env` absent ou vide | `cp backend/.env.example backend/.env` puis remets la clé |
| `400 model not found` | nom du modèle incorrect | change `GEMINI_MODEL` dans `.env` (ex: `gemini-2.5-flash`) |
| La clé a "fuité" | fichier `.env` poussé sur GitHub | régénère la clé sur AI Studio et efface l'historique |

## Comment le code utilise la clé ? (pour la curiosité)

1. `backend/config.py` lit `.env` et stocke la valeur dans `config.GEMINI_API_KEY`.
2. `backend/services/llm_service.py` la passe au SDK officiel :

```python
client = genai.Client(api_key=config.GEMINI_API_KEY)
response = client.models.generate_content(model=config.GEMINI_MODEL, contents=prompt)
```

La clé ne se retrouve **jamais** dans une URL publique ni dans le frontend.

👉 Ensuite : ajoute une vraie base de connaissances avec le RAG, ou ajoute ta propre fonctionnalité : [`create_feature.md`](create_feature.md)
