"""RAG v2 -- corpus documenté + embeddings + base vectorielle + citations.

Moteurs d'embeddings :
- "gemini" : API Google text-embedding-004 (par défaut, vecteurs réels)
- "tfidf"  : repli local sans réseau (TF-IDF + cosinus)

Le service ne plante jamais : si l'API Gemini ne répond pas (clé absente /
invalide / hors-ligne), il bascule automatiquement sur le repli TF-IDF.

Chaque résultat est accompagné des métadonnées de source (titre, origine, date,
statut) pour une citation vérifiable, conformément au registre de traçabilité
data/sources/registre_sources.csv.
"""

import csv
import re
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from config import config

REGISTRE_PATH = Path(config.RAG_SOURCES_DIR) / "registre_sources.csv"


# ---------------------------------------------------------------------
#  Lecture du corpus documenté
# ---------------------------------------------------------------------
def _doc_id_from_filename(path: Path) -> str:
    name = path.stem
    name = re.sub(r"^\d+_", "", name)
    return name


def _load_registre() -> dict[str, dict]:
    """doc_id -> {titre, origine, date, statut}."""
    registre: dict[str, dict] = {}
    if not REGISTRE_PATH.exists():
        return registre
    with open(REGISTRE_PATH, encoding="utf-8") as file:
        for row in csv.DictReader(file, delimiter=";"):
            registre[row["doc_id"]] = {
                "titre": row["titre"],
                "origine": row["origine"],
                "date": row["date"],
                "statut": row["statut"],
            }
    return registre


def _chunker(text: str, max_chars: int = 900) -> list[str]:
    """Découpe un document en segments par section (titres + paragraphes)."""
    text = re.sub(r"(?m)^Source\s*:.*\n?", "", text)
    sections = re.split(r"\n(?=#{1,3} )", text)
    chunks: list[str] = []
    for section in sections:
        current = ""
        for paragraph in section.split("\n\n"):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            if len(current) + len(paragraph) <= max_chars:
                current = f"{current}\n{paragraph}" if current else paragraph
            else:
                if current:
                    chunks.append(current)
                current = paragraph
        if current:
            chunks.append(current)
    return chunks


def load_corpus() -> list[dict[str, Any]]:
    """Charge tous les documents .md de data/sources/ et les découpe en segments."""
    sources_dir = Path(config.RAG_SOURCES_DIR)
    registre = _load_registre()
    chunks: list[dict[str, Any]] = []
    for path in sorted(sources_dir.glob("*.md")):
        doc_id = _doc_id_from_filename(path)
        metadata = registre.get(doc_id, {})
        text = path.read_text(encoding="utf-8")
        content = re.sub(r"^#.*\n", "", text, count=1)
        for i, segment in enumerate(_chunker(content)):
            chunks.append(
                {
                    "chunk_id": f"{doc_id}#{i}",
                    "doc_id": doc_id,
                    "titre": metadata.get("titre", doc_id),
                    "origine": metadata.get("origine", "non documentée"),
                    "date": metadata.get("date", "non datée"),
                    "statut": metadata.get("statut", "externe"),
                    "text": segment,
                }
            )
    return chunks


# ---------------------------------------------------------------------
#  Moteurs d'embeddings
# ---------------------------------------------------------------------
class EmbeddingUnavailable(Exception):
    """Levée quand aucun moteur d'embeddings ne répond."""


class _Embedder(ABC):
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray: ...


class _GeminiEmbedder(_Embedder):
    def __init__(self) -> None:
        from google import genai

        if not config.GEMINI_API_KEY:
            raise EmbeddingUnavailable("GEMINI_API_KEY absente")
        self._client = genai.Client(api_key=config.GEMINI_API_KEY)
        self._model = config.GEMINI_EMBEDDING_MODEL

    def name(self) -> str:
        return "gemini"

    def embed(self, texts: list[str]) -> np.ndarray:
        try:
            response = self._client.models.embed_content(
                model=self._model, contents=texts
            )
            vectors = [emb.values for emb in response.embeddings]
            return np.asarray(vectors, dtype=np.float32)
        except Exception as exc:
            raise EmbeddingUnavailable(f"Gemini embeddings: {exc}") from exc


class _TfidfEmbedder(_Embedder):
    """Repli local : TF-IDF + normalisation L2 (pas d'API, pas de réseau)."""

    def __init__(self) -> None:
        self._vectorizer = TfidfVectorizer(stop_words="english", lowercase=True)
        self._fitted = False

    def name(self) -> str:
        return "tfidf"

    def fit(self, texts: list[str]) -> None:
        self._vectorizer.fit(texts)
        self._fitted = True

    def embed(self, texts: list[str]) -> np.ndarray:
        matrix = self._vectorizer.transform(texts)
        matrix = matrix.toarray().astype(np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9
        return matrix / norms


# ---------------------------------------------------------------------
#  Index vectoriel (persisté en SQLite pour la traçabilité)
# ---------------------------------------------------------------------
class _VectorStore:
    def __init__(self) -> None:
        self._chunks: list[dict[str, Any]] = []
        self._matrix: np.ndarray | None = None
        self._engine: _Embedder | None = None

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(config.DB_PATH)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rag_chunks (
                chunk_id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                titre TEXT,
                origine TEXT,
                date TEXT,
                statut TEXT,
                text TEXT NOT NULL,
                vector BLOB,
                dim INTEGER,
                engine TEXT
            )
            """
        )
        conn.commit()
        return conn

    def engine(self) -> _Embedder:
        """Sélectionne le moteur : gemini, sinon tfidf (jamais d'exception)."""
        if self._engine is not None:
            return self._engine
        candidates: list[_Embedder] = []
        if config.RAG_EMBEDDING == "gemini":
            candidates.append(_GeminiEmbedder())
        candidates.append(_TfidfEmbedder())
        for candidate in candidates:
            try:
                if isinstance(candidate, _TfidfEmbedder):
                    candidate.fit([c["text"] for c in self._chunks])
                # test rapide du moteur sur le premier segment
                candidate.embed([self._chunks[0]["text"]])
                self._engine = candidate
                return candidate
            except EmbeddingUnavailable:
                continue
        raise EmbeddingUnavailable("aucun moteur d'embeddings disponible")

    def build(self, chunks: list[dict[str, Any]]) -> None:
        self._chunks = chunks
        engine = self.engine()
        vectors = engine.embed([c["text"] for c in chunks])
        self._matrix = vectors
        self._persist(engine.name(), vectors)

    def _persist(self, engine_name: str, vectors: np.ndarray) -> None:
        conn = self._connect()
        conn.execute("DELETE FROM rag_chunks")
        for chunk, vector in zip(self._chunks, vectors):
            conn.execute(
                "INSERT OR REPLACE INTO rag_chunks "
                "(chunk_id, doc_id, titre, origine, date, statut, text, vector, dim, engine) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    chunk["chunk_id"],
                    chunk["doc_id"],
                    chunk["titre"],
                    chunk["origine"],
                    chunk["date"],
                    chunk["statut"],
                    chunk["text"],
                    vector.astype(np.float32).tobytes(),
                    int(vector.shape[0]),
                    engine_name,
                ),
            )
        conn.commit()
        conn.close()

    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not self._chunks or self._matrix is None:
            self.build(load_corpus())
        engine = self.engine()
        query_vec = engine.embed([query])[0]
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-9)
        matrix = self._matrix
        matrix = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9)
        scores = matrix @ query_norm

        order = np.argsort(scores)[::-1]
        results: list[dict[str, Any]] = []
        for idx in order[:top_k]:
            chunk = self._chunks[idx]
            results.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "doc_id": chunk["doc_id"],
                    "titre": chunk["titre"],
                    "origine": chunk["origine"],
                    "date": chunk["date"],
                    "statut": chunk["statut"],
                    "text": chunk["text"],
                    "score": round(float(scores[idx]), 4),
                }
            )
        return results


_store = _VectorStore()


# ---------------------------------------------------------------------
#  API publique (compatible avec l'ancien SimpleRetriever)
# ---------------------------------------------------------------------
def moteur_embedding() -> str:
    if not _store._chunks:
        load_documents()
    if not _store._chunks:
        return "aucun"
    try:
        return _store.engine().name()
    except EmbeddingUnavailable:
        return "aucun"


def load_documents() -> int:
    chunks = load_corpus()
    _store.build(chunks)
    return len(chunks)


def retrieve(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Recherche les segments les plus proches de la requête, avec citations."""
    if not _store._chunks:
        load_documents()
    try:
        return _store.retrieve(query, top_k=top_k)
    except EmbeddingUnavailable:
        return []


retriever = _store
