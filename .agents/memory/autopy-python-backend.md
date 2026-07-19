---
name: Autopy AI Python backend
description: Notes on the FastAPI backend setup, Python installation, and start script behavior.
---

## Rule
The API server is a Python FastAPI app, not Node.js. The artifact.toml runs `bash /home/runner/workspace/artifacts/api-server/start.sh` (absolute path required — workflow CWD is not workspace root).

**Why:** The original workspace had a Node.js api-server scaffold that was replaced with Python FastAPI from the imported GitHub repo. The start.sh creates/updates a venv at `/home/runner/workspace/.venv` using `uv`.

## How to apply
- `uv` is available inside the workflow environment (via the start.sh which calls `uv venv` and `uv pip install`), but NOT available as a shell command from agent bash tool.
- To install Python packages from the agent, use `installProgrammingLanguage({ language: "python-3.11" })` then `installLanguagePackages({ language: "python", packages: [...] })`.
- The venv lives at `/home/runner/workspace/.venv` — reference Python as `/home/runner/workspace/.venv/bin/python3`.
- Redis is optional — the app has an in-memory fallback cache.
- Required env vars: `DATABASE_URL` (auto-provisioned), `OPENAI_API_KEY`, `GROQ_API_KEY`, `ADMIN_KEY` (default: `autopy-admin-secret-change-in-prod`).
