"""
GET /api/v1/status — system status, model health, and resource metrics.
"""
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

import psutil

from app.database import get_db
from app.middleware.auth import require_api_key
from app.models.api_key import ApiKey
from app.models.log import RequestLog
from app.services.ai_service import get_all_models
from app.services.cache import cache
from app.config import settings

router = APIRouter()
_start_time = time.time()


@router.get("/v1/status")
async def get_system_status(
    _: ApiKey = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    models = get_all_models()
    active = sum(1 for m in models if m["status"] == "active")
    down = sum(1 for m in models if m["status"] == "down")

    total_requests = db.query(func.count(RequestLog.id)).scalar() or 0

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    requests_today = db.query(func.count(RequestLog.id)).filter(
        RequestLog.created_at >= today_start
    ).scalar() or 0

    avg_latency = db.query(func.avg(RequestLog.latency_ms)).filter(
        RequestLog.status == "success"
    ).scalar() or 0

    uptime_seconds = time.time() - _start_time

    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.1)

    formatted_models = [
        {
            "id": m["id"],
            "name": m["name"],
            "provider": m["provider"],
            "speed": m["speed"],
            "status": m["status"],
            "priority": m["priority"],
            "maxTokens": m.get("max_tokens"),
            "supportsImages": m.get("supports_images", False),
            "latencyMs": m.get("latencyMs"),
        }
        for m in models
    ]

    return {
        "success": True,
        "modelsActive": active,
        "modelsDown": down,
        "totalRequests": total_requests,
        "requestsToday": requests_today,
        "avgLatencyMs": round(float(avg_latency), 1),
        "uptime": round(uptime_seconds, 1),
        "ramUsageMb": round(mem.used / 1024 / 1024, 1),
        "cpuPercent": round(cpu, 1),
        "models": formatted_models,
        "cacheHitRate": cache.hit_rate(),
        "version": settings.version,
    }
