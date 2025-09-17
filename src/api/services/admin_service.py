from typing import List
from fastapi import HTTPException, status
from tortoise.functions import Count
from tortoise.expressions import Q

from src.models.models import User, Request
from src.api.schemas.schemas import StatsResponse, UserResponse, StaffResponse, PaginationParams
from src.enums import RequestStatus, UserRole


class AdminService:

    @staticmethod
    async def get_statistics(admin_id: int) -> StatsResponse:
        admin = await User.filter(id=admin_id, role=UserRole.ADMIN).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )

        total_requests = await Request.all().count()
        new_requests = await Request.filter(status=RequestStatus.NEW).count()
        in_progress_requests = await Request.filter(status=RequestStatus.IN_PROGRESS).count()
        completed_requests = await Request.filter(status=RequestStatus.COMPLETED).count()
        closed_requests = await Request.filter(status=RequestStatus.CLOSED).count()

        total_users = await User.filter(role=UserRole.USER).count()
        total_staff = await User.filter(role=UserRole.STAFF).count()

        return StatsResponse(
            total_requests=total_requests,
            new_requests=new_requests,
            in_progress_requests=in_progress_requests,
            completed_requests=completed_requests,
            closed_requests=closed_requests,
            total_users=total_users,
            total_staff=total_staff
        )

    @staticmethod
    async def get_all_users(admin_id: int, pagination: PaginationParams) -> dict:
        admin = await User.filter(id=admin_id, role=UserRole.ADMIN).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )

        total = await User.filter(role=UserRole.USER).count()
        users = await User.filter(role=UserRole.USER).offset(
            (pagination.page - 1) * pagination.size
        ).limit(pagination.size)

        user_responses = [UserResponse.model_validate(user) for user in users]

        return {
            "items": user_responses,
            "total": total,
            "page": pagination.page,
            "size": pagination.size,
            "pages": (total + pagination.size - 1) // pagination.size
        }

    @staticmethod
    async def get_all_staff(admin_id: int, pagination: PaginationParams) -> dict:
        admin = await User.filter(id=admin_id, role=UserRole.ADMIN).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )

        total = await User.filter(role=UserRole.STAFF).count()
        staff_members = await User.filter(role=UserRole.STAFF).offset(
            (pagination.page - 1) * pagination.size
        ).limit(pagination.size)

        staff_responses = [StaffResponse.model_validate(staff) for staff in staff_members]

        return {
            "items": staff_responses,
            "total": total,
            "page": pagination.page,
            "size": pagination.size,
            "pages": (total + pagination.size - 1) // pagination.size
        }

    @staticmethod
    async def delete_user(admin_id: int, user_id: int) -> dict:
        admin = await User.filter(id=admin_id, role=UserRole.ADMIN).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )

        user = await User.filter(id=user_id, role=UserRole.USER).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user_requests_count = await Request.filter(owner_id=user_id).count()
        if user_requests_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete user with existing requests"
            )

        await user.delete()
        return {"message": "User deleted successfully"}

    @staticmethod
    async def delete_staff(admin_id: int, staff_id: int) -> dict:
        admin = await User.filter(id=admin_id, role=UserRole.ADMIN).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )

        staff = await User.filter(id=staff_id, role=UserRole.STAFF).first()
        if not staff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found"
            )

        assigned_requests = await Request.filter(staff_member_id=staff_id).count()
        if assigned_requests > 0:
            await Request.filter(staff_member_id=staff_id).update(staff_member_id=None)

        await staff.delete()
        return {"message": "Staff member deleted successfully"}

    @staticmethod
    async def get_staff_workload(admin_id: int) -> List[dict]:
        admin = await User.filter(id=admin_id, role=UserRole.ADMIN).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )

        staff_workload = await User.filter(role=UserRole.STAFF).annotate(
            total_requests=Count("assigned_requests"),
            new_requests=Count("assigned_requests", _filter=Q(assigned_requests__status=RequestStatus.NEW)),
            in_progress_requests=Count("assigned_requests", _filter=Q(assigned_requests__status=RequestStatus.IN_PROGRESS)),
            completed_requests=Count("assigned_requests", _filter=Q(assigned_requests__status=RequestStatus.COMPLETED)),
            closed_requests=Count("assigned_requests", _filter=Q(assigned_requests__status=RequestStatus.CLOSED))
        ).values(
            "id", "email", "total_requests", "new_requests",
            "in_progress_requests", "completed_requests", "closed_requests"
        )

        return staff_workload