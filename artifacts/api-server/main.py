"""
Autopy AI — Unified AI Platform API
FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import init_db
from app.routers import health, chat, images, status, models, discord, user, openai_compat
from app.routers.admin import keys, dashboard, logs, models_admin, verify, extra


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


# ── Uniform JSON error responses ──────────────────────────────────────────────

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # If the router already set a dict detail, forward it; otherwise wrap it.
    detail = exc.detail
    if isinstance(detail, dict):
        body = detail
    else:
        body = {"success": False, "error": str(detail), "status_code": exc.status_code}
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(l) for l in e["loc"]), "message": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": "Validation error", "details": errors},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"},
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
app.include_router(user.router, prefix=API, tags=["user"])
app.include_router(openai_compat.router, prefix=API + "/openai", tags=["openai-compat"])

# Admin routes
app.include_router(verify.router, prefix=ADMIN, tags=["admin"])
app.include_router(keys.router, prefix=ADMIN, tags=["admin"])
app.include_router(dashboard.router, prefix=ADMIN, tags=["admin"])
app.include_router(logs.router, prefix=ADMIN, tags=["admin"])
app.include_router(models_admin.router, prefix=ADMIN, tags=["admin"])
app.include_router(extra.router, prefix=ADMIN, tags=["admin"])
