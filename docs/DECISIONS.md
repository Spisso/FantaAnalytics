# Decisioni architetturali

- **ADR-001 — Evoluzione incrementale.** Il prototipo Python viene preservato dietro un nuovo package analytics; non si scaffolda Laravel/Vue finché non esiste una persistenza canonica verificabile.
- **ADR-002 — Offline first.** Fixture e CSV sono percorsi di prima classe. Il live scraping non blocca l'uso dell'applicazione.
- **ADR-003 — Baseline spiegabile.** Score e prezzi sono formule deterministiche versionate prima di ogni ML.
- **ADR-004 — Dati generati fuori da Git.** Database SQLite, output e dati raw sono ignorati; il dataset demo fittizio rimane versionato.
- **ADR-005 — Repository SQLite migrato.** In questa milestone SQLite è il backend locale/test, gestito da repository astratto e migrazioni SQL esplicite. Evita due implementazioni di dominio; PostgreSQL sarà introdotto dietro lo stesso confine quando API e ambiente d'integrazione saranno disponibili.
- **ADR-006 — Idempotenza file-first.** File checksum uguale per stessa fonte/stagione restituisce il run esistente. Con `--force`, il matching usa prima fonte+external ID, poi nome+nascita, poi nome+squadra; ambiguità non vengono fuse.
