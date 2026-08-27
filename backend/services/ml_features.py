"""Construction du vecteur de features pour un profil ORIENT'IA.

Règle de gestion des valeurs manquantes (décision projet) :
- les notes et scores absents (ex: note_ses pour une série S) restent NaN,
- on ajoute une colonne indicateur `*_presente` pour chaque note/score,
- les modèles arborés (RF) gèrent NaN nativement ; les modèles linéaires
  (LogisticRegression) sont entraînés sur une version imputée (médiane).

L'ordre des features est fixe et stocké dans le payload du modèle entraîné
pour la traçabilité (feature importance, analyse de biais).
"""

import numpy as np
import pandas as pd

SERIE_VALUES = ["c", "d", "s", "a1", "a2", "l", "ose"]
ENV_VALUES = ["bureau", "relationnel", "recherche", "terrain", "indifferent", "laboratoire"]

NOTE_COLS = [
    "note_malagasy", "note_francais", "note_langue_vivante", "note_hg",
    "note_philosophie", "note_mathematiques", "note_spc", "note_svt", "note_ses",
]
SCORE_COLS = [
    "score_scientifique_dur", "score_scientifique_naturel",
    "score_litteraire", "score_economique",
]
NUMERIC_COLS = NOTE_COLS + SCORE_COLS + ["moyenne_generale", "mention_diplome"]

MATIERE_COLS = [
    "matiere_mathematiques", "matiere_physique", "matiere_informatique", "matiere_svt",
    "matiere_francais", "matiere_malagasy", "matiere_hg", "matiere_ses",
    "matiere_arts", "matiere_autre",
]
COMPETENCE_COLS = [
    "competence_logique", "competence_programmation", "competence_expression",
    "competence_manuelle", "competence_relationnelle", "competence_creativite",
    "competence_organisation", "competence_esprit_critique", "competence_autre",
]
INTERET_COLS = [
    "interet_technologie", "interet_science", "interet_art", "interet_sante",
    "interet_entrepreneuriat", "interet_environnement", "interet_social",
    "interet_sport", "interet_autre",
]
EXPERIENCE_COLS = [
    "experience_projet_prog", "experience_stage", "experience_association",
    "experience_projet_perso",
]
PREREQUIS_COLS = [
    "prerequis_bases_algo", "prerequis_anglais", "prerequis_maths_avancees",
]
BINARY_COLS = (
    MATIERE_COLS + COMPETENCE_COLS + INTERET_COLS + EXPERIENCE_COLS + PREREQUIS_COLS
)

MISSING_INDICATORS = [f"{col}_presente" for col in NOTE_COLS + SCORE_COLS]
SERIE_ONE_HOT = [f"serie_{s}" for s in SERIE_VALUES] + ["serie_autre"]
ENV_ONE_HOT = [f"env_{e}" for e in ENV_VALUES]


def feature_names() -> list[str]:
    """Ordre exact des colonnes du vecteur de features (stabilité des modèles)."""
    return NUMERIC_COLS + MISSING_INDICATORS + SERIE_ONE_HOT + ENV_ONE_HOT + BINARY_COLS


def _to_frame(profils: pd.DataFrame) -> pd.DataFrame:
    """Transforme un DataFrame brut (colonnes CSV) en DataFrame de features.

    Tolérant aux colonnes manquantes (profil partiel) : les colonnes absentes
    sont traitées comme NaN (numériques) ou 0 (binaires).
    """
    X = pd.DataFrame(index=profils.index)

    for col in NUMERIC_COLS:
        if col in profils.columns:
            X[col] = pd.to_numeric(profils[col], errors="coerce")
        else:
            X[col] = np.nan

    for col in NOTE_COLS + SCORE_COLS:
        X[f"{col}_presente"] = (~X[col].isna()).astype(int)

    if "serie_bac" in profils.columns:
        serie = profils["serie_bac"].astype(str).str.lower().str.strip()
    else:
        serie = pd.Series([""] * len(profils), index=profils.index)
    for value in SERIE_VALUES:
        X[f"serie_{value}"] = (serie == value).astype(int)
    X["serie_autre"] = (~serie.isin(SERIE_VALUES)).astype(int)

    if "environnement" in profils.columns:
        env = profils["environnement"].astype(str).str.lower().str.strip()
    else:
        env = pd.Series([""] * len(profils), index=profils.index)
    for value in ENV_VALUES:
        X[f"env_{value}"] = (env == value).astype(int)

    for col in BINARY_COLS:
        if col in profils.columns:
            X[col] = pd.to_numeric(profils[col], errors="coerce").fillna(0)
        else:
            X[col] = 0

    return X[feature_names()]


def df_to_features(profils: pd.DataFrame) -> np.ndarray:
    """Vecteur de features pour un DataFrame de profils (shape (n, d))."""
    return _to_frame(profils).to_numpy(dtype=float)


def profil_to_vector(profil: dict) -> np.ndarray:
    """Vecteur de features pour un profil unique (shape (d,))."""
    return df_to_features(pd.DataFrame([profil]))[0]
