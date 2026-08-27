"""Questionnaire guidé ORIENT'IA (formulaire à choix multiples).

Le dialogue d'orientation est piloté par une machine à états, PAS par le LLM :
- chaque question est prédéfinie avec ses options de choix multiples,
- la réponse est enregistrée dans le profil de session,
- quand le profil est complet, la recommandation est générée par les règles + ML
  (texte prédéfini formaté) SANS appeler Gemini.

Gemini n'est appelé que si nécessaire : questions libres posées par l'utilisateur
après la recommandation (explications, comparaisons...).
"""

from services import orientation_service, profiles
from services.rules_fallback import PARCOURS_DATA, famille_bac

# Options de métier : union des débouchés des 16 parcours
METIERS = sorted({m for data in PARCOURS_DATA.values() for m in data["metiers"]})

QUESTIONS: list[dict] = [
    {
        "champ": "serie_bac",
        "question": "Quelle est votre série de baccalauréat ?",
        "multiple": False,
        "options": [
            {"label": "Scientifique (C, D, S)", "value": "s"},
            {"label": "Littéraire (A1, A2, L)", "value": "l"},
            {"label": "Économique (OSE)", "value": "ose"},
            {"label": "Autre", "value": "autre"},
        ],
    },
    {
        "champ": "moyenne_generale",
        "question": "Quelle est votre moyenne générale approximative au bac ?",
        "multiple": False,
        "options": [
            {"label": "Moins de 10", "value": "1"},
            {"label": "10 à 12", "value": "2"},
            {"label": "12 à 14", "value": "3"},
            {"label": "14 à 16", "value": "4"},
            {"label": "16 à 20", "value": "5"},
        ],
    },
    {
        "champ": "matieres",
        "question": "Quelles sont vos matières préférées ? (plusieurs choix possibles)",
        "multiple": True,
        "options": [
            {"label": "Mathématiques", "value": "mathematiques"},
            {"label": "Physique / électronique", "value": "physique"},
            {"label": "Informatique / programmation", "value": "informatique"},
            {"label": "SVT / biologie", "value": "svt"},
            {"label": "Français / littérature", "value": "francais"},
            {"label": "Malagasy", "value": "malagasy"},
            {"label": "Histoire-Géo", "value": "hg"},
            {"label": "SES / économie", "value": "ses"},
            {"label": "Arts / dessin", "value": "arts"},
        ],
    },
    {
        "champ": "competences",
        "question": "Quelles compétences pensez-vous avoir ? (plusieurs choix possibles)",
        "multiple": True,
        "options": [
            {"label": "Logique / analyse", "value": "logique"},
            {"label": "Programmation", "value": "programmation"},
            {"label": "Expression écrite / orale", "value": "expression"},
            {"label": "Travail manuel / technique", "value": "manuelle"},
            {"label": "Relationnel / communication", "value": "relationnelle"},
            {"label": "Créativité", "value": "creativite"},
            {"label": "Organisation / gestion de projet", "value": "organisation"},
            {"label": "Esprit critique", "value": "esprit_critique"},
        ],
    },
    {
        "champ": "interets",
        "question": "Quels sont vos centres d'intérêt ? (plusieurs choix possibles)",
        "multiple": True,
        "options": [
            {"label": "Technologie / numérique", "value": "technologie"},
            {"label": "Science / recherche", "value": "science"},
            {"label": "Art / design", "value": "art"},
            {"label": "Santé", "value": "sante"},
            {"label": "Entrepreneuriat", "value": "entrepreneuriat"},
            {"label": "Environnement", "value": "environnement"},
            {"label": "Social / humanitaire", "value": "social"},
            {"label": "Sport", "value": "sport"},
        ],
    },
    {
        "champ": "metier_vise",
        "question": "Avez-vous un métier précis en tête ?",
        "multiple": False,
        "options": [
            {"label": "Oui, data scientist", "value": "data_scientist"},
            {"label": "Oui, ingénieur ML / IA", "value": "ingenieur_ml"},
            {"label": "Oui, développeur logiciel", "value": "developpeur"},
            {"label": "Oui, chef de projet", "value": "chef_de_projet"},
            {"label": "Oui, commercial / affaires", "value": "commercial_export"},
            {"label": "Oui, finance / comptabilité", "value": "analyste_financier"},
            {"label": "Oui, droit", "value": "juriste"},
            {"label": "Oui, environnement / agronomie", "value": "environnementaliste"},
            {"label": "Oui, tourisme / hôtellerie", "value": "directeur_hotel"},
            {"label": "Pas encore sûr", "value": ""},
        ],
    },
    {
        "champ": "environnement",
        "question": "Quel environnement de travail préférez-vous ?",
        "multiple": False,
        "options": [
            {"label": "Bureau / informatique", "value": "bureau"},
            {"label": "Relationnel / social", "value": "relationnel"},
            {"label": "Recherche / laboratoire", "value": "recherche"},
            {"label": "Terrain", "value": "terrain"},
        ],
    },
    {
        "champ": "prerequis",
        "question": "Parmi ces suggestions d'acquis (non bloquantes, elles renforcent le conseil), lesquelles possédez-vous ?",
        "multiple": True,
        "options": [
            {"label": "Bases en algorithmique", "value": "bases_algo"},
            {"label": "Bon niveau d'anglais", "value": "anglais"},
            {"label": "Mathématiques avancées", "value": "maths_avancees"},
        ],
    },
]

# champs à choix unique qui doivent être renseignés pour considérer le profil complet
SINGLE_CHAMPS = ["serie_bac", "moyenne_generale", "metier_vise", "environnement"]

# Options de note (mêmes seuils que l'ancienne question de maths)
NOTE_OPTIONS = [
    {"label": "0 à 8", "value": "6"},
    {"label": "8 à 12", "value": "10"},
    {"label": "12 à 16", "value": "14"},
    {"label": "16 à 20", "value": "17"},
]

# Les 3 matières de base par famille de bac (notes /20 demandées dans le chat)
MATIERES_BASE_PAR_FAMILLE: dict[str, list[tuple[str, str]]] = {
    "scientifique": [
        ("note_mathematiques", "en mathématiques"),
        ("note_spc", "en physique-chimie (SPC)"),
        ("note_svt", "en SVT / biologie"),
    ],
    "litteraire": [
        ("note_malagasy", "en malagasy"),
        ("note_francais", "en français"),
        ("note_philosophie", "en philosophie"),
    ],
    "economique": [
        ("note_ses", "en SES / économie"),
        ("note_mathematiques", "en mathématiques"),
        ("note_hg", "en histoire-géo"),
    ],
}

NOTE_LABELS: dict[str, str] = {
    "note_mathematiques": "Mathématiques", "note_spc": "Physique-Chimie (SPC)",
    "note_svt": "SVT / Biologie", "note_francais": "Français",
    "note_malagasy": "Malagasy", "note_langue_vivante": "Langue vivante",
    "note_hg": "Histoire-Géo", "note_philosophie": "Philosophie",
    "note_ses": "SES / Économie",
}

_SERIE_TO_FAMILLE: dict[str, str] = {
    "c": "scientifique", "d": "scientifique", "s": "scientifique",
    "a1": "litteraire",  "a2": "litteraire",  "l": "litteraire",
    "ose": "economique",
}


def _famille_from_serie(serie: str | None) -> str | None:
    """Retourne la famille de bac (scientifique/litteraire/economique) à partir de la série."""
    if not serie:
        return None
    return _SERIE_TO_FAMILLE.get(str(serie).lower().strip())


def _question_note(champ: str, sujet: str) -> dict:
    """Construit la question à choix multiples pour une note (sur 20)."""
    return {
        "champ": champ,
        "question": f"Vos résultats approximatifs {sujet} (sur 20) ?",
        "multiple": False,
        "options": NOTE_OPTIONS,
    }


def questions_notes(profil: dict) -> list[dict]:
    """Questions sur les notes des 3 matières de base de la série choisie.

    Sans série connue (ou série "autre"), aucune question de note n'est posée :
    le modèle gère les notes absentes (NaN + indicateurs *_presente).
    """
    famille = _famille_from_serie(profil.get("serie_bac"))
    return [
        _question_note(champ, sujet)
        for champ, sujet in MATIERES_BASE_PAR_FAMILLE.get(famille or "", [])
    ]


def questions_pour(profil: dict) -> list[dict]:
    """Questions ordonnées pour ce profil : série, moyenne, les 3 notes de base
    de la série, puis le reste du formulaire."""
    return QUESTIONS[:2] + questions_notes(profil) + QUESTIONS[2:]


def trouver_question(champ: str) -> dict | None:
    """Renvoie la question associée à un champ (prédéfinie ou note dynamique)."""
    q = next((question for question in QUESTIONS if question["champ"] == champ), None)
    if q:
        return q
    if champ.startswith("note_") and champ in NOTE_LABELS:
        return _question_note(champ, f"en {NOTE_LABELS[champ].lower()}")
    return None


def prochaine_question(profil: dict) -> dict | None:
    """Renvoie la première question encore sans réponse (avec ses options)."""
    for question in questions_pour(profil):
        champ = question["champ"]
        if question["multiple"]:
            prefix = {"matieres": "matiere", "competences": "competence",
                      "interets": "interet", "prerequis": "prerequis"}[champ]
            map_ = {"matieres": MATIERE_MAP, "competences": COMPETENCE_MAP,
                    "interets": INTERET_MAP, "prerequis": PREREQUIS_MAP}[champ]
            if not any(str(profil.get(col, "0")) == "1" for col in map_.values()):
                return question
        elif str(profil.get(champ, "")) == "":
            return question
    return None


def profil_est_complet(profil: dict) -> bool:
    return prochaine_question(profil) is None


def appliquer_reponse(profil: dict, champ: str, valeur) -> dict:
    """Enregistre la réponse d'une question dans le profil (retourne le profil)."""
    if champ in {"matieres", "competences", "interets", "prerequis"}:
        mapping = {
            "matieres": MATIERE_MAP, "competences": COMPETENCE_MAP,
            "interets": INTERET_MAP, "prerequis": PREREQUIS_MAP,
        }[champ]
        valeurs = valeur if isinstance(valeur, list) else [valeur]
        for option in valeurs:
            col = mapping.get(str(option))
            if col:
                profil[col] = "1"
    else:
        # Extraire la première valeur si c'est une liste (le frontend envoie des tableaux)
        single_val = valeur[0] if isinstance(valeur, list) and len(valeur) > 0 else valeur
        single_val = str(single_val) if single_val is not None else ""
        if champ == "serie_bac":
            profil["serie_bac"] = single_val
        elif champ == "moyenne_generale" or champ.startswith("note_"):
            profil[champ] = single_val
        elif champ == "environnement":
            profil["environnement"] = single_val
        elif champ == "metier_vise":
            profil["metier_vise"] = single_val
    return profil

# correspondance option -> colonne CSV / champ de profil
MATIERE_MAP = {
    "mathematiques": "matiere_mathematiques", "physique": "matiere_physique",
    "informatique": "matiere_informatique", "svt": "matiere_svt",
    "francais": "matiere_francais", "malagasy": "matiere_malagasy",
    "hg": "matiere_hg", "ses": "matiere_ses", "arts": "matiere_arts",
}
COMPETENCE_MAP = {
    "logique": "competence_logique", "programmation": "competence_programmation",
    "expression": "competence_expression", "manuelle": "competence_manuelle",
    "relationnelle": "competence_relationnelle", "creativite": "competence_creativite",
    "organisation": "competence_organisation", "esprit_critique": "competence_esprit_critique",
}
INTERET_MAP = {
    "technologie": "interet_technologie", "science": "interet_science",
    "art": "interet_art", "sante": "interet_sante",
    "entrepreneuriat": "interet_entrepreneuriat", "environnement": "interet_environnement",
    "social": "interet_social", "sport": "interet_sport",
}
PREREQUIS_MAP = {
    "bases_algo": "prerequis_bases_algo",
    "anglais": "prerequis_anglais",
    "maths_avancees": "prerequis_maths_avancees",
}


def question_payload(question: dict) -> dict:
    return {
        "champ": question["champ"],
        "question": question["question"],
        "multiple": question["multiple"],
        "options": question["options"],
    }


# Accusés de réception naturels par question (pour des réponses non robotiques)
ACK = {
    "serie_bac": "Bien reçu pour votre série.",
    "moyenne_generale": "Je note votre moyenne.",
    "matieres": "Très bien, vos matières préférées sont notées.",
    "competences": "Merci, vos compétences sont enregistrées.",
    "interets": "Vos centres d'intérêt sont bien notés.",
    "metier_vise": "Un objectif clair, c'est parfait !",
    "environnement": "Bien reçu pour l'environnement de travail.",
    "prerequis": "Merci, c'est tout noté.",
}

WELCOME_MESSAGE = (
    "Bonjour ! Je suis ORIENT'IA, votre assistant d'orientation à l'ISPM. "
    "Pour mieux vous orienter, je vais vous poser quelques questions."
)


def reponse_predictive(profil: dict, champ_repondu: str | None = None) -> dict:
    """Réponse prédéfinie : prochaine question OU recommandation finale.

    `champ_repondu` : question à laquelle l'utilisateur vient de répondre
    (utilisé pour produire un accusé de réception naturel).
    """
    next_question = prochaine_question(profil)
    if next_question is not None:
        if champ_repondu is None:
            reply = WELCOME_MESSAGE
        elif champ_repondu.startswith("note_"):
            reply = "C'est noté pour cette matière."
        else:
            reply = ACK.get(champ_repondu, "C'est noté !")
        return {
            "reply": reply,
            "question": question_payload(next_question),
            "recommendation": None,
            "terminé": False,
        }

    result = orientation_service.recommander(profil, top_k=3)
    return {
        "reply": _format_recommandation(result),
        "question": None,
        "recommendation": result,
        "terminé": True,
    }


def _format_recommandation(result: dict) -> str:
    lignes = [
        "Voici ma recommandation, construite à partir de votre profil :",
        "",
    ]
    for i, item in enumerate(result["classement"], start=1):
        lignes.append(f"{i}. {item['parcours'].upper()} ({item['categorie']})")
        motifs = []
        if item["motifs"]["matieres"]:
            motifs.append("matières : " + ", ".join(item["motifs"]["matieres"]))
        if item["motifs"]["competences"]:
            motifs.append("compétences : " + ", ".join(item["motifs"]["competences"]))
        if item["motifs"]["interets"]:
            motifs.append("intérêts : " + ", ".join(item["motifs"]["interets"]))
        if item["motifs"]["metier_alignee"]:
            motifs.append("métier visé préparé par ce parcours")
        if item["motifs"].get("suggestions"):
            motifs.append(
                "suggestions : " + ", ".join(item["motifs"]["suggestions"])
            )
        if motifs:
            lignes.append("   Pourquoi : " + " · ".join(motifs))
        if item["description"]:
            lignes.append(f"   {item['description'][:160]}")
        lignes.append("")
    if result["parcours_bloques"]:
        lignes.append(
            "Parcours non recommandés (prérequis manquants) : "
            + ", ".join(result["parcours_bloques"])
        )
        lignes.append("")
    lignes.append("Rappel : ORIENT'IA est une aide à la décision, "
                  "pas une décision officielle d'admission.")
    return "\n".join(lignes)


def profiler(session_id: str) -> dict:
    return profiles.get_profile(session_id)
