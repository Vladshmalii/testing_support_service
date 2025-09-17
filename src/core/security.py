from typing import List, Dict, Any

from src.enums import UserRole
from src.middleware.permissions import RolePermissions

class SecurityConfig:
    PASSWORD_MIN_LENGTH = 8
    TOKEN_BLACKLIST_ENABLED = True
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15


class PermissionHierarchy:

    HIERARCHY = {
        UserRole.USER: [],
        UserRole.STAFF: [UserRole.USER],
        UserRole.ADMIN: [UserRole.USER, UserRole.STAFF]
    }

    @classmethod
    def get_inherited_permissions(cls, role: UserRole) -> List[str]:
        permissions = set(RolePermissions.get_role_permissions(role))

        for inherited_role in cls.HIERARCHY.get(role, []):
            permissions.update(RolePermissions.get_role_permissions(inherited_role))

        return list(permissions)