import logging
from typing import Any, List
from fastapi import Depends, HTTPException, status

from src.enums import UserRole
from src.middleware.auth_middleware import get_current_user

LOGGER = logging.getLogger(__name__)


class Permissions:
    VIEW_USERS = "view-users"
    MANAGE_USERS = "manage-users"
    DELETE_USERS = "delete-users"
    VIEW_STAFF = "view-staff"
    MANAGE_STAFF = "manage-staff"
    DELETE_STAFF = "delete-staff"

    VIEW_REQUESTS = "view-requests"
    VIEW_OWN_REQUESTS = "view-own-requests"
    CREATE_REQUEST = "create-request"
    UPDATE_OWN_REQUESTS = "update-own-requests"
    DELETE_OWN_REQUESTS = "delete-own-requests"

    MANAGE_REQUESTS = "manage-requests"
    ASSIGN_REQUESTS = "assign-requests"
    UPDATE_REQUEST_STATUS = "update-request-status"

    VIEW_STATISTICS = "view-statistics"
    EXPORT_DATA = "export-data"
    VIEW_LOGS = "view-logs"
    MANAGE_PROFILE = "manage-profile"


class RolePermissions:
    ROLE_PERMISSIONS = {
        UserRole.USER: [
            Permissions.VIEW_OWN_REQUESTS,
            Permissions.CREATE_REQUEST,
            Permissions.UPDATE_OWN_REQUESTS,
            Permissions.DELETE_OWN_REQUESTS,
            Permissions.MANAGE_PROFILE
        ],
        UserRole.STAFF: [
            Permissions.VIEW_REQUESTS,
            Permissions.MANAGE_REQUESTS,
            Permissions.UPDATE_REQUEST_STATUS,
            Permissions.VIEW_OWN_REQUESTS,
            Permissions.MANAGE_PROFILE
        ],
        UserRole.ADMIN: [
            Permissions.VIEW_USERS,
            Permissions.MANAGE_USERS,
            Permissions.DELETE_USERS,
            Permissions.VIEW_STAFF,
            Permissions.MANAGE_STAFF,
            Permissions.DELETE_STAFF,
            Permissions.VIEW_REQUESTS,
            Permissions.VIEW_OWN_REQUESTS,
            Permissions.CREATE_REQUEST,
            Permissions.UPDATE_OWN_REQUESTS,
            Permissions.DELETE_OWN_REQUESTS,
            Permissions.MANAGE_REQUESTS,
            Permissions.ASSIGN_REQUESTS,
            Permissions.UPDATE_REQUEST_STATUS,
            Permissions.VIEW_STATISTICS,
            Permissions.EXPORT_DATA,
            Permissions.VIEW_LOGS,
            Permissions.MANAGE_PROFILE
        ]
    }

    @classmethod
    def get_role_permissions(cls, role: UserRole) -> List[str]:
        return cls.ROLE_PERMISSIONS.get(role, [])

    @classmethod
    def has_permission(cls, role: UserRole, permission: str) -> bool:
        return permission in cls.get_role_permissions(role)


class PermissionsValidator:
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions

    def __call__(self, current_user: dict[str, Any] = Depends(get_current_user)) -> None:
        user_role = UserRole(current_user["role"])
        user_permissions = RolePermissions.get_role_permissions(user_role)

        missing_permissions = set(self.required_permissions) - set(user_permissions)

        if missing_permissions:
            LOGGER.warning(
                f"User {current_user.get('user_id')} missing permissions: {missing_permissions}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        return None


class ResourceOwnerValidator:
    def __init__(self, resource_id_field: str = "user_id"):
        self.resource_id_field = resource_id_field

    def __call__(
            self,
            resource_owner_id: int,
            current_user: dict[str, Any] = Depends(get_current_user)
    ) -> None:
        user_role = UserRole(current_user["role"])
        user_id = current_user["user_id"]

        if user_role in [UserRole.ADMIN, UserRole.STAFF]:
            return None

        if user_role == UserRole.USER and user_id == resource_owner_id:
            return None

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this resource"
        )