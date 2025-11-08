"""Tests for Q&A functionality."""

import pytest
from unittest.mock import AsyncMock, patch

from app.controllers.qa import QAController
from app.models.qa_response import QAResponse


@pytest.mark.asyncio
async def test_answer_query_with_documents(test_db, sample_document_in_db, sample_qa_request):
    """Test Q&A with available documents."""
    controller = QAController(test_db)

    # Mock model adapter
    with patch('app.controllers.qa.get_model_adapter') as mock_adapter:
        mock_adapter_instance = AsyncMock()
        mock_adapter_instance.generate_answer.return_value = {
            "answer": "Personal data must be retained for no longer than necessary according to GDPR Article 5(1)(e).",
            "confidence": 0.85
        }
        mock_adapter_instance.get_model_id.return_value = "test_model_v1"
        mock_adapter.return_value = mock_adapter_instance

        # Mock embedding adapter for vector search
        with patch('app.controllers.vector_search.get_embedding_adapter') as mock_emb_adapter:
            mock_emb_instance = AsyncMock()
            # Return same embedding as document for high similarity
            mock_emb_instance.generate_embedding.return_value = sample_document_in_db["embeddings"]
            mock_emb_adapter.return_value = mock_emb_instance

            response = await controller.answer_query(
                query=sample_qa_request["query"],
                top_k=sample_qa_request["top_k"],
            )

            assert isinstance(response, QAResponse)
            assert response.answer is not None
            assert len(response.answer) > 0
            assert 0.0 <= response.confidence <= 1.0
            assert response.query == sample_qa_request["query"]
            assert response.model_used == "test_model_v1"


@pytest.mark.asyncio
async def test_answer_query_no_documents(test_db, sample_qa_request):
    """Test Q&A when no relevant documents found."""
    controller = QAController(test_db)

    with patch('app.controllers.qa.get_model_adapter') as mock_adapter:
        mock_adapter_instance = AsyncMock()
        mock_adapter_instance.get_model_id.return_value = "test_model_v1"
        mock_adapter.return_value = mock_adapter_instance

        with patch('app.controllers.vector_search.get_embedding_adapter') as mock_emb_adapter:
            mock_emb_instance = AsyncMock()
            mock_emb_instance.generate_embedding.return_value = [0.1] * 768
            mock_emb_adapter.return_value = mock_emb_instance

            response = await controller.answer_query(
                query="What is the airspeed velocity of an unladen swallow?",
                top_k=5,
            )

            assert response.confidence == 0.0
            assert "couldn't find" in response.answer.lower() or "no relevant" in response.answer.lower()


@pytest.mark.asyncio
async def test_citations_included_in_response(test_db, sample_document_in_db):
    """Test that citations are included in Q&A response."""
    controller = QAController(test_db)

    with patch('app.controllers.qa.get_model_adapter') as mock_adapter:
        mock_adapter_instance = AsyncMock()
        mock_adapter_instance.generate_answer.return_value = {
            "answer": "Test answer",
            "confidence": 0.9
        }
        mock_adapter_instance.get_model_id.return_value = "test_model_v1"
        mock_adapter.return_value = mock_adapter_instance

        with patch('app.controllers.vector_search.get_embedding_adapter') as mock_emb_adapter:
            mock_emb_instance = AsyncMock()
            mock_emb_instance.generate_embedding.return_value = sample_document_in_db["embeddings"]
            mock_emb_adapter.return_value = mock_emb_instance

            response = await controller.answer_query(
                query="What are the requirements?",
                top_k=5,
                include_sources=True,
            )

            assert len(response.citations) > 0
            citation = response.citations[0]
            assert citation.doc_id == sample_document_in_db["_id"]
            assert citation.filename == sample_document_in_db["filename"]
            assert citation.excerpt is not None
            assert 0.0 <= citation.similarity_score <= 1.0


@pytest.mark.asyncio
async def test_audit_log_created_for_qa(test_db, sample_document_in_db):
    """Test that audit logs are created for Q&A queries."""
    controller = QAController(test_db)

    query = "Test query for audit"

    with patch('app.controllers.qa.get_model_adapter') as mock_adapter:
        mock_adapter_instance = AsyncMock()
        mock_adapter_instance.generate_answer.return_value = {
            "answer": "Test answer",
            "confidence": 0.8
        }
        mock_adapter_instance.get_model_id.return_value = "test_model_v1"
        mock_adapter.return_value = mock_adapter_instance

        with patch('app.controllers.vector_search.get_embedding_adapter') as mock_emb_adapter:
            mock_emb_instance = AsyncMock()
            mock_emb_instance.generate_embedding.return_value = sample_document_in_db["embeddings"]
            mock_emb_adapter.return_value = mock_emb_instance

            await controller.answer_query(
                query=query,
                user_id="test_user_123",
            )

            # Verify audit log
            audit_log = await test_db.audit_logs.find_one({"query": query})
            assert audit_log is not None
            assert audit_log["event_type"] == "qa_query"
            assert audit_log["user_id"] == "test_user_123"
            assert audit_log["confidence"] == 0.8


@pytest.mark.asyncio
async def test_query_history_retrieval(test_db):
    """Test retrieving query history."""
    controller = QAController(test_db)

    # Insert test audit logs
    from datetime import datetime
    audit_entries = [
        {
            "event_type": "qa_query",
            "timestamp": datetime.utcnow(),
            "user_id": "test_user",
            "query": f"Query {i}",
            "answer": f"Answer {i}",
            "confidence": 0.8,
            "num_citations": 2,
        }
        for i in range(5)
    ]

    await test_db.audit_logs.insert_many(audit_entries)

    # Get history
    history = await controller.get_query_history(user_id="test_user", limit=10)

    assert len(history) == 5
    assert all("query" in entry for entry in history)
    assert all("confidence" in entry for entry in history)


@pytest.mark.asyncio
async def test_top_k_parameter(test_db, sample_document_in_db):
    """Test that top_k parameter limits results."""
    controller = QAController(test_db)

    with patch('app.controllers.qa.get_model_adapter') as mock_adapter:
        mock_adapter_instance = AsyncMock()
        mock_adapter_instance.generate_answer.return_value = {
            "answer": "Test answer",
            "confidence": 0.9
        }
        mock_adapter_instance.get_model_id.return_value = "test_model_v1"
        mock_adapter.return_value = mock_adapter_instance

        with patch('app.controllers.vector_search.get_embedding_adapter') as mock_emb_adapter:
            mock_emb_instance = AsyncMock()
            mock_emb_instance.generate_embedding.return_value = sample_document_in_db["embeddings"]
            mock_emb_adapter.return_value = mock_emb_instance

            response = await controller.answer_query(
                query="Test query",
                top_k=2,
            )

            # Should have at most 2 citations (limited by top_k)
            assert len(response.citations) <= 2


@pytest.mark.asyncio
async def test_processing_time_recorded(test_db, sample_document_in_db):
    """Test that processing time is recorded."""
    controller = QAController(test_db)

    with patch('app.controllers.qa.get_model_adapter') as mock_adapter:
        mock_adapter_instance = AsyncMock()
        mock_adapter_instance.generate_answer.return_value = {
            "answer": "Test answer",
            "confidence": 0.9
        }
        mock_adapter_instance.get_model_id.return_value = "test_model_v1"
        mock_adapter.return_value = mock_adapter_instance

        with patch('app.controllers.vector_search.get_embedding_adapter') as mock_emb_adapter:
            mock_emb_instance = AsyncMock()
            mock_emb_instance.generate_embedding.return_value = sample_document_in_db["embeddings"]
            mock_emb_adapter.return_value = mock_emb_instance

            response = await controller.answer_query(query="Test query")

            assert response.processing_time_ms is not None
            assert response.processing_time_ms > 0

