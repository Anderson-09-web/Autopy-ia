"""
POST /api/v1/discord/chat — Discord-formatted chat response with embeds.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_api_key
from app.models.api_key import ApiKey
from app.schemas.chat import ChatRequest
from app.services.ai_service import chat_with_failover
from app.services.moderation import moderate_text

router = APIRouter()


@router.post("/v1/discord/chat")
async def discord_chat(
    body: ChatRequest,
    request: Request,
    api_key: ApiKey = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    user_text = " ".join(m.content for m in body.messages if m.role == "user")
    is_safe, reason = await moderate_text(user_text)
    if not is_safe:
        raise HTTPException(
            status_code=403,
            detail={"success": False, "error": "Explicit content is not allowed."},
        )

    messages_raw = [{"role": m.role, "content": m.content} for m in body.messages]
    try:
        result, failover_count = await chat_with_failover(
            messages=messages_raw,
            model=body.model,
            max_tokens=body.max_tokens,
            temperature=body.temperature,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})

    return {
        "embeds": [
            {
                "title": "Autopy AI",
                "description": result.text,
                "color": 5814783,
                "fields": [
                    {"name": "Model", "value": result.model, "inline": True},
                    {"name": "Provider", "value": result.provider.upper(), "inline": True},
                    {"name": "Tokens", "value": str(result.tokens_used or "N/A"), "inline": True},
                ],
                "footer": {"text": "Autopy AI \u2022 Powered by Multiple AI Models"},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }
