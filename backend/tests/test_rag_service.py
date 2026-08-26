from services.rag_service import SimpleRetriever

DOCUMENTS = [
    "The clinic opens at 8am.",
    "Cardiology consultations are on Tuesdays.",
    "The clinic closes at 6pm.",
]


def test_retriever_finds_relevant_document():
    retriever = SimpleRetriever()
    retriever.documents = DOCUMENTS
    retriever._matrix = retriever._vectorizer.fit_transform(DOCUMENTS)

    hits = retriever.retrieve("when does cardiology happen", top_k=1)
    assert hits, "should return at least one result"
    assert "Tuesday" in hits[0]["text"]


def test_retriever_without_documents_returns_empty():
    retriever = SimpleRetriever()
    assert retriever.retrieve("anything") == []
