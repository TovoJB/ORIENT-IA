import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent


class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
    ML_MODEL_PATH = os.getenv("ML_MODEL_PATH", str(BACKEND_DIR / "ml_model.joblib"))
    # Jeu de données d'entraînement (synthétique documenté par défaut,
    # remplaçable par les vraies réponses de l'enquête)
    DATASET_PATH = os.getenv(
        "DATASET_PATH", str(PROJECT_DIR / "data" / "synthetique" / "dataset_orientia_synthetique.csv")
    )
    RAG_DOCUMENTS_PATH = os.getenv(
        "RAG_DOCUMENTS_PATH", str(BACKEND_DIR / "rag_documents.txt")
    )
    # Dossier du corpus RAG documenté (data/sources/*.md)
    RAG_SOURCES_DIR = os.getenv(
        "RAG_SOURCES_DIR", str(PROJECT_DIR / "data" / "sources")
    )
    # Moteur d'embeddings : "gemini" (API) ou "tfidf" (fallback sans réseau)
    RAG_EMBEDDING = os.getenv("RAG_EMBEDDING", "gemini")
    DB_PATH = os.getenv("DB_PATH", str(BACKEND_DIR / "clinique.db"))
    # Répertoire contenant le binaire swipl (mode Prolog exclusif), si hors PATH
    SWIPL_BIN_DIR = os.getenv("SWIPL_BIN_DIR", "")


config = Config()
