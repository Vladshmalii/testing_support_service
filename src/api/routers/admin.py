from fastapi import APIRouter, Depends, status
from typing import Dict, Any

from src.middleware.permissions import PermissionsValidator, Permissions
from src.api.services.request_service import RequestService
from src.middleware.auth_middleware import require_admin
from src.api.services.admin_service import AdminService
from src.api.services.user_service import UserService
from src.api.services.csv_service import CSVService
from src.api.schemas.schemas import (
    AdminRegistration, AdminResponse, StatsResponse,
    PaginationParams, PaginatedResponse, RequestFilters
)

router = APIRouter()


@router.post("/register", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def register_admin(admin_data: AdminRegistration):
    return await UserService.register_admin(admin_data)


@router.get(
    "/statistics",
    response_model=StatsResponse,
    dependencies=[Depends(PermissionsValidator([Permissions.VIEW_STATISTICS]))]
)
async def get_statistics(current_admin: Dict[str, Any] = Depends(require_admin)):
    return await AdminService.get_statistics(current_admin["user_id"])


@router.get(
    "/users",
    dependencies=[Depends(PermissionsValidator([Permissions.VIEW_USERS]))]
)
async def get_all_users(
    pagination: PaginationParams = Depends(),
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    return await AdminService.get_all_users(current_admin["user_id"], pagination)


@router.get(
    "/staff",
    dependencies=[Depends(PermissionsValidator([Permissions.VIEW_STAFF]))]
)
async def get_all_staff(
    pagination: PaginationParams = Depends(),
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    return await AdminService.get_all_staff(current_admin["user_id"], pagination)


@router.delete(
    "/users/{user_id}",
    dependencies=[Depends(PermissionsValidator([Permissions.DELETE_USERS]))]
)
async def delete_user(
    user_id: int,
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    return await AdminService.delete_user(current_admin["user_id"], user_id)


@router.delete(
    "/staff/{staff_id}",
    dependencies=[Depends(PermissionsValidator([Permissions.DELETE_STAFF]))]
)
async def delete_staff(
    staff_id: int,
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    return await AdminService.delete_staff(current_admin["user_id"], staff_id)


@router.get(
    "/staff/workload",
    dependencies=[Depends(PermissionsValidator([Permissions.VIEW_STAFF, Permissions.VIEW_STATISTICS]))]
)
async def get_staff_workload(current_admin: Dict[str, Any] = Depends(require_admin)):
    return await AdminService.get_staff_workload(current_admin["user_id"])


@router.get(
    "/requests",
    response_model=PaginatedResponse,
    dependencies=[Depends(PermissionsValidator([Permissions.VIEW_REQUESTS]))]
)
async def get_all_requests(
    pagination: PaginationParams = Depends(),
    filters: RequestFilters = Depends(),
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    return await RequestService.get_all_requests(pagination, filters)


@router.get(
    "/requests/export",
    dependencies=[Depends(PermissionsValidator([Permissions.EXPORT_DATA]))]
)
async def export_requests_csv(
    filters: RequestFilters = Depends(),
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    return await CSVService.export_requests_csv(filters, current_admin["user_id"])