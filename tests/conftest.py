"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.main import app
from app.config import get_settings

settings = get_settings()


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_client() -> AsyncGenerator:
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_db():
    """Create test database connection."""
    # Use a separate test database
    test_db_name = f"{settings.mongo_db_name}_test"

    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client[test_db_name]

    yield db

    # Cleanup: drop test database
    await client.drop_database(test_db_name)
    client.close()


@pytest.fixture
def sample_text_document():
    """Sample text document for testing."""
    return {
        "text": "This is a sample compliance document about data retention policies. "
                "Personal data must be retained for no longer than necessary. "
                "GDPR Article 5(1)(e) requires storage limitation.",
        "metadata": {
            "source": "test",
            "document_type": "policy",
            "version": "1.0"
        }
    }


@pytest.fixture
def sample_qa_request():
    """Sample Q&A request for testing."""
    return {
        "query": "What are the data retention requirements?",
        "scope": "all",
        "top_k": 5,
        "include_sources": True
    }


@pytest.fixture
def mock_embedding():
    """Mock embedding vector for testing."""
    import numpy as np
    np.random.seed(42)
    embedding = np.random.randn(768)
    embedding = embedding / np.linalg.norm(embedding)
    return embedding.tolist()


@pytest_asyncio.fixture
async def sample_document_in_db(test_db, mock_embedding):
    """Insert a sample document in test database."""
    from datetime import datetime

    doc = {
        "_id": "test-doc-001",
        "filename": "test_policy.txt",
        "mime_type": "text/plain",
        "storage_path": "",
        "text_content": "Sample compliance policy about GDPR data retention requirements.",
        "metadata": {"source": "test"},
        "embeddings": mock_embedding,
        "image_embeddings": None,
        "extracted_images": [],
        "sensitive_flag": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    await test_db.documents.insert_one(doc)
    yield doc
    await test_db.documents.delete_one({"_id": "test-doc-001"})

