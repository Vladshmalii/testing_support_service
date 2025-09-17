from typing import Optional, Union, Dict
from fastapi import HTTPException, status
from tortoise.exceptions import IntegrityError

from src.api.auth.password_manager import PasswordManager
from src.middleware.permissions import RolePermissions
from src.api.auth.jwt_handler import JWTHandler
from src.models.models import User
from src.enums import UserRole
from src.api.schemas.schemas import (
    UserRegistration, AdminRegistration, StaffRegistration,
    UserLogin, UserResponse, AdminResponse, StaffResponse,
    TokenResponse, UserProfileUpdate, PasswordChange
)


class UserService:

    @staticmethod
    async def register_user(data: UserRegistration, ip_address: Optional[str] = None) -> UserResponse:
        is_strong, password_errors = PasswordManager.is_password_strong(data.password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password validation failed: {', '.join(password_errors)}"
            )

        try:
            hashed_password = PasswordManager.hash_password(data.password)
            birth_date = data.birth_date if data.birth_date else None

            user = await User.create(
                email=data.email,
                password_hash=hashed_password,
                role=UserRole.USER,
                inn=data.inn,
                phone=data.phone,
                first_name=data.first_name,
                last_name=data.last_name,
                birth_date=birth_date,
                father_name=data.father_name
            )

            return UserResponse.model_validate(user)

        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    @staticmethod
    async def register_admin(data: AdminRegistration, ip_address: Optional[str] = None) -> AdminResponse:
        is_strong, password_errors = PasswordManager.is_password_strong(data.password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password validation failed: {', '.join(password_errors)}"
            )

        try:
            hashed_password = PasswordManager.hash_password(data.password)

            admin = await User.create(
                email=data.email,
                password_hash=hashed_password,
                role=UserRole.ADMIN
            )

            return AdminResponse.model_validate(admin)

        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    @staticmethod
    async def register_staff(data: StaffRegistration, ip_address: Optional[str] = None) -> StaffResponse:
        is_strong, password_errors = PasswordManager.is_password_strong(data.password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password validation failed: {', '.join(password_errors)}"
            )

        try:
            hashed_password = PasswordManager.hash_password(data.password)

            staff = await User.create(
                email=data.email,
                password_hash=hashed_password,
                role=UserRole.STAFF
            )

            return StaffResponse.model_validate(staff)

        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    @staticmethod
    async def authenticate_user(data: UserLogin, ip_address: Optional[str] = None) -> TokenResponse:
        user = await User.filter(email=data.email).first()

        if not user or not PasswordManager.verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        permissions = RolePermissions.get_role_permissions(user.role)

        token_data = JWTHandler.create_token_pair(
            user.id,
            user.email,
            user.role,
            permissions
        )

        return TokenResponse(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            expires_in=token_data["expires_in"],
            user_id=user.id,
            role=user.role,
            permissions=permissions
        )

    @staticmethod
    async def get_user_profile(user_id: int) -> Union[UserResponse, AdminResponse, StaffResponse]:
        user = await User.filter(id=user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.role == UserRole.ADMIN:
            return AdminResponse.model_validate(user)
        elif user.role == UserRole.STAFF:
            return StaffResponse.model_validate(user)
        else:
            return UserResponse.model_validate(user)

    @staticmethod
    async def update_user_profile(user_id: int, data: UserProfileUpdate) -> UserResponse:
        user = await User.filter(id=user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            await User.filter(id=user_id).update(**update_data)
            user = await User.filter(id=user_id).first()

        return UserResponse.model_validate(user)

    @staticmethod
    async def change_password(user_id: int, data: PasswordChange) -> Dict[str, str]:
        user = await User.filter(id=user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not PasswordManager.verify_password(data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        is_strong, password_errors = PasswordManager.is_password_strong(data.new_password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"New password validation failed: {', '.join(password_errors)}"
            )

        if data.current_password == data.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )

        new_password_hash = PasswordManager.hash_password(data.new_password)
        await User.filter(id=user_id).update(password_hash=new_password_hash)

        return {"message": "Password changed successfully"}

    @staticmethod
    async def verify_user_permissions(user_id: int) -> Dict:
        user = await User.filter(id=user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        permissions = RolePermissions.get_role_permissions(user.role)

        return {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
            "permissions": permissions
        }