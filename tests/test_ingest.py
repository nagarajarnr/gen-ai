"""Tests for document ingestion."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.controllers.ingest import IngestController


@pytest.mark.asyncio
async def test_ingest_text_document(test_db, sample_text_document, mock_embedding):
    """Test text document ingestion."""
    controller = IngestController(test_db)

    # Mock embedding adapter
    with patch('app.controllers.ingest.get_embedding_adapter') as mock_adapter:
        mock_adapter_instance = AsyncMock()
        mock_adapter_instance.generate_embedding.return_value = mock_embedding
        mock_adapter.return_value = mock_adapter_instance

        # Ingest document
        doc_id = await controller.ingest_text(
            text=sample_text_document["text"],
            metadata=sample_text_document["metadata"]
        )

        assert doc_id is not None
        assert isinstance(doc_id, str)

        # Verify document in database
        doc = await test_db.documents.find_one({"_id": doc_id})
        assert doc is not None
        assert doc["text_content"] == sample_text_document["text"]
        assert doc["metadata"] == sample_text_document["metadata"]
        assert doc["embeddings"] == mock_embedding
        assert "created_at" in doc


@pytest.mark.asyncio
async def test_ingest_text_with_sensitive_content(test_db, mock_embedding):
    """Test ingestion of text with PII."""
    controller = IngestController(test_db)

    # Text with PII
    text_with_pii = "Contact John Doe at john.doe@example.com or call 555-123-4567."

    with patch('app.controllers.ingest.get_embedding_adapter') as mock_adapter:
        mock_adapter_instance = AsyncMock()
        mock_adapter_instance.generate_embedding.return_value = mock_embedding
        mock_adapter.return_value = mock_adapter_instance

        doc_id = await controller.ingest_text(text=text_with_pii)

        # Verify sensitive flag
        doc = await test_db.documents.find_one({"_id": doc_id})
        assert doc["sensitive_flag"] is True
        assert "email" in doc["detected_pii_patterns"]
        assert "phone" in doc["detected_pii_patterns"]


@pytest.mark.asyncio
async def test_ingest_creates_embeddings(test_db, sample_text_document):
    """Test that embeddings are generated during ingestion."""
    controller = IngestController(test_db)

    with patch('app.controllers.ingest.get_embedding_adapter') as mock_adapter:
        mock_adapter_instance = AsyncMock()
        mock_adapter_instance.generate_embedding.return_value = [0.1] * 768
        mock_adapter.return_value = mock_adapter_instance

        doc_id = await controller.ingest_text(
            text=sample_text_document["text"],
            metadata=sample_text_document["metadata"]
        )

        # Verify embedding was generated
        mock_adapter_instance.generate_embedding.assert_called_once()

        # Verify embedding stored
        doc = await test_db.documents.find_one({"_id": doc_id})
        assert doc["embeddings"] is not None
        assert len(doc["embeddings"]) == 768


@pytest.mark.asyncio
async def test_audit_log_created_on_ingestion(test_db, sample_text_document, mock_embedding):
    """Test that audit logs are created during ingestion."""
    controller = IngestController(test_db)

    with patch('app.controllers.ingest.get_embedding_adapter') as mock_adapter:
        mock_adapter_instance = AsyncMock()
        mock_adapter_instance.generate_embedding.return_value = mock_embedding
        mock_adapter.return_value = mock_adapter_instance

        doc_id = await controller.ingest_text(
            text=sample_text_document["text"],
            metadata=sample_text_document["metadata"]
        )

        # Verify audit log entry
        audit_log = await test_db.audit_logs.find_one({"details.doc_id": doc_id})
        assert audit_log is not None
        assert audit_log["event_type"] == "document_ingestion"
        assert audit_log["details"]["type"] == "text"


@pytest.mark.asyncio
async def test_ingest_empty_text_fails(test_db):
    """Test that empty text ingestion fails."""
    controller = IngestController(test_db)

    with pytest.raises(Exception):
        await controller.ingest_text(text="")


@pytest.mark.asyncio
async def test_metadata_stored_correctly(test_db, mock_embedding):
    """Test that metadata is stored correctly."""
    controller = IngestController(test_db)

    custom_metadata = {
        "department": "legal",
        "classification": "confidential",
        "version": "2.1",
        "tags": ["gdpr", "privacy"]
    }

    with patch('app.controllers.ingest.get_embedding_adapter') as mock_adapter:
        mock_adapter_instance = AsyncMock()
        mock_adapter_instance.generate_embedding.return_value = mock_embedding
        mock_adapter.return_value = mock_adapter_instance

        doc_id = await controller.ingest_text(
            text="Sample document text",
            metadata=custom_metadata
        )

        doc = await test_db.documents.find_one({"_id": doc_id})
        assert doc["metadata"] == custom_metadata
        assert doc["metadata"]["department"] == "legal"
        assert "gdpr" in doc["metadata"]["tags"]

