from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Callable, Dict, Any

from src.api.auth.jwt_handler import JWTHandler
from src.enums import UserRole

security = HTTPBearer()


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    token = credentials.credentials
    payload = JWTHandler.get_token_payload(token)
    return payload


async def get_current_user_optional(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(
            HTTPBearer(auto_error=False)
        )
) -> Optional[Dict[str, Any]]:
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = JWTHandler.get_token_payload(token)
        return payload
    except HTTPException:
        return None


def require_roles(allowed_roles: List[UserRole]) -> Callable:
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = UserRole(current_user["role"])

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions"
            )

        return current_user

    return role_checker


async def require_admin(
        current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    user_role = UserRole(current_user["role"])

    if user_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user


async def require_staff_or_admin(
        current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    user_role = UserRole(current_user["role"])

    if user_role not in [UserRole.STAFF, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff or admin access required"
        )

    return current_user


async def require_user_access(
        current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    user_role = UserRole(current_user["role"])

    if user_role not in [UserRole.USER, UserRole.STAFF, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User access required"
        )

    return current_user


def require_owner_or_elevated_access(resource_owner_id: int):
    def owner_checker(
            current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        user_role = UserRole(current_user["role"])
        user_id = current_user["user_id"]

        if user_role in [UserRole.STAFF, UserRole.ADMIN]:
            return current_user

        if user_role == UserRole.USER and user_id == resource_owner_id:
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this resource"
        )

    return owner_checker


async def verify_user_context(
        current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    required_fields = ["user_id", "email", "role"]

    for field in required_fields:
        if field not in current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: missing {field}"
            )

    try:
        UserRole(current_user["role"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user role in token"
        )

    return current_user