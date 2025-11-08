"""MongoDB database connection and utilities."""

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class Database:
    """MongoDB database manager."""

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        """Connect to MongoDB."""
        try:
            logger.info(f"Connecting to MongoDB at {settings.mongo_uri}")
            self.client = AsyncIOMotorClient(settings.mongo_uri)

            # Test connection
            await self.client.admin.command("ping")

            self.db = self.client[settings.mongo_db_name]
            logger.info(f"Connected to MongoDB database: {settings.mongo_db_name}")

            # Create indexes
            await self._create_indexes()

        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def _create_indexes(self) -> None:
        """Create database indexes for performance."""
        if self.db is None:
            return

        # Documents collection indexes
        await self.db.documents.create_index("created_at")
        await self.db.documents.create_index("mime_type")
        await self.db.documents.create_index("metadata.source")

        # Audit logs collection indexes
        await self.db.audit_logs.create_index("timestamp")
        await self.db.audit_logs.create_index("query")
        await self.db.audit_logs.create_index("user_id")

        # Model registry collection indexes
        await self.db.model_registry.create_index("created_at")
        await self.db.model_registry.create_index("status")
        await self.db.model_registry.create_index("model_type")
        
        # Users collection indexes
        await self.db.users.create_index("username", unique=True)
        await self.db.users.create_index("email", unique=True)
        await self.db.users.create_index("phone", unique=True)
        await self.db.users.create_index("created_at")

        logger.info("Database indexes created successfully")

    def get_database(self) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if self.db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.db


# Global database instance
db_manager = Database()


async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance for dependency injection."""
    return db_manager.get_database()

