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
    """
    Response uses camelCase to match the dict returned by the router
    and the field names expected by the generated TypeScript client.
    """
    success: bool = True
    text: str
    model: str
    provider: str
    tokensUsed: int | None = None
    latencyMs: int | None = None
    cached: bool = False
    failoverCount: int = 0
