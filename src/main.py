import logging
from typing import Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise

from src.api.routers import admin, auth, logs, staff, user_request
from src.core.config import settings, tortoise_config
from src.core.database import db_manager
from src.core.dependencies import get_database_manager
from src.middleware import LoggingMiddleware, RequestActionMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Support System API",
        version="1.0.0",
        description="Modern support system with tickets and knowledge base",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    _setup_event_handlers(app)
    _setup_middleware(app)
    _setup_routers(app)
    _setup_database(app)
    _setup_service_endpoints(app)

    logger.info("Application successfully configured")
    return app


def _setup_event_handlers(app: FastAPI) -> None:
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting application...")
        await db_manager.init_mongo()
        logger.info("MongoDB connected")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down application...")
        await db_manager.close_mongo()
        logger.info("MongoDB disconnected")


def _setup_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestActionMiddleware)
    app.add_middleware(LoggingMiddleware)

    logger.info("Middleware configured")


def _setup_routers(app: FastAPI) -> None:
    routers_config = [
        (auth.router, "/auth", ["Authentication"]),
        (staff.router, "/staff", ["Staff"]),
        (user_request.router, "/user_request", ["Requests"]),
        (admin.router, "/admin", ["Administration"]),
        (logs.router, "/admin/logs", ["Logs"]),
    ]

    for router, prefix, tags in routers_config:
        app.include_router(router, prefix=prefix, tags=tags)

    logger.info("API routes configured")


def _setup_database(app: FastAPI) -> None:
    register_tortoise(
        app,
        db_url=settings.database_url,
        modules={"models": ["src.models", "aerich.models"]},
        generate_schemas=False,
        add_exception_handlers=True
    )

    logger.info("PostgreSQL connected via Tortoise ORM")


def _setup_service_endpoints(app: FastAPI) -> None:
    @app.get("/health", summary="System health check", tags=["System"])
    async def health_check(
        db: db_manager.__class__ = Depends(get_database_manager)
    ) -> Dict[str, Any]:
        health_status = {
            "status": "healthy",
            "components": {
                "api": "operational",
                "postgresql": "unknown",
                "mongodb": "unknown"
            }
        }

        postgres_healthy = await db.is_postgres_healthy()
        mongo_healthy = await db.is_mongo_healthy()

        health_status["components"]["postgresql"] = "connected" if postgres_healthy else "error"
        health_status["components"]["mongodb"] = "connected" if mongo_healthy else "disconnected"

        if not postgres_healthy or not mongo_healthy:
            if not postgres_healthy and not mongo_healthy:
                health_status["status"] = "unhealthy"
            else:
                health_status["status"] = "degraded"

        return health_status


app = create_app()

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting in development mode")
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )