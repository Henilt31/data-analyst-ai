import pytest
from app.rag.embeddings import LocalEmbeddingService

def test_local_embeddings_dimensionality():
    service = LocalEmbeddingService()
    texts = ["customer churn rate distribution", "revenue versus marketing spend correlation"]
    embeddings = service.encode(texts)

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    assert len(embeddings[1]) == 384
    assert all(isinstance(x, float) for x in embeddings[0])

def test_local_embeddings_determinism():
    service = LocalEmbeddingService()
    text = "monthly active users and churn"
    emb1 = service.encode([text])[0]
    emb2 = service.encode([text])[0]
    assert emb1 == emb2
