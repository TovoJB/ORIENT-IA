from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from repositories.conversation_repository import conversation_repository

app = FastAPI(title="Hackathon AI Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health() -> dict:
    database = "connected" if conversation_repository.health_check() else "error"
    return {"status": "ok", "database": database}
