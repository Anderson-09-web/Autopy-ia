"""List available AI models."""
from fastapi import APIRouter, Depends

from app.middleware.auth import require_api_key
from app.models.api_key import ApiKey
from app.services.ai_service import get_all_models

router = APIRouter()


@router.get("/v1/models")
async def list_models(_: ApiKey = Depends(require_api_key)):
    models = get_all_models()
    formatted = [
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
    return {"success": True, "models": formatted}
