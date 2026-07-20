"""
Application configuration loaded from environment variables.
"""
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = ""

    # AI Provider API Keys
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

    # Cache
    redis_url: Optional[str] = None

    # Admin
    admin_key: str = "autopy-admin-secret-change-in-prod"

    # Rate limiting defaults
    default_rate_limit_rpm: int = 100  # requests per minute

    # Provider timeouts (seconds)
    provider_timeout: float = 20.0       # max for the last/only provider
    failover_timeout: float = 5.0        # timeout before trying next provider

    # App version
    version: str = "1.0.0"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
