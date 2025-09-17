import logging

from tortoise import Tortoise, connections
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

from src.core.config import settings, tortoise_config

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self._mongo_client: Optional[AsyncIOMotorClient] = None
        self._mongo_db = None
        self._postgres_initialized = False

    async def init_postgres(self):
        if not self._postgres_initialized:
            await Tortoise.init(config=tortoise_config)
            await Tortoise.generate_schemas()
            self._postgres_initialized = True
            logger.info("PostgreSQL initialized successfully")

    async def close_postgres(self):
        if self._postgres_initialized:
            await Tortoise.close_connections()
            self._postgres_initialized = False
            logger.info("PostgreSQL closed successfully")

    async def init_mongo(self):
        if self._mongo_client is None:
            self._mongo_client = AsyncIOMotorClient(settings.mongodb_url)
            self._mongo_db = self._mongo_client[settings.mongodb_database]
            await self._mongo_db.command("ping")
            logger.info("MongoDB initialized successfully")

    async def close_mongo(self):
        if self._mongo_client:
            self._mongo_client.close()
            self._mongo_client = None
            self._mongo_db = None
            logger.info("MongoDB closed successfully")

    def get_mongo_db(self):
        return self._mongo_db

    async def is_postgres_healthy(self) -> bool:
        try:
            conn = connections.get("default")
            if conn is None:
                return False
            await conn.execute_query("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False

    async def is_mongo_healthy(self) -> bool:
        if self._mongo_db is None:
            return False
        try:
            result = await self._mongo_db.command("ping")
            return result.get("ok") == 1
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False

    async def log_to_mongo(self, collection: str, data: dict):
        if self._mongo_db is None:
            raise RuntimeError("MongoDB not initialized")

        try:
            result = await self._mongo_db[collection].insert_one(data)
            logger.info(f"Successfully inserted into {collection}, ID: {result.inserted_id}")
        except Exception as e:
            logger.error(f"Failed to insert into {collection}: {e}")
            raise

    async def get_mongo_logs(self, collection: str, filters: dict = None, page: int = 1, size: int = 50):
        if self._mongo_db is None:
            return {"items": [], "total": 0, "page": page, "size": size, "pages": 0}

        try:
            query = filters or {}
            skip = (page - 1) * size

            cursor = self._mongo_db[collection].find(query).sort("timestamp", -1).skip(skip).limit(size)

            logs = []
            async for doc in cursor:
                doc['_id'] = str(doc['_id'])
                logs.append(doc)

            total = await self._mongo_db[collection].count_documents(query)

            return {
                "items": logs,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            }
        except Exception as e:
            logger.error(f"Error getting logs from {collection}: {e}")
            return {"items": [], "total": 0, "page": page, "size": size, "pages": 0}

    async def count_mongo_logs(self, collection: str, filters: dict = None):
        if self._mongo_db is None:
            return 0

        try:
            query = filters or {}
            return await self._mongo_db[collection].count_documents(query)
        except Exception as e:
            logger.error(f"Error counting logs in {collection}: {e}")
            return 0


db_manager = DatabaseManager()