"""Génération de données synthétiques ORIENT'IA (documentée).

Méthode documentée (exigence du sujet, Phase 1) :
- 16 parcours répartis dans 5 catégories, alignés sur data/mapping_taxonomie_orientia.md
  et backend/services/rules_fallback.py (mêmes matières/compétences/intérêts/débouchés).
- Pour chaque profil synthétique :
    1. on tire un parcours cible (label `parcours_choisi`) uniformément,
    2. on choisit une série de bac compatible avec ce parcours,
    3. on génère des notes cohérentes avec la série de bac spécifique et les matières
       enseignées par le parcours (bruit gaussien contrôlé),
    4. on active les multi-hot (matières préférées, compétences, intérêts,
       expériences) en cohérence avec le parcours et les notes obtenues,
    5. le métier visé / exercé est tiré en cohérence (ou léger désalignement) avec le parcours,
    6. la satisfaction et la récurrence du choix sont modulées proportionnellement à la proximité Prolog
       et à la pertinence des notes de l'étudiant par rapport au parcours.
- Biais assumés et documentés : données générées (pas réelles), corrélations
  fortes volontaires (parcours → préférences) pour que le ML apprenne ;
  ne PAS confondre avec une enquête réelle. Les vraies réponses (data/enquete)
  remplaceront ce jeu pour la validation finale.

Usage : python data/synthetique/generate_synthetic_data.py
Sortie : data/synthetique/dataset_orientia_synthetique.csv
"""

import csv
import random
import sys
from pathlib import Path

# Ajouter le chemin racine du projet pour importer rules_fallback
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.services.rules_fallback import PARCOURS_DATA  # noqa: E402

PROJECT_DIR = Path(__file__).resolve().parents[2]
OUT_PATH = PROJECT_DIR / "data" / "synthetique" / "dataset_orientia_synthetique.csv"

RNG = random.Random(42)
N_ETUDIANTS = 260
N_PROFESSIONNELS = 140

# En-tête officiel du dataset ORIENT'IA (correspondant au schéma requis)
_HEADER = [
    "id_anonyme", "type_repondant", "sexe", "serie_bac", "famille_bac", "note_malagasy",
    "note_francais", "note_langue_vivante", "note_hg", "note_philosophie",
    "note_mathematiques", "note_spc", "note_svt", "note_ses", "score_scientifique_dur",
    "score_scientifique_naturel", "score_litteraire", "score_economique",
    "moyenne_generale", "mention_diplome", "matiere_mathematiques", "matiere_physique",
    "matiere_informatique", "matiere_svt", "matiere_francais", "matiere_malagasy",
    "matiere_hg", "matiere_ses", "matiere_arts", "matiere_autre", "competence_logique",
    "competence_programmation", "competence_expression", "competence_manuelle",
    "competence_relationnelle", "competence_creativite", "competence_organisation",
    "competence_esprit_critique", "competence_autre", "interet_technologie",
    "interet_science", "interet_art", "interet_sante", "interet_entrepreneuriat",
    "interet_environnement", "interet_social", "interet_sport", "interet_autre",
    "experience_projet_prog", "experience_stage", "experience_association",
    "experience_projet_perso", "metier_vise", "environnement", "prerequis_bases_algo",
    "prerequis_anglais", "prerequis_maths_avancees", "parcours_choisi", "niveau_actuel",
    "annee_fin_etudes", "metier_exerce", "anciennete_metier", "satisfaction",
    "referait_choix", "commentaire_retrospectif"
]

# Listes d'options fermées prédéfinies pour validation
COMPETENCES_LIST = [
    "competence_logique", "competence_programmation", "competence_expression",
    "competence_manuelle", "competence_relationnelle", "competence_creativite",
    "competence_organisation", "competence_esprit_critique", "competence_autre"
]

INTERETS_LIST = [
    "technologie", "science", "art", "sante", "entrepreneuriat",
    "environnement", "social", "sport", "autre"
]

PREREQUIS_LIST = [
    "bases_algorithmique", "anglais", "maths_avancees"
]


# Série de bac autorisée par parcours
SERIES_PAR_PARCOURS = {
    "esii": ["c", "d", "s"],
    "isaia": ["c", "d", "s"],
    "imticia": ["c", "d", "s"],
    "iggia": ["ose", "s", "d"],
    "caa": ["a1", "a2", "l", "ose"],
    "fic": ["ose", "s", "c"],
    "dtja": ["a1", "a2", "l"],
    "emp": ["ose", "a1", "a2"],
    "iaa": ["d", "s", "c"],
    "pip": ["d", "s", "c"],
    "aee": ["d", "s", "c"],
    "emii": ["c", "d", "s"],
    "gca": ["c", "d", "s"],
    "icmp": ["c", "d", "s"],
    "tee": ["a1", "a2", "l", "ose"],
    "teh": ["a1", "a2", "l", "ose"],
}

FAMILLE = {
    "c": "scientifique", "d": "scientifique", "s": "scientifique",
    "a1": "litteraire", "a2": "litteraire", "l": "litteraire",
    "ose": "economique"
}

# Matières scolaires par série de bac (moyenne, écart-type)
NOTES_SERIE = {
    "c": {
        "note_malagasy": (10, 3), "note_francais": (10, 3), "note_langue_vivante": (11, 3),
        "note_hg": (11, 3), "note_philosophie": (10, 3), "note_mathematiques": (16.5, 1.5),
        "note_spc": (15.5, 1.5), "note_svt": (11.0, 2.5), "note_ses": (None, None),
    },
    "s": {
        "note_malagasy": (10, 3), "note_francais": (11, 3), "note_langue_vivante": (11, 3),
        "note_hg": (11, 3), "note_philosophie": (10, 3), "note_mathematiques": (14.5, 2.0),
        "note_spc": (14.0, 2.0), "note_svt": (12.0, 2.0), "note_ses": (None, None),
    },
    "d": {
        "note_malagasy": (10, 3), "note_francais": (11, 3), "note_langue_vivante": (11, 3),
        "note_hg": (11, 3), "note_philosophie": (10, 3), "note_mathematiques": (12.5, 2.5),
        "note_spc": (12.0, 2.5), "note_svt": (16.0, 1.5), "note_ses": (None, None),
    },
    "a1": {
        "note_malagasy": (15.5, 1.5), "note_francais": (15.5, 1.5), "note_langue_vivante": (15.5, 1.5),
        "note_hg": (13.0, 2.0), "note_philosophie": (15.5, 1.5), "note_mathematiques": (10.0, 2.5),
        "note_spc": (None, None), "note_svt": (None, None), "note_ses": (None, None),
    },
    "a2": {
        "note_malagasy": (13.5, 2.0), "note_francais": (13.5, 2.0), "note_langue_vivante": (13.5, 2.0),
        "note_hg": (14.0, 2.0), "note_philosophie": (13.5, 2.0), "note_mathematiques": (9.5, 2.5),
        "note_spc": (None, None), "note_svt": (None, None), "note_ses": (None, None),
    },
    "l": {
        "note_malagasy": (13.5, 2.0), "note_francais": (13.5, 2.0), "note_langue_vivante": (13.5, 2.0),
        "note_hg": (14.0, 2.0), "note_philosophie": (13.5, 2.0), "note_mathematiques": (9.5, 2.5),
        "note_spc": (None, None), "note_svt": (None, None), "note_ses": (None, None),
    },
    "ose": {
        "note_malagasy": (11, 3), "note_francais": (12, 3), "note_langue_vivante": (12, 3),
        "note_hg": (13.5, 2.0), "note_philosophie": (11, 3), "note_mathematiques": (12.5, 2.5),
        "note_spc": (None, None), "note_svt": (None, None), "note_ses": (15.5, 1.5),
    },
}

# Correspondance matière enseignée (taxonomie) -> colonne note scolaire
NOTE_BOOST = {
    "mathematiques": "note_mathematiques", "statistiques": "note_mathematiques",
    "electronique": "note_spc", "sciences": "note_spc", "chimie": "note_spc",
    "biologie": "note_svt", "agroalimentaire": "note_svt", "etudes_flore": "note_svt",
    "etudes_faune": "note_svt", "agriculture_biologique": "note_svt",
    "langues": "note_langue_vivante", "commerce": "note_ses", "gestion": "note_ses",
    "finance": "note_ses", "comptabilite": "note_ses", "economie": "note_ses",
    "economie_internationale": "note_ses", "micro_economie": "note_ses",
    "macro_economie": "note_ses", "droit_public": "note_hg", "droit_prive": "note_hg",
    "multimedia": "note_francais", "dessin": "note_francais", "art_culinaire": "note_francais",
    "hotelierie": "note_francais",
}

MATIERE_COL = {
    "mathematiques": "matiere_mathematiques", "statistiques": "matiere_mathematiques",
    "electronique": "matiere_physique", "sciences": "matiere_physique", "chimie": "matiere_physique",
    "programmation": "matiere_informatique", "algorithmique": "matiere_informatique",
    "biologie": "matiere_svt", "agroalimentaire": "matiere_svt", "etudes_flore": "matiere_svt",
    "etudes_faune": "matiere_svt", "agriculture_biologique": "matiere_svt", "environnement": "matiere_svt",
    "langues": "matiere_francais", "commerce": "matiere_ses", "gestion": "matiere_ses",
    "finance": "matiere_ses", "comptabilite": "matiere_ses", "economie": "matiere_ses",
    "economie_internationale": "matiere_ses", "micro_economie": "matiere_ses",
    "macro_economie": "matiere_ses", "droit_public": "matiere_hg", "droit_prive": "matiere_hg",
    "multimedia": "matiere_arts", "dessin": "matiere_arts", "art_culinaire": "matiere_arts",
    "hotelierie": "matiere_arts", "tourisme": "matiere_arts", "ecologie": "matiere_svt",
    "agriculture": "matiere_svt",
}

ENV_PAR_CATEGORIE = {
    "informatique": ["bureau", "bureau", "recherche"],
    "affaires": ["bureau", "relationnel", "bureau"],
    "biotech": ["terrain", "recherche", "laboratoire"],
    "genie": ["terrain", "bureau", "recherche"],
    "tourisme": ["terrain", "relationnel", "relationnel"],
}

METIERS_LIST = [
    "ingenieur_electronique",
    "developpeur",
    "data_scientist",
    "ingenieur_ml",
    "developpeur_web",
    "chef_de_projet_multimedia",
    "chef_de_projet",
    "consultant",
    "commercial_export",
    "charge_affaires",
    "analyste_financier",
    "comptable",
    "juriste",
    "assistant_juridique",
    "economiste",
    "charge_etudes",
    "technicien_agroalimentaire",
    "controleur_qualite",
    "horticulteur",
    "technicien_production_vegetale",
    "agronome",
    "environnementaliste",
    "ingenieur_maintenance",
    "technicien_superieur",
    "ingenieur_genie_civil",
    "conducteur_travaux",
    "technicien_laboratoire",
    "ingenieur_materiaux",
    "gestionnaire_tourisme",
    "ecoguide",
    "directeur_hotel",
    "responsable_restauration"
]



def clamp_note(value: float) -> int:
    return max(0, min(20, int(round(value))))


def _generate_profile(rep_id: str, is_pro: bool, existing: list) -> dict:
    parcours = RNG.choice(sorted(PARCOURS_DATA.keys()))
    data = PARCOURS_DATA[parcours]
    serie = RNG.choice(SERIES_PAR_PARCOURS[parcours])
    famille = FAMILLE[serie]
    notes_base = NOTES_SERIE[serie]

    row = {col: "0" for col in _HEADER}
    row["id_anonyme"] = rep_id
    row["type_repondant"] = "professionnel" if is_pro else "etudiant"

    # Genre du profil (homme/femme)
    sexe = RNG.choice(["homme", "femme"])
    row["sexe"] = sexe

    row["serie_bac"] = serie
    row["famille_bac"] = famille

    # Notes : moyenne série + boost si le parcours enseigne cette matière
    notes = {}
    for note_col, (mean, std) in notes_base.items():
        if mean is None:
            notes[note_col] = None
            row[note_col] = ""
            continue
        boost = 0.0
        for matiere in data["matieres"]:
            if NOTE_BOOST.get(matiere) == note_col:
                boost = 2.5
        notes[note_col] = clamp_note(RNG.gauss(mean + boost, std))
        row[note_col] = str(notes[note_col])

    # Moyenne générale (1-5) et mention (1-4), corrélées aux notes
    mean_notes = [v for v in notes.values() if v is not None]
    avg = sum(mean_notes) / len(mean_notes) if mean_notes else 10.0
    if avg >= 15:
        moy, mention = 5, 4
    elif avg >= 13.5:
        moy, mention = 4, 3
    elif avg >= 12:
        moy, mention = 3, 2
    else:
        moy, mention = RNG.choice([1, 2]), 1
    row["moyenne_generale"] = str(moy)
    row["mention_diplome"] = str(mention)

    # Multi-hot matières préférées (base par parcours)
    for matiere in data["matieres"]:
        col = MATIERE_COL.get(matiere)
        if col and RNG.random() < 0.8:
            row[col] = "1"
    if RNG.random() < 0.25:
        row[RNG.choice([c for c in _HEADER if c.startswith("matiere_") and c != "matiere_autre"])] = "1"

    # Compétences (base par parcours)
    for competence in data["competences"]:
        if competence in _HEADER and RNG.random() < 0.8:
            row[competence] = "1"

    # Intérêts (base par parcours)
    for interet in data["interets"]:
        col = f"interet_{interet}"
        if col in _HEADER and RNG.random() < 0.75:
            row[col] = "1"

    # Expériences
    for col in ("experience_projet_prog", "experience_stage", "experience_association", "experience_projet_perso"):
        if RNG.random() < 0.35:
            row[col] = "1"

    # Prérequis de base
    prerequis = data.get("prerequis", [])
    row["prerequis_bases_algo"] = "1" if ("bases_algorithmique" in prerequis or RNG.random() < 0.2) else "0"
    row["prerequis_anglais"] = "1" if RNG.random() < 0.7 else "0"
    row["prerequis_maths_avancees"] = "1" if ("maths_avancees" in prerequis or RNG.random() < 0.2) else "0"

    # Corrélation notes -> matières, compétences, intérêts, prérequis
    # Fort en math
    if notes.get("note_mathematiques") is not None and notes["note_mathematiques"] >= 14:
        if RNG.random() < 0.85:
            row["matiere_mathematiques"] = "1"
        if RNG.random() < 0.85:
            row["competence_logique"] = "1"
        if RNG.random() < 0.85:
            row["interet_science"] = "1"
        if RNG.random() < 0.85:
            row["prerequis_maths_avancees"] = "1"

    # Fort en physique
    if notes.get("note_spc") is not None and notes["note_spc"] >= 14:
        if RNG.random() < 0.85:
            row["matiere_physique"] = "1"
        if RNG.random() < 0.85:
            row["competence_logique"] = "1"
        if RNG.random() < 0.85:
            row["interet_science"] = "1"

    # Fort en SVT
    if notes.get("note_svt") is not None and notes["note_svt"] >= 14:
        if RNG.random() < 0.85:
            row["matiere_svt"] = "1"
        if RNG.random() < 0.85:
            row["interet_environnement"] = "1"
        if RNG.random() < 0.85:
            row["interet_science"] = "1"

    # Fort en français / langues
    if notes.get("note_francais") is not None and notes["note_francais"] >= 14:
        if RNG.random() < 0.85:
            row["matiere_francais"] = "1"
        if RNG.random() < 0.85:
            row["competence_expression"] = "1"

    if notes.get("note_langue_vivante") is not None and notes["note_langue_vivante"] >= 14:
        if RNG.random() < 0.85:
            row["prerequis_anglais"] = "1"

    # Fort en SES
    if notes.get("note_ses") is not None and notes["note_ses"] >= 14:
        if RNG.random() < 0.85:
            row["matiere_ses"] = "1"
        if RNG.random() < 0.85:
            row["competence_organisation"] = "1"
        if RNG.random() < 0.85:
            row["interet_entrepreneuriat"] = "1"

    # Métiers et Cible
    row["parcours_choisi"] = parcours
    row["environnement"] = RNG.choice(ENV_PAR_CATEGORIE[data["categorie"]])

    # Métier visé (avec un potentiel désalignement de 15% pour les étudiants)
    if RNG.random() < 0.85:
        metier_vise = RNG.choice(data["metiers"])
    else:
        other_parcours = RNG.choice([p for p in PARCOURS_DATA if p != parcours])
        metier_vise = RNG.choice(PARCOURS_DATA[other_parcours]["metiers"])
    row["metier_vise"] = metier_vise

    if is_pro:
        row["niveau_actuel"] = ""
        row["annee_fin_etudes"] = str(RNG.randint(2008, 2021))
        row["anciennete_metier"] = ""
        # Professionnel : métier exercé avec 10% de chances de reconversion hors parcours
        if RNG.random() < 0.90:
            row["metier_exerce"] = RNG.choice(data["metiers"])
        else:
            other_parcours = RNG.choice([p for p in PARCOURS_DATA if p != parcours])
            row["metier_exerce"] = RNG.choice(PARCOURS_DATA[other_parcours]["metiers"])
    else:
        row["niveau_actuel"] = RNG.choice(["l1", "l2", "l3", "m1", "m2"])
        row["metier_exerce"] = ""

    # Calcul dynamique des scores composites
    # 1. score_scientifique_dur
    if notes.get("note_mathematiques") is not None and notes.get("note_spc") is not None:
        row["score_scientifique_dur"] = f"{(notes['note_mathematiques'] + notes['note_spc']) / 2:.1f}"
    else:
        row["score_scientifique_dur"] = ""

    # 2. score_scientifique_naturel
    if notes.get("note_svt") is not None:
        row["score_scientifique_naturel"] = f"{float(notes['note_svt']):.1f}"
    else:
        row["score_scientifique_naturel"] = ""

    # 3. score_litteraire
    lit_notes = [notes.get(k) for k in ["note_malagasy", "note_francais", "note_langue_vivante", "note_hg", "note_philosophie"]]
    lit_notes = [n for n in lit_notes if n is not None]
    if lit_notes:
        row["score_litteraire"] = f"{sum(lit_notes) / len(lit_notes):.1f}"
    else:
        row["score_litteraire"] = ""

    # 4. score_economique
    if notes.get("note_ses") is not None:
        eco_notes = [notes.get(k) for k in ["note_mathematiques", "note_ses", "note_hg"]]
        eco_notes = [n for n in eco_notes if n is not None]
        row["score_economique"] = f"{sum(eco_notes) / len(eco_notes):.1f}"
    else:
        row["score_economique"] = ""

    # Calcul de la proximité Prolog (score_alignement) pour la satisfaction
    prefere_set = set()
    for col in MATIERE_COL.values():
        if row[col] == "1":
            prefere_set.add(col.replace("matiere_", ""))
    matieres_communes = prefere_set & set(data.get("matieres", []))

    possede_set = set()
    for col in _HEADER:
        if col.startswith("competence_") and row[col] == "1":
            possede_set.add(col)
    competences_communes = possede_set & set(data.get("competences", []))

    interet_set = set()
    for col in _HEADER:
        if col.startswith("interet_") and row[col] == "1":
            interet_set.add(col.replace("interet_", ""))
    interets_communs = interet_set & set(data.get("interets", []))

    metier_aligne = row["metier_vise"] in data.get("metiers", [])

    suggestions_count = 0
    if row["prerequis_bases_algo"] == "1" and "bases_algorithmique" in data.get("prerequis", []):
        suggestions_count += 1
    if row["prerequis_anglais"] == "1" and "anglais" in data.get("prerequis", []):
        suggestions_count += 1
    if row["prerequis_maths_avancees"] == "1" and "maths_avancees" in data.get("prerequis", []):
        suggestions_count += 1

    score_alignement = (
        len(matieres_communes)
        + len(competences_communes)
        + len(interets_communs)
        + (2 if metier_aligne else 0)
        + suggestions_count
    )

    # Initialisation de la satisfaction
    satisfaction_val = 2.0 + (score_alignement * 0.4)

    # Boosts de satisfaction (conditions favorables)
    # - Série C en filières scientifiques
    if serie == "c" and data["categorie"] in ["informatique", "genie", "biotech"]:
        satisfaction_val += 0.5
    # - Série A1 en filières littéraires/langues
    if serie == "a1" and data["categorie"] in ["affaires", "tourisme"]:
        satisfaction_val += 0.5
    # - Série OSE en filières économiques/gestion
    if serie == "ose" and data["categorie"] in ["affaires"] and parcours in ["fic", "emp", "iggia", "caa"]:
        satisfaction_val += 0.5
    # - Boost de genre (favorable aux femmes/hommes selon le parcours adapté)
    if sexe == "femme" and parcours in ["iggia", "caa", "fic", "dtja", "emp", "teh", "tee", "iaa"]:
        satisfaction_val += 0.5
    elif sexe == "homme" and parcours in ["emii", "esii", "gca", "imticia", "isaia", "icmp", "pip", "aee"]:
        satisfaction_val += 0.5
    # - Informatique
    if data["categorie"] == "informatique":
        if notes.get("note_mathematiques") and notes["note_mathematiques"] >= 15:
            satisfaction_val += 0.5
        if avg >= 14:
            satisfaction_val += 0.5
    # - SVT (iaa, pip, aee, tee)
    if parcours in ["iaa", "pip", "aee", "tee"]:
        if notes.get("note_svt") and notes["note_svt"] >= 15:
            satisfaction_val += 0.5
    # - ICMP & IAA (Physique-Chimie)
    if parcours in ["icmp", "iaa"]:
        if notes.get("note_spc") and notes["note_spc"] >= 15:
            satisfaction_val += 0.5

    # Pénalités de satisfaction (conditions de notes défavorables)
    # - Informatique : maths ou générale trop basse
    if data["categorie"] == "informatique":
        if notes.get("note_mathematiques") and notes["note_mathematiques"] < 12:
            satisfaction_val -= 1.5
        elif avg < 11:
            satisfaction_val -= 1.0
    # - SVT : SVT trop basse
    if parcours in ["iaa", "pip", "aee", "tee"]:
        if notes.get("note_svt") and notes["note_svt"] < 11:
            satisfaction_val -= 1.5
    # - Littéraire : français/langues trop bas
    if parcours in ["dtja", "caa"]:
        if (notes.get("note_francais") and notes["note_francais"] < 11) or (notes.get("note_langue_vivante") and notes["note_langue_vivante"] < 11):
            satisfaction_val -= 1.5
    # - Économique : SES ou maths trop bas
    if parcours in ["fic", "emp", "iggia"]:
        if (notes.get("note_ses") and notes["note_ses"] < 11) or (notes.get("note_mathematiques") and notes["note_mathematiques"] < 11):
            satisfaction_val -= 1.5
    # - ICMP & IAA : SPC trop basse
    if parcours in ["icmp", "iaa"]:
        if notes.get("note_spc") and notes["note_spc"] < 11:
            satisfaction_val -= 1.5
    # - Professionnel reconverti
    if is_pro and row["metier_exerce"] not in data.get("metiers", []):
        satisfaction_val -= 2.0

    # Finalisation satisfaction
    satisfaction = max(1, min(5, int(round(satisfaction_val))))
    row["satisfaction"] = str(satisfaction)

    # Récurrence du choix
    rand_val = RNG.random()
    if satisfaction == 5:
        ref_val = "oui" if rand_val < 0.95 else "non"
    elif satisfaction == 4:
        ref_val = "oui" if rand_val < 0.85 else "non"
    elif satisfaction == 3:
        ref_val = "oui" if rand_val < 0.70 else "non"
    else:
        ref_val = "oui" if rand_val < 0.15 else "non"
    row["referait_choix"] = ref_val

    # Calcul de l'ancienneté en mois corrélée à la satisfaction
    if is_pro:
        max_months = (2026 - int(row["annee_fin_etudes"])) * 12
        if max_months < 1:
            max_months = 12
        if satisfaction >= 4:
            months = RNG.randint(max(1, int(max_months * 0.6)), max_months)
        elif satisfaction == 3:
            months = RNG.randint(max(1, int(max_months * 0.3)), max(1, int(max_months * 0.7)))
        else:
            months = RNG.randint(1, max(1, int(max_months * 0.4)))
        row["anciennete_metier"] = str(months)
    else:
        row["anciennete_metier"] = ""

    # metier_vise et metier_exerce restent des chaînes de caractères pour la visibilité
    if not is_pro:
        row["metier_exerce"] = ""

    row["commentaire_retrospectif"] = ""
    return row


def main() -> None:
    rows = []
    idx = 0
    for i in range(N_ETUDIANTS):
        idx += 1
        rows.append(_generate_profile(f"rep_synth_{idx:04d}", is_pro=False, existing=rows))
    for i in range(N_PROFESSIONNELS):
        idx += 1
        rows.append(_generate_profile(f"rep_synth_{idx:04d}", is_pro=True, existing=rows))

    RNG.shuffle(rows)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=_HEADER)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Généré : {len(rows)} profils synthétiques -> {OUT_PATH}")
    from collections import Counter
    print("Répartition parcours :", dict(Counter(r["parcours_choisi"] for r in rows)))
    print("Répartition types :", dict(Counter(r["type_repondant"] for r in rows)))


if __name__ == "__main__":
    main()
