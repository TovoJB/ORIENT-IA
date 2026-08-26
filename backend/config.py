import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BACKEND_DIR = Path(__file__).resolve().parent


class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    ML_MODEL_PATH = os.getenv("ML_MODEL_PATH", str(BACKEND_DIR / "ml_model.joblib"))
    RAG_DOCUMENTS_PATH = os.getenv(
        "RAG_DOCUMENTS_PATH", str(BACKEND_DIR / "rag_documents.txt")
    )
    DB_PATH = os.getenv("DB_PATH", str(BACKEND_DIR / "clinique.db"))


config = Config()
