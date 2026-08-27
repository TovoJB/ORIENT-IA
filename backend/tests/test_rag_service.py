from services import rag_service


def test_load_corpus_documents():
    chunks = rag_service.load_corpus()
    assert len(chunks) >= 6, "le corpus documenté doit contenir les 6 documents"
    for chunk in chunks:
        assert chunk["doc_id"]
        assert {"titre", "origine", "date", "statut"} <= set(chunk)


def test_retrieve_with_citations():
    hits = rag_service.retrieve("devenir data scientist statistiques", top_k=3)
    assert hits
    for hit in hits:
        # chaque résultat porte ses métadonnées de source (citation vérifiable)
        assert {"text", "titre", "origine", "date", "statut", "score"} <= set(hit)
    assert any("ISAIA" in hit["text"] or "isaia" in hit["text"].lower() for hit in hits)


def test_retrieve_pertinence():
    hits_tourisme = rag_service.retrieve("hôtellerie art culinaire restauration", top_k=1)
    assert hits_tourisme
    assert "TEH" in hits_tourisme[0]["text"]


def test_moteur_embedding():
    assert rag_service.moteur_embedding() in ("gemini", "tfidf", "aucun")
