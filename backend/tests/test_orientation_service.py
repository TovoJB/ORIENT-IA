from services import orientation_service

PROFIL = {
    "serie_bac": "s",
    "environnement": "bureau",
    "prerequis_bases_algo": "1",
    "prerequis_maths_avancees": "1",
    "matiere_mathematiques": "1",
    "matiere_informatique": "1",
    "competence_programmation": "1",
    "interet_technologie": "1",
    "interet_science": "1",
    "metier_vise": "data_scientist",
}


def test_recommander_fusion():
    result = orientation_service.recommander(PROFIL, top_k=3)
    assert result["classement"]
    assert len(result["classement"]) <= 3
    top1 = result["classement"][0]
    assert top1["parcours"] == "isaia"
    assert top1["score_fusion"] > 0
    assert top1["description"], "une description sourcée est fournie"
    assert "methodologie" in result


def test_recommander_filtrage_serie():
    profil_litteraire = {"serie_bac": "l", "metier_vise": "juriste"}
    result = orientation_service.recommander(profil_litteraire, top_k=5)
    codes = [c["parcours"] for c in result["classement"]]
    assert "caa" in codes or "dtja" in codes
    assert "isaia" not in codes


def test_comparer():
    result = orientation_service.comparer(PROFIL, "isaia", "iggia")
    parcours = result["parcours"]
    assert "isaia" in parcours and "iggia" in parcours
    assert parcours["isaia"]["eligibile"] is True
    assert "matieres" in parcours["isaia"]


def test_recommander_nouvelle_politique_decision():
    # Tester avec le modèle ML disponible
    result = orientation_service.recommander(PROFIL, top_k=3)
    assert result["classement"]
    
    # Vérifier que le score_fusion décroît et suit l'ordre de classement décidé
    scores = [item["score_fusion"] for item in result["classement"]]
    assert scores == sorted(scores, reverse=True)
    
    # Vérifier la présence de la méthodologie appropriée
    assert "consensus" in result["methodologie"].lower() or "priorisation" in result["methodologie"].lower() or "not disponible" in result["methodologie"].lower() or "non disponible" in result["methodologie"].lower()

