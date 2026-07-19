"""
POST /api/v1/chat — chat completion with automatic failover and caching.
"""
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_api_key
from app.models.api_key import ApiKey
from app.models.log import RequestLog
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai_service import chat_with_failover
from app.services.cache import cache
from app.services.moderation import moderate_text

router = APIRouter()


@router.post("/v1/chat", response_model=ChatResponse)
async def create_chat_completion(
    body: ChatRequest,
    request: Request,
    api_key: ApiKey = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    start_ms = time.time()
    ip = request.client.host if request.client else "unknown"

    # Moderation check on all user messages
    user_text = " ".join(m.content for m in body.messages if m.role == "user")
    is_safe, reason = await moderate_text(user_text)
    if not is_safe:
        _log(db, api_key, ip, "/api/v1/chat", None, None, "blocked", 403, 0, 0, 0, reason)
        raise HTTPException(
            status_code=403,
            detail={
                "success": False,
                "error": "Explicit content is not available on Autopy AI. Please modify your request and try again.",
            },
        )

    # Cache lookup
    messages_raw = [{"role": m.role, "content": m.content} for m in body.messages]
    cache_key = cache.chat_key(messages_raw, body.model)
    cached = cache.get(cache_key)
    if cached:
        _log(db, api_key, ip, "/api/v1/chat", cached.get("model"), cached.get("provider"),
             "success", 200, int((time.time() - start_ms) * 1000), cached.get("tokensUsed", 0), 0)
        return {**cached, "cached": True}

    # Call AI service with failover
    try:
        result, failover_count = await chat_with_failover(
            messages=messages_raw,
            model=body.model,
            max_tokens=body.max_tokens,
            temperature=body.temperature,
        )
    except Exception as e:
        latency = int((time.time() - start_ms) * 1000)
        _log(db, api_key, ip, "/api/v1/chat", body.model, None, "error", 500, latency, 0, failover_count if 'failover_count' in dir() else 0, str(e))
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})

    latency_ms = int((time.time() - start_ms) * 1000)

    # Update API key stats
    api_key.total_requests += 1
    if result.tokens_used:
        api_key.tokens_used += result.tokens_used
    api_key.last_used_at = datetime.now(timezone.utc)

    _log(db, api_key, ip, "/api/v1/chat", result.model, result.provider,
         "success", 200, latency_ms, result.tokens_used or 0, failover_count)

    response_data = {
        "success": True,
        "text": result.text,
        "model": result.model,
        "provider": result.provider,
        "tokensUsed": result.tokens_used,
        "latencyMs": latency_ms,
        "cached": False,
        "failoverCount": failover_count,
    }

    # Cache the result (5 min TTL)
    cache.set(cache_key, response_data, ttl=300)
    return response_data


def _log(db, api_key, ip, endpoint, model, provider, status, status_code, latency_ms, tokens, failover_count, error=None):
    try:
        log = RequestLog(
            api_key_id=api_key.id if api_key else None,
            api_key_name=api_key.name if api_key else None,
            ip=ip,
            endpoint=endpoint,
            method="POST",
            model=model,
            provider=provider,
            status=status,
            status_code=status_code,
            latency_ms=latency_ms,
            tokens_used=tokens if tokens else None,
            failover_count=failover_count,
            error_message=error,
        )
        db.add(log)
        db.commit()
    except Exception:
        pass
