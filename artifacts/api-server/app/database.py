"""
SQLAlchemy database setup (sync engine with thread pool via FastAPI).
"""
import asyncio
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.config import settings


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal = None


def _get_engine():
    global _engine
    if _engine is None:
        if not settings.database_url:
            raise RuntimeError("DATABASE_URL is not configured")
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=_get_engine(), autoflush=False, autocommit=False)
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    factory = get_session_factory()
    db = factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def init_db():
    """Create all tables on startup."""
    import app.models.api_key  # noqa: F401
    import app.models.log  # noqa: F401

    loop = asyncio.get_event_loop()
    try:
        engine = _get_engine()
        await loop.run_in_executor(None, lambda: Base.metadata.create_all(bind=engine))
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
