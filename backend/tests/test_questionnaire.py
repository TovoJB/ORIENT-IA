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
        ("note_spc", "15"),
        ("note_svt", "16"),
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


def test_notes_suivent_la_serie():
    # Série scientifique -> les 3 matières de base (maths, SPC, SVT) sont demandées
    profil = {"serie_bac": "s", "moyenne_generale": "4"}
    for i in range(3):
        q = questionnaire.prochaine_question(profil)
        assert q is not None and q["champ"].startswith("note_")
        questionnaire.appliquer_reponse(profil, q["champ"], "14")
    assert questionnaire.prochaine_question(profil)["champ"] == "matieres"

    # Série économique -> SES, maths, histoire-géo
    profil2 = {"serie_bac": "ose", "moyenne_generale": "4"}
    champs = []
    for _ in range(3):
        q = questionnaire.prochaine_question(profil2)
        champs.append(q["champ"])
        questionnaire.appliquer_reponse(profil2, q["champ"], "12")
    assert champs == ["note_ses", "note_mathematiques", "note_hg"]

    # Série inconnue / autre -> aucune question de note
    assert questionnaire.prochaine_question({"serie_bac": "autre", "moyenne_generale": "3"})["champ"] == "matieres"


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
        ("note_spc", "15"),
        ("note_svt", "16"),
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
