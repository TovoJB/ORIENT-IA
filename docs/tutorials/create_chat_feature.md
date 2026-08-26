# Tutoriel : reconstruire la fonctionnalité "Chat" pas à pas

> Objectif : te montrer **comment la fonctionnalité chat a réellement été construite**
> dans ce projet, dans quel ordre, quels fichiers ont été créés en premier,
> et comment on a vérifié chaque étape (y compris sur la base de données),
> jusqu'aux tests.
>
> C'est un **exemple rétroactif** : le code existe déjà, mais on le lit
> comme si on le créait pour la première fois. Quand tu veux créer TA fonctionnalité,
> reproduis **le même ordre et les mêmes vérifications**.

## La fonctionnalité en une image

```
POST /chat  {"message": "Bonjour"}
   │
   ▼
routes.py ──► llm_service.py ──► Google Gemini  (le cerveau)
   │              │
   │              └──► renvoie la réponse
   │
   ├──► repository (SQLite)  ──► on SAUVEGARDE le message + la réponse
   │
   ▼
réponse  {"reply": "...", "conversation_id": "..."}
```

Deux choses à retenir sur le chat :
- il **répond** grâce à l'IA (Gemini),
- il **se souvient** grâce à la base SQLite (chaque message est enregistré).

## L'ordre de création (à connaître par cœur)

Le chat a été créé **dans cet ordre** — et c'est l'ordre à suivre pour toute fonctionnalité :

| Étape | Fichier(s) | Rôle | On vérifie quoi ? |
| ----- | ---------- | ---- | ---------------- |
| 1 | `domain/entities.py` | les entités (Message, Conversation) | rien encore, c'est juste des définitions |
| 2 | `repositories/` (base, sqlite, in_memory, factory) | le stockage (SQLite) | **la structure de la base** (tables, données) |
| 3 | `services/llm_service.py` | appeler Gemini | le service répond (test manuel) |
| 4 | `api/schemas.py` | le format entrée/sortie | la validation |
| 5 | `api/routes.py` | la route `/chat` | **curl sur l'API** |
| 6 | `tests/` | les tests | `pytest` au vert |
| 7 | frontend (`lib/api.ts`, composants) | l'écran | le chat dans le navigateur |
| 8 | `./pony test` | tout vérifier | tout est vert |

> **Pourquoi les entités en premier ?** Parce que tout le reste (stockage, services,
> routes) va manipuler ces objets. Si la définition de "Message" est claire dès le départ,
> tout le code qui suit est plus simple.

---

## Étape 1 — Les entités (le vocabulaire métier)

**Fichier : `backend/domain/entities.py`** (créé en premier)

Avant d'écrire la moindre ligne de code qui tourne, on définit **les objets du métier** :
une conversation contient des messages ; un message a un rôle (`user` ou `assistant`),
un contenu et une date. On utilise `@dataclass` : une syntaxe Python très courte
pour créer une classe qui ne fait que "porter des données".

```python
@dataclass
class Message:
    role: str                                  # "user" ou "assistant"
    content: str                               # le texte
    timestamp: datetime = field(default_factory=datetime.now)  # horodatage auto

@dataclass
class Conversation:
    id: str                                    # identifiant unique
    messages: list[Message] = field(default_factory=list)      # les messages
```

Rien ne s'exécute encore : ce sont des **définitions**. Elles vont être utilisées
par le stockage (étape 2), les services (étape 3) et les routes (étape 5).

---

## Étape 2 — Le stockage : SQLite + vérification du modèle sur la base

C'est ici qu'intervient la **base de données**. On veut que chaque message soit
**enregistré pour de bon** (même si le serveur redémarre).

### 2a. Le contrat : `repositories/base.py`

On définit d'abord "ce que tout stockage doit savoir faire" : créer une conversation,
la retrouver, ajouter un message, vérifier qu'elle est vivante.

```python
class ConversationRepository(ABC):
    @abstractmethod
    def create(self) -> Conversation: ...
    @abstractmethod
    def get(self, conversation_id: str) -> Conversation | None: ...
    @abstractmethod
    def add_message(self, conversation_id, role, content) -> Conversation: ...
    @abstractmethod
    def health_check(self) -> bool: ...
```

### 2b. L'implémentation SQLite : `repositories/sqlite_repository.py`

Le "modèle de données" se matérialise en **2 tables** :

```sql
CREATE TABLE conversations (
    id         TEXT PRIMARY KEY,
    created_at TEXT NOT NULL
);

CREATE TABLE messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,          -- → référence à conversations.id
    role            TEXT NOT NULL,          -- "user" ou "assistant"
    content         TEXT NOT NULL,
    timestamp       TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
```

Le lien entre les deux tables est la clé `conversation_id` (une conversation = plusieurs messages).

### 2c. La fabrique : `repositories/conversation_repository.py`

Elle choisit quelle implémentation utiliser selon la config :

```python
def build_repository() -> ConversationRepository:
    if config.DB_PATH:                       # par défaut: clinique.db
        return SQLiteConversationRepository(config.DB_PATH)
    return InMemoryConversationRepository()  # alternative sans base de fichiers

conversation_repository = build_repository()
```

### ✅ VÉRIFICATION du modèle sur la base de données

On ne croit pas sur parole que la base est correcte : on **l'inspecte**.
Après avoir envoyé 2 messages, on ouvre `backend/clinique.db` et on regarde :

```bash
cd backend
./.venv/bin/python -c "
import sqlite3
conn = sqlite3.connect('clinique.db')

# 1. Quelles tables existent ?
print(conn.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'\").fetchall())
# → [('conversations',), ('messages',)]

# 2. Quelle est la structure exacte de la table messages ?
print(conn.execute(\"SELECT sql FROM sqlite_master WHERE name='messages'\").fetchone()[0])
# → CREATE TABLE messages (...)

# 3. Quelles données sont réellement enregistrées ?
for r in conn.execute('SELECT conversation_id, role, substr(content,1,30) FROM messages'):
    print(r)
# → ('4950d8f2-...', 'user', 'Bonjour')
# → ('4950d8f2-...', 'assistant', 'Salut !')
"
```

Ce que cette vérification nous apprend :
- ✅ les tables **existent** avec le bon nom,
- ✅ la structure (colonnes, clé étrangère) est **conforme au modèle**,
- ✅ les données **écrites par le code** sont bien **relisibles** → la persistance marche.

> Astuce : si tu as l'outil `sqlite3` installé, c'est encore plus direct :
> `sqlite3 backend/clinique.db ".tables"` et `sqlite3 backend/clinique.db ".schema messages"`.

---

## Étape 3 — Le service : appeler Gemini

**Fichier : `backend/services/llm_service.py`**

La logique "répondre intelligemment" vit dans un service dédié. Le projet utilise
le SDK officiel de Google et lit la clé dans `config` (jamais en dur dans le code).

```python
def ask_gemini(prompt: str, system_instruction: str | None = None) -> str:
    if not config.GEMINI_API_KEY:                        # pas de clé → message clair
        return "Erreur: GEMINI_API_KEY manquante. ..."
    try:
        response = _get_client().models.generate_content(
            model=config.GEMINI_MODEL, contents=prompt, config=request_config
        )
        return (response.text or "").strip()
    except Exception as exc:
        return f"Erreur Gemini: {exc}"                   # erreur → texte lisible
```

Deux points importants :
- la fonction **ne plante jamais** : en cas d'erreur elle renvoie un texte expliquant quoi faire,
- elle est **réutilisable** : le chat, le RAG, et toute future fonctionnalité peuvent l'appeler.

### ✅ Vérification (sans le serveur)

```bash
cd backend
./.venv/bin/python -c "from services import llm_service; print(llm_service.ask_gemini('Dis bonjour'))"
# → réponse de l'IA (ou un message d'erreur clair si la clé manque)
```

---

## Étape 4 — Les schémas API (le format de la requête / réponse)

**Fichier : `backend/api/schemas.py`**

L'API doit savoir **exactement** ce qu'elle accepte et ce qu'elle renvoie.
Pydantic s'en charge : si la requête n'est pas conforme, FastAPI renvoie une erreur `422`
automatiquement.

```python
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)   # obligatoire, non vide
    conversation_id: Optional[str] = None     # optionnel (on en crée une si absente)
    history: list[dict] = Field(default_factory=list)

class ChatResponse(BaseModel):
    reply: str                                # la réponse de l'IA
    conversation_id: str                      # l'identifiant de la conversation
```

### ✅ Vérification de la validation

```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{}'
# → {"detail":[...]}  (erreur 422 : le champ message est manquant)
```

---

## Étape 5 — La route : exposer `/chat` en HTTP

**Fichier : `backend/api/routes.py`**

La route est **volontairement courte** : elle orchestre les autres couches
(prompt, service, repository) mais ne contient aucune "intelligence".

```python
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    # 1. récupère des infos utiles dans la base RAG
    context = retriever.retrieve(request.message)
    # 2. construit le prompt avec le message + l'historique + le contexte
    prompt = _build_prompt(request.message, request.history, context)
    # 3. appelle Gemini
    reply = llm_service.ask_gemini(prompt, system_instruction=SYSTEM_INSTRUCTION)
    # 4. sauvegarde le message et la réponse en base (SQLite)
    conversation = conversation_repository.add_message(request.conversation_id, "user", request.message)
    conversation_repository.add_message(conversation.id, "assistant", reply)
    # 5. renvoie la réponse
    return ChatResponse(reply=reply, conversation_id=conversation.id)
```

### ✅ Vérification avec curl

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Bonjour, que peux-tu faire ?", "history": []}'
# → {"reply":"...","conversation_id":"9f8b..."}
```

Et maintenant, on peut **re-vérifier la base** : la conversation vient d'être
écrite par la vraie route, pas par un script de test. La persistance est prouvée
de bout en bout (étape 2 revisitée).

---

## Étape 6 — Les tests

**Fichiers : `backend/tests/`**

Règle : on teste **sans payer d'appels Gemini ni toucher au vrai fichier de base**.
Deux techniques :

1. **`monkeypatch`** → on simule `ask_gemini` pour tester la route sans Internet :

```python
def test_chat_uses_llm_service(monkeypatch):
    monkeypatch.setattr(llm_service, "ask_gemini", lambda *a, **k: "Réponse de test")
    response = client.post("/chat", json={"message": "bonjour", "history": []})
    assert response.status_code == 200
    assert response.json()["reply"] == "Réponse de test"
    assert response.json()["conversation_id"]
```

2. **Base en mémoire** → `conftest.py` bascule `DB_PATH=":memory:"` pour que les tests
   ne créent jamais de fichier. Et on teste le stockage SQLite séparément :

```python
def test_add_message_creates_conversation_when_missing(repo):
    conversation = repo.add_message(None, "user", "Bonjour")
    got = repo.get(conversation.id)
    assert len(got.messages) == 1            # le message est bien enregistré
    assert got.messages[0].content == "Bonjour"
```

Les fichiers de test du chat : `test_api.py` (les routes), `test_llm_service.py`
(la gestion d'erreur sans clé), `test_sqlite_repository.py` (la persistance).

### ✅ Vérification

```bash
cd backend
./.venv/bin/python -m pytest -q        # → 15 passed
```

---

## Étape 7 — Le frontend (l'écran)

**Fichier : `frontend/lib/api.ts`** — le pont vers le backend :

```ts
export async function sendChatMessage(message: string): Promise<string> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history: [] }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  const data = await res.json();
  return data.reply;
}
```

**Composants** : `chat-main.tsx` (le chef d'orchestre : messages, chargement,
appel à `sendChatMessage`), `chat-input-box.tsx` (la zone de saisie),
`chat-message.tsx` (la bulle), `chat-conversation-view.tsx` (l'écran de discussion).

Test frontend avec un `fetch` simulé (`frontend/lib/api.test.ts`) :

```ts
it("posts the message to /chat and returns the reply", async () => {
  mockFetchOnce({ reply: "Bonjour !", conversation_id: "abc" });
  const reply = await sendChatMessage("salut");
  expect(reply).toBe("Bonjour !");
});
```

### ✅ Vérification

```bash
cd frontend
npm test          # → 3 passed
```

---

## Étape 8 — La vérification finale

Depuis la racine du projet, **tout d'un coup** :

```bash
./pony test       # pytest + eslint + vitest + build  → tout vert
./pony run        # backend (:8000) + frontend (:3000)
```

Ouvre http://localhost:3000, envoie "Bonjour", puis vérifie que la conversation
a bien été **sauvegardée en base** :

```bash
sqlite3 backend/clinique.db "SELECT role, substr(content,1,40) FROM messages;"
```

---

## La recette réutilisable (à imprimer)

Pour **n'importe quelle** future fonctionnalité, dans cet ordre :

1. **`domain/entities.py`** → les objets métier (définitions pures).
2. **`repositories/`** → le stockage (SQLite ou autre) → **vérifie la base** (tables + données).
3. **`services/`** → la logique (LLM, ML, calculs...) → **vérifie par un test manuel**.
4. **`api/schemas.py`** → le format entrée/sortie → **vérifie la validation (422)**.
5. **`api/routes.py`** → la route HTTP → **vérifie avec curl**.
6. **`tests/`** → les tests (simule le LLM avec `monkeypatch`, la base avec `:memory:`) → **pytest vert**.
7. **Frontend** (`lib/api.ts` puis composants) → **vérifie dans le navigateur**.
8. **`./pony test`** → tout est vert.

👉 Une variante avec **tout le code complet** (fonctionnalité "Résumé") :
[`implementation_example.md`](implementation_example.md) ·
La version courte sans rétrospective : [`create_feature.md`](create_feature.md) ·
Comprendre les couches : [`../architecture/backend_structure.md`](../architecture/backend_structure.md)
