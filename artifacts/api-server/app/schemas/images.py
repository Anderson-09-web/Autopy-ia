"""Image generation Pydantic schemas."""
from pydantic import BaseModel


class ImageRequest(BaseModel):
    prompt: str
    size: str = "1024x1024"
    format: str = "url"  # url | base64
    model: str | None = None


class ImageResponse(BaseModel):
    success: bool = True
    message: str = ""          # friendly acknowledgment message
    url: str | None = None
    base64: str | None = None
    model: str
    provider: str
    latencyMs: int | None = None   # camelCase matches the generated API client
