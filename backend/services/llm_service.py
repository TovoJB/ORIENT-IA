from functools import lru_cache

from google import genai

from config import config


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    return genai.Client(api_key=config.GEMINI_API_KEY)


def gemini_disponible() -> bool:
    return bool(config.GEMINI_API_KEY)


def ask_gemini(prompt: str, system_instruction: str | None = None) -> str:
    """Send a prompt to Google Gemini and return the text response.

    Returns a user-friendly error message if anything goes wrong.
    """
    if not config.GEMINI_API_KEY:
        return "Erreur: GEMINI_API_KEY manquante. Copiez .env.example vers .env et ajoutez votre clé."

    try:
        request_config = None
        if system_instruction:
            request_config = genai.types.GenerateContentConfig(
                system_instruction=system_instruction
            )
        response = _get_client().models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
            config=request_config,
        )
        return (response.text or "").strip()
    except Exception as exc:
        return f"Erreur Gemini: {exc}"


def generate_with_tools(
    system_instruction: str,
    history: list[dict],
    user_message: str,
    tools: list[dict],
) -> "genai.types.GenerateContentResponse":
    """Appelle Gemini avec des outils (function calling).

    `history` : liste de messages {"role": "user"|"assistant", "content": ...}.
    `tools`   : liste de dictionnaires Gemini FunctionDeclaration (déjà construits).
    """
    from google.genai import types

    def _role(role: str) -> str:
        return "model" if role == "assistant" else "user"

    contents = [
        types.Content(role=_role(m["role"]), parts=[types.Part(text=m["content"])])
        for m in history
    ]
    contents.append(
        types.Content(role="user", parts=[types.Part(text=user_message)])
    )
    request_config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=tools,
        temperature=0.3,
    )
    return _get_client().models.generate_content(
        model=config.GEMINI_MODEL,
        contents=contents,
        config=request_config,
    )
