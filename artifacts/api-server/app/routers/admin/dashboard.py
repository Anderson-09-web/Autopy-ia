"""
GET /api/admin/dashboard — aggregated statistics for the admin dashboard.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.database import get_db
from app.middleware.auth import require_admin_key
from app.models.api_key import ApiKey
from app.models.log import RequestLog
from app.services.ai_service import get_all_models
from app.services.cache import cache

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(
    _: None = Depends(require_admin_key),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today - timedelta(days=7)

    total_requests = db.query(func.count(RequestLog.id)).scalar() or 0
    requests_today = db.query(func.count(RequestLog.id)).filter(RequestLog.created_at >= today).scalar() or 0
    requests_week = db.query(func.count(RequestLog.id)).filter(RequestLog.created_at >= week_start).scalar() or 0

    total_tokens = db.query(func.coalesce(func.sum(RequestLog.tokens_used), 0)).scalar() or 0
    tokens_today = db.query(func.coalesce(func.sum(RequestLog.tokens_used), 0)).filter(
        RequestLog.created_at >= today
    ).scalar() or 0

    active_keys = db.query(func.count(ApiKey.id)).filter(ApiKey.status == "active").scalar() or 0
    total_keys = db.query(func.count(ApiKey.id)).scalar() or 0

    avg_latency = db.query(func.avg(RequestLog.latency_ms)).filter(
        RequestLog.status == "success"
    ).scalar() or 0

    total_errors = db.query(func.count(RequestLog.id)).filter(RequestLog.status == "error").scalar() or 0
    error_rate = round(total_errors / total_requests, 3) if total_requests > 0 else 0

    models = get_all_models()
    active_models = sum(1 for m in models if m["status"] == "active")
    down_models = sum(1 for m in models if m["status"] == "down")

    # Top models
    top_models_rows = (
        db.query(
            RequestLog.model,
            func.count(RequestLog.id).label("requests"),
            func.coalesce(func.sum(RequestLog.tokens_used), 0).label("tokens"),
        )
        .filter(RequestLog.model.isnot(None))
        .group_by(RequestLog.model)
        .order_by(func.count(RequestLog.id).desc())
        .limit(5)
        .all()
    )
    top_models = [{"model": r.model, "requests": r.requests, "tokens": r.tokens} for r in top_models_rows]

    # Requests over last 7 days
    requests_over_time = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        next_day = day + timedelta(days=1)
        count = db.query(func.count(RequestLog.id)).filter(
            RequestLog.created_at >= day,
            RequestLog.created_at < next_day,
        ).scalar() or 0
        tok = db.query(func.coalesce(func.sum(RequestLog.tokens_used), 0)).filter(
            RequestLog.created_at >= day,
            RequestLog.created_at < next_day,
        ).scalar() or 0
        requests_over_time.append({"date": day.strftime("%Y-%m-%d"), "requests": count, "tokens": tok})

    # Errors by type
    errors_by_type_rows = (
        db.query(
            RequestLog.status,
            func.count(RequestLog.id).label("count"),
        )
        .group_by(RequestLog.status)
        .all()
    )
    errors_by_type = [{"type": r.status, "count": r.count} for r in errors_by_type_rows]

    return {
        "success": True,
        "totalRequests": total_requests,
        "requestsToday": requests_today,
        "requestsThisWeek": requests_week,
        "totalTokens": int(total_tokens),
        "tokensToday": int(tokens_today),
        "activeApiKeys": active_keys,
        "totalApiKeys": total_keys,
        "avgLatencyMs": round(float(avg_latency), 1),
        "errorRate": error_rate,
        "cacheHitRate": cache.hit_rate(),
        "modelsActive": active_models,
        "modelsDown": down_models,
        "topModels": top_models,
        "requestsOverTime": requests_over_time,
        "errorsByType": errors_by_type,
    }
