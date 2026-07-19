"""Shared Pydantic schemas."""
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    code: str | None = None


class SuccessResponse(BaseModel):
    success: bool = True
    message: str | None = None
