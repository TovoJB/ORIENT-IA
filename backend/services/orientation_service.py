"""Hybridation ORIENT'IA : Prolog filtre, ML choisit, fusion + explication.

Pipeline de recommandation (aligné sur la décision d'architecture) :
1. **Prolog** élimine les parcours non éligibles (série de bac, prérequis)
   et fournit un score symbolique + les motifs d'explication.
2. **ML** (si entraîné) fournit des probabilités sur les parcours.
3. **Fusion** pondérée : proba_ML (poids 0.6) + score règles normalisé (poids 0.4).
   Sans modèle entraîné : le classement repose uniquement sur les règles.
4. Chaque parcours renvoyé contient ses motifs, ses prérequis manquants et
   une description sourcée depuis le corpus RAG.

Mode inspection (`services/inspection`) : quand il est actif, `recommander`
renvoie en plus un bloc `inspection` contenant le raisonnement complet :
filtrage Prolog (avec raisons de blocage), scores/motifs des règles, probabilités
RandomForest et détail de la fusion, ainsi que les requêtes Prolog réellement
exécutées (mode "Prolog exclusif").
"""

from services import ml_service, prolog_service, rag_service
from services.inspection import PrologUnavailable, state as inspection_state
from services.rules_fallback import PARCOURS_DATA

POIDS_ML = 0.6
POIDS_REGLES = 0.4
DESCRIPTION_KEYWORDS = {
    "esii": "ESIIA", "isaia": "ISAIA", "imticia": "IMTICIA", "iggia": "IGGLIA",
    "caa": "CAA", "fic": "FIC", "dtja": "DTJA", "emp": "EMP",
    "iaa": "IAA", "pip": "PIP", "aee": "AEE",
    "emii": "EMII", "gca": "GCA", "icmp": "ICMP",
    "tee": "TEE", "teh": "TEH",
}


def _description(parcours: str) -> str:
    """Description sourcée du parcours (best-effort via RAG)."""
    keyword = DESCRIPTION_KEYWORDS.get(parcours, parcours.upper())
    hits = rag_service.retrieve(keyword, top_k=3)
    for hit in hits:
        if keyword.lower() in hit["text"].lower():
            return hit["text"].strip()
    return hits[0]["text"].strip() if hits else ""


def recommander(profil: dict, top_k: int = 3) -> dict:
    """Recommandation complète pour un profil (filtrage + fusion + explication)."""
    if inspection_state.mode:
        prolog_service.derniere_trace.clear()

    # 1. Contraintes symboliques (filtrage Prolog)
    try:
        possibles = prolog_service.parcours_possibles(profil)
        erreur_prolog = None
    except PrologUnavailable as exc:
        possibles = []
        erreur_prolog = str(exc)

    bloques = [
        {
            "parcours": code,
            "raisons": prolog_service.motifs_blocage(profil, code),
        }
        for code in PARCOURS_DATA
        if code not in possibles
    ]

    # 2. Probabilités ML (si modèle entraîné)
    probas_ml: dict[str, float] = {}
    ml_ok = False
    ml_detail = {"modele": None, "confiance": None}
    if ml_service.modele_existe():
        try:
            result = ml_service.predict(profil)
            probas_ml = result["probabilities"]
            ml_ok = True
            ml_detail = {"modele": result["model"], "confiance": result["confidence"]}
        except RuntimeError:
            pass

    # 3. Fusion et Décision (Prolog vs ML)
    detail_regles_par_code: dict[str, dict] = {}
    for code in possibles:
        detail_regles_par_code[code] = prolog_service.explication(profil, code)

    max_regles = max(
        (detail["score"] for detail in detail_regles_par_code.values()), default=1
    ) or 1

    # Trier par Prolog (score descendant, puis probabilité ML descendante si égalité)
    sorted_prolog = sorted(
        possibles,
        key=lambda c: (detail_regles_par_code[c]["score"], probas_ml.get(c, 0.0) if ml_ok else 0.0),
        reverse=True
    )
    top3_prolog = sorted_prolog[:3]

    # Trier par ML (probabilité descendante, puis score Prolog descendant si égalité)
    sorted_ml = sorted(
        possibles,
        key=lambda c: (probas_ml.get(c, 0.0) if ml_ok else 0.0, detail_regles_par_code[c]["score"]),
        reverse=True
    )
    top3_ml = sorted_ml[:3]

    # Politique de décision :
    # Si les top 3 sont identiques en contenu et ordre, on garde cet ordre.
    # Sinon, on priorise l'ordre de Prolog.
    if ml_ok and top3_ml == top3_prolog:
        final_order = top3_prolog
        methodologie = (
            "Décision par consensus : Les classements du modèle Random Forest (top 3) "
            "et de Prolog sont identiques. Affichage par ordre de consensus."
        )
    elif ml_ok:
        final_order = top3_prolog
        methodologie = (
            "Priorisation Prolog : Les classements diffèrent entre le modèle Random Forest "
            "et les règles Prolog. Priorité donnée à l'ordre de Prolog, avec affichage "
            "de la probabilité Random Forest associée."
        )
    else:
        final_order = sorted_prolog
        methodologie = (
            "Modèle ML non disponible. Recommandation basée uniquement sur les règles de compatibilité Prolog."
        )

    # Construire la liste de classement finale
    classement = []
    for i, code in enumerate(final_order):
        detail_regles = detail_regles_par_code[code]
        score_regles = float(detail_regles["score"])
        proba_ml = float(probas_ml.get(code, 0.0)) if ml_ok else 0.0

        # score_fusion doit décroître pour préserver notre ordre décidé
        score_fusion = float(len(final_order) - i)

        classement.append(
            {
                "parcours": code,
                "categorie": PARCOURS_DATA[code]["categorie"],
                "score_fusion": score_fusion,
                "proba_ml": round(proba_ml, 4) if ml_ok else None,
                "score_regles": int(score_regles),
                "motifs": {
                    "matieres": detail_regles["matieres"],
                    "competences": detail_regles["competences"],
                    "interets": detail_regles["interets"],
                    "metier_alignee": detail_regles["metier_alignee"],
                    "suggestions": detail_regles.get("suggestions", []),
                },
                "description": _description(code),
            }
        )

    result = {
        "profil": profil,
        "moteur_regles": prolog_service.moteur(),
        "ml_utilise": ml_ok,
        "ml": ml_detail,
        "parcours_possibles": possibles,
        "parcours_bloques": [b["parcours"] for b in bloques],
        "classement": classement[:top_k],
        "methodologie": methodologie,
    }

    if inspection_state.mode:
        result["inspection"] = {
            "mode": True,
            "force_prolog": inspection_state.force_prolog,
            "moteur": prolog_service.moteur(),
            "erreur_prolog": erreur_prolog,
            "profil": profil,
            "filtrage": {
                "possibles": possibles,
                "bloques": bloques,
            },
            "regles": [
                {
                    "parcours": code,
                    "score": detail["score"],
                    "motifs": detail,
                }
                for code, detail in detail_regles_par_code.items()
            ],
            "ml": {
                "utilise": ml_ok,
                "modele": ml_detail["modele"],
                "confiance": ml_detail["confiance"],
                "probabilites": {k: round(v, 4) for k, v in probas_ml.items()},
            },
            "fusion": [
                {
                    "parcours": item["parcours"],
                    "proba_ml": item["proba_ml"],
                    "score_regles_norm": round(
                        float(detail_regles_par_code[item["parcours"]]["score"])
                        / max_regles,
                        4,
                    ),
                    "score_regles": int(detail_regles_par_code[item["parcours"]]["score"]),
                    "score_fusion": item["score_fusion"],
                }
                for item in classement
            ],
            "methodologie": methodologie,
            "requetes_prolog": list(prolog_service.derniere_trace),
        }
    return result


def comparer(profil: dict, parcours_a: str, parcours_b: str) -> dict:
    """Comparaison côté à côte de deux parcours pour un profil donné."""
    result = {"parcours": {}}
    for code in (parcours_a, parcours_b):
        data = PARCOURS_DATA.get(code, {})
        expl = prolog_service.explication(profil, code)
        result["parcours"][code] = {
            "parcours": code,
            "categorie": data.get("categorie", ""),
            "matieres": data.get("matieres", []),
            "competences": data.get("competences", []),
            "prerequis": data.get("prerequis", []),
            "metiers": data.get("metiers", []),
            "prerequis_manquants": prolog_service.prerequis_manquants(profil, code),
            "eligibile": code in prolog_service.parcours_possibles(profil),
            "score_regles": expl.get("score", 0),
            "proba_ml": None,  # pas de probabilité ML hors orientation complète
            "description": _description(code),
            "motifs": {
                "matieres": expl.get("matieres", []),
                "competences": expl.get("competences", []),
                "interets": expl.get("interets", []),
                "metier_alignee": expl.get("metier_alignee", False),
                "suggestions": expl.get("suggestions", []),
            }
        }
    return result
