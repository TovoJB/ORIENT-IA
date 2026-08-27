from config import config
from services import chat_service, profiles


def test_tool_poser_question():
    result = chat_service.execute_tool("poser_question", {"champ": "serie_bac"}, "s1")
    assert result["champ"] == "serie_bac"
    assert result["question"] is not None
    assert result["question"]["multiple"] is False
    assert result["question"]["options"]


def test_tool_poser_question_inconnu():
    result = chat_service.execute_tool("poser_question", {"champ": "inconnu"}, "s1")
    assert result["question"] is None


def test_execute_tool_inconnu():
    result = chat_service.execute_tool("outil_inexistant", {}, "s1")
    assert "erreur" in result


def test_tool_enregistrer_profil_merges():
    chat_service.execute_tool(
        "enregistrer_profil", {"champ": "serie_bac", "valeur": "s"}, "session_test"
    )
    chat_service.execute_tool(
        "enregistrer_profil", {"champ": "metier_vise", "valeur": "data_scientist"}, "session_test"
    )
    profil = profiles.get_profile("session_test")
    assert profil.get("serie_bac") == "s"
    assert profil.get("metier_vise") == "data_scientist"


def test_tool_rechercher_docs():
    result = chat_service.execute_tool("rechercher_docs", {"query": "data scientist"}, "s1")
    assert "resultats" in result
    for hit in result["resultats"]:
        assert {"text", "titre", "origine", "date", "statut"} <= set(hit)


def test_tool_verifier_prerequis():
    chat_service.execute_tool(
        "enregistrer_profil", {"champ": "serie_bac", "valeur": "s"}, "s2"
    )
    result = chat_service.execute_tool("verifier_prerequis", {"parcours": "isaia"}, "s2")
    assert result["parcours"] == "isaia"
    assert result["eligibile"] in (True, False)


def test_chat_turn_without_key(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    result = chat_service.chat_turn("s3", "bonjour")
    assert "GEMINI_API_KEY" in result["reply"]
    assert result["tools_used"] == []


def test_chat_turn_gemini_error(monkeypatch):
    def fake_send(self, *args, **kwargs):
        raise RuntimeError("réseau simulé")

    monkeypatch.setattr(config, "GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr("services.chat_service.llm_service._get_client", lambda: None)
    result = chat_service.chat_turn("s4", "bonjour")
    assert "Erreur" in result["reply"]


def test_enregistrer_profil_valeur_invalide_serie_bac():
    """Une valeur de serie_bac hors liste (ex: 'x') doit être rejetée sans enregistrement."""
    result = chat_service.execute_tool(
        "enregistrer_profil", {"champ": "serie_bac", "valeur": "x"}, "s_invalid"
    )
    assert "erreur" in result
    assert "action_requise" in result
    # Le profil ne doit PAS contenir la valeur invalide
    import services.profiles as profiles
    profil = profiles.get_profile("s_invalid")
    assert profil.get("serie_bac") is None


def test_enregistrer_profil_valeur_valide_serie_bac():
    """Une valeur valide de serie_bac (ex: 'd') doit être enregistrée normalement."""
    result = chat_service.execute_tool(
        "enregistrer_profil", {"champ": "serie_bac", "valeur": "D"}, "s_valid"
    )
    # La valeur doit être normalisée en minuscule et enregistrée
    assert result.get("enregistre") == "serie_bac"
    assert result.get("valeur") == "d"
    import services.profiles as profiles
    profil = profiles.get_profile("s_valid")
    assert profil.get("serie_bac") == "d"

