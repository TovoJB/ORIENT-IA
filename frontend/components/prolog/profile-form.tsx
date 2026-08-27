export interface FieldOption {
  value: string;
  label: string;
}

export interface FormField {
  champ: string;
  label: string;
  multiple: boolean;
  options: FieldOption[];
}

export const FORM_FIELDS: FormField[] = [
  {
    champ: "serie_bac",
    label: "Série de baccalauréat",
    multiple: false,
    options: [
      { value: "s", label: "Scientifique (C, D, S)" },
      { value: "l", label: "Littéraire (A1, A2, L)" },
      { value: "ose", label: "Économique (OSE)" },
      { value: "autre", label: "Autre / inconnue" },
    ],
  },
  {
    champ: "moyenne_generale",
    label: "Moyenne générale au bac",
    multiple: false,
    options: [
      { value: "1", label: "Moins de 10" },
      { value: "2", label: "10 à 12" },
      { value: "3", label: "12 à 14" },
      { value: "4", label: "14 à 16" },
      { value: "5", label: "16 à 20" },
    ],
  },
  {
    champ: "note_mathematiques",
    label: "Résultats en mathématiques",
    multiple: false,
    options: [
      { value: "6", label: "0 à 8" },
      { value: "10", label: "8 à 12" },
      { value: "14", label: "12 à 16" },
      { value: "17", label: "16 à 20" },
    ],
  },
  {
    champ: "matieres",
    label: "Matières préférées",
    multiple: true,
    options: [
      { value: "mathematiques", label: "Mathématiques" },
      { value: "physique", label: "Physique / électronique" },
      { value: "informatique", label: "Informatique / programmation" },
      { value: "svt", label: "SVT / biologie" },
      { value: "francais", label: "Français / littérature" },
      { value: "malagasy", label: "Malagasy" },
      { value: "hg", label: "Histoire-Géo" },
      { value: "ses", label: "SES / économie" },
      { value: "arts", label: "Arts / dessin" },
    ],
  },
  {
    champ: "competences",
    label: "Compétences",
    multiple: true,
    options: [
      { value: "logique", label: "Logique / analyse" },
      { value: "programmation", label: "Programmation" },
      { value: "expression", label: "Expression écrite / orale" },
      { value: "manuelle", label: "Travail manuel / technique" },
      { value: "relationnelle", label: "Relationnel / communication" },
      { value: "creativite", label: "Créativité" },
      { value: "organisation", label: "Organisation / gestion de projet" },
      { value: "esprit_critique", label: "Esprit critique" },
    ],
  },
  {
    champ: "interets",
    label: "Centres d'intérêt",
    multiple: true,
    options: [
      { value: "technologie", label: "Technologie / numérique" },
      { value: "science", label: "Science / recherche" },
      { value: "art", label: "Art / design" },
      { value: "sante", label: "Santé" },
      { value: "entrepreneuriat", label: "Entrepreneuriat" },
      { value: "environnement", label: "Environnement" },
      { value: "social", label: "Social / humanitaire" },
      { value: "sport", label: "Sport" },
    ],
  },
  {
    champ: "metier_vise",
    label: "Métier visé",
    multiple: false,
    options: [
      { value: "data_scientist", label: "Data scientist" },
      { value: "ingenieur_ml", label: "Ingénieur ML / IA" },
      { value: "developpeur", label: "Développeur logiciel" },
      { value: "chef_de_projet", label: "Chef de projet" },
      { value: "commercial_export", label: "Commercial / affaires" },
      { value: "analyste_financier", label: "Finance / comptabilité" },
      { value: "juriste", label: "Droit" },
      { value: "environnementaliste", label: "Environnement / agronomie" },
      { value: "directeur_hotel", label: "Tourisme / hôtellerie" },
      { value: "", label: "Pas encore sûr" },
    ],
  },
  {
    champ: "environnement",
    label: "Environnement de travail",
    multiple: false,
    options: [
      { value: "bureau", label: "Bureau / informatique" },
      { value: "relationnel", label: "Relationnel / social" },
      { value: "recherche", label: "Recherche / laboratoire" },
      { value: "terrain", label: "Terrain" },
    ],
  },
  {
    champ: "prerequis",
    label: "Suggestions d'acquis (non bloquantes)",
    multiple: true,
    options: [
      { value: "bases_algo", label: "Bases en algorithmique" },
      { value: "anglais", label: "Bon niveau d'anglais" },
      { value: "maths_avancees", label: "Mathématiques avancées" },
    ],
  },
];

export type ProfileForm = Record<string, string | string[]>;

const MULTI_PREFIX: Record<string, string> = {
  matieres: "matiere_",
  competences: "competence_",
  interets: "interet_",
  prerequis: "prerequis_",
};

export function buildProfileFromForm(form: ProfileForm): Record<string, string> {
  const profile: Record<string, string> = {};
  for (const field of FORM_FIELDS) {
    const value = form[field.champ];
    if (!value || (Array.isArray(value) && value.length === 0)) continue;
    if (field.multiple) {
      const prefix = MULTI_PREFIX[field.champ];
      for (const v of value as string[]) {
        if (v) profile[`${prefix}${v}`] = "1";
      }
    } else if (String(value) !== "") {
      profile[field.champ] = String(value);
    }
  }
  return profile;
}

export function emptyForm(): ProfileForm {
  const form: ProfileForm = {};
  for (const field of FORM_FIELDS) {
    form[field.champ] = field.multiple ? [] : "";
  }
  return form;
}
