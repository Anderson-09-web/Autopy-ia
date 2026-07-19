"""Admin-related Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel


class CreateApiKeyRequest(BaseModel):
    name: str
    rate_limit: int = 100
    expires_at: datetime | None = None


class UpdateApiKeyRequest(BaseModel):
    name: str | None = None
    status: str | None = None
    rate_limit: int | None = None


class UpdateModelRequest(BaseModel):
    id: str
    status: str  # active | degraded | down
    priority: int | None = None
