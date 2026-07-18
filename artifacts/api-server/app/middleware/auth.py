"""
API key authentication and admin key authentication dependencies.
"""
from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.api_key import ApiKey
from app.services.rate_limiter import rate_limiter
from app.config import settings


def _extract_key(authorization: str | None) -> str | None:
    """Extract key from 'Bearer apt_...' or raw key."""
    if not authorization:
        return None
    if authorization.startswith("Bearer "):
        return authorization[7:].strip()
    return authorization.strip()


def require_api_key(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> ApiKey:
    """Dependency: validate API key, enforce rate limit, return ApiKey model."""
    raw_key = _extract_key(authorization)
    if not raw_key:
        raise HTTPException(
            status_code=401,
            detail={"success": False, "error": "Missing API key. Include Authorization: Bearer apt_xxx"},
        )

    api_key = db.query(ApiKey).filter(ApiKey.key == raw_key).first()
    if not api_key or not api_key.is_valid():
        raise HTTPException(
            status_code=401,
            detail={"success": False, "error": "Invalid or revoked API key"},
        )

    # Rate limiting
    allowed, remaining = rate_limiter.check(api_key.id, api_key.rate_limit)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={"success": False, "error": f"Rate limit exceeded. Limit: {api_key.rate_limit} RPM"},
        )

    return api_key


def require_admin_key(
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> None:
    """Dependency: validate admin key against ADMIN_KEY env var."""
    if not x_admin_key or x_admin_key != settings.admin_key:
        raise HTTPException(
            status_code=401,
            detail={"success": False, "error": "Invalid admin key"},
        )
