from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

PROFIL_SCIENTIFIQUE = {
    "serie_bac": "s",
    "environnement": "bureau",
    "note_mathematiques": "16",
    "note_spc": "15",
    "note_svt": "12",
    "note_francais": "11",
    "note_malagasy": "12",
    "note_langue_vivante": "11",
    "note_hg": "10",
    "note_philosophie": "10",
    "note_ses": "",
    "moyenne_generale": "4",
    "mention_diplome": "3",
    "matiere_mathematiques": "1",
    "matiere_informatique": "1",
    "competence_programmation": "1",
    "competence_logique": "1",
    "interet_technologie": "1",
    "interet_science": "1",
    "prerequis_bases_algo": "1",
    "prerequis_maths_avancees": "1",
    "metier_vise": "data_scientist",
}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_orienter_returns_classement():
    response = client.post("/orienter", json={"profil": PROFIL_SCIENTIFIQUE})
    assert response.status_code == 200
    data = response.json()
    assert data["classement"], "au moins un parcours recommandé"
    assert data["ml_utilise"] is True
    assert data["classement"][0]["parcours"] == "isaia"
    assert "methodologie" in data


def test_predict_returns_parcours():
    response = client.post("/predict", json={"profil": PROFIL_SCIENTIFIQUE})
    assert response.status_code == 200
    data = response.json()
    assert data["parcours"] == "isaia"
    assert 0 < data["confidence"] <= 1
    assert "probabilities" in data


def test_predict_without_model_returns_503(monkeypatch):
    monkeypatch.setattr("services.ml_service.modele_existe", lambda: False)
    response = client.post("/predict", json={"profil": PROFIL_SCIENTIFIQUE})
    assert response.status_code == 503


def test_comparer():
    response = client.post(
        "/comparer",
        json={"profil": PROFIL_SCIENTIFIQUE, "parcours_a": "isaia", "parcours_b": "iggia"},
    )
    assert response.status_code == 200
    data = response.json()
    assert set(data["parcours"]) == {"isaia", "iggia"}
    assert data["parcours"]["isaia"]["eligibile"] is True


def test_prerequis():
    response = client.post(
        "/prerequis", json={"profil": PROFIL_SCIENTIFIQUE, "parcours": "isaia"}
    )
    assert response.status_code == 200
    assert response.json()["prerequis_manquants"] == []


def test_sources_returns_registre():
    response = client.get("/sources")
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) >= 6
    for doc in docs:
        assert {"doc_id", "titre", "origine", "date", "statut"} <= set(doc)


def test_moteurs():
    response = client.get("/moteurs")
    assert response.status_code == 200
    data = response.json()
    assert data["moteur_regles"] in ("swipl", "fallback")
    assert data["moteur_embeddings"] in ("gemini", "tfidf", "aucun")


def test_inspection_endpoints():
    response = client.get("/inspection")
    assert response.status_code == 200
    assert response.json()["mode"] is False

    response = client.post("/inspection", json={"mode": True, "force_prolog": True})
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] is True and data["force_prolog"] is True
    assert "swipl_disponible" in data

    client.post("/inspection", json={"mode": False, "force_prolog": False})


def test_orienter_inspection_payload():
    from services import prolog_service

    client.post("/inspection", json={"mode": True, "force_prolog": False})
    response = client.post("/orienter", json={"profil": PROFIL_SCIENTIFIQUE})
    data = response.json()
    inspection = data["inspection"]
    assert inspection is not None
    assert inspection["moteur"] in ("swipl", "fallback")
    assert inspection["filtrage"]["possibles"]
    assert "isaia" in inspection["filtrage"]["possibles"]
    assert inspection["ml"]["utilise"] is True
    assert inspection["ml"]["probabilites"]
    assert inspection["fusion"]
    # les requêtes Prolog ne sont tracées que si le vrai moteur swipl est utilisé
    if prolog_service.USING_SWIPL:
        assert any(q["requete"].startswith("parcours_possibles") for q in inspection["requetes_prolog"])
    else:
        assert inspection["requetes_prolog"] == []


def test_orienter_force_prolog_sans_swipl():
    from services import prolog_service

    if prolog_service.USING_SWIPL:
        return  # SWI-Prolog disponible : le test ne s'applique pas

    client.post("/inspection", json={"mode": True, "force_prolog": True})
    response = client.post("/orienter", json={"profil": PROFIL_SCIENTIFIQUE})
    data = response.json()
    assert data["inspection"]["erreur_prolog"] is not None
    assert "SWI-Prolog" in data["inspection"]["erreur_prolog"]
    assert data["classement"] == []


def test_traces_logged():
    response = client.get("/traces")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_chat_message_libre_appelle_toujours_gemini(monkeypatch):
    """Tout message libre passe par l'agent Gemini, même le premier.
    Après la réponse Gemini, le backend attache automatiquement
    la prochaine question de formulaire non remplie."""
    from services import chat_service

    appel_llm = {"count": 0}

    def spy(session_id, message, history=None):
        appel_llm["count"] += 1
        return {"reply": "réponse LLM", "tools_used": [], "question": None, "recommendation": None}

    monkeypatch.setattr(chat_service, "chat_turn", spy)

    # 1er message : Gemini est appelé et le backend attache la 1ère question de formulaire
    first = client.post("/chat", json={"message": "Bonjour", "history": []}).json()
    assert appel_llm["count"] == 1
    assert first["question"] is not None  # auto-attach de la 1ère question manquante
    assert first["question"]["champ"] == "serie_bac"

    # 2ème message : Gemini toujours appelé
    client.post("/chat", json={"message": "j'ai un bac série C", "history": []})
    assert appel_llm["count"] == 2


def test_chat_rep_choix_sans_gemini(monkeypatch):
    """Un clic sur une option du formulaire est traité SANS Gemini.
    Un message libre appelle Gemini, puis le backend attache automatiquement
    la prochaine question de formulaire."""
    from services import chat_service

    appel_llm = {"count": 0}

    def spy(session_id, message, history=None):
        appel_llm["count"] += 1
        return {"reply": "x", "tools_used": [], "question": None, "recommendation": None}

    monkeypatch.setattr(chat_service, "chat_turn", spy)

    # 1er message libre : Gemini appelé (count=1), backend attache serie_bac
    first = client.post("/chat", json={"message": "Bonjour", "history": []}).json()
    assert appel_llm["count"] == 1
    conv = first["conversation_id"]

    # Clic sur le formulaire : PAS de Gemini
    r = client.post(
        "/chat", json={"answer": {"champ": "serie_bac", "valeur": "s"}, "conversation_id": conv}
    ).json()
    assert appel_llm["count"] == 1  # toujours 1, le clic n'appelle pas Gemini
    assert r["question"]["champ"] == "moyenne_generale"


def _repondre(client, conversation_id, champ, valeur):
    return client.post(
        "/chat",
        json={"answer": {"champ": champ, "valeur": valeur}, "conversation_id": conversation_id},
    ).json()


def test_chat_complet_recommande_sans_gemini():
    """Répondre à tout le questionnaire produit une recommandation, sans LLM."""
    first = client.post("/chat", json={"message": "Bonjour", "history": []}).json()
    conv = first["conversation_id"]
    reponses = [
        ("serie_bac", "s"),
        ("moyenne_generale", "4"),
        ("note_mathematiques", "17"),
        ("matieres", ["mathematiques", "informatique"]),
        ("competences", ["programmation", "logique"]),
        ("interets", ["technologie", "science"]),
        ("metier_vise", "data_scientist"),
        ("environnement", "bureau"),
        ("prerequis", ["bases_algo", "maths_avancees"]),
    ]
    dernier = None
    for champ, valeur in reponses:
        dernier = _repondre(client, conv, champ, valeur)
    assert dernier["termine"] is True
    assert dernier["recommendation"] is not None
    top1 = dernier["recommendation"]["classement"][0]["parcours"]
    assert top1 == "isaia"


def test_chat_renvoie_profil_collecte():
    """Chaque réponse /chat renvoie le profil de l'étudiant en cours de collecte."""
    first = client.post("/chat", json={"message": "Bonjour", "history": []}).json()
    assert first["profil"] == {}
    conv = first["conversation_id"]
    reponse = _repondre(client, conv, "serie_bac", "s")
    assert reponse["profil"]["serie_bac"] == "s"
    reponse2 = _repondre(client, conv, "moyenne_generale", "4")
    assert reponse2["profil"]["moyenne_generale"] == "4"
    assert reponse2["profil"]["serie_bac"] == "s"
