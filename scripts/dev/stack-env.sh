#!/bin/zsh

# Shared runtime configuration for the isolated local FantaAnalytics stack.
export COMPOSE_PROJECT_NAME=fantaanalytics_real
export POSTGRES_PORT=55432
export ANALYTICS_API_PORT=18000
export API_PORT=18081
export API_CACHE_STORE=file

LAN_IP=""
if LAN_IP="$(ipconfig getifaddr en0 2>/dev/null)" && [[ -z "$LAN_IP" ]]; then
  LAN_IP=""
fi
if [[ -z "$LAN_IP" ]]; then
  LAN_IP="$(ipconfig getifaddr en1 2>/dev/null || true)"
fi

if [[ -n "$LAN_IP" ]]; then
  export CORS_ALLOWED_ORIGINS="http://localhost:5173,http://${LAN_IP}:5173"
  export FRONTEND_API_BASE_URL="http://${LAN_IP}:18081/api/v1"
else
  export CORS_ALLOWED_ORIGINS="http://localhost:5173"
  export FRONTEND_API_BASE_URL="http://localhost:18081/api/v1"
fi

export FANTA_LAN_IP="$LAN_IP"
