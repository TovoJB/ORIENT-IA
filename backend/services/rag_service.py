from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import config


class SimpleRetriever:
    """Minimal RAG: TF-IDF embeddings + cosine similarity search."""

    def __init__(self) -> None:
        self.documents: list[str] = []
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix: np.ndarray | None = None

    def load_documents(self, path: str | None = None) -> int:
        path = path or config.RAG_DOCUMENTS_PATH
        self.documents = Path(path).read_text(encoding="utf-8").splitlines()
        self._matrix = self._vectorizer.fit_transform(self.documents)
        return len(self.documents)

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        if not self.documents:
            return []
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix)[0]
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [
            {"text": self.documents[i], "score": float(scores[i])}
            for i in top_indices
            if scores[i] > 0
        ]


retriever = SimpleRetriever()
