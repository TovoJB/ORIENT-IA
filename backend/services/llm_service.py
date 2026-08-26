from functools import lru_cache

from google import genai

from config import config


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    return genai.Client(api_key=config.GEMINI_API_KEY)


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
