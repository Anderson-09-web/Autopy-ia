"""
POST /api/v1/images — image generation with moderation and failover.
"""
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_api_key
from app.models.api_key import ApiKey
from app.models.log import RequestLog
from app.schemas.images import ImageRequest, ImageResponse
from app.services.ai_service import image_with_failover
from app.services.moderation import moderate_text

router = APIRouter()


@router.post("/v1/images", response_model=ImageResponse)
async def generate_image(
    body: ImageRequest,
    request: Request,
    api_key: ApiKey = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    start_ms = time.time()
    ip = request.client.host if request.client else "unknown"

    # Moderation on prompt
    is_safe, reason = await moderate_text(body.prompt)
    if not is_safe:
        _log(db, api_key, ip, None, None, "blocked", 403, 0, None, 0, reason)
        raise HTTPException(
            status_code=403,
            detail={
                "success": False,
                "error": "Explicit content is not available on Autopy AI. Please modify your request and try again.",
            },
        )

    # Map format
    response_format = "b64_json" if body.format == "base64" else "url"

    try:
        result, failover_count = await image_with_failover(
            prompt=body.prompt,
            size=body.size,
            response_format=response_format,
            model=body.model,
        )
    except Exception as e:
        latency = int((time.time() - start_ms) * 1000)
        _log(db, api_key, ip, None, None, "error", 500, latency, None, 0, str(e))
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})

    latency_ms = int((time.time() - start_ms) * 1000)
    api_key.total_requests += 1
    api_key.last_used_at = datetime.now(timezone.utc)

    # Build a friendly acknowledgment message
    short_prompt = body.prompt[:80] + "…" if len(body.prompt) > 80 else body.prompt
    ack_message = (
        f"¡Aquí está tu imagen! La generé a partir de: \"{short_prompt}\". "
        f"Modelo usado: {result.model}. "
        f"Tiempo de generación: {latency_ms / 1000:.1f}s."
    )

    _log(db, api_key, ip, result.model, result.provider, "success", 200, latency_ms, None, failover_count)
    return ImageResponse(
        success=True,
        message=ack_message,
        url=result.url,
        base64=result.base64,
        model=result.model,
        provider=result.provider,
        latencyMs=latency_ms,
    )


def _log(db, api_key, ip, model, provider, status, status_code, latency_ms, tokens, failover_count, error=None):
    try:
        log = RequestLog(
            api_key_id=api_key.id if api_key else None,
            api_key_name=api_key.name if api_key else None,
            ip=ip,
            endpoint="/api/v1/images",
            method="POST",
            model=model,
            provider=provider,
            status=status,
            status_code=status_code,
            latency_ms=latency_ms,
            tokens_used=tokens,
            failover_count=failover_count,
            error_message=error,
        )
        db.add(log)
        db.commit()
    except Exception:
        pass
