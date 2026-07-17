# Deployment

Il Compose locale avvia PostgreSQL 16, Analytics Gunicorn e Laravel 12. Prima del traffico applicare esplicitamente Alembic:

```bash
docker compose build
docker compose up -d postgres analytics api
docker compose exec analytics alembic upgrade head
```

`/health` è liveness e risponde 200 finché il processo è vivo. `/ready` verifica connessione, schema canonico e revisione Alembic; il healthcheck del container usa `/ready`.

Per fermare senza perdere dati usare `docker compose stop`, oppure `docker compose down`: il volume nominato resta presente. Il reset distruttivo ed esplicito è `docker compose down -v`; rimuove il volume PostgreSQL e richiede una nuova migrazione/importazione.

La persistenza è stata verificata con `docker compose restart postgres`: readiness è tornata verde e gli 11 player demo erano ancora presenti. Questo Compose è un ambiente locale, non include TLS, gestione segreti o orchestrazione di produzione.

Laravel è raggiungibile su `http://localhost:8081`; dentro Docker usa `ANALYTICS_BASE_URL=http://analytics:8000`. Verifica rapida:

```bash
make stack-up
make stack-test
```

Troubleshooting: se `/api/v1/analytics/status` mostra `alive=false`, controllare `docker compose ps` e `make api-logs`. Fermando Analytics, `/api/v1/health` resta 200, lo status diventa degradato e i player restituiscono un 503 strutturato. `make stack-down` conserva il volume PostgreSQL.
