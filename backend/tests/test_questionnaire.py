from services import questionnaire


def test_premiere_question_est_serie():
    q = questionnaire.prochaine_question({})
    assert q is not None
    assert q["champ"] == "serie_bac"
    assert q["multiple"] is False
    assert q["options"]


def test_reponses_reparties():
    profil = {}
    for champ, valeur in [
        ("serie_bac", "s"),
        ("moyenne_generale", "4"),
        ("note_mathematiques", "17"),
        ("matieres", ["mathematiques", "informatique"]),
        ("competences", ["programmation"]),
        ("interets", ["technologie"]),
        ("metier_vise", "data_scientist"),
        ("environnement", "bureau"),
        ("prerequis", ["bases_algo", "maths_avancees"]),
    ]:
        questionnaire.appliquer_reponse(profil, champ, valeur)
    assert questionnaire.profil_est_complet(profil) is True
    assert questionnaire.prochaine_question(profil) is None


def test_profil_incomplet_poserait_question():
    profil = {"serie_bac": "s"}
    q = questionnaire.prochaine_question(profil)
    assert q["champ"] == "moyenne_generale"


def test_reponse_predictive_reco():
    profil = {}
    for champ, valeur in [
        ("serie_bac", "s"),
        ("moyenne_generale", "4"),
        ("note_mathematiques", "17"),
        ("matieres", ["mathematiques", "informatique"]),
        ("competences", ["programmation", "logique"]),
        ("interets", ["technologie", "science"]),
        ("metier_vise", "data_scientist"),
        ("environnement", "bureau"),
        ("prerequis", ["bases_algo", "maths_avancees"]),
    ]:
        questionnaire.appliquer_reponse(profil, champ, valeur)

    result = questionnaire.reponse_predictive(profil)
    assert result["terminé"] is True
    assert result["question"] is None
    assert result["recommendation"] is not None
    assert result["recommendation"]["classement"][0]["parcours"] == "isaia"
    assert "officielle d'admission" in result["reply"]
