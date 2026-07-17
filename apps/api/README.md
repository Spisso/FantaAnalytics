# FantaAnalytics API

Gateway pubblico Laravel 12. Non interroga direttamente le tabelle Analytics: usa il client HTTP configurato da `ANALYTICS_BASE_URL` e il contratto OpenAPI versionato nella root del repository.

```bash
make api-install
make api-lint
make api-test
make api-up
```

Endpoint: `/api/v1/health`, `/api/v1/analytics/status`, `/api/v1/players`, `/api/v1/players/{id}` e `/api/v1/import-runs`.
