from src.core.database import db_manager, DatabaseManager


async def get_database_manager() -> DatabaseManager:
    return db_manager