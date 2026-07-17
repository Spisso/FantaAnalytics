# FantaAnalytics

FantaAnalytics è una piattaforma in italiano per analizzare giocatori e preparare un'asta di fantacalcio. Il repository è in evoluzione verso API Laravel, web Vue e analytics Python; oggi include un vertical slice offline, testato e utilizzabile.

## Cosa funziona ora

- import di CSV UTF-8 con validazione riga per riga;
- normalizzazione di nomi, date, ruoli e valori Transfermarkt italiani;
- Fanta Score deterministico, per ruolo e spiegabile in italiano;
- stima prezzi coerente con budget e quote ruolo configurabili;
- dataset demo fittizio ed export CSV;
- migrazioni SQLite, import run, raw record, source mapping e query canonica dei player;
- API WSGI di sola lettura con health, player e import run, coperta da OpenAPI;
- scraper Transfermarkt storico con fallback CSV (non necessario né verificato live).

Le proiezioni e i prezzi sono supporto decisionale, non garanzie; dati e disponibilità dei giocatori possono cambiare.

## Avvio rapido

Richiede Python 3.9+ (3.11+ consigliato) e `make`.

```bash
make bootstrap
make test
make db-upgrade
make import-sample
make list-players
make seed-demo
```

Il risultato è `data/exports/demo_player_scores.csv`. Per usare un ambiente già esistente senza installare strumenti aggiuntivi:

```bash
venv/bin/python -m unittest discover -s tests -v
venv/bin/python -m services.analytics.fantaanalytics.cli score data/samples/demo_players.csv data/exports/demo_player_scores.csv
```

## Import canonico

```bash
make db-upgrade
make import-sample
make list-players
```

L'import conserva ogni riga raw, errori strutturati e provenienza. A parità di fonte, stagione e checksum del file, un re-import è ignorato; `--force` riesegue il matching e aggiorna solo i campi cambiati. Il backend locale è SQLite e la destinazione PostgreSQL non è ancora implementata.

## Architettura

```text
CSV / fixture → contratto → import run + repository SQLite → query CLI
                                           ↓
                              score → prezzo → export
                                           ↓
                         futura API Laravel/PostgreSQL ↔ futura UI Vue
```

Vedi [ARCHITECTURE.md](docs/ARCHITECTURE.md) e lo stato reale in [PROGRESS.md](docs/PROGRESS.md).

## Dati

`data/samples/demo_players.csv` contiene dati fittizi, riproducibili e versionati. I dati raw, gli export e i database locali non vengono versionati. Per le fonti esterne, rispettare licenze, termini e limiti di accesso: nessun meccanismo anti-bot deve essere aggirato.

## Sviluppo

```bash
make test
make lint
make format
```

La documentazione tecnica e le decisioni sono in [docs/](docs/). Non esiste ancora una UI, un container Docker o un deployment supportato; sono riportati in modo esplicito nel piano, non simulati come pronti.
