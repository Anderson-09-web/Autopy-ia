"""
Content moderation — blocks explicit/harmful content before processing.
Uses keyword matching + optional OpenAI moderation API.
"""
import re
from app.config import settings

# Explicit content patterns to block
_BLOCKED_PATTERNS = [
    r"\bporn(?:ography)?\b",
    r"\bpornographic\b",
    r"\bexplicit\s+(?:sexual|nude|naked)\b",
    r"\bnude(?:s|ity)?\b",
    r"\bnaked\b",
    r"\bsexual\s+(?:content|act|scene)\b",
    r"\bxxx\b",
    r"\badult\s+content\b",
    r"\berotica\b",
    r"\bsexually\s+explicit\b",
    r"\bchild\s+(?:abuse|exploitation|pornography|nude)\b",
    r"\bcsam\b",
    r"\bunderage\s+(?:sex|nude|explicit)\b",
    r"\bsexual\s+violence\b",
    r"\brape\b",
    r"\bsexual\s+assault\b",
    r"\bgenerate\s+(?:nude|naked|porn|explicit\s+image)\b",
    r"\bdraw\s+(?:nude|naked|porn|explicit)\b",
    r"\bcreate\s+(?:nude|naked|porn|explicit)\b",
]

_compiled = [re.compile(p, re.IGNORECASE) for p in _BLOCKED_PATTERNS]


def is_content_blocked(text: str) -> bool:
    """Return True if the text contains blocked content."""
    for pattern in _compiled:
        if pattern.search(text):
            return True
    return False


async def moderate_text(text: str) -> tuple[bool, str | None]:
    """
    Check if text is safe.
    Returns (is_safe, reason).
    """
    # Keyword check first (fast)
    if is_content_blocked(text):
        return False, "Explicit content detected"

    # Optional: OpenAI moderation API for better accuracy
    if settings.openai_api_key:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            result = await client.moderations.create(input=text)
            if result.results and result.results[0].flagged:
                return False, "Content flagged by moderation system"
        except Exception:
            pass  # Fall through to allow if moderation API is unavailable

    return True, None
