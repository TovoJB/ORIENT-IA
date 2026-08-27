"""Service Prolog : contraintes et explications symboliques.

Préfère un vrai moteur SWI-Prolog via pyswip (moteur = 'swipl').
Si SWI-Prolog/pyswip est absent, bascule automatiquement sur le miroir
Python rules_fallback (même logique, moteur = 'fallback').

Mode inspection :
- `force_prolog` (voir services/inspection) désactive TEMPORAIREMENT le
  fallback et force l'utilisation EXCLUSIVE de SWI-Prolog. Sans SWI-Prolog,
  une PrologUnavailable est levée (jamais de repli silencieux dans ce mode).
- `derniere_trace` : liste des requêtes Prolog réellement exécutées lors du
  dernier calcul (pour l'affichage du raisonnement dans l'interface).

API publique (identique quel que soit le moteur) :
- moteur()                    -> "swipl" | "fallback"
- parcours_possibles(profil)  -> liste de codes parcours éligibles
- classement(profil, top_k)   -> parcours classés (score + motifs)
- explication(profil, parcours) -> motifs détaillés
- prerequis_manquants(profil, parcours) -> liste
"""

import os
import time
from pathlib import Path

from config import config
from services import rules_fallback
from services.inspection import PrologUnavailable, state as inspection_state

KB_PATH = Path(__file__).resolve().parent.parent / "knowledge_base" / "orientia_rules.pl"

# Trace du dernier raisonnement Prolog exécuté (mode inspection)
derniere_trace: list[dict] = []

# Emplacements possibles du binaire swipl (conda/brew...) si absent du PATH
SWIPL_BIN_DIRS = [
    config.SWIPL_BIN_DIR,
    "/home/tovo/miniconda3/envs/swipl/bin",
]


def _ensure_swipl_on_path() -> None:
    for directory in SWIPL_BIN_DIRS:
        if directory and Path(directory, "swipl").exists() and directory not in os.environ.get("PATH", ""):
            os.environ["PATH"] = directory + os.pathsep + os.environ["PATH"]


def _pyswip_disponible() -> bool:
    _ensure_swipl_on_path()
    try:
        import pyswip  # noqa: F401

        return True
    except Exception:
        return False


USING_SWIPL = _pyswip_disponible()


def _doit_utiliser_swipl() -> bool:
    """Le mode 'prolog exclusif' force swipl, sinon on préfère swipl s'il existe."""
    return inspection_state.force_prolog or USING_SWIPL


def moteur() -> str:
    return "swipl" if USING_SWIPL else "fallback"


def _exige_swipl() -> None:
    if not USING_SWIPL:
        raise PrologUnavailable(
            "SWI-Prolog n'est pas disponible : le mode 'Prolog exclusif' "
            "ne peut pas s'exécuter (installez SWI-Prolog)."
        )


# ---------------------------------------------------------------------
#  Moteur pyswip (SWI-Prolog) -- faits dynamiques assertés par profil
# ---------------------------------------------------------------------
def _swipl() -> "object":
    from pyswip import Prolog

    prolog = Prolog()
    prolog.consult(str(KB_PATH))
    return prolog


def _profil_facts(profil: dict) -> dict:
    """Traduit un profil en faits Prolog pour un étudiant frais.

    L'atome étudiant est UNIQUE (`s_<timestamp>`) : plusieurs sessions
    pyswip peuvent partager le même moteur SWI-Prolog, un atome fixe
    laisserait des faits résiduels d'une session à l'autre.

    Les faits sont fournis SANS point final : pyswip.assertz ajoute
    lui-même la syntaxe `assertz((fait)).`.
    """
    student = f"s_{int(time.time() * 1000)}"
    facts: list[str] = []

    serie = profil.get("serie_bac")
    if serie:
        facts.append(f"serie_bac({student}, {serie.lower()})")

    for matiere in rules_fallback._prefere(profil):
        facts.append(f"prefere({student}, {matiere})")
    for competence in rules_fallback._competences(profil):
        facts.append(f"possede({student}, {competence})")
    for interet in rules_fallback._interets(profil):
        facts.append(f"interet({student}, {interet})")
    for prereq in rules_fallback._prerequis_possedes(profil):
        facts.append(f"possede({student}, {prereq})")

    metier = rules_fallback._metier_vise(profil)
    if metier:
        facts.append(f"vise({student}, {metier})")

    return {"student": student, "facts": facts}


class _SwiplSession:
    """Session Prolog : faits du profil assertés puis retractés."""

    def __init__(self, profil: dict) -> None:
        self._prolog = _swipl()
        self._ctx = _profil_facts(profil)
        for fact in self._ctx["facts"]:
            self._prolog.assertz(fact)

    @property
    def student(self) -> str:
        return self._ctx["student"]

    @property
    def prolog(self) -> "object":
        return self._prolog

    def query(self, requete: str) -> list:
        resultats = list(self._prolog.query(requete))
        derivere_trace_append(requete, resultats)
        return resultats

    def close(self) -> None:
        for fact in self._ctx["facts"]:
            self._prolog.retractall(fact)
        self._prolog.retractall(f"serie_bac({self._ctx['student']}, _)")


def derivere_trace_append(requete: str, resultats: list) -> None:
    """Consigne une requête Prolog exécutée (mode inspection)."""
    if inspection_state.mode:
        derniere_trace.append(
            {
                "moteur": "swipl",
                "requete": requete,
                "resultats": [
                    {str(k): str(v) for k, v in r.items()} for r in resultats
                ],
            }
        )


def _swipl_parcours_possibles(profil: dict) -> list[str]:
    session = _SwiplSession(profil)
    try:
        return [
            str(result["P"])
            for result in session.query(f"parcours_possibles({session.student}, P)")
        ]
    finally:
        session.close()


def _swipl_explication(profil: dict, parcours: str) -> dict:
    session = _SwiplSession(profil)
    try:
        scores = session.query(
            f"score_compatibilite({session.student}, {parcours}, S)"
        )
        total = int(scores[0]["S"]) if scores else 0

        motifs: dict[str, list[str]] = {
            "matieres": [], "competences": [], "interets": [], "metiers": [], "suggestions": [], "bonus_croise": []
        }
        metier_alignee = False
        for row in session.query(f"motif({session.student}, {parcours}, M)"):
            terme = str(row["M"])
            if terme.startswith("matiere("):
                motifs["matieres"].append(terme[len("matiere("):-1])
            elif terme.startswith("competence("):
                motifs["competences"].append(terme[len("competence("):-1])
            elif terme.startswith("interet("):
                motifs["interets"].append(terme[len("interet("):-1])
            elif terme.startswith("metier("):
                motifs["metiers"].append(terme[len("metier("):-1])
                metier_alignee = True
            elif terme.startswith("suggestion("):
                motifs["suggestions"].append(terme[len("suggestion("):-1])
            elif terme.startswith("bonus_croise("):
                args = terme[len("bonus_croise("):-1].split(", ")
                if len(args) == 2:
                    motifs["bonus_croise"].append(f"{args[0]}->{args[1]}")

        return {
            "score": total,
            "matieres": list(dict.fromkeys(motifs["matieres"])),
            "competences": list(dict.fromkeys(motifs["competences"])),
            "interets": list(dict.fromkeys(motifs["interets"])),
            "metier_alignee": metier_alignee,
            "metiers": list(dict.fromkeys(motifs["metiers"])),
            "suggestions": list(dict.fromkeys(motifs["suggestions"])),
            "bonus_croise": list(dict.fromkeys(motifs["bonus_croise"])),
        }
    finally:
        session.close()


def _swipl_classement(profil: dict, top_k: int | None = None) -> list[dict]:
    possibles = _swipl_parcours_possibles(profil)
    results = []
    for code in possibles:
        detail = _swipl_explication(profil, code)
        results.append(
            {
                "parcours": code,
                "categorie": rules_fallback.PARCOURS_DATA[code]["categorie"],
                "score": detail["score"],
                "motifs": detail,
            }
        )
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k] if top_k else results


# ---------------------------------------------------------------------
#  API publique
# ---------------------------------------------------------------------
def parcours_possibles(profil: dict) -> list[str]:
    """Parcours éligibles (contraintes de série + prérequis)."""
    if _doit_utiliser_swipl():
        _exige_swipl()
        return _swipl_parcours_possibles(profil)
    return rules_fallback.parcours_possibles(profil)


def classement(profil: dict, top_k: int | None = None) -> list[dict]:
    """Parcours possibles classés par score de compatibilité (avec motifs)."""
    if _doit_utiliser_swipl():
        _exige_swipl()
        return _swipl_classement(profil, top_k=top_k)
    return rules_fallback.classement(profil, top_k=top_k)


def explication(profil: dict, parcours: str) -> dict:
    """Détail des motifs de compatibilité pour un parcours donné."""
    if _doit_utiliser_swipl():
        _exige_swipl()
        return _swipl_explication(profil, parcours)
    return rules_fallback.score_compatibilite(profil, parcours)


def prerequis_manquants(profil: dict, parcours: str) -> list[str]:
    """Prérequis non satisfaits pour un parcours (miroir des règles)."""
    return rules_fallback.blocage_prerequis(profil, parcours)


def motifs_blocage(profil: dict, parcours: str) -> list[str]:
    """Raisons de blocage d'un parcours (pour l'affichage).

    Seule la série de bac bloque désormais : le métier visé et les prérequis
    sont des suggestions non bloquantes (boost de score, jamais d'exclusion).
    """
    raisons: list[str] = []
    if rules_fallback.bloque_par_serie(profil, parcours):
        famille = rules_fallback.famille_bac(profil.get("serie_bac"))
        raisons.append(f"famille de bac '{famille}' non autorisée pour ce parcours")
    if not raisons and not profil.get("serie_bac"):
        raisons.append("série de bac inconnue")
    return raisons
