"""Miroir Python de la base de règles Prolog (orientia_rules.pl).

Utilisé comme moteur de secours si SWI-Prolog/pyswip n'est pas disponible,
et comme source de vérité pour les scores de compatibilité.
Les faits doivent rester strictement alignés sur le fichier .pl.
"""

PARCOURS_DATA: dict[str, dict] = {
    "esii": {
        "categorie": "informatique",
        "matieres": ["electronique", "mathematiques", "programmation", "algorithmique"],
        "competences": ["competence_programmation", "competence_logique", "competence_manuelle"],
        "prerequis": ["bac_scientifique", "bases_algorithmique"],
        "metiers": ["ingenieur_electronique", "developpeur"],
        "interets": ["technologie", "science"],
    },
    "isaia": {
        "categorie": "informatique",
        "matieres": ["statistiques", "mathematiques", "programmation", "algorithmique"],
        "competences": ["competence_programmation", "competence_logique", "competence_esprit_critique"],
        "prerequis": ["bac_scientifique", "bases_algorithmique", "maths_avancees"],
        "metiers": ["data_scientist", "ingenieur_ml", "developpeur"],
        "interets": ["technologie", "science"],
    },
    "imticia": {
        "categorie": "informatique",
        "matieres": ["mathematiques", "multimedia", "programmation", "algorithmique"],
        "competences": ["competence_programmation", "competence_creativite", "competence_expression"],
        "prerequis": ["bases_algorithmique"],
        "metiers": ["developpeur_web", "chef_de_projet_multimedia"],
        "interets": ["technologie", "art"],
    },
    "iggia": {
        "categorie": "informatique",
        "matieres": ["gestion", "mathematiques", "programmation", "algorithmique"],
        "competences": ["competence_organisation", "competence_relationnelle", "competence_programmation", "competence_esprit_critique"],
        "prerequis": ["bases_algorithmique"],
        "metiers": ["chef_de_projet", "consultant", "developpeur"],
        "interets": ["technologie", "entrepreneuriat", "social"],
    },
    "caa": {
        "categorie": "affaires",
        "matieres": ["commerce", "langues", "economie_internationale"],
        "competences": ["competence_relationnelle", "competence_expression", "competence_organisation"],
        "prerequis": [],
        "metiers": ["commercial_export", "charge_affaires"],
        "interets": ["social", "entrepreneuriat"],
    },
    "fic": {
        "categorie": "affaires",
        "matieres": ["finance", "comptabilite", "economie", "langues"],
        "competences": ["competence_organisation", "competence_esprit_critique", "competence_logique"],
        "prerequis": [],
        "metiers": ["analyste_financier", "comptable"],
        "interets": ["entrepreneuriat", "social"],
    },
    "dtja": {
        "categorie": "affaires",
        "matieres": ["droit_public", "droit_prive", "langues"],
        "competences": ["competence_expression", "competence_esprit_critique", "competence_relationnelle"],
        "prerequis": [],
        "metiers": ["juriste", "assistant_juridique"],
        "interets": ["social"],
    },
    "emp": {
        "categorie": "affaires",
        "matieres": ["economie_internationale", "micro_economie", "macro_economie"],
        "competences": ["competence_esprit_critique", "competence_organisation", "competence_relationnelle"],
        "prerequis": [],
        "metiers": ["economiste", "charge_etudes"],
        "interets": ["entrepreneuriat", "social"],
    },
    "iaa": {
        "categorie": "biotech",
        "matieres": ["agroalimentaire", "biologie", "chimie"],
        "competences": ["competence_manuelle", "competence_esprit_critique"],
        "prerequis": ["bac_scientifique"],
        "metiers": ["technicien_agroalimentaire", "controleur_qualite"],
        "interets": ["science", "sante", "environnement"],
    },
    "pip": {
        "categorie": "biotech",
        "matieres": ["etudes_flore", "biologie", "agriculture"],
        "competences": ["competence_manuelle", "competence_esprit_critique", "competence_organisation"],
        "prerequis": ["bac_scientifique"],
        "metiers": ["horticulteur", "technicien_production_vegetale"],
        "interets": ["science", "environnement"],
    },
    "aee": {
        "categorie": "biotech",
        "matieres": ["etudes_faune", "agriculture_biologique", "environnement"],
        "competences": ["competence_esprit_critique", "competence_manuelle", "competence_organisation"],
        "prerequis": ["bac_scientifique"],
        "metiers": ["agronome", "environnementaliste"],
        "interets": ["science", "environnement"],
    },
    "emii": {
        "categorie": "genie",
        "matieres": ["electronique", "programmation", "mathematiques"],
        "competences": ["competence_manuelle", "competence_logique", "competence_programmation"],
        "prerequis": ["bac_scientifique", "bases_algorithmique"],
        "metiers": ["ingenieur_maintenance", "technicien_superieur"],
        "interets": ["technologie", "science"],
    },
    "gca": {
        "categorie": "genie",
        "matieres": ["dessin", "programmation", "mathematiques"],
        "competences": ["competence_creativite", "competence_manuelle", "competence_logique", "competence_organisation"],
        "prerequis": ["bac_scientifique", "bases_algorithmique"],
        "metiers": ["ingenieur_genie_civil", "conducteur_travaux"],
        "interets": ["art", "technologie"],
    },
    "icmp": {
        "categorie": "genie",
        "matieres": ["chimie", "sciences"],
        "competences": ["competence_esprit_critique", "competence_manuelle", "competence_logique"],
        "prerequis": ["bac_scientifique"],
        "metiers": ["technicien_laboratoire", "ingenieur_materiaux"],
        "interets": ["science", "environnement"],
    },
    "tee": {
        "categorie": "tourisme",
        "matieres": ["environnement", "tourisme", "ecologie"],
        "competences": ["competence_relationnelle", "competence_organisation", "competence_expression"],
        "prerequis": [],
        "metiers": ["gestionnaire_tourisme", "ecoguide"],
        "interets": ["environnement", "social"],
    },
    "teh": {
        "categorie": "tourisme",
        "matieres": ["hotelierie", "art_culinaire", "tourisme"],
        "competences": ["competence_relationnelle", "competence_organisation", "competence_expression", "competence_creativite"],
        "prerequis": [],
        "metiers": ["directeur_hotel", "responsable_restauration"],
        "interets": ["social"],
    },
}

# Liens compétence → intérêt thématique (bonus croisé)
# Si l'étudiant possède une compétence liée à un intérêt du parcours, bonus +1.
COMPETENCE_LIE_INTERET: dict[str, list[str]] = {
    "competence_programmation": ["technologie"],
    "competence_logique": ["technologie", "science"],
    "competence_manuelle": ["technologie"],
    "competence_esprit_critique": ["science"],
    "competence_creativite": ["art"],
    "competence_relationnelle": ["social"],
    "competence_expression": ["social"],
    "competence_organisation": ["entrepreneuriat"],
}

# Familles de bac accessibles par parcours
ACCESSIBLES = {
    "scientifique": {"esii", "isaia", "imticia", "iggia", "emii", "gca", "icmp", "iaa", "pip", "aee", "fic"},
    "litteraire": {"caa", "dtja", "tee", "teh"},
    "economique": {"caa", "fic", "emp", "iggia"},
}

SERIE_FAMILLE = {
    "c": "scientifique",
    "d": "scientifique",
    "s": "scientifique",
    "a1": "litteraire",
    "a2": "litteraire",
    "l": "litteraire",
    "ose": "economique",
}

# Prérequis dérivés automatiquement (pas besoin de les déclarer possédés)
PREREQUIS_AUTO = {"bac_scientifique"}


def famille_bac(serie: str | None) -> str | None:
    """Dérive la famille de bac depuis la série (None si inconnue)."""
    if not serie:
        return None
    return SERIE_FAMILLE.get(str(serie).lower().strip())


def _as_set(profil: dict, prefix: str) -> set[str]:
    """Récupère les clés multi-hot `prefix_*` à 1 dans le profil."""
    result = set()
    for key, value in profil.items():
        if key.startswith(prefix + "_") and str(value) in ("1", "true", "True", 1, True):
            result.add(key[len(prefix) + 1:])
    return result


def _metier_vise(profil: dict) -> str | None:
    value = profil.get("metier_vise")
    if not value:
        return None
    # Normalisation (le LLM peut écrire "data scientist" au lieu de "data_scientist")
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def _prefere(profil: dict) -> set[str]:
    """Matières préférées : colonnes matiere_* à 1, sinon le champ libre `matiere`."""
    return _as_set(profil, "matiere")


def _competences(profil: dict) -> set[str]:
    return {f"competence_{c}" for c in _as_set(profil, "competence")}


def _interets(profil: dict) -> set[str]:
    return _as_set(profil, "interet")


def _prerequis_possedes(profil: dict) -> set[str]:
    result = set()
    mapping = {
        "prerequis_bases_algo": "bases_algorithmique",
        "prerequis_anglais": "anglais",
        "prerequis_maths_avancees": "maths_avancees",
    }
    for key, atom in mapping.items():
        if str(profil.get(key, "0")) in ("1", "true", "True", 1, True):
            result.add(atom)
    return result


def bloque_par_serie(profil: dict, parcours: str) -> bool:
    """Vrai si la famille de bac du profil exclut le parcours."""
    famille = famille_bac(profil.get("serie_bac"))
    if famille is None:
        return False  # série inconnue : on ne bloque pas, on laisse le score décider
    return parcours not in ACCESSIBLES.get(famille, set())


def blocage_prerequis(profil: dict, parcours: str) -> list[str]:
    """Les prérequis sont des SUGGESTIONS NON BLOQUANTES (décision projet).

    Depuis la mise à jour des conditions d'admission, l'éligibilité repose
    UNIQUEMENT sur la série du bac (voir `accessibles`). Posséder une base en
    algorithmique (etc.) booste le score de compatibilité sans jamais bloquer.
    """
    return []


def parcours_possibles(profil: dict) -> list[str]:
    """Parcours éligibles : critère UNIQUE = série de bac autorisée.

    Le métier visé et les prérequis sont des SUGGESTIONS NON BLOQUANTES :
    ils renforcent le score de compatibilité sans jamais exclure un parcours.
    """
    return [
        code
        for code in PARCOURS_DATA
        if not bloque_par_serie(profil, code)
    ]


def score_compatibilite(profil: dict, parcours: str) -> dict:
    """Score de compatibilité pondéré avec le détail des motifs (miroir du .pl).

    Pondérations :
    - Matière commune        : ×1
    - Compétence commune     : ×2 (plus discriminant)
    - Intérêt commun        : ×1
    - Métier aligné          : ×3 (signal le plus fort)
    - Suggestion possédée   : ×1
    - Bonus croisé comp→int : +1 par correspondance
    """
    data = PARCOURS_DATA.get(parcours, {})
    matieres_communes = _prefere(profil) & set(data.get("matieres", []))
    competences_communes = _competences(profil) & set(data.get("competences", []))
    interets_communs = _interets(profil) & set(data.get("interets", []))
    metier = _metier_vise(profil)
    metier_alignee = metier in data.get("metiers", [])
    suggestions = _prerequis_possedes(profil) & set(data.get("prerequis", []))

    # Bonus croisé : compétence de l'étudiant liée à un intérêt du parcours
    interets_parcours = set(data.get("interets", []))
    competences_etudiant = _competences(profil)
    bonus_croise = 0
    bonus_croise_details: list[str] = []
    for comp in competences_etudiant:
        comp_full = f"competence_{comp}" if not comp.startswith("competence_") else comp
        for interet_lie in COMPETENCE_LIE_INTERET.get(comp_full, []):
            if interet_lie in interets_parcours:
                bonus_croise += 1
                bonus_croise_details.append(f"{comp_full}->{interet_lie}")

    total = (
        len(matieres_communes)        # ×1
        + len(competences_communes) * 2  # ×2
        + len(interets_communs)        # ×1
        + (3 if metier_alignee else 0) # ×3
        + len(suggestions)             # ×1
        + bonus_croise                 # +1 chacun
    )
    return {
        "score": total,
        "matieres": sorted(matieres_communes),
        "competences": sorted(competences_communes),
        "interets": sorted(interets_communs),
        "metier_alignee": metier_alignee,
        "suggestions": sorted(suggestions),
        "bonus_croise": sorted(bonus_croise_details),
    }


def classement(profil: dict, top_k: int | None = None) -> list[dict]:
    """Parcours possibles classés par score de compatibilité décroissant."""
    results = []
    for code in parcours_possibles(profil):
        detail = score_compatibilite(profil, code)
        results.append(
            {
                "parcours": code,
                "categorie": PARCOURS_DATA[code]["categorie"],
                "score": detail["score"],
                "motifs": detail,
            }
        )
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k] if top_k else results
