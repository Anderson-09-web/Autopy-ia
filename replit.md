# Autopy AI

A unified AI platform that routes developer requests through multiple AI models (OpenAI, Groq) behind a single API. Includes automatic failover, content moderation, caching, rate limiting, and a full admin dashboard.

## Run & Operate

- `bash /home/runner/workspace/artifacts/api-server/start.sh` — run the Python FastAPI server (port 8080, proxied at `/api`); workflow: `artifacts/api-server: API Server`
- `PORT=22333 BASE_PATH=/ pnpm --filter @workspace/web run dev` — run the React web frontend; workflow: `artifacts/web: web`
- `pnpm --filter @workspace/web run dev` — run the React web frontend (port dynamic, proxied at `/`)
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks from OpenAPI spec

## Stack

- **Frontend**: React + Vite + Tailwind CSS + Wouter routing + React Query
- **Backend**: Python 3.11 + FastAPI + Uvicorn (replaces the original Node.js api-server)
- **Database**: PostgreSQL + SQLAlchemy (sync) — tables auto-created on startup
- **Cache**: Redis (optional) with in-memory fallback
- **AI Providers**: OpenAI, Groq (extensible via `app/services/providers/`)

## Where things live

- `artifacts/api-server/` — Python FastAPI backend
  - `main.py` — FastAPI app entry + router registration
  - `app/config.py` — environment settings
  - `app/models/` — SQLAlchemy models (api_keys, request_logs)
  - `app/services/ai_service.py` — failover + model registry
  - `app/services/providers/` — OpenAI / Groq provider adapters
  - `app/routers/` — endpoint handlers (chat, images, status, discord, admin/*)
  - `requirements.txt` — Python dependencies
- `artifacts/web/` — React web app
  - `src/pages/` — Landing, Playground, Docs, Dashboard, Status
- `lib/api-spec/openapi.yaml` — single source of truth for API contracts

## Environment Variables Required

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (auto-provisioned by Replit) |
| `OPENAI_API_KEY` | Your OpenAI API key |
| `GROQ_API_KEY` | Your Groq API key |
| `ADMIN_KEY` | Admin panel secret (default: `autopy-admin-secret-change-in-prod`) |
| `REDIS_URL` | Optional Redis URL for caching |

## Architecture decisions

- **Python FastAPI** replaces the Node.js template api-server; the artifact.toml was updated to run `start.sh` with an absolute path since the workflow CWD is not `/home/runner/workspace`.
- **Sync SQLAlchemy** (psycopg2) over async for simplicity; FastAPI runs sync routes in thread pools automatically.
- **In-memory fallback cache** — works without Redis; hit rate is tracked and exposed via `/api/v1/status`.
- **Failover is provider-level** — each provider has a backoff timer; on failure the next provider in priority order is tried silently.
- **Content moderation** — keyword regex first (fast), then optional OpenAI Moderation API.

## Adding new AI providers

1. Create `app/services/providers/my_provider.py` extending `BaseProvider`
2. Implement `async def chat(...)` (and optionally `generate_image`)
3. Add to `_build_providers()` in `app/services/ai_service.py`
4. Add model entries to `_MODEL_REGISTRY`

## Admin Access

Default admin key: `autopy-admin-secret-change-in-prod` (change via `ADMIN_KEY` env var)

## User preferences

_Populate as you build._

## Gotchas

- The workflow for the API server uses an **absolute path** (`bash /home/runner/workspace/artifacts/api-server/start.sh`) because the workflow runner does not set CWD to the workspace root.
- Python packages are installed into `.venv/` (a `uv` virtualenv at `/home/runner/workspace/.venv`). The Nix Python interpreter is immutable, so `--system` installs are blocked; always use the venv. Reference Python with `/home/runner/workspace/.venv/bin/python3`.
- `start.sh` creates/updates the venv automatically on each run via `uv pip install --python`.
- The web workflow must receive `PORT=22333 BASE_PATH=/` inline — these are not injected automatically since the workflow was manually configured rather than managed by artifact.toml.
