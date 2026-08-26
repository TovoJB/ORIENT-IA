# Architecture du frontend (expliquée simplement)

> Objectif de ce document : comprendre le frontend Next.js **sans aucun prérequis**.
> C'est la partie React du projet : l'interface de chat que voit l'utilisateur.

## 1. L'idée en une phrase

Le frontend est une **application web** : elle affiche une fenêtre de chat (copiée du template [square-ui](https://github.com/zerostaticthemes/square-ui/tree/master/templates-baseui/chat)), elle récupère ce que tape l'utilisateur, et elle **parle au backend** pour obtenir les réponses de l'IA et du ML.

```
Utilisateur ──► Interface React ──► lib/api.ts ──► Backend FastAPI (localhost:8000)
                    │                    │
                    ▼                    ▼
              affiche la réponse    /chat (IA) · /predict (ML)
```

Le frontend **ne sait pas** comment fonctionne Gemini ni le modèle ML. Il ne fait que **demander** au backend et **afficher** ce qui revient.

## 2. L'arborescence du frontend

```
frontend/
├── package.json                # les dépendances + les commandes (dev, build, test...)
├── next.config.ts              # réglages Next.js (vide = réglages par défaut)
├── vitest.config.ts            # réglages des tests frontend
├── tsconfig.json               # réglages TypeScript
├── app/                        # la page principale
│   ├── layout.tsx              #   le "cadre" (titre, thème clair/sombre)
│   ├── page.tsx                #   la page chat complète (sidebar + zone de chat)
│   └── globals.css             #   les styles (Tailwind)
├── components/                 # les briques visuelles
│   ├── chat/
│   │   ├── chat-main.tsx           #   LE chef d'orchestre de la zone de chat
│   │   ├── chat-welcome-screen.tsx #   l'écran d'accueil (avant la 1ère question)
│   │   ├── chat-conversation-view.tsx  # l'écran de discussion
│   │   ├── chat-input-box.tsx      #   la zone où on tape le message
│   │   ├── chat-message.tsx        #   une bulle de message (user / IA)
│   │   └── chat-sidebar.tsx        #   la barre latérale (historique)
│   ├── ui/                     #   petits composants génériques (bouton, zone de texte...)
│   └── theme-toggle.tsx        #   le bouton clair/sombre
├── store/
│   └── chat-store.ts           # la "mémoire" du frontend (Zustand)
├── lib/
│   ├── api.ts                  # LE pont vers le backend (fetch)
│   └── api.test.ts             #   + ses tests
├── hooks/
│   └── use-mobile.ts           # détecte si l'écran est petit (mobile)
└── mock-data/
    └── chats.ts                # exemples de conversations (démo)
```

## 3. Le trajet d'un message (de A à Z)

Quand l'utilisateur tape **"Bonjour"** et appuie sur Entrée :

```
1. chat-input-box.tsx  détecte la touche Entrée
        │  appelle onSend(message)
        ▼
2. chat-main.tsx       ajoute la bulle "Bonjour" à l'écran (en "user")
        │  appelle sendChatMessage("Bonjour") de lib/api.ts
        ▼
3. lib/api.ts          envoie une requête POST à http://localhost:8000/chat
        │  (avec {"message": "Bonjour"})
        ▼
4. Backend             appelle Gemini, renvoie {"reply": "...", "conversation_id": "..."}
        │
        ▼
5. lib/api.ts          lit la réponse et renvoie le texte
        │
        ▼
6. chat-main.tsx       ajoute la bulle de l'IA à l'écran
        │
        ▼
7. chat-conversation-view.tsx  affiche la conversation (les bulles + l'IA "réfléchit")
```

## 4. Les fichiers importants, un par un

### `app/page.tsx` — la page principale

Assemble les gros morceaux :
- à gauche, la **sidebar** (`ChatSidebar`) avec l'historique,
- au centre, **la zone de chat** (`ChatMain`) où tout se passe,
- en haut à droite, le bouton **clair/sombre**.

Sur mobile, la sidebar devient un panneau qui se cache (composant `Sheet`).

### `components/chat/chat-main.tsx` — LE chef d'orchestre

C'est **le fichier le plus important** à comprendre. Il contient :

| Élément | Rôle |
| ------- | ---- |
| `messages` (state) | la liste des bulles affichées à l'écran |
| `message` (state) | ce que l'utilisateur est en train de taper |
| `isLoading` (state) | est-ce que l'IA "réfléchit" encore ? (affiche "Thinking...") |
| `send(content)` | ajoute la bulle user, appelle le backend, ajoute la bulle IA |
| `handlePredict()` | appelle `/predict` et affiche le résultat du modèle ML |
| `handleReset()` | vide la conversation |

### `lib/api.ts` — LE pont vers le backend

C'est le **seul endroit** du frontend qui fait des requêtes réseau. Tout le reste du frontend appelle les fonctions de ce fichier. Si le backend change, on modifie uniquement ce fichier.

```ts
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function sendChatMessage(message: string): Promise<string> {
  const res = await fetch(`${API_URL}/chat`, {   // POST vers le backend
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history: [] }),
  });
  if (!res.ok) throw new Error(...);              // si erreur, on la propage
  const data = await res.json();
  return data.reply;                              // on renvoie juste le texte
}
```

L'URL du backend se configure dans un fichier `.env.local` :

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### `store/chat-store.ts` — la mémoire partagée (Zustand)

Sert surtout à la **sidebar** : la liste des conversations, celle qui est sélectionnée, archiver/supprimer. C'est de la "mémoire globale" accessible depuis n'importe quel composant.

### Les composants `chat/`

- **`chat-welcome-screen`** : l'écran de bienvenue avec la grande zone de saisie et les boutons de mode (Fast, In-depth...). Affiché tant que la conversation n'a pas commencé.
- **`chat-conversation-view`** : la vue discussion avec les bulles en haut et la petite zone de saisie en bas. Elle reçoit `messages`, `message`, `isLoading` et les fonctions `onSend`, `onReset`, `onPredict`.
- **`chat-input-box`** : la zone de saisie avec les boutons d'outils (**ML Predict** appelle `/predict`) et le sélecteur de modèle (Gemini...).
- **`chat-message`** : une bulle. Affiche l'avatar de l'IA à gauche, celle de l'utilisateur à droite, et le texte.
- **`chat-sidebar`** : la liste des conversations récentes/archivées avec les menus (renommer, archiver, supprimer).

### Les composants `ui/`

Des petits composants réutilisables (Bouton, Zone de texte, Avatar, Menu déroulant...). On les utilise partout mais **on ne les modifie presque jamais**.

## 5. Les tests du frontend

### `lib/api.test.ts` — les tests du pont réseau

Ces tests vérifient que `sendChatMessage` et `sendPrediction` envoient bien la bonne requête et gèrent les erreurs. Ils **simulent le réseau** (avec un faux `fetch`) : aucun serveur n'est nécessaire, c'est instantané.

### Comment lancer les tests et la qualité

```bash
cd frontend
npm test            # lance vitest (les tests de lib/api.test.ts)
npm run lint        # vérifie le style du code
npm run build       # vérifie les types TypeScript + compile le site
npm run dev         # démarre le serveur de dev (http://localhost:3000)
```

> Encore plus simple : depuis la racine du projet, `./pony test` lance **tout** (backend + frontend) d'un coup.

## 6. Communiquer entre composants (rapide)

Deux façons, à connaître sans tout retenir :

1. **Via les "props"** : un parent donne des valeurs à son enfant.
   Exemple : `ChatMain` donne `messages` et `onSend` à `ChatConversationView`.
   → Utilisé pour la zone de chat.

2. **Via le store Zustand** : n'importe quel composant lit/écrit la mémoire globale.
   → Utilisé pour la sidebar (qui a besoin des conversations).

Règle simple : si **deux frères** ont besoin des mêmes données (pas parent/enfant), on passe par le store.

## 7. Recette : comment lire un composant inconnu

1. **Regarde la première ligne** : `"use client"` (composant interactif) ou rien.
2. **Lis les imports** : ils disent de quoi il a besoin (composants `ui/`, `lib/api`, store).
3. **Regarde la signature** `function Xxx({...props})` : ce sont les "entrées" fournies par le parent.
4. **Cherche le `return (`** : c'est ce qui s'affiche à l'écran.
5. **Cherche les `onClick`, `onChange`** : ce sont les événements branchés.

---

👉 Ensuite :
- [`backend_structure.md`](backend_structure.md) → comprendre la partie serveur
- [`../tutorials/create_feature.md`](../tutorials/create_feature.md) → ajouter une fonctionnalité de bout en bout
