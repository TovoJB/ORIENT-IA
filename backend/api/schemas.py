from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    history: list[dict] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str


class PredictRequest(BaseModel):
    features: list[float] = Field(..., min_length=1)


class PredictResponse(BaseModel):
    prediction: int
    class_name: str
    probabilities: list[float]
