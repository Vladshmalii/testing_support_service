from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

from src.enums import UserRole, RequestStatus


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    role: UserRole
    permissions: Optional[List[str]] = []


class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    inn: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[datetime] = None
    father_name: Optional[str] = None


class AdminRegistration(BaseModel):
    email: EmailStr
    password: str


class StaffRegistration(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    role: UserRole
    inn: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[datetime] = None
    father_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminResponse(BaseModel):
    id: int
    email: str
    role: UserRole
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StaffResponse(BaseModel):
    id: int
    email: str
    role: UserRole
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    inn: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[datetime] = None
    father_name: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class RequestCreate(BaseModel):
    text: str


class RequestUpdate(BaseModel):
    text: Optional[str] = None


class RequestStatusUpdate(BaseModel):
    status: RequestStatus
    staff_comment: Optional[str] = None


class StaffAssignment(BaseModel):
    staff_id: int


class RequestResponse(BaseModel):
    id: int
    text: str
    status: RequestStatus
    staff_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    owner: UserResponse
    staff_member: Optional[StaffResponse] = None

    class Config:
        from_attributes = True


class RequestListResponse(BaseModel):
    id: int
    text: str
    status: RequestStatus
    created_at: datetime
    updated_at: datetime
    owner_email: str
    staff_member_email: Optional[str] = None

    class Config:
        from_attributes = True


class PaginationParams(BaseModel):
    page: int = 1
    size: int = 50


class RequestFilters(BaseModel):
    status: Optional[RequestStatus] = None
    staff_id: Optional[int] = None
    owner_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class PaginatedResponse(BaseModel):
    items: List[RequestListResponse]
    total: int
    page: int
    size: int
    pages: int


class StatsResponse(BaseModel):
    total_requests: int
    new_requests: int
    in_progress_requests: int
    completed_requests: int
    closed_requests: int
    total_users: int
    total_staff: int


class PermissionResponse(BaseModel):
    name: str
    description: Optional[str] = None


class RolePermissionsResponse(BaseModel):
    role: UserRole
    permissions: List[str]