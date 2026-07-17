# Decisioni architetturali

- **ADR-001 — Evoluzione incrementale.** Il prototipo Python viene preservato dietro un nuovo package analytics; non si scaffolda Laravel/Vue finché non esiste una persistenza canonica verificabile.
- **ADR-002 — Offline first.** Fixture e CSV sono percorsi di prima classe. Il live scraping non blocca l'uso dell'applicazione.
- **ADR-003 — Baseline spiegabile.** Score e prezzi sono formule deterministiche versionate prima di ogni ML.
- **ADR-004 — Dati generati fuori da Git.** Database SQLite, output e dati raw sono ignorati; il dataset demo fittizio rimane versionato.
- **ADR-005 — Repository SQLite migrato.** In questa milestone SQLite è il backend locale/test, gestito da repository astratto e migrazioni SQL esplicite. Evita due implementazioni di dominio; PostgreSQL sarà introdotto dietro lo stesso confine quando API e ambiente d'integrazione saranno disponibili.
- **ADR-006 — Idempotenza file-first.** File checksum uguale per stessa fonte/stagione restituisce il run esistente. Con `--force`, il matching usa prima fonte+external ID, poi nome+nascita, poi nome+squadra; ambiguità non vengono fuse.
- **ADR-007 — Configurazione database unica.** `DATABASE_URL` letto da `Settings` ha priorità; in assenza della variabile si usa SQLite locale. Alembic sovrascrive il fallback di `alembic.ini`, evitando che il container apra erroneamente un file SQLite.
- **ADR-008 — Liveness separata dalla readiness.** `/health` segnala solo il processo; `/ready` verifica connessione, schema canonico e revisione applicata. Il healthcheck Compose usa readiness.
- **ADR-009 — Ownership per servizio.** Analytics possiede dati e calcoli dei giocatori; Laravel possiede il futuro dominio utente/fantacalcio. Nessuna query SQL attraversa il confine: l'integrazione usa API HTTP e OpenAPI versionato.
- **ADR-010 — Laravel come gateway pubblico.** Laravel 12 espone `/api/v1`, valida una allowlist di filtri e usa un client HTTP centralizzato con timeout, retry limitato, DTO ed errori stabili.
- **ADR-011 — Porta Laravel locale 8081.** La porta 8080 era già occupata da un servizio esterno durante la verifica; il container ascolta 8080 internamente ed è pubblicato su 8081 senza alterare container non appartenenti al progetto.
