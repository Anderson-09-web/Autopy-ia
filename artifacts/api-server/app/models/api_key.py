"""
API Key model — stores developer API keys issued by Autopy AI.
"""
import secrets
import string
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _generate_key() -> str:
    """Generate an apt_xxx style API key."""
    alphabet = string.ascii_letters + string.digits
    suffix = "".join(secrets.choice(alphabet) for _ in range(40))
    return f"apt_{suffix}"


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: secrets.token_hex(16))
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True, default=_generate_key)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | inactive | revoked
    rate_limit: Mapped[int] = mapped_column(Integer, default=100)  # RPM; 0 = unlimited
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def is_valid(self) -> bool:
        """Check if the key is currently usable."""
        if self.status != "active":
            return False
        if self.expires_at and self.expires_at < datetime.now(timezone.utc):
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "status": self.status,
            "rateLimit": self.rate_limit,
            "totalRequests": self.total_requests,
            "tokensUsed": self.tokens_used,
            "lastUsedAt": self.last_used_at.isoformat() if self.last_used_at else None,
            "createdAt": self.created_at.isoformat(),
            "expiresAt": self.expires_at.isoformat() if self.expires_at else None,
        }
