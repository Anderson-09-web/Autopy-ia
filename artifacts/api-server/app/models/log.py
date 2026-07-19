"""
Request Log model — stores every API request for monitoring and analytics.
"""
import secrets
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RequestLog(Base):
    __tablename__ = "request_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: secrets.token_hex(16))
    api_key_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    api_key_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip: Mapped[str] = mapped_column(String(45), nullable=False, default="unknown")
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False, default="POST")
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success | error | blocked
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failover_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "apiKeyId": self.api_key_id,
            "apiKeyName": self.api_key_name,
            "ip": self.ip,
            "endpoint": self.endpoint,
            "method": self.method,
            "model": self.model,
            "provider": self.provider,
            "status": self.status,
            "statusCode": self.status_code,
            "latencyMs": self.latency_ms,
            "tokensUsed": self.tokens_used,
            "failoverCount": self.failover_count,
            "errorMessage": self.error_message,
            "createdAt": self.created_at.isoformat(),
        }
