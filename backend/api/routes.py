from fastapi import APIRouter, HTTPException

from api.schemas import (
    ChatRequest,
    ChatResponse,
    CompareRequest,
    InspectionRequest,
    MlRfExploreRequest,
    PredictRequest,
    PredictResponse,
    PrerequisRequest,
    ProfilRequest,
    PrologQueryRequest,
    PrologTestRequest,
    RecommendationResponse,
    SourceDocument,
)
from repositories.conversation_repository import conversation_repository
from services import (
    chat_service,
    inspection,
    ml_rf_explorer,
    ml_service,
    orientation_service,
    profiles,
    prolog_console,
    prolog_service,
    questionnaire,
    rag_service,
    traces,
)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    conversation = conversation_repository.add_message(
        request.conversation_id, "user", request.message or ""
    )
    session_id = conversation.id

    if request.answer is not None:
        # Clic sur une option du formulaire -> réponse prédéfinie (PAS de Gemini)
        profil = questionnaire.appliquer_reponse(
            profiles.get_profile(session_id), request.answer.champ, request.answer.valeur
        )
        profiles.set_profile(session_id, profil)
        predictive = questionnaire.reponse_predictive(profil, request.answer.champ)
        reply = predictive["reply"]
        question = predictive["question"]
        recommendation = predictive["recommendation"]
        tools_used = []
        comparison = None
        traces.trace("chat:reponse_formulaire", session_id, {"champ": request.answer.champ})
    else:
        # Message libre → TOUJOURS l'agent Gemini, qui extrait le profil
        # et répond librement. Après sa réponse, si aucune question de formulaire
        # n'a été posée par l'outil poser_question ET qu'il n'y a pas encore de
        # recommandation, on détecte automatiquement la prochaine question de
        # formulaire non remplie et on l'attache à la réponse.
        result = chat_service.chat_turn(session_id, request.message or "", request.history)
        reply = result["reply"]
        question = result["question"]
        recommendation = result["recommendation"]
        tools_used = result["tools_used"]
        traces.trace("chat:llm", session_id, {
            "message": (request.message or "")[:120], "outils": tools_used
        })

        # Auto-attach : si Gemini n'a pas déclenché de formulaire ni de recommandation,
        # chercher la prochaine question manquante et l'afficher.
        # On évite d'attacher si le message concerne une comparaison de filières ou une demande d'info générale.
        is_info_request = False
        msg_lower = (request.message or "").lower()
        info_keywords = [
            "différence", "compare", "vs", "versus", "entre", "pourquoi",
            "expliqu", "qu'est-ce", "quest-ce", "c'est quoi", "information",
            "détail", "prerequis", "prérequis", "connaître", "connaitre"
        ]
        parcours_codes = [
            "esii", "isaia", "imticia", "iggia", "caa", "fic", "dtja", "emp",
            "iaa", "pip", "aee", "emii", "gca", "icmp", "tee", "teh"
        ]
        if any(kw in msg_lower for kw in info_keywords) or any(code in msg_lower for code in parcours_codes):
            is_info_request = True
        if any(t in tools_used for t in ["rechercher_docs", "comparer_parcours", "verifier_prerequis"]):
            is_info_request = True

        if question is None and recommendation is None and not is_info_request:
            profil_actuel = profiles.get_profile(session_id)
            next_q = questionnaire.prochaine_question(profil_actuel)
            if next_q is not None:
                question = questionnaire.question_payload(next_q)

        comparison = result.get("comparison")

    conversation_repository.add_message(conversation.id, "assistant", reply)
    return ChatResponse(
        reply=reply,
        conversation_id=conversation.id,
        tools_used=tools_used,
        question=question,
        recommendation=recommendation,
        comparison=comparison,
        termine=recommendation is not None,
        profil=profiles.get_profile(session_id),
        inspection=recommendation.get("inspection") if recommendation else None,
    )


@router.get("/inspection")
async def get_inspection() -> dict:
    return {
        "mode": inspection.state.mode,
        "force_prolog": inspection.state.force_prolog,
        "swipl_disponible": prolog_service.USING_SWIPL,
    }


@router.post("/inspection")
async def set_inspection(request: InspectionRequest) -> dict:
    inspection.state.mode = request.mode
    inspection.state.force_prolog = request.force_prolog
    traces.trace(
        "inspection:mode",
        None,
        {"mode": request.mode, "force_prolog": request.force_prolog},
    )
    return {
        "mode": inspection.state.mode,
        "force_prolog": inspection.state.force_prolog,
        "swipl_disponible": prolog_service.USING_SWIPL,
    }


@router.post("/predict", response_model=PredictResponse)
async def ml_predict(request: PredictRequest) -> PredictResponse:
    """Outil ML brut : probabilités du modèle sur un profil."""
    if not ml_service.modele_existe():
        raise HTTPException(
            status_code=503,
            detail="Aucun modèle entraîné. Lancez ./pony train (≥30 profils).",
        )
    result = ml_service.predict(request.profil)
    return PredictResponse(**result)


@router.post("/orienter", response_model=RecommendationResponse)
async def orienter(request: ProfilRequest) -> RecommendationResponse:
    """Recommandation complète : Prolog filtre, ML choisit, fusion + explication."""
    result = orientation_service.recommander(request.profil, top_k=3)
    return RecommendationResponse(**result)


@router.post("/comparer")
async def comparer(request: CompareRequest) -> dict:
    return orientation_service.comparer(request.profil, request.parcours_a, request.parcours_b)


@router.post("/prerequis")
async def prerequis(request: PrerequisRequest) -> dict:
    return {
        "parcours": request.parcours,
        "eligibile": request.parcours in prolog_service.parcours_possibles(request.profil),
        "prerequis_manquants": prolog_service.prerequis_manquants(request.profil, request.parcours),
    }


@router.get("/sources", response_model=list[SourceDocument])
async def sources() -> list[SourceDocument]:
    """Liste des documents du corpus (registre de traçabilité des sources)."""
    documents: list[SourceDocument] = []
    for chunk in rag_service.load_corpus():
        documents.append(
            SourceDocument(
                doc_id=chunk["doc_id"],
                titre=chunk["titre"],
                origine=chunk["origine"],
                date=chunk["date"],
                statut=chunk["statut"],
            )
        )
    # déduplique par doc_id en conservant le premier
    seen: set[str] = set()
    uniques: list[SourceDocument] = []
    for doc in documents:
        if doc.doc_id not in seen:
            seen.add(doc.doc_id)
            uniques.append(doc)
    return uniques


@router.get("/traces/{trace_id}")
async def trace_detail(trace_id: int) -> dict:
    trace = traces.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace introuvable")
    return trace


@router.get("/traces")
async def trace_list(session_id: str | None = None, limit: int = 100) -> list[dict]:
    return traces.list_traces(session_id=session_id, limit=limit)


@router.get("/moteurs")
async def moteurs() -> dict:
    """État des moteurs (observabilité) : règles, embeddings, ML."""
    return {
        "moteur_regles": prolog_service.moteur(),
        "moteur_embeddings": rag_service.moteur_embedding(),
        "ml_entraine": ml_service.modele_existe(),
    }


@router.post("/prolog/test")
async def prolog_test(request: PrologTestRequest) -> dict:
    """Banc de test : raisonnement Prolog complet sur un profil étudiant.

    Renvoie les faits assertés, l'éligibilité (possibles/bloqués avec raisons),
    les scores de compatibilité (motifs) et les requêtes Prolog exécutées.
    """
    return prolog_console.tester(request.profil, force_prolog=request.force_prolog)


@router.post("/prolog/query")
async def prolog_query(request: PrologQueryRequest) -> dict:
    """Console Prolog : exécute une requête arbitraire sur les faits du profil."""
    return prolog_console.requete_brute(request.profil, request.requete)


@router.post("/ml/rf/explore")
async def ml_rf_explore(request: MlRfExploreRequest) -> dict:
    """Explorateur Random Forest : analyse le modèle SAUVEGARDÉ
    (config.ML_MODEL_PATH) — métriques, importances et prédiction."""
    try:
        return ml_rf_explorer.explorer(request.profil or None)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
