from fastapi import APIRouter, Depends
from typing import Dict, Any

from src.middleware.permissions import PermissionsValidator, Permissions
from src.middleware.auth_middleware import require_user_access
from src.api.services.request_service import RequestService
from src.enums import UserRole
from src.api.schemas.schemas import (
    RequestCreate, RequestUpdate, RequestResponse,
    PaginatedResponse, RequestFilters, PaginationParams
)

router = APIRouter()


@router.post(
    "/",
    response_model=RequestResponse,
    dependencies=[Depends(PermissionsValidator([Permissions.CREATE_REQUEST]))]
)
async def create_request(
    data: RequestCreate,
    current_user: Dict[str, Any] = Depends(require_user_access)
):
    return await RequestService.create_request(current_user["user_id"], data)


@router.get(
    "/my",
    response_model=PaginatedResponse,
    dependencies=[Depends(PermissionsValidator([Permissions.VIEW_OWN_REQUESTS]))]
)
async def get_my_requests(
    pagination: PaginationParams = Depends(),
    filters: RequestFilters = Depends(),
    current_user: Dict[str, Any] = Depends(require_user_access)
):
    return await RequestService.get_user_requests(current_user["user_id"], pagination, filters)


@router.get(
    "/{request_id}",
    response_model=RequestResponse,
    dependencies=[Depends(PermissionsValidator([Permissions.VIEW_OWN_REQUESTS]))]
)
async def get_request_by_id(
    request_id: int,
    current_user: Dict[str, Any] = Depends(require_user_access)
):
    user_role = UserRole(current_user["role"])
    return await RequestService.get_request_by_id(request_id, current_user["user_id"], user_role)


@router.put(
    "/{request_id}",
    response_model=RequestResponse,
    dependencies=[Depends(PermissionsValidator([Permissions.UPDATE_OWN_REQUESTS]))]
)
async def update_request(
    request_id: int,
    data: RequestUpdate,
    current_user: Dict[str, Any] = Depends(require_user_access)
):
    return await RequestService.update_request(request_id, current_user["user_id"], data)


@router.delete(
    "/{request_id}",
    dependencies=[Depends(PermissionsValidator([Permissions.DELETE_OWN_REQUESTS]))]
)
async def delete_request(
    request_id: int,
    current_user: Dict[str, Any] = Depends(require_user_access)
):
    return await RequestService.delete_request(request_id, current_user["user_id"])