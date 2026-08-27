import pytest

from services import prolog_console, prolog_service

PROFIL_S = {
    "serie_bac": "s",
    "prerequis_bases_algo": "1",
    "prerequis_maths_avancees": "1",
    "matiere_mathematiques": "1",
    "matiere_informatique": "1",
    "competence_programmation": "1",
    "competence_logique": "1",
    "interet_technologie": "1",
    "interet_science": "1",
    "metier_vise": "data_scientist",
}


def test_tester_structure():
    result = prolog_console.tester(profil := {"serie_bac": "s"})
    assert result["profil"] == profil
    assert result["faits"] and "serie_bac(" in result["faits"][0]
    assert set(result["eligibilite"]) == {"possibles", "bloques"}
    assert result["scores"] == sorted(result["scores"], key=lambda s: s["score"], reverse=True)
    for code in result["eligibilite"]["possibles"]:
        assert code not in {b["parcours"] for b in result["eligibilite"]["bloques"]}


def test_tester_eligibilite_scientifique():
    result = prolog_console.tester(PROFIL_S)
    possibles = result["eligibilite"]["possibles"]
    assert "isaia" in possibles
    assert "caa" not in possibles  # série littéraire
    assert "teh" not in possibles


def test_tester_scores_motifs():
    result = prolog_console.tester(PROFIL_S)
    isaia = next(s for s in result["scores"] if s["parcours"] == "isaia")
    assert isaia["score"] >= 5
    assert "mathematiques" in isaia["motifs"]["matieres"]
    assert isaia["motifs"]["metier_alignee"] is True


@pytest.mark.skipif(
    prolog_service.USING_SWIPL,
    reason="SWI-Prolog disponible : le mode exclusif s'exécute réellement",
)
def test_tester_force_prolog_sans_swipl():
    result = prolog_console.tester({"serie_bac": "s"}, force_prolog=True)
    assert result["erreur_prolog"] is not None
    assert result["eligibilite"]["possibles"] == []
    assert result["moteur"] == "swipl"


@pytest.mark.skipif(
    not prolog_service.USING_SWIPL,
    reason="Requête brute : nécessite SWI-Prolog (pyswip)",
)
def test_requete_brute():
    result = prolog_console.requete_brute({"serie_bac": "s"}, "parcours(P)")
    assert result["erreur"] is None
    assert len(result["resultats"]) == 16
    assert result["moteur"] == "swipl"


@pytest.mark.skipif(
    not prolog_service.USING_SWIPL,
    reason="Requête brute : nécessite SWI-Prolog (pyswip)",
)
def test_requete_brute_invalide():
    result = prolog_console.requete_brute({"serie_bac": "s"}, "prédicat_inexistant(X)")
    assert result["erreur"] is not None
    assert result["resultats"] == []


def test_requete_brute_sans_swipl():
    if prolog_service.USING_SWIPL:
        pytest.skip("SWI-Prolog disponible : le repli n'est pas testable ici")
    result = prolog_console.requete_brute({"serie_bac": "s"}, "parcours(P)")
    assert result["erreur"] is not None
    assert result["moteur"] == "fallback"
