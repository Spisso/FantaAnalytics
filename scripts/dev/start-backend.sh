#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
cd "$SCRIPT_DIR/../.."
source "$SCRIPT_DIR/stack-env.sh"

make stack-up

echo "FantaAnalytics backend attivo: Analytics :${ANALYTICS_API_PORT}, API :${API_PORT}"
if [[ -n "$FANTA_LAN_IP" ]]; then
  echo "CORS LAN: http://${FANTA_LAN_IP}:5173"
fi
