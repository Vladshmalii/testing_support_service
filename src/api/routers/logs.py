from fastapi import APIRouter, Depends, Query
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from src.middleware.permissions import PermissionsValidator, Permissions
from src.core.database import DatabaseManager
from src.core.dependencies import get_database_manager
from src.middleware.auth_middleware import require_admin

router = APIRouter()


@router.get(
    "/api-logs",
    dependencies=[Depends(PermissionsValidator([Permissions.VIEW_LOGS]))]
)
async def get_api_logs(
    current_user: Dict[str, Any] = Depends(require_admin),
    db: DatabaseManager = Depends(get_database_manager),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    method: Optional[str] = Query(None),
    status_code: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    hours_ago: int = Query(24, ge=1, le=168)
):
    since = datetime.utcnow() - timedelta(hours=hours_ago)
    filters = {"timestamp": {"$gte": since}}

    if method:
        filters["method"] = method
    if status_code:
        filters["status_code"] = status_code
    if user_id:
        filters["user_info.user_id"] = user_id

    return await db.get_mongo_logs(
        collection="app_logs",
        filters=filters,
        page=page,
        size=size
    )


@router.get(
    "/request-actions",
    dependencies=[Depends(PermissionsValidator([Permissions.VIEW_LOGS]))]
)
async def get_request_action_logs(
    current_user: Dict[str, Any] = Depends(require_admin),
    db: DatabaseManager = Depends(get_database_manager),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    request_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    hours_ago: int = Query(24, ge=1, le=168)
):
    since = datetime.utcnow() - timedelta(hours=hours_ago)
    filters = {"timestamp": {"$gte": since}}

    if request_id:
        filters["request_id"] = request_id
    if user_id:
        filters["user_id"] = user_id
    if action:
        filters["action"] = action

    return await db.get_mongo_logs(
        collection="request_actions",
        filters=filters,
        page=page,
        size=size
    )


@router.get(
    "/stats",
    dependencies=[Depends(PermissionsValidator([Permissions.VIEW_LOGS, Permissions.VIEW_STATISTICS]))]
)
async def get_logging_stats(
    current_user: Dict[str, Any] = Depends(require_admin),
    db: DatabaseManager = Depends(get_database_manager),
    hours_ago: int = Query(24, ge=1, le=168)
):
    since = datetime.utcnow() - timedelta(hours=hours_ago)

    api_logs_count = await db.count_mongo_logs("app_logs", {"timestamp": {"$gte": since}})
    action_logs_count = await db.count_mongo_logs("request_actions", {"timestamp": {"$gte": since}})

    return {
        "period_hours": hours_ago,
        "api_requests": api_logs_count,
        "request_actions": action_logs_count,
        "total_logs": api_logs_count + action_logs_count
    }