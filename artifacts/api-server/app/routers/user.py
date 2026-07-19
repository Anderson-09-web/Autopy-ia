"""
User-facing account endpoints (require API key auth).

GET  /api/v1/me       — key info + usage summary
GET  /api/v1/usage    — per-day usage breakdown (last 30 days)
"""
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_api_key
from app.models.api_key import ApiKey
from app.models.log import RequestLog

router = APIRouter()


@router.get("/v1/me")
def get_me(
    api_key: ApiKey = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    """Return the authenticated key's profile and aggregate usage."""
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    requests_today = (
        db.query(func.count(RequestLog.id))
        .filter(
            RequestLog.api_key_id == api_key.id,
            RequestLog.created_at >= today,
        )
        .scalar()
        or 0
    )

    errors_total = (
        db.query(func.count(RequestLog.id))
        .filter(
            RequestLog.api_key_id == api_key.id,
            RequestLog.status.in_(["error", "blocked"]),
        )
        .scalar()
        or 0
    )

    return {
        "success": True,
        "key": {
            "id": api_key.id,
            "name": api_key.name,
            "status": api_key.status,
            "rateLimit": api_key.rate_limit,
            "createdAt": api_key.created_at.isoformat(),
            "expiresAt": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "lastUsedAt": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
        },
        "usage": {
            "totalRequests": api_key.total_requests,
            "tokensUsed": api_key.tokens_used,
            "requestsToday": requests_today,
            "errorsTotal": errors_total,
        },
    }


@router.get("/v1/usage")
def get_usage(
    days: int = 30,
    api_key: ApiKey = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    """Return per-day request/token counts for the past *days* days."""
    if days < 1 or days > 90:
        days = 30

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    all_logs = (
        db.query(RequestLog)
        .filter(
            RequestLog.api_key_id == api_key.id,
            RequestLog.created_at >= since,
        )
        .all()
    )

    # Build a full date range with zeros for missing days
    data: dict[str, dict] = {}
    for i in range(days):
        day = (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        data[day] = {"date": day, "requests": 0, "tokens": 0, "errors": 0}

    for log in all_logs:
        if not log.created_at:
            continue
        day_str = log.created_at.strftime("%Y-%m-%d")
        if day_str in data:
            data[day_str]["requests"] += 1
            data[day_str]["tokens"] += log.tokens_used or 0
            if log.status in ("error", "blocked"):
                data[day_str]["errors"] += 1

    return {
        "success": True,
        "days": days,
        "data": list(data.values()),
    }
