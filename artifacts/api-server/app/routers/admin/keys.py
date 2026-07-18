"""
Admin API key management endpoints.
"""
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_admin_key
from app.models.api_key import ApiKey
from app.schemas.admin import CreateApiKeyRequest, UpdateApiKeyRequest

router = APIRouter()


@router.get("/keys")
async def list_api_keys(
    page: int = 1,
    limit: int = 20,
    _: None = Depends(require_admin_key),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * limit
    total = db.query(ApiKey).count()
    keys = db.query(ApiKey).order_by(ApiKey.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "success": True,
        "keys": [k.to_dict() for k in keys],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.post("/keys", status_code=201)
async def create_api_key(
    body: CreateApiKeyRequest,
    _: None = Depends(require_admin_key),
    db: Session = Depends(get_db),
):
    key = ApiKey(
        id=secrets.token_hex(16),
        name=body.name,
        rate_limit=body.rate_limit,
        expires_at=body.expires_at,
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    return key.to_dict()


@router.get("/keys/{key_id}")
async def get_api_key(
    key_id: str,
    _: None = Depends(require_admin_key),
    db: Session = Depends(get_db),
):
    key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail={"success": False, "error": "API key not found"})
    return key.to_dict()


@router.patch("/keys/{key_id}")
async def update_api_key(
    key_id: str,
    body: UpdateApiKeyRequest,
    _: None = Depends(require_admin_key),
    db: Session = Depends(get_db),
):
    key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail={"success": False, "error": "API key not found"})

    if body.name is not None:
        key.name = body.name
    if body.status is not None:
        key.status = body.status
    if body.rate_limit is not None:
        key.rate_limit = body.rate_limit

    db.commit()
    db.refresh(key)
    return key.to_dict()


@router.delete("/keys/{key_id}")
async def delete_api_key(
    key_id: str,
    _: None = Depends(require_admin_key),
    db: Session = Depends(get_db),
):
    key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail={"success": False, "error": "API key not found"})
    db.delete(key)
    db.commit()
    return {"success": True, "message": "API key deleted"}
