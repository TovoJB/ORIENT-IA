const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface RecommendationItem {
  parcours: string;
  categorie: string;
  score_fusion: number;
  proba_ml: number | null;
  score_regles: number;
  motifs: {
    matieres: string[];
    competences: string[];
    interets: string[];
    metier_alignee: boolean;
    suggestions?: string[];
  };
  description: string;
}

export interface RecommendationResult {
  moteur_regles: string;
  ml_utilise: boolean;
  ml: { modele: string | null; confiance: number | null };
  parcours_possibles: string[];
  parcours_bloques: string[];
  classement: RecommendationItem[];
  methodologie: string;
  inspection?: InspectionData | null;
}

export interface InspectionData {
  mode: boolean;
  force_prolog: boolean;
  moteur: string;
  erreur_prolog: string | null;
  filtrage: {
    possibles: string[];
    bloques: { parcours: string; raisons: string[] }[];
  };
  regles: {
    parcours: string;
    score: number;
    motifs: {
      matieres: string[];
      competences: string[];
      interets: string[];
      metier_alignee: boolean;
    };
  }[];
  ml: {
    utilise: boolean;
    modele: string | null;
    confiance: number | null;
    probabilites: Record<string, number>;
  };
  fusion: {
    parcours: string;
    proba_ml: number | null;
    score_regles_norm: number;
    score_regles?: number;
    score_fusion: number;
  }[];
  methodologie: string;
  requetes_prolog: {
    moteur: string;
    requete: string;
    resultats: Record<string, string>[];
  }[];
}

export interface InspectionState {
  mode: boolean;
  force_prolog: boolean;
  swipl_disponible: boolean;
}

export interface QuestionOption {
  label: string;
  value: string;
}

export interface Question {
  champ: string;
  question: string;
  multiple: boolean;
  options: QuestionOption[];
}

export interface ChatApiResponse {
  reply: string;
  conversation_id: string;
  tools_used: string[];
  question: Question | null;
  recommendation: RecommendationResult | null;
  termine: boolean;
  profil: Record<string, string>;
}

interface ChatTurnBody {
  message?: string;
  answer?: { champ: string; valeur: string | string[] };
  conversationId?: string;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }

  return res.json();
}

export async function sendChatTurn(body: ChatTurnBody): Promise<ChatApiResponse> {
  return post<ChatApiResponse>("/chat", {
    message: body.message,
    answer: body.answer,
    conversation_id: body.conversationId,
    history: [],
  });
}

export async function sendOrientation(
  profil: Record<string, string>
): Promise<RecommendationResult> {
  return post<RecommendationResult>("/orienter", { profil });
}

export async function getInspection(): Promise<InspectionState> {
  const res = await fetch(`${API_URL}/inspection`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export async function setInspection(
  mode: boolean,
  forceProlog: boolean
): Promise<InspectionState> {
  return post<InspectionState>("/inspection", { mode, force_prolog: forceProlog });
}

export interface PrologMotifs {
  matieres: string[];
  competences: string[];
  interets: string[];
  metier_alignee: boolean;
  metiers: string[];
  suggestions: string[];
}

export interface PrologScore {
  parcours: string;
  categorie: string;
  score: number;
  motifs: PrologMotifs;
}

export interface PrologQuery {
  requete: string;
  resultats: Record<string, string>[];
}

export interface PrologTestResult {
  moteur: string;
  force_prolog: boolean;
  swipl_disponible: boolean;
  erreur_prolog: string | null;
  profil: Record<string, string>;
  faits: string[];
  eligibilite: {
    possibles: string[];
    bloques: { parcours: string; raisons: string[] }[];
  };
  scores: PrologScore[];
  requetes: PrologQuery[];
}

export interface PrologQueryResult {
  moteur: string;
  requete: string;
  resultats: Record<string, string>[];
  erreur: string | null;
}

export async function testProlog(
  profil: Record<string, string>,
  forceProlog?: boolean
): Promise<PrologTestResult> {
  return post<PrologTestResult>("/prolog/test", {
    profil,
    force_prolog: forceProlog ?? null,
  });
}

export async function runPrologQuery(
  profil: Record<string, string>,
  requete: string
): Promise<PrologQueryResult> {
  return post<PrologQueryResult>("/prolog/query", { profil, requete });
}

export interface RfExploreResult {
  train: {
    n_samples: number;
    n_features: number;
    n_classes: number;
    train_size: number;
    test_size: number;
    duree_s: number;
  };
  modele: {
    nom: string | null;
    accuracy_test: number | null;
    trained_at: string | null;
    dataset_path: string | null;
  };
  metriques: {
    accuracy: number;
    log_loss: number | null;
    precision_macro: number;
    recall_macro: number;
    f1_macro: number;
  };
  feature_importances: { feature: string; importance: number }[];
  prediction: {
    parcours: string;
    confidence: number;
    probabilities: Record<string, number>;
  } | null;
}

export async function exploreRandomForest(
  profil: Record<string, string>
): Promise<RfExploreResult> {
  return post<RfExploreResult>("/ml/rf/explore", { profil });
}
