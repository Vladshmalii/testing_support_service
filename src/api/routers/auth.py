from fastapi import APIRouter, HTTPException, Depends, Request, status
from typing import Dict, Any

from src.middleware.auth_middleware import get_current_user, verify_user_context
from src.middleware.permissions import PermissionsValidator, Permissions, RolePermissions
from src.api.auth.jwt_handler import JWTHandler
from src.api.services import UserService
from src.enums import UserRole
from src.api.schemas.schemas import (
    UserRegistration, UserLogin, TokenResponse,
    UserResponse, UserProfileUpdate, PasswordChange
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegistration, request: Request):
    ip_address = request.client.host if request.client else None
    return await UserService.register_user(user_data, ip_address)


@router.post("/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin, request: Request):
    ip_address = request.client.host if request.client else None
    return await UserService.authenticate_user(login_data, ip_address)


@router.get(
    "/profile",
    dependencies=[Depends(PermissionsValidator([Permissions.MANAGE_PROFILE]))]
)
async def get_profile(current_user: Dict[str, Any] = Depends(verify_user_context)):
    return await UserService.get_user_profile(current_user["user_id"])


@router.put(
    "/profile",
    response_model=UserResponse,
    dependencies=[Depends(PermissionsValidator([Permissions.MANAGE_PROFILE]))]
)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: Dict[str, Any] = Depends(verify_user_context)
):
    return await UserService.update_user_profile(current_user["user_id"], profile_data)


@router.post(
    "/change-password",
    dependencies=[Depends(PermissionsValidator([Permissions.MANAGE_PROFILE]))]
)
async def change_password(
    password_data: PasswordChange,
    current_user: Dict[str, Any] = Depends(verify_user_context)
):
    return await UserService.change_password(current_user["user_id"], password_data)


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    try:
        refresh_payload = JWTHandler.verify_refresh_token(refresh_token)
        user_id = refresh_payload["user_id"]

        user_profile = await UserService.get_user_profile(user_id)
        user_role = UserRole(user_profile.role)
        permissions = RolePermissions.get_role_permissions(user_role)

        token_data = JWTHandler.create_token_pair(
            user_id, user_profile.email, user_role, permissions
        )

        return {
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "token_type": "bearer",
            "expires_in": token_data["expires_in"]
        }

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/verify-token")
async def verify_token(current_user: Dict[str, Any] = Depends(verify_user_context)):
    return {
        "valid": True,
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "role": current_user["role"],
        "permissions": current_user.get("permissions", [])
    }