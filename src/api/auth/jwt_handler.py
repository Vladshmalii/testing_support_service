from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
import jwt

from src.enums import UserRole
from src.core.config import settings


class JWTHandler:

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "token_type": "access"
        })

        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    @staticmethod
    def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(days=7))

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "token_type": "refresh"
        })

        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    @staticmethod
    def create_user_token(user_id: int, email: str, role: UserRole, permissions: Optional[List[str]] = None) -> str:
        payload = {
            "user_id": user_id,
            "email": email,
            "role": role.value,
            "permissions": permissions or [],
            "type": "access"
        }
        return JWTHandler.create_access_token(payload)

    @staticmethod
    def create_token_pair(user_id: int, email: str, role: UserRole, permissions: Optional[List[str]] = None) -> Dict[
        str, Any]:
        base_payload = {
            "user_id": user_id,
            "email": email,
            "role": role.value,
            "permissions": permissions or []
        }

        access_token = JWTHandler.create_access_token(base_payload)
        refresh_token = JWTHandler.create_refresh_token({"user_id": user_id, "email": email})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60
        }

    @staticmethod
    def get_token_payload(token: str) -> Dict[str, Any]:
        payload = JWTHandler.decode_token(token)

        if payload.get("token_type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        required_fields = ["user_id", "email", "role"]
        missing_fields = [field for field in required_fields if field not in payload]

        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token payload: missing {', '.join(missing_fields)}"
            )

        try:
            UserRole(payload["role"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid role in token"
            )

        return payload

    @staticmethod
    def verify_refresh_token(token: str) -> Dict[str, Any]:
        payload = JWTHandler.decode_token(token)

        if payload.get("token_type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        return payload

    @staticmethod
    def verify_token_permissions(token: str, required_permissions: List[str]) -> Dict[str, Any]:
        payload = JWTHandler.get_token_payload(token)
        token_permissions = set(payload.get("permissions", []))
        required_permissions_set = set(required_permissions)

        if not required_permissions_set.issubset(token_permissions):
            missing_permissions = required_permissions_set - token_permissions
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing_permissions)}"
            )

        return payload

    @staticmethod
    def verify_token_role(token: str, allowed_roles: List[UserRole]) -> Dict[str, Any]:
        payload = JWTHandler.get_token_payload(token)
        user_role = UserRole(payload["role"])

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions"
            )

        return payload