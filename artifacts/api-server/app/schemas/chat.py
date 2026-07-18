"""Chat-related Pydantic schemas."""
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str  # system | user | assistant
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None
    max_tokens: int = 1024
    temperature: float = 0.7
    stream: bool = False


class ChatResponse(BaseModel):
    success: bool = True
    text: str
    model: str
    provider: str
    tokens_used: int | None = None
    latency_ms: int | None = None
    cached: bool = False
    failover_count: int = 0
