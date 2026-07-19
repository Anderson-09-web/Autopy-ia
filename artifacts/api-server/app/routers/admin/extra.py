"""
Additional admin endpoints.

POST   /api/admin/keys/{keyId}/reset-usage  — zero out a key's counters
DELETE /api/admin/logs                       — bulk-delete logs (with filters)
GET    /api/admin/logs/export                — download logs as JSON
GET    /api/admin/stats/realtime             — live snapshot (last 60 s)
"""
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_admin_key
from app.models.api_key import ApiKey
from app.models.log import RequestLog

router = APIRouter()


# ── Reset usage counters ───────────────────────────────────────────────────────

@router.post("/keys/{key_id}/reset-usage")
def reset_key_usage(
    key_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
):
    key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not key:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "error": f"API key '{key_id}' not found"},
        )
    key.total_requests = 0
    key.tokens_used = 0
    db.commit()
    return {
        "success": True,
        "message": f"Usage counters reset for key '{key.name}'",
        "key": key.to_dict(),
    }


# ── Export logs ────────────────────────────────────────────────────────────────

@router.get("/logs/export")
def export_logs(
    limit: int = Query(default=1000, le=10000),
    status: str | None = None,
    provider: str | None = None,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
):
    """Return up to *limit* logs as a JSON array (newest first)."""
    q = db.query(RequestLog)
    if status:
        q = q.filter(RequestLog.status == status)
    if provider:
        q = q.filter(RequestLog.provider == provider)
    logs = q.order_by(RequestLog.created_at.desc()).limit(limit).all()

    return {
        "success": True,
        "count": len(logs),
        "exportedAt": datetime.now(timezone.utc).isoformat(),
        "logs": [_log_to_dict(l) for l in logs],
    }


# ── Bulk delete logs ───────────────────────────────────────────────────────────

@router.delete("/logs")
def delete_logs(
    older_than_days: int = Query(default=0, description="Delete logs older than N days. 0 = all."),
    status: str | None = Query(default=None, description="Only delete logs with this status"),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
):
    q = db.query(RequestLog)
    if older_than_days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        q = q.filter(RequestLog.created_at < cutoff)
    if status:
        q = q.filter(RequestLog.status == status)
    deleted = q.delete(synchronize_session=False)
    db.commit()
    return {
        "success": True,
        "deleted": deleted,
        "message": f"Deleted {deleted} log(s)",
    }


# ── Real-time stats ────────────────────────────────────────────────────────────

@router.get("/stats/realtime")
def realtime_stats(
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
):
    """Snapshot of the last 60 seconds of activity."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=60)

    rows = (
        db.query(RequestLog)
        .filter(RequestLog.created_at >= window_start)
        .order_by(RequestLog.created_at.desc())
        .limit(200)
        .all()
    )

    total = len(rows)
    errors = sum(1 for r in rows if r.status == "error")
    avg_latency = (
        int(sum(r.latency_ms for r in rows if r.latency_ms) / max(1, sum(1 for r in rows if r.latency_ms)))
        if rows else 0
    )
    providers: dict[str, int] = {}
    for r in rows:
        if r.provider:
            providers[r.provider] = providers.get(r.provider, 0) + 1

    return {
        "success": True,
        "windowSeconds": 60,
        "asOf": now.isoformat(),
        "requests": total,
        "errors": errors,
        "avgLatencyMs": avg_latency,
        "byProvider": providers,
        "recent": [_log_to_dict(r) for r in rows[:20]],
    }


def _log_to_dict(log: RequestLog) -> dict:
    return {
        "id": log.id,
        "apiKeyName": log.api_key_name,
        "ip": log.ip,
        "endpoint": log.endpoint,
        "method": log.method,
        "model": log.model,
        "provider": log.provider,
        "status": log.status,
        "statusCode": log.status_code,
        "latencyMs": log.latency_ms,
        "tokensUsed": log.tokens_used,
        "failoverCount": log.failover_count,
        "errorMessage": log.error_message,
        "createdAt": log.created_at.isoformat() if log.created_at else None,
    }
