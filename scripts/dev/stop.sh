#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
cd "$SCRIPT_DIR/../.."
source "$SCRIPT_DIR/stack-env.sh"

for pid in ${(f)"$(lsof -tiTCP:5173 -sTCP:LISTEN 2>/dev/null || true)"}; do
  command="$(ps -p "$pid" -o command= 2>/dev/null || true)"
  if [[ "$command" == *vite* || "$command" == *"npm run dev"* ]]; then
    kill "$pid" 2>/dev/null || true
  fi
done

docker compose down --remove-orphans
echo "FantaAnalytics fermato; i volumi non sono stati rimossi."
