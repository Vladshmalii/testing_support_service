from typing import Optional
from fastapi import HTTPException, status
from tortoise.queryset import QuerySet
from datetime import datetime

from src.enums import UserRole, RequestStatus
from src.models.models import Request, User
from src.api.schemas.schemas import (
    RequestCreate, RequestUpdate, RequestResponse, RequestListResponse,
    RequestStatusUpdate, PaginatedResponse, RequestFilters,
    PaginationParams, StaffAssignment
)


class RequestService:

    @staticmethod
    async def create_request(user_id: int, data: RequestCreate) -> RequestResponse:
        request = await Request.create(
            owner_id=user_id,
            text=data.text,
            status=RequestStatus.NEW
        )

        request = await Request.get(id=request.id).prefetch_related("owner", "staff_member")
        return await RequestService._build_request_response(request)

    @staticmethod
    async def get_user_requests(
            user_id: int,
            pagination: PaginationParams,
            filters: Optional[RequestFilters] = None
    ) -> PaginatedResponse:
        query = Request.filter(owner_id=user_id)
        query = RequestService._apply_filters(query, filters)

        total = await query.count()

        requests = await query.offset(
            (pagination.page - 1) * pagination.size
        ).limit(pagination.size).prefetch_related("owner", "staff_member")

        items = [await RequestService._build_list_response(req) for req in requests]

        return PaginatedResponse(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=(total + pagination.size - 1) // pagination.size
        )

    @staticmethod
    async def get_all_requests(
            pagination: PaginationParams,
            filters: Optional[RequestFilters] = None
    ) -> PaginatedResponse:
        query = Request.all()
        query = RequestService._apply_filters(query, filters)

        total = await query.count()

        requests = await query.offset(
            (pagination.page - 1) * pagination.size
        ).limit(pagination.size).prefetch_related("owner", "staff_member")

        items = [await RequestService._build_list_response(req) for req in requests]

        return PaginatedResponse(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=(total + pagination.size - 1) // pagination.size
        )

    @staticmethod
    async def get_request_by_id(request_id: int, user_id: int, user_role: UserRole) -> RequestResponse:
        if user_role == UserRole.USER:
            request = await Request.get_or_none(id=request_id, owner_id=user_id).prefetch_related("owner", "staff_member")
        else:
            request = await Request.get_or_none(id=request_id).prefetch_related("owner", "staff_member")

        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )

        return await RequestService._build_request_response(request)

    @staticmethod
    async def update_request(request_id: int, user_id: int, data: RequestUpdate) -> RequestResponse:
        request = await Request.get_or_none(id=request_id, owner_id=user_id).prefetch_related("owner")

        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )

        if request.status != RequestStatus.NEW:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update request that is being processed"
            )

        update_data = data.model_dump(exclude_unset=True)

        if update_data:
            await Request.filter(id=request_id).update(**update_data)
            request = await Request.get(id=request_id).prefetch_related("owner", "staff_member")

        return await RequestService._build_request_response(request)

    @staticmethod
    async def update_request_status(request_id: int, staff_id: int, data: RequestStatusUpdate) -> RequestResponse:
        request = await Request.get_or_none(id=request_id).prefetch_related("owner", "staff_member")

        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )

        await Request.filter(id=request_id).update(
            status=data.status,
            staff_comment=data.staff_comment,
            staff_member_id=staff_id,
            updated_at=datetime.utcnow()
        )

        request = await Request.get(id=request_id).prefetch_related("owner", "staff_member")
        return await RequestService._build_request_response(request)

    @staticmethod
    async def assign_staff_to_request(request_id: int, assignment: StaffAssignment, admin_id: int) -> RequestResponse:
        request = await Request.get_or_none(id=request_id).prefetch_related("owner")

        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )

        staff = await User.get_or_none(id=assignment.staff_id, role=UserRole.STAFF)
        if not staff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found"
            )

        new_status = RequestStatus.IN_PROGRESS if request.status == RequestStatus.NEW else request.status

        await Request.filter(id=request_id).update(
            staff_member_id=assignment.staff_id,
            status=new_status,
            updated_at=datetime.utcnow()
        )

        request = await Request.get(id=request_id).prefetch_related("owner", "staff_member")
        return await RequestService._build_request_response(request)

    @staticmethod
    async def delete_request(request_id: int, user_id: int) -> dict:
        request = await Request.get_or_none(id=request_id, owner_id=user_id)

        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )

        if request.status not in [RequestStatus.NEW, RequestStatus.COMPLETED, RequestStatus.CLOSED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete request in progress"
            )

        await request.delete()
        return {"message": "Request deleted successfully"}

    @staticmethod
    def _apply_filters(query: QuerySet, filters: Optional[RequestFilters]) -> QuerySet:
        if not filters:
            return query.order_by("-created_at")

        if filters.status:
            query = query.filter(status=filters.status)

        if filters.staff_id:
            query = query.filter(staff_member_id=filters.staff_id)

        if filters.owner_id:
            query = query.filter(owner_id=filters.owner_id)

        if filters.date_from:
            query = query.filter(created_at__gte=filters.date_from)

        if filters.date_to:
            query = query.filter(created_at__lte=filters.date_to)

        return query.order_by("-created_at")

    @staticmethod
    async def _build_request_response(request: Request) -> RequestResponse:
        owner_data = {
            "id": request.owner.id,
            "email": request.owner.email,
            "role": request.owner.role,
            "inn": getattr(request.owner, 'inn', None),
            "phone": getattr(request.owner, 'phone', None),
            "first_name": getattr(request.owner, 'first_name', None),
            "last_name": getattr(request.owner, 'last_name', None),
            "birth_date": getattr(request.owner, 'birth_date', None),
            "father_name": getattr(request.owner, 'father_name', None),
            "created_at": request.owner.created_at,
            "updated_at": request.owner.updated_at
        }

        staff_data = None
        if request.staff_member:
            staff_data = {
                "id": request.staff_member.id,
                "email": request.staff_member.email,
                "role": request.staff_member.role,
                "created_at": request.staff_member.created_at,
                "updated_at": request.staff_member.updated_at
            }

        return RequestResponse(
            id=request.id,
            text=request.text,
            status=request.status,
            staff_comment=request.staff_comment,
            created_at=request.created_at,
            updated_at=request.updated_at,
            owner=owner_data,
            staff_member=staff_data
        )

    @staticmethod
    async def _build_list_response(request: Request) -> RequestListResponse:
        return RequestListResponse(
            id=request.id,
            text=request.text,
            status=request.status,
            created_at=request.created_at,
            updated_at=request.updated_at,
            owner_email=request.owner.email,
            staff_member_email=request.staff_member.email if request.staff_member else None
        )