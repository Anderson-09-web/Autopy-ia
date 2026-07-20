"""
OpenAI-compatible chat completions endpoint.

POST /api/openai/v1/chat/completions
  → accepts the standard OpenAI request body
  → returns a standard OpenAI response body

Discord bots and any OpenAI SDK can point their base_url at this API and
it will just work.  Example bot config:

    openai.api_base = "https://<your-replit-domain>"
    openai.api_key  = "apt_..."          # your Autopy API key

The path /v1/chat/completions (without /api) is proxied here by the Vite
dev server and should be handled similarly in production via the /openai
artifact path.
"""
import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_api_key
from app.models.api_key import ApiKey
from app.models.log import RequestLog
from app.services.ai_service import chat_with_failover
from app.services.moderation import moderate_text

router = APIRouter()


# ── Request / response schemas (OpenAI format) ────────────────────────────────

class OAIMessage(BaseModel):
    role: str
    content: str


class OAIRequest(BaseModel):
    messages: list[OAIMessage]
    model: str | None = "llama-3.3-70b-versatile"
    max_tokens: int | None = 1024
    temperature: float | None = 0.7
    stream: bool = False


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/v1/chat/completions")
async def openai_chat_completions(
    body: OAIRequest,
    request: Request,
    api_key: ApiKey = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    """
    OpenAI-compatible chat completions.  Streaming is not yet supported;
    pass stream=false (the default).
    """
    if body.stream:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "Streaming is not supported yet. Set stream=false."},
        )

    start_ms = time.time()
    ip = request.client.host if request.client else "unknown"

    # Moderation
    user_text = " ".join(m.content for m in body.messages if m.role == "user")
    is_safe, reason = await moderate_text(user_text)
    if not is_safe:
        _log(db, api_key, ip, "blocked", 403, 0, 0, 0, reason)
        raise HTTPException(
            status_code=403,
            detail={"error": {"message": reason, "type": "content_policy_violation", "code": "content_filter"}},
        )

    messages_raw = [{"role": m.role, "content": m.content} for m in body.messages]

    try:
        result, failover_count = await chat_with_failover(
            messages=messages_raw,
            model=body.model,
            max_tokens=body.max_tokens or 1024,
            temperature=body.temperature or 0.7,
        )
    except Exception as e:
        latency = int((time.time() - start_ms) * 1000)
        _log(db, api_key, ip, "error", 500, latency, 0, 0, str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": {"message": str(e), "type": "server_error", "code": "internal_error"}},
        )

    latency_ms = int((time.time() - start_ms) * 1000)
    tokens_used = result.tokens_used or 0

    # Update key stats
    api_key.total_requests += 1
    api_key.tokens_used += tokens_used
    api_key.last_used_at = datetime.now(timezone.utc)

    _log(db, api_key, ip, "success", 200, latency_ms, tokens_used, failover_count)

    # Return standard OpenAI response shape
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
        "object": "chat.completion",
        "created": int(datetime.now(timezone.utc).timestamp()),
        "model": result.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": result.text},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": tokens_used or None,
        },
        # Autopy extensions (ignored by standard clients)
        "x_autopy": {
            "provider": result.provider,
            "latency_ms": latency_ms,
            "failover_count": failover_count,
        },
    }


def _log(db, api_key, ip, status, status_code, latency_ms, tokens, failover_count, error=None):
    try:
        log = RequestLog(
            api_key_id=api_key.id if api_key else None,
            api_key_name=api_key.name if api_key else None,
            ip=ip,
            endpoint="/api/openai/v1/chat/completions",
            method="POST",
            model=None,
            provider=None,
            status=status,
            status_code=status_code,
            latency_ms=latency_ms,
            tokens_used=tokens or None,
            failover_count=failover_count,
            error_message=error,
        )
        db.add(log)
        db.commit()
    except Exception:
        pass
