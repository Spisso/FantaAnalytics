#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
cd "$SCRIPT_DIR/../.."
source "$SCRIPT_DIR/stack-env.sh"

check_endpoint() {
  local label="$1"
  local url="$2"
  curl --fail --silent --show-error "$url" >/dev/null
  echo "$label: OK"
}

check_endpoint "Analytics health" "http://localhost:${ANALYTICS_API_PORT}/health"
check_endpoint "Analytics ready" "http://localhost:${ANALYTICS_API_PORT}/ready"
check_endpoint "Laravel API" "http://localhost:${API_PORT}/api/v1/health"
check_endpoint "Analytics proxy" "http://localhost:${API_PORT}/api/v1/analytics/status"
check_endpoint "Serie A teams" "http://localhost:${API_PORT}/api/v1/teams?season=2026-27"
