"""
GET /api/admin/logs — paginated request logs with optional filters.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.middleware.auth import require_admin_key
from app.models.log import RequestLog

router = APIRouter()


@router.get("/logs")
async def get_request_logs(
    page: int = 1,
    limit: int = 50,
    model: str | None = None,
    status: str | None = None,
    _: None = Depends(require_admin_key),
    db: Session = Depends(get_db),
):
    query = db.query(RequestLog)
    if model:
        query = query.filter(RequestLog.model == model)
    if status:
        query = query.filter(RequestLog.status == status)

    total = query.count()
    offset = (page - 1) * limit
    logs = query.order_by(RequestLog.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "success": True,
        "logs": [log.to_dict() for log in logs],
        "total": total,
        "page": page,
        "limit": limit,
    }
