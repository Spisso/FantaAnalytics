# FantaAnalytics

Piattaforma italiana di supporto decisionale per il fantacalcio Serie A. La base attuale include import canonico SQLite con provenienza, oltre a normalizzazione, Fanta Score spiegabile e stime di prezzo offline.

## Mappa

- `services/analytics/fantaanalytics/`: calcoli, contratti, import service, repository e CLI.
- `apps/api/`: gateway pubblico Laravel; comunica con analytics soltanto via HTTP.
- `services/analytics/migrations/`: migrazioni SQL SQLite esplicite; non creare schema implicitamente nell'import.
- `scraper/`, `services/`, `models/`: compatibilità con il prototipo Transfermarkt/SQLite esistente.
- `data/samples/`: input demo versionati; `data/raw/` e `data/exports/`: locali e ignorati.
- `contracts/`: contratti JSON versionati; `tests/`: test unitari.
- `docs/`: stato, scelte e guida operativa.

## Comandi

```bash
make bootstrap
make test
make lint
make db-upgrade
make import-sample
make list-players
make seed-demo
make api-test
make api-lint
make stack-up
make stack-test
```

Con l'ambiente storico locale: `venv/bin/python -m unittest discover -s tests -v`.

## Regole

- Migrazioni future devono essere reversibili e verificate da database vuoto.
- Gli import sono best-effort per default; `--strict` conserva diagnostica/raw record e non persiste player del file con errori.
- Repository e dominio restano separati dalle query SQL; PostgreSQL è il target successivo, SQLite è il backend locale e di test corrente.
- Laravel possiede dati applicativi (utenti, leghe, aste, rose, watchlist e note) e non interroga direttamente le tabelle possedute da analytics.
- I contratti HTTP versionati in `contracts/` sono il solo confine Laravel/Python.
- Gli adapter dati separano fetch, salvataggio raw, parsing, normalizzazione ed export; mai aggirare CAPTCHA o controlli d'accesso.
- Non versionare segreti, ambienti virtuali, database locali, cache o dataset raw voluminosi.
- Aggiornare `docs/PROGRESS.md` e i documenti interessati dopo ogni milestone.

Vedi [architettura](docs/ARCHITECTURE.md), [sviluppo](docs/DEVELOPMENT.md), [fonti dati](docs/DATA_SOURCES.md) e [sicurezza](docs/SECURITY.md).
