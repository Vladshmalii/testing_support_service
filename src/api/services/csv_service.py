import csv
from io import StringIO
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse

from src.models.models import Request, User
from src.api.schemas.schemas import RequestFilters
from src.api.services.request_service import RequestService
from src.enums import UserRole


class CSVService:

    @staticmethod
    async def export_requests_csv(filters: Optional[RequestFilters], admin_id: int) -> StreamingResponse:
        admin = await User.get_or_none(id=admin_id, role=UserRole.ADMIN)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )

        query = Request.all()
        query = RequestService._apply_filters(query, filters)
        requests = await query.prefetch_related("owner", "staff_member")

        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "ID", "Request Text", "Status", "Created At", "Updated At",
            "Owner Email", "Owner Name", "Owner INN", "Owner Phone",
            "Staff Email", "Staff Comment"
        ])

        for request in requests:
            owner_name = ""
            if request.owner.first_name or request.owner.last_name:
                parts = [request.owner.first_name or "", request.owner.last_name or ""]
                owner_name = " ".join(filter(None, parts))

            writer.writerow([
                request.id,
                request.text,
                request.status.value,
                request.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                request.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                request.owner.email,
                owner_name,
                request.owner.inn or "",
                request.owner.phone or "",
                request.staff_member.email if request.staff_member else "",
                request.staff_comment or ""
            ])

        output.seek(0)
        filename = f"requests_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )