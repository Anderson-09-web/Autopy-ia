#!/usr/bin/env bash
# =============================================================================
# render-build.sh — Build script para Render
# Instala pnpm en $HOME (escribible) en vez de /usr/lib (read-only).
# =============================================================================
set -e

echo "==> Instalando pnpm en directorio local..."
export npm_config_prefix="$HOME/.npm-global"
npm install -g pnpm
export PATH="$HOME/.npm-global/bin:$PATH"
echo "    pnpm $(pnpm --version) listo"

echo "==> Instalando dependencias Node del monorepo..."
pnpm install

echo "==> Construyendo frontend React..."
BASE_PATH=/ pnpm --filter @workspace/web run build

echo "==> Instalando dependencias Python..."
pip install -r artifacts/api-server/requirements.txt

echo "==> Build completo ✓"
