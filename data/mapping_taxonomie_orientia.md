# ORIENT'IA — Mapping de la taxonomie

> Document de référence alignant **parcours ISPM**, **catégories**, **matières**,
> **compétences**, **prérequis**, **débouchés** et **centres d'intérêt**.
> Les noms d'atomes Prolog (ASCII pur) et les valeurs des colonnes CSV y font
> référence. Chaque parcours est codé en minuscules sans accent (ex: `isaia`).

## Catégories et parcours (16 parcours, 5 catégories)

### 1. Informatiques et télécommunications
| Code | Parcours | Matières dominantes |
| ---- | -------- | ------------------- |
| `esii`  | ESIIA — Électronique & Télécoms | électronique, mathématiques, programmation, algorithmique |
| `isaia` | ISAIA — Informatique & Statistique | statistiques, mathématiques, programmation, algorithmique |
| `imticia`| IMTICIA — Multimédia & TIC | mathématiques, multimédia, programmation, algorithmique |
| `iggia` | IGGLIA — Gestion & Informatique | gestion, mathématiques, programmation, algorithmique |

### 2. Techniques des affaires
| Code | Parcours | Matières dominantes |
| ---- | -------- | ------------------- |
| `caa` | CAA — Commerce & Affaires | commerce, langues, économie_internationale |
| `fic` | FIC — Finance & Comptabilité | finance, comptabilité, économie, langues |
| `dtja` | DTJA — Droit & Juridique | droit_public, droit_prive, langues |
| `emp` | EMP — Économie & Management Public | économie_internationale, micro_économie, macro_économie |

### 3. Biotechnologie et agronomie
| Code | Parcours | Matières dominantes |
| ---- | -------- | ------------------- |
| `iaa`  | IAA — Industries Agroalimentaires | agroalimentaire, biologie, chimie |
| `pip`  | PIP — Productions & Études Florales | études_flore, biologie, agriculture |
| `aee`  | AEE — Agriculture & Environnement | études_faune, agriculture_biologique, environnement |

### 4. Génie industriel et génie civil
| Code | Parcours | Matières dominantes |
| ---- | -------- | ------------------- |
| `emii` | EMII — Électromécanique & Industrialisation | électronique, programmation, mathématiques |
| `gca`  | GCA — Génie Civil & Architecture | dessin, programmation, mathématiques |
| `icmp` | ICMP — Chimie & Sciences des Matériaux | chimie, sciences |

### 5. Techniques du tourisme
| Code | Parcours | Matières dominantes |
| ---- | -------- | ------------------- |
| `tee` | TEE — Tourisme & Environnement | environnement, tourisme, écologie |
| `teh` | TEH — Tourisme & Hôtellerie | hôtellerie, art_culinaire, tourisme |

## Correspondance CSV → taxonomie

| Bloc CSV | Colonnes | Rôle |
| -------- | -------- | ---- |
| Profil académique | `serie_bac`, `famille_bac`, `moyenne_generale`, `mention_diplome`, `note_*` | filtre et features numériques |
| Scores composites | `score_scientifique_dur`, `score_scientifique_naturel`, `score_litteraire`, `score_economique` | features dérivées (bonus ML) |
| Préférences | `matiere_*` (10), `competence_*` (9), `interet_*` (9), `experience_*` (4) | features multi-hot |
| Projet | `environnement`, `metier_vise`, `prerequis_*` (3) | features multi-hot |
| Cible | `parcours_choisi`, `metier_exerce` | labels ML |

## Règles Prolog (résumé)

```
enseigne(Parcours, Matiere)          matières enseignées par le parcours
developpe(Parcours, Competence)      compétences développées
necessite(Parcours, Prerequis)       prérequis suggérés (non bloquants)
prepareA(Parcours, Metier)           débouchés métier
estRequisePour(Competence, Metier)   compétence requise pour un métier
serie_bac(Etudiant, Serie)           série déclarée
famille_bac(Etudiant, Famille)       famille dérivée (scientifique / litteraire / economique)
possede(Etudiant, Prerequis)         prérequis possédés
prefere / interet / vise / a_experience / possede(Competence)
```

Le fichier complet : `backend/knowledge_base/orientia_rules.pl`.
