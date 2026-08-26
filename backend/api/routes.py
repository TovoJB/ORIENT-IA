from fastapi import APIRouter, HTTPException

from api.schemas import (
    ChatRequest,
    ChatResponse,
    PredictRequest,
    PredictResponse,
)
from repositories.conversation_repository import conversation_repository
from services import llm_service
from services.ml_service import predict
from services.rag_service import retriever

router = APIRouter()

SYSTEM_INSTRUCTION = (
    "You are a helpful hackathon AI assistant. "
    "Answer concisely and in the same language as the user."
)


def _build_prompt(message: str, history: list[dict], context: list[dict]) -> str:
    parts = []

    if context:
        docs = "\n".join(f"- {hit['text']}" for hit in context)
        parts.append(f"RAG context:\n{docs}")

    if history:
        lines = [
            f"{item.get('role', 'user')}: {item.get('content', '')}"
            for item in history[-6:]
        ]
        parts.append("Recent conversation:\n" + "\n".join(lines))

    parts.append(f"User: {message}")
    return "\n\n".join(parts)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    context = retriever.retrieve(request.message)

    prompt = _build_prompt(request.message, request.history, context)
    reply = llm_service.ask_gemini(prompt, system_instruction=SYSTEM_INSTRUCTION)

    conversation = conversation_repository.add_message(
        request.conversation_id, "user", request.message
    )
    conversation_repository.add_message(conversation.id, "assistant", reply)

    return ChatResponse(
        reply=reply,
        conversation_id=conversation.id,
    )


@router.post("/predict", response_model=PredictResponse)
async def ml_predict(request: PredictRequest) -> PredictResponse:
    try:
        result = predict(request.features)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return PredictResponse(**result)
