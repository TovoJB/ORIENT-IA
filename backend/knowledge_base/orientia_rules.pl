% =====================================================================
% ORIENT'IA -- Base de connaissances Prolog
% Compatible pyswip (SWI-Prolog) ; miroir Python dans services/rules_fallback.py
% Atomes ASCII pur (sans accents). Aligné sur data/mapping_taxonomie_orientia.md
% =====================================================================

:- use_module(library(aggregate)).
:- discontiguous possede/2.

% Prédicats du profil étudiant, assertés dynamiquement par profil (pyswip)
:- dynamic serie_bac/2.
:- dynamic possede/2.
:- dynamic prefere/2.
:- dynamic interet/2.
:- dynamic vise/2.

% ---------------------------------------------------------------------
% 1. OFFRE DE FORMATION -- 16 parcours, 5 catégories
% ---------------------------------------------------------------------

% --- Catalogue : parcours/1 ---
parcours(esii). parcours(isaia). parcours(imticia). parcours(iggia).
parcours(caa).  parcours(fic).   parcours(dtja).   parcours(emp).
parcours(iaa).  parcours(pip).   parcours(aee).
parcours(emii). parcours(gca).   parcours(icmp).
parcours(tee).  parcours(teh).

% --- Catégorie : categorie(Parcours, Categorie) ---
categorie(esii, informatique). categorie(isaia, informatique).
categorie(imticia, informatique). categorie(iggia, informatique).
categorie(caa, affaires). categorie(fic, affaires).
categorie(dtja, affaires). categorie(emp, affaires).
categorie(iaa, biotech). categorie(pip, biotech). categorie(aee, biotech).
categorie(emii, genie). categorie(gca, genie). categorie(icmp, genie).
categorie(tee, tourisme). categorie(teh, tourisme).

% --- Matières enseignées : enseigne(Parcours, Matiere) ---
enseigne(esii, electronique). enseigne(esii, mathematiques).
enseigne(esii, programmation). enseigne(esii, algorithmique).
enseigne(isaia, statistiques). enseigne(isaia, mathematiques).
enseigne(isaia, programmation). enseigne(isaia, algorithmique).
enseigne(imticia, mathematiques). enseigne(imticia, multimedia).
enseigne(imticia, programmation). enseigne(imticia, algorithmique).
enseigne(iggia, gestion). enseigne(iggia, mathematiques).
enseigne(iggia, programmation). enseigne(iggia, algorithmique).
enseigne(caa, commerce). enseigne(caa, langues). enseigne(caa, economie_internationale).
enseigne(fic, finance). enseigne(fic, comptabilite).
enseigne(fic, economie). enseigne(fic, langues).
enseigne(dtja, droit_public). enseigne(dtja, droit_prive). enseigne(dtja, langues).
enseigne(emp, economie_internationale).
enseigne(emp, micro_economie). enseigne(emp, macro_economie).
enseigne(iaa, agroalimentaire). enseigne(iaa, biologie). enseigne(iaa, chimie).
enseigne(pip, etudes_flore). enseigne(pip, biologie). enseigne(pip, agriculture).
enseigne(aee, etudes_faune). enseigne(aee, agriculture_biologique).
enseigne(aee, environnement).
enseigne(emii, electronique). enseigne(emii, programmation).
enseigne(emii, mathematiques).
enseigne(gca, dessin). enseigne(gca, programmation). enseigne(gca, mathematiques).
enseigne(icmp, chimie). enseigne(icmp, sciences).
enseigne(tee, environnement). enseigne(tee, tourisme). enseigne(tee, ecologie).
enseigne(teh, hotelierie). enseigne(teh, art_culinaire). enseigne(teh, tourisme).

% --- Compétences développées : developpe(Parcours, Competence) ---
% Enrichi d'après l'analyse des descriptions de chaque filière (data/sources/).
developpe(esii, competence_programmation). developpe(esii, competence_logique).
developpe(esii, competence_manuelle).
developpe(isaia, competence_programmation). developpe(isaia, competence_logique).
developpe(isaia, competence_esprit_critique).
developpe(imticia, competence_programmation). developpe(imticia, competence_creativite).
developpe(imticia, competence_expression).
developpe(iggia, competence_organisation). developpe(iggia, competence_relationnelle).
developpe(iggia, competence_programmation). developpe(iggia, competence_esprit_critique).
developpe(caa, competence_relationnelle). developpe(caa, competence_expression).
developpe(caa, competence_organisation).
developpe(fic, competence_organisation). developpe(fic, competence_esprit_critique).
developpe(fic, competence_logique).
developpe(dtja, competence_expression). developpe(dtja, competence_esprit_critique).
developpe(dtja, competence_relationnelle).
developpe(emp, competence_esprit_critique). developpe(emp, competence_organisation).
developpe(emp, competence_relationnelle).
developpe(iaa, competence_manuelle). developpe(iaa, competence_esprit_critique).
developpe(pip, competence_manuelle). developpe(pip, competence_esprit_critique).
developpe(pip, competence_organisation).
developpe(aee, competence_esprit_critique). developpe(aee, competence_manuelle).
developpe(aee, competence_organisation).
developpe(emii, competence_manuelle). developpe(emii, competence_logique).
developpe(emii, competence_programmation).
developpe(gca, competence_creativite). developpe(gca, competence_manuelle).
developpe(gca, competence_logique). developpe(gca, competence_organisation).
developpe(icmp, competence_esprit_critique). developpe(icmp, competence_manuelle).
developpe(icmp, competence_logique).
developpe(tee, competence_relationnelle). developpe(tee, competence_organisation).
developpe(tee, competence_expression).
developpe(teh, competence_relationnelle). developpe(teh, competence_organisation).
developpe(teh, competence_expression). developpe(teh, competence_creativite).

% --- Prérequis : necessite(Parcours, Prerequis) ---
% Aligné sur rules_fallback.PARCOURS_DATA (miroir Python)
necessite(esii, bac_scientifique). necessite(esii, bases_algorithmique).
necessite(isaia, bac_scientifique). necessite(isaia, bases_algorithmique).
necessite(isaia, maths_avancees).
necessite(imticia, bases_algorithmique).
necessite(iggia, bases_algorithmique).
necessite(emii, bac_scientifique). necessite(emii, bases_algorithmique).
necessite(gca, bac_scientifique). necessite(gca, bases_algorithmique).
necessite(icmp, bac_scientifique).
necessite(iaa, bac_scientifique).
necessite(pip, bac_scientifique).
necessite(aee, bac_scientifique).

% --- Débouchés : prepareA(Parcours, Metier) ---
prepareA(esii, ingenieur_electronique). prepareA(esii, developpeur).
prepareA(isaia, data_scientist). prepareA(isaia, ingenieur_ml).
prepareA(isaia, developpeur).
prepareA(imticia, developpeur_web). prepareA(imticia, chef_de_projet_multimedia).
prepareA(iggia, chef_de_projet). prepareA(iggia, consultant).
prepareA(iggia, developpeur).
prepareA(caa, commercial_export). prepareA(caa, charge_affaires).
prepareA(fic, analyste_financier). prepareA(fic, comptable).
prepareA(dtja, juriste). prepareA(dtja, assistant_juridique).
prepareA(emp, economiste). prepareA(emp, charge_etudes).
prepareA(iaa, technicien_agroalimentaire). prepareA(iaa, controleur_qualite).
prepareA(pip, horticulteur). prepareA(pip, technicien_production_vegetale).
prepareA(aee, agronome). prepareA(aee, environnementaliste).
prepareA(emii, ingenieur_maintenance). prepareA(emii, technicien_superieur).
prepareA(gca, ingenieur_genie_civil). prepareA(gca, conducteur_travaux).
prepareA(icmp, technicien_laboratoire). prepareA(icmp, ingenieur_materiaux).
prepareA(tee, gestionnaire_tourisme). prepareA(tee, ecoguide).
prepareA(teh, directeur_hotel). prepareA(teh, responsable_restauration).

% --- Compétence requise pour un métier : estRequisePour(Competence, Metier) ---
estRequisePour(competence_programmation, data_scientist).
estRequisePour(competence_logique, ingenieur_ml).
estRequisePour(competence_programmation, developpeur).
estRequisePour(competence_programmation, developpeur_web).
estRequisePour(competence_organisation, chef_de_projet).
estRequisePour(competence_relationnelle, consultant).
estRequisePour(competence_relationnelle, commercial_export).
estRequisePour(competence_expression, juriste).
estRequisePour(competence_esprit_critique, economiste).
estRequisePour(competence_manuelle, technicien_superieur).
estRequisePour(competence_creativite, conducteur_travaux).

% ---------------------------------------------------------------------
% 2. ACCESSIBILITÉ PAR FAMILLE DE BAC
% ---------------------------------------------------------------------

% accessibles(Famille, Parcours)
accessibles(scientifique, esii). accessibles(scientifique, isaia).
accessibles(scientifique, imticia). accessibles(scientifique, iggia).
accessibles(scientifique, emii). accessibles(scientifique, gca).
accessibles(scientifique, icmp). accessibles(scientifique, iaa).
accessibles(scientifique, pip). accessibles(scientifique, aee).
accessibles(scientifique, fic).
accessibles(litteraire, caa). accessibles(litteraire, dtja).
accessibles(litteraire, tee). accessibles(litteraire, teh).
accessibles(economique, caa). accessibles(economique, fic).
accessibles(economique, emp). accessibles(economique, iggia).

% ---------------------------------------------------------------------
% 3. RÈGLES DÉRIVÉES -- famille de bac
% ---------------------------------------------------------------------

famille_bac(E, scientifique) :- serie_bac(E, c).
famille_bac(E, scientifique) :- serie_bac(E, d).
famille_bac(E, scientifique) :- serie_bac(E, s).
famille_bac(E, litteraire) :- serie_bac(E, a1).
famille_bac(E, litteraire) :- serie_bac(E, a2).
famille_bac(E, litteraire) :- serie_bac(E, l).
famille_bac(E, economique) :- serie_bac(E, ose).

% ---------------------------------------------------------------------
% 4. ÉLIGIBILITÉ
% ---------------------------------------------------------------------

% Prérequis dérivés automatiquement (pas besoin de possede/2)
prerequis_auto(bac_scientifique).

% Parcours possibles pour un étudiant : critère UNIQUE = série de bac autorisée.
% Le métier visé et les prérequis sont des SUGGESTIONS NON BLOQUANTES :
% ils boostent le score de compatibilité (voir section 5) sans jamais exclure.
parcours_possibles(E, P) :-
    parcours(P),
    \+ bloque_par_serie(E, P).

bloque_par_serie(E, P) :-
    famille_bac(E, scientifique),
    \+ accessibles(scientifique, P).

bloque_par_serie(E, P) :-
    famille_bac(E, litteraire),
    \+ accessibles(litteraire, P).

bloque_par_serie(E, P) :-
    famille_bac(E, economique),
    \+ accessibles(economique, P).

% Série inconnue ou "autre" : aucun blocage par série.
% Il n'y a plus de blocage par prérequis : voir suggestion/3 (section 5).

% ---------------------------------------------------------------------
% 5. SCORES DE COMPATIBILITÉ (motifs de recommandation)
% ---------------------------------------------------------------------

% matières communes entre les préférences de l'étudiant et le parcours
matiere_commune(E, P) :- prefere(E, M), enseigne(P, M).

% compétences possédées alignées sur le parcours
competence_commune(E, P) :- possede(E, C), developpe(P, C).

% le métier visé est préparé par le parcours
metier_alignee(E, P) :- vise(E, M), prepareA(P, M).

% --- Intérêts liés à un parcours ---
% Enrichi d'après l'analyse des descriptions de chaque filière (data/sources/).
lieA_interet(esii, technologie). lieA_interet(esii, science).
lieA_interet(isaia, technologie). lieA_interet(isaia, science).
lieA_interet(imticia, technologie). lieA_interet(imticia, art).
lieA_interet(iggia, technologie). lieA_interet(iggia, entrepreneuriat).
lieA_interet(iggia, social).
lieA_interet(caa, social). lieA_interet(caa, entrepreneuriat).
lieA_interet(fic, entrepreneuriat). lieA_interet(fic, social).
lieA_interet(emp, entrepreneuriat). lieA_interet(emp, social).
lieA_interet(iaa, science). lieA_interet(iaa, sante).
lieA_interet(iaa, environnement).
lieA_interet(pip, science). lieA_interet(pip, environnement).
lieA_interet(aee, science). lieA_interet(aee, environnement).
lieA_interet(emii, technologie). lieA_interet(emii, science).
lieA_interet(gca, art). lieA_interet(gca, technologie).
lieA_interet(icmp, science). lieA_interet(icmp, environnement).
lieA_interet(tee, environnement). lieA_interet(tee, social).
lieA_interet(teh, social).

% --- Liens compétence → intérêt thématique (bonus croisé) ---
% Si l'étudiant possède une compétence liée à un intérêt du parcours, bonus +1.
competence_lie_interet(competence_programmation, technologie).
competence_lie_interet(competence_logique, technologie).
competence_lie_interet(competence_logique, science).
competence_lie_interet(competence_manuelle, technologie).
competence_lie_interet(competence_esprit_critique, science).
competence_lie_interet(competence_creativite, art).
competence_lie_interet(competence_relationnelle, social).
competence_lie_interet(competence_expression, social).
competence_lie_interet(competence_organisation, entrepreneuriat).

interet_commun(E, P) :- interet(E, I), lieA_interet(P, I).

% Bonus croisé : l'étudiant possède une compétence liée à un intérêt du parcours
bonus_croise(E, P) :-
    possede(E, C),
    competence_lie_interet(C, I),
    lieA_interet(P, I).

% Suggestion de prérequis possédé (non dérivé automatiquement) : bonus, pas un blocage
suggestion(E, P, R) :-
    necessite(P, R),
    possede(E, R),
    \+ prerequis_auto(R).

% score global de compatibilité — PONDÉRÉ
% Matière commune ×1, Compétence ×2, Intérêt ×1, Métier ×3,
% Suggestion ×1, Bonus croisé ×1
score_compatibilite(E, P, Score) :-
    aggregate_all(count, matiere_commune(E, P), M),
    aggregate_all(count, competence_commune(E, P), C),
    aggregate_all(count, interet_commun(E, P), I),
    ( metier_alignee(E, P) -> Met = 3 ; Met = 0 ),
    aggregate_all(count, suggestion(E, P, _), Sg),
    aggregate_all(count, bonus_croise(E, P), Bc),
    Score is M + (C * 2) + I + Met + Sg + Bc.

% motifs d'explication pour un parcours
motif(E, P, matiere(M)) :- matiere_commune(E, P), prefere(E, M), enseigne(P, M).
motif(E, P, competence(C)) :- competence_commune(E, P), possede(E, C), developpe(P, C).
motif(E, P, interet(I)) :- interet_commun(E, P), interet(E, I), lieA_interet(P, I).
motif(E, P, metier(M)) :- metier_alignee(E, P), vise(E, M), prepareA(P, M).
motif(E, P, suggestion(R)) :- suggestion(E, P, R).
motif(E, P, bonus_croise(C, I)) :- possede(E, C), competence_lie_interet(C, I), lieA_interet(P, I).
