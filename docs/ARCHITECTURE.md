# Architettura

L'architettura target separa web Vue, API Laravel e analytics Python. La parte implementata oggi è il confine `services/analytics/fantaanalytics`:

```text
CSV/fixture → reader → contratto player.v1 → import service → repository SQLite
                                                   ↓
                    raw record / import run / errori / player e source mapping canonici
                                                   ↓
                                     query CLI → scoring → pricing → CSV export
```

`api.py` espone anche una WSGI read-only minimale: `/health`, `/api/v1/import-runs`, `/api/v1/players` e `/api/v1/players/{id}`. Il contratto OpenAPI è `contracts/openapi/analytics-read-api.v1.json`.

Le funzioni di dominio non richiedono rete. `CanonicalRepository` è l'unico confine SQL dell'import e le migrazioni sono in `services/analytics/migrations/`; SQLite è usato per sviluppo/test isolati. Il prototipo `scraper/` rimane un adapter opzionale e deve attraversare lo stesso normalizzatore. PostgreSQL resta il backend di produzione pianificato: non è ancora implementato né dichiarato compatibile.
