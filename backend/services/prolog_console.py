"""Banc de test Prolog : explorer le raisonnement d'orientia_rules.pl.

Utilisé par la page dédiée du frontend (`/prolog`) pour tester la base de
règles sur un profil étudiant construit via un formulaire :
- `tester(profil)` : exécute le raisonnement complet et renvoie les faits
  assertés, l'éligibilité (possibles/bloqués + raisons), les scores de
  compatibilité avec leurs motifs, ainsi que toutes les requêtes Prolog
  réellement exécutées (moteur SWI-Prolog).
- `requete_brute(profil, requete)` : console interactive — exécute une
  requête Prolog arbitraire contre les faits du profil.

Quand SWI-Prolog n'est pas disponible et que `force_prolog` est désactivé,
le raisonnement est simulé par le miroir Python `rules_fallback` et `moteur`
vaut "fallback" (aucune requête Prolog n'est alors capturée).
"""

from services import prolog_service, rules_fallback
from services.inspection import PrologUnavailable, state as inspection_state
from services.rules_fallback import PARCOURS_DATA

# Atome lisible affiché à la place du vrai identifiant de session (s_<timestamp>)
ETUDIANT_LISIBLE = "etudiant"


def _formater_resultats(resultats: list) -> list[dict]:
    """Convertit les résultats pyswip en dictionnaires {variable: valeur}."""
    return [{str(k): str(v) for k, v in row.items()} for row in resultats]


def _afficher(requete: str, student: str) -> str:
    """Rend une requête lisible : remplace l'identifiant de session par `etudiant`."""
    return requete.replace(student, ETUDIANT_LISIBLE)


def _motifs(resultats: list) -> dict:
    """Répartit les motifs renvoyés par `motif/3` par type."""
    motifs: dict[str, list[str]] = {
        "matieres": [], "competences": [], "interets": [], "metiers": [], "suggestions": []
    }
    for row in resultats:
        terme = str(row["M"])
        if terme.startswith("matiere("):
            motifs["matieres"].append(terme[len("matiere("):-1])
        elif terme.startswith("competence("):
            motifs["competences"].append(terme[len("competence("):-1])
        elif terme.startswith("interet("):
            motifs["interets"].append(terme[len("interet("):-1])
        elif terme.startswith("metier("):
            motifs["metiers"].append(terme[len("metier("):-1])
        elif terme.startswith("suggestion("):
            motifs["suggestions"].append(terme[len("suggestion("):-1])
    return {
        "matieres": list(dict.fromkeys(motifs["matieres"])),
        "competences": list(dict.fromkeys(motifs["competences"])),
        "interets": list(dict.fromkeys(motifs["interets"])),
        "metier_alignee": bool(motifs["metiers"]),
        "metiers": list(dict.fromkeys(motifs["metiers"])),
        "suggestions": list(dict.fromkeys(motifs["suggestions"])),
    }


def _executer_swipl(profil: dict) -> tuple[list[str], list[dict], list[dict]]:
    """Exécute le raisonnement sur SWI-Prolog et capture faits + requêtes.

    Renvoie (possibles, scores, requetes) où chaque requête exécutée est
    journalisée avec ses résultats (pour l'affichage du raisonnement).
    """
    session = prolog_service._SwiplSession(profil)
    requetes: list[dict] = []
    try:
        requete = f"parcours_possibles({session.student}, P)"
        resultats = list(session.prolog.query(requete))
        requetes.append(
            {"requete": _afficher(requete, session.student), "resultats": _formater_resultats(resultats)}
        )
        possibles = [str(row["P"]) for row in resultats]

        scores: list[dict] = []
        for code in possibles:
            requete_score = f"score_compatibilite({session.student}, {code}, S)"
            res_score = list(session.prolog.query(requete_score))
            requetes.append(
                {"requete": _afficher(requete_score, session.student), "resultats": _formater_resultats(res_score)}
            )
            score = int(res_score[0]["S"]) if res_score else 0

            requete_motif = f"motif({session.student}, {code}, M)"
            res_motif = list(session.prolog.query(requete_motif))
            requetes.append(
                {"requete": _afficher(requete_motif, session.student), "resultats": _formater_resultats(res_motif)}
            )

            scores.append(
                {
                    "parcours": code,
                    "categorie": PARCOURS_DATA[code]["categorie"],
                    "score": score,
                    "motifs": _motifs(res_motif),
                }
            )
        scores.sort(key=lambda item: item["score"], reverse=True)
        return possibles, scores, requetes
    finally:
        session.close()


def _simuler_fallback(profil: dict) -> tuple[list[str], list[dict]]:
    """Simule le raisonnement via le miroir Python (aucune requête Prolog)."""
    possibles = rules_fallback.parcours_possibles(profil)
    scores = [
        {
            "parcours": code,
            "categorie": PARCOURS_DATA[code]["categorie"],
            "score": detail["score"],
            "motifs": detail,
        }
        for code in possibles
        for detail in [rules_fallback.score_compatibilite(profil, code)]
    ]
    scores.sort(key=lambda item: item["score"], reverse=True)
    return possibles, scores


def _raisons_blocage(profil: dict, code: str) -> list[str]:
    """Raisons de non-éligibilité d'un parcours (via les règles miroir)."""
    return prolog_service.motifs_blocage(profil, code)


def tester(profil: dict, force_prolog: bool | None = None) -> dict:
    """Raisonnement Prolog complet sur un profil étudiant.

    `force_prolog` : si True, exige le moteur SWI-Prolog (une
    `PrologUnavailable` est alors remontée dans `erreur_prolog`) ; par défaut,
    respecte l'état global du mode inspection.
    """
    force = force_prolog if force_prolog is not None else inspection_state.force_prolog
    ctx = prolog_service._profil_facts(profil)
    faits = [fact.replace(ctx["student"], ETUDIANT_LISIBLE) for fact in ctx["facts"]]

    if prolog_service.USING_SWIPL or force:
        moteur = "swipl"
        try:
            prolog_service._exige_swipl()
            possibles, scores, requetes = _executer_swipl(profil)
            erreur_prolog = None
        except PrologUnavailable as exc:
            possibles, scores, requetes = [], [], []
            erreur_prolog = str(exc)
    else:
        moteur = "fallback"
        erreur_prolog = None
        possibles, scores = _simuler_fallback(profil)
        requetes = []

    bloques = [
        {"parcours": code, "raisons": _raisons_blocage(profil, code)}
        for code in PARCOURS_DATA
        if code not in possibles
    ]

    return {
        "moteur": moteur,
        "force_prolog": force,
        "swipl_disponible": prolog_service.USING_SWIPL,
        "erreur_prolog": erreur_prolog,
        "profil": profil,
        "faits": faits,
        "eligibilite": {"possibles": possibles, "bloques": bloques},
        "scores": scores,
        "requetes": requetes,
    }


def requete_brute(profil: dict, requete: str) -> dict:
    """Console Prolog : exécute une requête arbitraire sur les faits du profil.

    Nécessite SWI-Prolog (pyswip). En l'absence du moteur, un message
    d'erreur explicite est renvoyé (jamais de repli silencieux).
    """
    if not prolog_service.USING_SWIPL:
        return {
            "moteur": "fallback",
            "requete": requete,
            "resultats": [],
            "erreur": (
                "SWI-Prolog est indisponible : la console de requêtes brutes "
                "nécessite le moteur pyswip."
            ),
        }
    session = prolog_service._SwiplSession(profil)
    try:
        resultats = list(session.prolog.query(requete))
        return {
            "moteur": "swipl",
            "requete": _afficher(requete, session.student),
            "resultats": _formater_resultats(resultats),
            "erreur": None,
        }
    except Exception as exc:  # noqa: BLE001 — requête invalide côté utilisateur
        return {
            "moteur": "swipl",
            "requete": requete,
            "resultats": [],
            "erreur": str(exc),
        }
    finally:
        session.close()
