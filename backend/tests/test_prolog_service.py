from services import prolog_service, rules_fallback


def test_famille_bac():
    assert rules_fallback.famille_bac("s") == "scientifique"
    assert rules_fallback.famille_bac("ose") == "economique"
    assert rules_fallback.famille_bac("l") == "litteraire"
    assert rules_fallback.famille_bac("inconnue") is None


def test_parcours_possibles_scientifique():
    profil = {"serie_bac": "s", "prerequis_bases_algo": "1", "prerequis_maths_avancees": "1"}
    possibles = prolog_service.parcours_possibles(profil)
    assert "isaia" in possibles
    assert "caa" not in possibles  # littéraire
    assert "teh" not in possibles


def test_parcours_possibles_economique():
    profil = {"serie_bac": "ose"}
    possibles = prolog_service.parcours_possibles(profil)
    assert "caa" in possibles and "fic" in possibles and "emp" in possibles
    assert "iggia" in possibles  # série OSE autorisée (sans prérequis bloquant)
    assert "isaia" not in possibles


def test_prerequis_non_bloquants():
    # Depuis la mise à jour : les prérequis sont des suggestions, plus aucun
    # parcours n'est bloqué par un prérequis manquant.
    profil = {"serie_bac": "s"}  # pas de bases_algorithmique
    assert prolog_service.prerequis_manquants(profil, "isaia") == []
    assert prolog_service.prerequis_manquants(profil, "caa") == []


def test_suggestion_bonus_score():
    profil = {"serie_bac": "s", "prerequis_bases_algo": "1"}
    sans = rules_fallback.score_compatibilite({"serie_bac": "s"}, "esii")
    avec = rules_fallback.score_compatibilite(profil, "esii")
    assert avec["score"] == sans["score"] + 1
    assert "bases_algorithmique" in avec["suggestions"]


def test_swipl_suggestion_bonus():
    profil = {"serie_bac": "s", "prerequis_bases_algo": "1"}
    detail = prolog_service.explication(profil, "esii")
    assert "bases_algorithmique" in detail["suggestions"]
    assert detail["score"] >= 1


def test_metier_non_bloquant():
    # Le métier visé est un signal de score, JAMAIS un critère de blocage.
    profil = {"serie_bac": "s", "metier_vise": "ingenieur_ml"}
    possibles = prolog_service.parcours_possibles(profil)
    assert "isaia" in possibles       # prépare le métier visé
    assert "esii" in possibles        # ne le prépare pas, mais reste éligible
    assert len(possibles) > 1
    # isaia reste le premier au classement grâce au bonus métier (×3)
    classement = prolog_service.classement(profil, top_k=1)
    assert classement[0]["parcours"] == "isaia"


def test_classement_motifs():
    profil = {
        "serie_bac": "s",
        "prerequis_bases_algo": "1",
        "prerequis_maths_avancees": "1",
        "matiere_mathematiques": "1",
        "competence_programmation": "1",
        "interet_technologie": "1",
        "metier_vise": "data_scientist",
    }
    classement = prolog_service.classement(profil, top_k=3)
    assert classement, "au moins un parcours classé"
    top1 = classement[0]
    assert top1["parcours"] == "isaia"
    assert top1["motifs"]["metier_alignee"] is True
    assert top1["motifs"]["matieres"]  # matières communes non vides
    assert "competence_programmation" in top1["motifs"]["competences"]
    assert "competence_programmation->technologie" in top1["motifs"]["bonus_croise"]
