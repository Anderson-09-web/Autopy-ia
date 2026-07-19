#!/usr/bin/env bash
# =============================================================================
# render-build.sh — Build script para Render
# NO intenta instalar pnpm globalmente (causa EROFS).
# Usa pnpm si ya está disponible, si no usa npx como fallback.
# =============================================================================
set -e

# ── 1. Resolver qué pnpm usar ─────────────────────────────────────────────────
if command -v pnpm &>/dev/null; then
    echo "==> pnpm $(pnpm --version) encontrado en PATH"
    PNPM="pnpm"
elif [ -f /usr/lib/node_modules/pnpm/bin/pnpm.cjs ]; then
    echo "==> pnpm encontrado en /usr/lib/node_modules/pnpm"
    PNPM="node /usr/lib/node_modules/pnpm/bin/pnpm.cjs"
else
    echo "==> pnpm no encontrado, usando npx pnpm@9"
    PNPM="npx --yes pnpm@9"
fi

# ── 2. Dependencias Node ──────────────────────────────────────────────────────
echo "==> Instalando dependencias Node..."
$PNPM install

# ── 3. Build del frontend React ───────────────────────────────────────────────
echo "==> Construyendo frontend React..."
BASE_PATH=/ $PNPM --filter @workspace/web run build

# ── 4. Dependencias Python ────────────────────────────────────────────────────
echo "==> Instalando dependencias Python..."
pip install -r artifacts/api-server/requirements.txt

echo "==> Build completo ✓"
