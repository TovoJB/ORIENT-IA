# Exemple d'implémentation complet : la fonctionnalité "Résumé"

> Objectif : montrer **la démarche complète** pour créer une fonctionnalité,
> du tout premier fichier jusqu'au test final. Rien n'est supposé connu.
>
> Fonctionnalité à créer : **`POST /summarize`** — l'utilisateur envoie un texte,
> l'agent le résume en 3 phrases grâce à Gemini, et renvoie le résumé.
>
> Résultat final attendu : un appel HTTP → un résumé, **et** un test vert.

## Avant tout : les 3 règles d'or

1. **On crée le backend d'abord**, le frontend ensuite. L'écran a besoin d'une API qui existe.
2. **On teste à chaque étape**, pas à la fin. Si une étape casse, on le voit tout de suite.
3. **Une nouvelle logique métier = un nouveau fichier dans `services/`.**
   Une nouvelle requête HTTP = un ajout dans `api/routes.py` (fichier existant).
   Un nouveau format de données = un ajout dans `api/schemas.py` (fichier existant).

## La règle : fichier existant ou nouveau fichier ?

| Ce que tu veux faire | Où ? | Fichier existant ou nouveau ? |
| -------------------- | ---- | ----------------------------- |
| Définir ce que le client envoie / reçoit | `backend/api/schemas.py` | **existant** (on ajoute) |
| Écrire la logique métier | `backend/services/` | **nouveau** (1 fichier = 1 métier) |
| Exposer la fonctionnalité en HTTP | `backend/api/routes.py` | **existant** (on ajoute) |
| Tester le backend | `backend/tests/` | **existant** (`test_api.py`) ou nouveau fichier de test |
| Parler au backend depuis l'écran | `frontend/lib/api.ts` | **existant** (on ajoute) |
| Tester le frontend | `frontend/lib/api.test.ts` | **existant** (on ajoute) |
| Afficher un bouton | `frontend/components/chat/` | **existant** (on modifie) |

> Si la fonctionnalité est un **nouveau domaine** (ex: gestion des patients), crée un
> nouveau fichier dans `services/` ET un nouveau fichier de test `backend/tests/test_patients.py`.

---

## Étape 0 — Vérifier qu'on part d'un état sain

```bash
./pony test        # tout doit être vert AVANT de commencer
```

On note : **15 tests backend** + **3 tests frontend**. À la fin, on en aura **16** et **4**.

---

## Étape 1 — Les schémas (format de la donnée)

**Fichier : `backend/api/schemas.py`** (existant → on ajoute à la fin)

La forme d'un schéma est toujours la même : une classe qui hérite de `BaseModel`,
avec des champs typés et des règles de validation.

```python
class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=10)   # le texte à résumer (min 10 caractères)

class SummarizeResponse(BaseModel):
    summary: str                            # le résumé renvoyé
```

---

## Étape 2 — Le service (la logique)

**Fichier : `backend/services/summarize_service.py`** (NOUVEAU — on le crée)

La forme d'une fonction de service est toujours :
**un nom clair + une docstring qui dit quoi + un `return` simple**.
Ici, le service réutilise le service existant `llm_service.ask_gemini(...)` :

```python
from services import llm_service


def summarize(text: str, max_sentences: int = 3) -> str:
    """Résume un texte en quelques phrases grâce à Gemini."""
    prompt = (
        f"Résume le texte suivant en {max_sentences} phrases maximum, "
        f"en gardant les informations essentielles.\n\nTexte:\n{text}"
    )
    return llm_service.ask_gemini(prompt)
```

Pourquoi un service ? Parce que la route reste **fine et lisible** :
elle ne fait qu'appeler `summarize(...)` et renvoyer le résultat. Tout ce qui est
"intelligent" vit dans le service et est testable indépendamment de HTTP.

---

## Étape 3 — La route (exposer en HTTP)

**Fichier : `backend/api/routes.py`** (existant → on ajoute)

**3a.** Complète l'import des schémas en haut du fichier :

```python
from api.schemas import (
    ChatRequest,
    ChatResponse,
    PredictRequest,
    PredictResponse,
    SummarizeRequest,
    SummarizeResponse,
)
```

**3b.** Ajoute l'import du service (avec les autres imports de services) :

```python
from services import llm_service, summarize_service
```

**3c.** Ajoute la route à la fin du fichier :

```python
@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest) -> SummarizeResponse:
    summary = summarize_service.summarize(request.text)
    return SummarizeResponse(summary=summary)
```

La forme d'une route est toujours : décorateur `@router.post("/nom", response_model=...)`,
une fonction `async` dont les paramètres sont les schémas de requête, et un `return`
construit à partir du schéma de réponse.

### Test immédiat (l'API se recharge toute seule grâce à `--reload`)

```bash
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "FastAPI est un framework Python moderne, rapide et facile à utiliser pour construire des API. Il est basé sur Starlette et Pydantic, ce qui lui permet de valider les données automatiquement et de générer une documentation interactive gratuite."}'
# → {"summary":"FastAPI est un framework Python rapide et moderne pour construire des API..."}
```

Ou plus simple : ouvre http://localhost:8000/docs → `POST /summarize` → *Try it out*.

---

## Étape 4 — Le test backend (crucial)

**Fichier : `backend/tests/test_api.py`** (existant → on ajoute)

On ne veut PAS appeler réellement Gemini pendant les tests (ça coûte de l'argent et ça
dépend du réseau). La technique : **simuler** `ask_gemini` avec `monkeypatch`.
Quand `summarize` appellera `ask_gemini(...)`, elle renverra le texte qu'on décide, sans taper sur Google.

```python
def test_summarize_uses_llm_service(monkeypatch):
    monkeypatch.setattr(
        llm_service, "ask_gemini", lambda *args, **kwargs: "Résumé de test."
    )
    response = client.post(
        "/summarize", json={"text": "Un texte de plus de dix caractères."}
    )
    assert response.status_code == 200
    assert response.json() == {"summary": "Résumé de test."}


def test_summarize_rejects_short_text():
    response = client.post("/summarize", json={"text": "court"})
    assert response.status_code == 422   # la validation du schéma refuse
```

Lance les tests :

```bash
cd backend
./.venv/bin/python -m pytest tests/test_api.py -q     # 7 passed (5 + les 2 nouveaux)
```

---

## Étape 5 — Le frontend : la fonction API

**Fichier : `frontend/lib/api.ts`** (existant → on ajoute)

La forme d'une fonction API frontend est toujours la même :
un `fetch` vers `${API_URL}/...`, une vérification d'erreur, un `return` de la donnée utile.

```ts
export async function summarizeText(text: string): Promise<string> {
  const res = await fetch(`${API_URL}/summarize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  const data = await res.json();
  return data.summary;
}
```

---

## Étape 6 — Le test frontend

**Fichier : `frontend/lib/api.test.ts`** (existant → on ajoute)

Le frontend a déjà un aide `mockFetchOnce` qui simule le réseau. On réutilise.

```ts
describe("summarizeText", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the summary", async () => {
    mockFetchOnce({ summary: "Résumé rapide." });
    const summary = await summarizeText("Un très long texte à résumer.");
    expect(summary).toBe("Résumé rapide.");
  });
});
```

```bash
cd frontend
npm test        # 4 passed (3 + le nouveau)
```

---

## Étape 7 — L'écran (pour montrer la fonctionnalité à la démo)

**Fichiers modifiés : `frontend/components/chat/`**

Le plus rapide : ajouter un bouton **"Résumer"** qui résume le message tapé.

1. **`chat-main.tsx`** — importer la fonction et ajouter le gestionnaire :

```tsx
import { sendChatMessage, sendPrediction, summarizeText } from "@/lib/api";

const handleSummarize = async () => {
  if (isLoading || !message.trim()) return;
  const textToSummarize = message;
  setMessage("");
  setIsLoading(true);
  try {
    const summary = await summarizeText(textToSummarize);
    appendMessage(`Résumé : ${summary}`, "ai");
  } catch (error) {
    appendMessage(`Erreur: ${(error as Error).message}`, "ai");
  } finally {
    setIsLoading(false);
  }
};
```

2. **Passer `onSummarize`** à `ChatWelcomeScreen` et `ChatConversationView`,
   **déclarer la prop** dans leurs interfaces TypeScript,
   puis **ajouter un bouton** dans `chat-input-box.tsx` (copie du bouton "ML Predict").

Rappel important : en TypeScript, une prop reçue doit TOUJOURS être déclarée dans
l'`interface` du composant, sinon le build échoue. Exemple :

```tsx
interface ChatInputBoxProps {
  // ...props existantes...
  onSummarize: () => void;      // ← à ajouter
}
```

---

## Étape 8 — La vérification finale (le grand chekpoint)

Depuis la racine du projet, tout en un :

```bash
./pony test
```

Résultat attendu :

```
  [ OK ]  tests backend réussis        (16 tests)
  [ OK ]  lint frontend propre
  [ OK ]  tests frontend réussis       (4 tests)
  [ OK ]  build frontend OK
```

Puis teste dans le navigateur :

```bash
./pony run        # http://localhost:3000 → envoie un texte → bouton "Résumer"
```

---

## Le récapitulatif en une image

```
backend/                            frontend/
│                                   │
├─ api/schemas.py       1. format   ├─ lib/api.ts            5. fonction API
├─ services/summarize_service.py  2. logique  ├─ lib/api.test.ts         6. test
│   (NOUVEAU fichier)                          └─ components/chat/*       7. bouton
├─ api/routes.py       3. route
├─ tests/test_api.py   4. test
```

**Ordre de création : 1 → 2 → 3 → 4 (backend), puis 5 → 6 → 7 (frontend), puis 8 (tests globaux).**

## La checklist à garder près de soi

- [ ] Le service est dans `services/` (fichier dédié), pas dans la route.
- [ ] La route est fine : elle appelle un service et renvoie un schéma.
- [ ] Le schéma valide les entrées (`Field(..., min_length=...)`).
- [ ] Le test backend simule le LLM avec `monkeypatch`.
- [ ] Le test frontend simule le réseau avec `mockFetchOnce`.
- [ ] `./pony test` est vert.

👉 Pour changer de modèle ML : [`add_ml_model.md`](add_ml_model.md) ·
Activer l'IA : [`setup_gemini.md`](setup_gemini.md) ·
Comprendre les couches : [`../architecture/backend_structure.md`](../architecture/backend_structure.md) ·
**Comment le chat a été construit (avec la base SQLite)** : [`create_chat_feature.md`](create_chat_feature.md)
