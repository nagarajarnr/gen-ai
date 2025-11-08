"""Tests for vector similarity search."""

import pytest
from unittest.mock import AsyncMock, patch
import numpy as np

from app.controllers.vector_search import VectorSearchController


@pytest.mark.asyncio
async def test_search_documents_finds_similar(test_db, sample_document_in_db):
    """Test vector search finds similar documents."""
    controller = VectorSearchController(test_db)

    # Mock embedding adapter to return similar embedding
    with patch('app.controllers.vector_search.get_embedding_adapter') as mock_adapter:
        mock_adapter_instance = AsyncMock()
        # Return same embedding for high similarity
        mock_adapter_instance.generate_embedding.return_value = sample_document_in_db["embeddings"]
        mock_adapter.return_value = mock_adapter_instance

        results = await controller.search_documents(
            query="GDPR data retention",
            top_k=5,
        )

        assert len(results) > 0
        assert results[0]["doc_id"] == sample_document_in_db["_id"]
        assert results[0]["similarity_score"] > 0.9  # High similarity


@pytest.mark.asyncio
async def test_search_documents_no_matches(test_db):
    """Test vector search with no matching documents."""
    controller = VectorSearchController(test_db)

    with patch('app.controllers.vector_search.get_embedding_adapter') as mock_adapter:
        mock_adapter_instance = AsyncMock()
        # Random embedding unlikely to match
        mock_adapter_instance.generate_embedding.return_value = [0.1] * 768
        mock_adapter.return_value = mock_adapter_instance

        results = await controller.search_documents(
            query="Completely unrelated query",
            top_k=5,
            similarity_threshold=0.9,  # High threshold
        )

        assert len(results) == 0  # No matches above threshold


@pytest.mark.asyncio
async def test_cosine_similarity_calculation():
    """Test cosine similarity calculation."""
    controller = VectorSearchController(None)

    # Identical vectors should have similarity 1.0
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    similarity = controller._cosine_similarity(vec1, vec2)
    assert abs(similarity - 1.0) < 0.001

    # Orthogonal vectors should have similarity ~0.0
    vec3 = [1.0, 0.0, 0.0]
    vec4 = [0.0, 1.0, 0.0]
    similarity = controller._cosine_similarity(vec3, vec4)
    assert abs(similarity - 0.0) < 0.001

    # Opposite vectors should have similarity 0.0 (clamped from -1.0)
    vec5 = [1.0, 0.0, 0.0]
    vec6 = [-1.0, 0.0, 0.0]
    similarity = controller._cosine_similarity(vec5, vec6)
    assert similarity >= 0.0  # Clamped to [0, 1]


@pytest.mark.asyncio
async def test_search_with_document_ids_filter(test_db, sample_document_in_db):
    """Test searching within specific document IDs."""
    controller = VectorSearchController(test_db)

    # Add another document
    other_doc = {
        "_id": "other-doc-001",
        "filename": "other.txt",
        "mime_type": "text/plain",
        "text_content": "Other content",
        "embeddings": [0.2] * 768,
    }
    await test_db.documents.insert_one(other_doc)

    with patch('app.controllers.vector_search.get_embedding_adapter') as mock_adapter:
        mock_adapter_instance = AsyncMock()
        mock_adapter_instance.generate_embedding.return_value = sample_document_in_db["embeddings"]
        mock_adapter.return_value = mock_adapter_instance

        # Search only in specific document
        results = await controller.search_documents(
            query="test query",
            top_k=5,
            document_ids=[sample_document_in_db["_id"]],
        )

        # Should only find the specified document
        assert len(results) == 1
        assert results[0]["doc_id"] == sample_document_in_db["_id"]

    # Cleanup
    await test_db.documents.delete_one({"_id": "other-doc-001"})


@pytest.mark.asyncio
async def test_search_results_sorted_by_similarity(test_db):
    """Test that search results are sorted by similarity score."""
    controller = VectorSearchController(test_db)

    # Create multiple documents with varying similarity
    query_embedding = [1.0] + [0.0] * 767

    docs = []
    for i in range(5):
        # Create embeddings with decreasing similarity to query
        embedding = np.array(query_embedding)
        noise = np.random.randn(768) * (i * 0.1)
        doc_embedding = (embedding + noise)
        doc_embedding = doc_embedding / np.linalg.norm(doc_embedding)

        doc = {
            "_id": f"doc-{i}",
            "filename": f"doc{i}.txt",
            "mime_type": "text/plain",
            "text_content": f"Document {i}",
            "embeddings": doc_embedding.tolist(),
        }
        docs.append(doc)

    await test_db.documents.insert_many(docs)

    with patch('app.controllers.vector_search.get_embedding_adapter') as mock_adapter:
        mock_adapter_instance = AsyncMock()
        mock_adapter_instance.generate_embedding.return_value = query_embedding
        mock_adapter.return_value = mock_adapter_instance

        results = await controller.search_documents(
            query="test",
            top_k=5,
            similarity_threshold=0.0,
        )

        # Verify results are sorted by similarity (descending)
        for i in range(len(results) - 1):
            assert results[i]["similarity_score"] >= results[i + 1]["similarity_score"]

    # Cleanup
    await test_db.documents.delete_many({"_id": {"$regex": "^doc-"}})


@pytest.mark.asyncio
async def test_get_similar_documents(test_db, sample_document_in_db):
    """Test finding similar documents to a given document."""
    controller = VectorSearchController(test_db)

    # Add another similar document
    similar_embedding = np.array(sample_document_in_db["embeddings"])
    similar_embedding = similar_embedding + np.random.randn(768) * 0.1
    similar_embedding = similar_embedding / np.linalg.norm(similar_embedding)

    similar_doc = {
        "_id": "similar-doc-001",
        "filename": "similar.txt",
        "mime_type": "text/plain",
        "text_content": "Similar content",
        "embeddings": similar_embedding.tolist(),
    }
    await test_db.documents.insert_one(similar_doc)

    results = await controller.get_similar_documents(
        document_id=sample_document_in_db["_id"],
        top_k=5,
    )

    # Should find the similar document
    assert len(results) > 0
    assert results[0]["doc_id"] == "similar-doc-001"
    assert results[0]["similarity_score"] > 0.8

    # Cleanup
    await test_db.documents.delete_one({"_id": "similar-doc-001"})


@pytest.mark.asyncio
async def test_similarity_threshold_filtering(test_db, sample_document_in_db):
    """Test that similarity threshold filters results."""
    controller = VectorSearchController(test_db)

    with patch('app.controllers.vector_search.get_embedding_adapter') as mock_adapter:
        mock_adapter_instance = AsyncMock()
        # Create a moderately similar embedding
        moderate_embedding = np.array(sample_document_in_db["embeddings"])
        moderate_embedding = moderate_embedding + np.random.randn(768) * 0.5
        moderate_embedding = moderate_embedding / np.linalg.norm(moderate_embedding)
        mock_adapter_instance.generate_embedding.return_value = moderate_embedding.tolist()
        mock_adapter.return_value = mock_adapter_instance

        # High threshold - may not find results
        results_high = await controller.search_documents(
            query="test",
            top_k=5,
            similarity_threshold=0.99,
        )

        # Low threshold - should find results
        results_low = await controller.search_documents(
            query="test",
            top_k=5,
            similarity_threshold=0.1,
        )

        # Low threshold should find more results
        assert len(results_low) >= len(results_high)

