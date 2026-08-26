# Tutoriel : créer / ajouter une fonctionnalité

> Objectif : ajouter une fonctionnalité **complète** au projet, de l'API jusqu'à l'écran,
> sans rien casser. Chaque étape est expliquée pour un débutant.
>
> Exemple fil rouge tout au long du tutoriel : ajouter une route `/hello`
> qui renvoie un message personnalisé.
>
> 💡 **Tu préfères un exemple complet avec tout le code ?** Voir
> [`implementation_example.md`](implementation_example.md) : il montre la fonctionnalité
> "Résumé" de bout en bout, avec l'ordre exact des fichiers à créer, la forme des fonctions
> et les tests, étape par étape.

## Avant de commencer : l'ordre des couches

Une fonctionnalité traverse toujours **les mêmes étages**, dans cet ordre (schéma du restaurant dans [`../architecture/backend_structure.md`](../architecture/backend_structure.md)) :

```
1. domain/     → la définition de la donnée (optionnel)
2. api/schemas.py → ce que le client envoie / reçoit
3. services/   → la logique (le "cerveau")
4. api/routes.py → la route HTTP qui relie tout
5. frontend/   → l'écran qui appelle la route
6. tests       → vérifier que ça marche
```

On va faire ces étapes dans l'ordre. **Règle d'or : à chaque étape, on teste.**

---

## Étape 0 — Préparer l'environnement

```bash
./pony run        # ou au minimum: backend + frontend lancés
```

Lance les tests une première fois pour vérifier que tout est vert **avant** de toucher au code :

```bash
./pony test
```

Note le résultat (11 tests backend + tests frontend). On devra le retrouver à la fin, plus 2 nouveaux tests.

---

## Étape 1 — Définir les schémas (api/schemas.py)

Les schémas décrivent la forme des données qui entrent et sortent de l'API.
Ouvre **`backend/api/schemas.py`** et ajoute à la fin :

```python
class HelloRequest(BaseModel):
    name: str = Field(..., min_length=1)

class HelloResponse(BaseModel):
    message: str
```

- `HelloRequest` : l'utilisateur doit envoyer un `name` non vide.
- `HelloResponse` : l'API renverra un `message`.

**Test rapide** : ce n'est pas encore branché à une route, donc rien à tester ici — passe à la suite.

---

## Étape 2 — Écrire le service (services/)

Le service contient **la logique**. On n'écrit JAMAIS de logique compliquée dans une route ;
les routes restent fines et lisibles.

Crée le fichier **`backend/services/hello_service.py`** :

```python
def build_hello(name: str) -> str:
    """Construit un message de bienvenue simple."""
    return f"Bonjour {name} ! Bienvenue sur l'agent Clinique AI."
```

C'est volontairement minuscule : un service peut être aussi simple qu'une fonction.
La structure est là pour **grandir** avec le projet (quand le service fera de vraies choses :
appels LLM, calculs, bases de données...).

---

## Étape 3 — Ajouter la route (api/routes.py)

Ouvre **`backend/api/routes.py`**. Ajoute l'import du service en haut :

```python
from services import hello_service
```

puis, à la fin du fichier (avant ou après les autres routes, peu importe) :

```python
@router.post("/hello", response_model=HelloResponse)
async def hello(request: HelloRequest) -> HelloResponse:
    return HelloResponse(message=hello_service.build_hello(request.name))
```

Il faut aussi importer les nouveaux schémas. La ligne d'import devient :

```python
from api.schemas import (
    ChatRequest,
    ChatResponse,
    HelloRequest,
    HelloResponse,
    PredictRequest,
    PredictResponse,
)
```

**Test immédiat** — le serveur FastAPI se recharge tout seul (`--reload`). Vérifie :

```bash
curl -X POST http://localhost:8000/hello -H "Content-Type: application/json" -d '{"name":"Marie"}'
# → {"message":"Bonjour Marie ! Bienvenue sur l'agent Clinique AI."}
```

Ou bien ouvre **http://localhost:8000/docs** → clique sur `POST /hello` → "Try it out".

---

## Étape 4 — Ajouter un test backend (tests/test_api.py)

C'est **important** : un test protège ta fonctionnalité pour la suite du hackathon.
Ouvre **`backend/tests/test_api.py`** et ajoute :

```python
def test_hello_returns_message():
    response = client.post("/hello", json={"name": "Marie"})
    assert response.status_code == 200
    assert response.json() == {"message": "Bonjour Marie ! Bienvenue sur l'agent Clinique AI."}
```

Lance les tests backend :

```bash
cd backend
./.venv/bin/python -m pytest -q          # 12 passed (11 + le nouveau)
```

---

## Étape 5 — Brancher le frontend (frontend/lib/api.ts)

Le frontend ne parle JAMAIS au backend directement ; il passe par **`frontend/lib/api.ts`**.
Ajoute-y une fonction :

```ts
export async function sayHello(name: string): Promise<string> {
  const res = await fetch(`${API_URL}/hello`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  const data = await res.json();
  return data.message;
}
```

---

## Étape 6 — Ajouter un test frontend (lib/api.test.ts)

Ouvre **`frontend/lib/api.test.ts`** et ajoute (le fichier contient déjà l'aide `mockFetchOnce`) :

```ts
describe("sayHello", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the personalized message", async () => {
    mockFetchOnce({ message: "Bonjour Marie !" });
    const message = await sayHello("Marie");
    expect(message).toBe("Bonjour Marie !");
  });
});
```

Lance les tests frontend :

```bash
cd frontend
npm test
```

---

## Étape 7 — Brancher l'écran (facultatif mais utile pour la démo)

Pour rendre la fonctionnalité **visible**, on peut l'ajouter à l'interface.
Exemple minimal : un bouton **"Bonjour"** dans la barre d'outils de la zone de saisie.

Ouvre **`frontend/components/chat/chat-main.tsx`** :

1. Importe la fonction : `import { sendChatMessage, sendPrediction, sayHello } from "@/lib/api";`
2. Ajoute un gestionnaire à côté de `handlePredict` :

```tsx
const handleHello = async () => {
  if (isLoading) return;
  setIsLoading(true);
  try {
    const greeting = await sayHello("Visiteur");
    appendMessage(greeting, "ai");
  } catch (error) {
    appendMessage(`Erreur: ${(error as Error).message}`, "ai");
  } finally {
    setIsLoading(false);
  }
};
```

3. Passe `onHello={handleHello}` dans `ChatWelcomeScreen` et `ChatConversationView`,
   puis ajoute un bouton dans **`chat-input-box.tsx`** (copie le bouton "ML Predict"
   et remplace son libellé par "Bonjour").

> Astuce : quand tu modifies les "props" d'un composant (ce qu'il reçoit), il faut la déclarer
> dans l'interface TypeScript du composant (`interface ChatInputBoxProps { ... onHello: () => void }`),
> sinon TypeScript refusera la compilation.

Vérifie ensuite que tout compile :

```bash
cd frontend
npm run build
```

---

## Étape 8 — Le test de bout en bout avec PONY

C'est le moment de vérifier **que rien n'est cassé** :

```bash
./pony test
```

Tu devrais voir :

```
  [ OK ]  tests backend réussis
  [ OK ]  lint frontend propre
  [ OK ]  tests frontend réussis
  [ OK ]  build frontend OK
```

Puis lance le projet et teste la fonctionnalité dans le navigateur :

```bash
./pony run
```

---

## Récapitulatif : qu'est-ce qu'on a touché ?

| Fichier | Rôle |
| ------- | ---- |
| `backend/api/schemas.py` | les modèles `HelloRequest` / `HelloResponse` |
| `backend/services/hello_service.py` | la logique (`build_hello`) |
| `backend/api/routes.py` | la route `POST /hello` |
| `backend/tests/test_api.py` | le test backend |
| `frontend/lib/api.ts` | la fonction `sayHello` |
| `frontend/lib/api.test.ts` | le test frontend |
| `frontend/components/chat/*` | l'écran (bouton "Bonjour") |

C'est **exactement** cette recette pour TOUTE fonctionnalité future :
1. schéma → 2. service → 3. route → 4. test backend → 5. api.ts → 6. test frontend → 7. écran → 8. `./pony test`.

## Erreurs fréquentes et comment les corriger

| Erreur | Cause | Correction |
| ------ | ----- | ---------- |
| `422 Unprocessable Entity` | le `name` manque ou est vide dans la requête | respecte le schéma (min_length=1) |
| `ImportError: cannot import name 'HelloRequest'` | oubli d'import dans `routes.py` | ajoute le schéma à l'import |
| `Property 'onHello' does not exist` | prop non déclarée dans l'interface du composant | ajoute `onHello: () => void` dans l'interface |
| `build frontend KO` | erreur TypeScript | lis l'erreur, corrige, relance `npm run build` |

## Aller plus loin

- [Changer le modèle ML](add_ml_model.md)
- [Activer l'IA Gemini](setup_gemini.md)
- [Comprendre le backend](../architecture/backend_structure.md)
- [Comprendre le frontend](../architecture/frontend_structure.md)
- [Comment le chat a été construit (entités → SQLite → tests)](create_chat_feature.md)
