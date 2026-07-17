# Architettura

L'architettura target separa web Vue, API Laravel e analytics Python. La parte implementata oggi è il confine `services/analytics/fantaanalytics`:

```text
CSV/fixture → reader → contratto player.v1 → import service → repository SQLAlchemy
                                                   ↓
                    raw record / import run / errori / player e source mapping canonici
                                                   ↓
                                     query CLI → scoring → pricing → CSV export
```

`api.py` espone anche una WSGI read-only minimale: `/health`, `/ready`, `/api/v1/import-runs`, `/api/v1/players` e `/api/v1/players/{id}`. `/health` non dipende dal database; `/ready` verifica connessione e schema migrato. Il contratto OpenAPI è `contracts/openapi/analytics-read-api.v1.json`.

Le funzioni di dominio non richiedono rete. `CanonicalRepository` è l'unico confine SQL dell'import: usa SQLAlchemy per SQLite e PostgreSQL. Le migrazioni SQL storiche restano per il workflow SQLite; Alembic gestisce lo schema portabile PostgreSQL. Il prototipo `scraper/` rimane un adapter opzionale e deve attraversare lo stesso normalizzatore.
