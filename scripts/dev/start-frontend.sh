#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
cd "$SCRIPT_DIR/../.."
source "$SCRIPT_DIR/stack-env.sh"

printf 'VITE_API_BASE_URL=%s\n' "$FRONTEND_API_BASE_URL" > apps/web/.env.local
cd apps/web
npm run dev -- --host 0.0.0.0 --port 5173 --strictPort
