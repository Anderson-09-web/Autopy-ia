"""
POST /api/admin/verify — lightweight endpoint to test if an admin key is valid.
Returns 200 on success, 401 on failure.
"""
from fastapi import APIRouter, Depends
from app.middleware.auth import require_admin_key

router = APIRouter()


@router.post("/verify")
async def verify_admin_key(_: None = Depends(require_admin_key)):
    """Returns 200 if the supplied X-Admin-Key is valid."""
    return {"success": True}
