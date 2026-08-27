from typing import Any, Optional

from pydantic import BaseModel, Field


class AnswerPayload(BaseModel):
    champ: str
    valeur: Any


class OptionPayload(BaseModel):
    label: str
    value: str


class QuestionPayload(BaseModel):
    champ: str
    question: str
    multiple: bool
    options: list[OptionPayload]


class ChatRequest(BaseModel):
    message: Optional[str] = Field(default=None, min_length=1)
    answer: Optional[AnswerPayload] = None
    conversation_id: Optional[str] = None
    history: list[dict] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    tools_used: list[str] = Field(default_factory=list)
    question: Optional[QuestionPayload] = None
    recommendation: Optional[dict] = None
    termine: bool = False
    profil: dict = Field(default_factory=dict)
    inspection: Optional[dict] = None


class InspectionRequest(BaseModel):
    mode: bool
    force_prolog: bool = False


class PredictRequest(BaseModel):
    profil: dict = Field(default_factory=dict)


class PredictResponse(BaseModel):
    parcours: str
    confidence: float
    probabilities: dict[str, float]
    model: str


class ProfilRequest(BaseModel):
    profil: dict = Field(default_factory=dict)


class RecommendationItem(BaseModel):
    parcours: str
    categorie: str
    score_fusion: float
    proba_ml: Optional[float]
    score_regles: int
    motifs: dict[str, Any]
    description: str


class RecommendationResponse(BaseModel):
    profil: dict
    moteur_regles: str
    ml_utilise: bool
    ml: dict
    parcours_possibles: list[str]
    parcours_bloques: list[str]
    classement: list[RecommendationItem]
    methodologie: str
    inspection: Optional[dict] = None


class CompareRequest(BaseModel):
    parcours_a: str
    parcours_b: str
    profil: dict = Field(default_factory=dict)


class PrerequisRequest(BaseModel):
    parcours: str
    profil: dict = Field(default_factory=dict)


class SourceDocument(BaseModel):
    doc_id: str
    titre: str
    origine: str
    date: str
    statut: str


class PrologTestRequest(BaseModel):
    profil: dict = Field(default_factory=dict)
    force_prolog: bool | None = None


class PrologQueryRequest(BaseModel):
    profil: dict = Field(default_factory=dict)
    requete: str


class MlRfExploreRequest(BaseModel):
    params: dict = Field(default_factory=dict)
    profil: dict = Field(default_factory=dict)
