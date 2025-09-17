from fastapi import APIRouter, Depends
from typing import Dict, Any

from src.middleware.auth_middleware import require_staff_or_admin, require_admin
from src.middleware.permissions import PermissionsValidator, Permissions
from src.api.services.request_service import RequestService
from src.api.services.user_service import UserService
from src.api.schemas.schemas import (
    StaffRegistration, StaffResponse, RequestStatusUpdate,
    RequestResponse, PaginatedResponse, RequestFilters,
    PaginationParams, StaffAssignment
)

router = APIRouter()


@router.post(
    "/register",
    response_model=StaffResponse,
    dependencies=[
        Depends(PermissionsValidator([Permissions.MANAGE_STAFF]))
    ]
)
async def register_staff(
    staff_data: StaffRegistration,
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    return await UserService.register_staff(staff_data)


@router.get(
    "/requests",
    response_model=PaginatedResponse,
    dependencies=[
        Depends(PermissionsValidator([Permissions.VIEW_REQUESTS]))
    ]
)
async def get_assigned_requests(
    pagination: PaginationParams = Depends(),
    filters: RequestFilters = Depends(),
    current_staff: Dict[str, Any] = Depends(require_staff_or_admin)
):
    staff_id = current_staff["user_id"]

    if filters.staff_id is None:
        filters.staff_id = staff_id

    return await RequestService.get_all_requests(pagination, filters)


@router.put(
    "/requests/{request_id}/status",
    response_model=RequestResponse,
    dependencies=[
        Depends(PermissionsValidator([Permissions.MANAGE_REQUESTS]))
    ]
)
async def update_request_status(
    request_id: int,
    data: RequestStatusUpdate,
    current_staff: Dict[str, Any] = Depends(require_staff_or_admin)
):
    staff_id = current_staff["user_id"]
    return await RequestService.update_request_status(request_id, staff_id, data)


@router.post(
    "/requests/{request_id}/assign",
    response_model=RequestResponse,
    dependencies=[
        Depends(PermissionsValidator([Permissions.ASSIGN_REQUESTS]))
    ]
)
async def assign_request_to_staff(
    request_id: int,
    assignment: StaffAssignment,
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    admin_id = current_admin["user_id"]
    return await RequestService.assign_staff_to_request(request_id, assignment, admin_id)