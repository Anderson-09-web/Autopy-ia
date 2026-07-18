"""
Admin model management — list models with admin detail and update status.
"""
from fastapi import APIRouter, Depends

from app.middleware.auth import require_admin_key
from app.schemas.admin import UpdateModelRequest
from app.services.ai_service import get_all_models, update_model_status

router = APIRouter()


@router.get("/models")
async def admin_list_models(_: None = Depends(require_admin_key)):
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


@router.patch("/models")
async def update_model(
    body: UpdateModelRequest,
    _: None = Depends(require_admin_key),
):
    update_model_status(body.id, body.status, body.priority)
    models = get_all_models()
    updated = next((m for m in models if m["id"] == body.id), None)
    if not updated:
        return {"id": body.id, "status": body.status, "priority": body.priority}
    return {
        "id": updated["id"],
        "name": updated["name"],
        "provider": updated["provider"],
        "speed": updated["speed"],
        "status": updated["status"],
        "priority": updated["priority"],
        "maxTokens": updated.get("max_tokens"),
        "supportsImages": updated.get("supports_images", False),
        "latencyMs": updated.get("latencyMs"),
    }
