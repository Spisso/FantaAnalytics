# Deployment

Il Compose locale avvia PostgreSQL 16 e il servizio analytics Gunicorn. Prima del traffico applicare esplicitamente Alembic:

```bash
docker compose build analytics
docker compose up -d postgres analytics
docker compose exec analytics alembic upgrade head
```

`/health` è liveness e risponde 200 finché il processo è vivo. `/ready` verifica connessione, schema canonico e revisione Alembic; il healthcheck del container usa `/ready`.

Per fermare senza perdere dati usare `docker compose stop`, oppure `docker compose down`: il volume nominato resta presente. Il reset distruttivo ed esplicito è `docker compose down -v`; rimuove il volume PostgreSQL e richiede una nuova migrazione/importazione.

La persistenza è stata verificata con `docker compose restart postgres`: readiness è tornata verde e gli 11 player demo erano ancora presenti. Questo Compose è un ambiente locale, non include TLS, gestione segreti o orchestrazione di produzione.
