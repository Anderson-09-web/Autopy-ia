"""
Autopy AI — Unified AI Platform API
FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import health, chat, images, status, models, discord
from app.routers.admin import keys, dashboard, logs, models_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Autopy AI",
    description="Unified AI Platform — Multiple AI models behind a single API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API = "/api"
ADMIN = "/api/admin"

# Core API routes
app.include_router(health.router, prefix=API, tags=["health"])
app.include_router(models.router, prefix=API, tags=["models"])
app.include_router(chat.router, prefix=API, tags=["chat"])
app.include_router(images.router, prefix=API, tags=["images"])
app.include_router(status.router, prefix=API, tags=["status"])
app.include_router(discord.router, prefix=API, tags=["discord"])

# Admin routes
app.include_router(keys.router, prefix=ADMIN, tags=["admin"])
app.include_router(dashboard.router, prefix=ADMIN, tags=["admin"])
app.include_router(logs.router, prefix=ADMIN, tags=["admin"])
app.include_router(models_admin.router, prefix=ADMIN, tags=["admin"])
