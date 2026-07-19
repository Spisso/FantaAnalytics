# FantaAnalytics

FantaAnalytics è una piattaforma in italiano per analizzare giocatori e preparare un'asta di fantacalcio. Il repository è in evoluzione verso API Laravel, web Vue e analytics Python; oggi include un vertical slice offline, testato e utilizzabile.

## Cosa funziona ora

- import di CSV UTF-8 con validazione riga per riga;
- normalizzazione di nomi, date, ruoli e valori Transfermarkt italiani;
- Fanta Score deterministico, per ruolo e spiegabile in italiano;
- stima prezzi coerente con budget e quote ruolo configurabili;
- dataset demo fittizio ed export CSV;
- repository canonico SQLAlchemy compatibile con SQLite e PostgreSQL;
- migrazioni Alembic PostgreSQL, import run, raw record, source mapping e query player;
- API WSGI di sola lettura con liveness, readiness, player e import run, coperta da OpenAPI;
- gateway pubblico Laravel 12 con client Analytics tipizzato, validazione ed error handling;
- stack Docker PostgreSQL → Analytics → Laravel;
- adapter Transfermarkt responsabile con export CSV canonico e import SQLAlchemy (non verificato live).

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

L'import conserva ogni riga raw, errori strutturati e provenienza. A parità di fonte, stagione e checksum del file, un re-import è ignorato; `--force` riesegue il matching e aggiorna solo i campi cambiati. SQLite resta il default locale; `DATABASE_URL` seleziona PostgreSQL per API, CLI, repository e Alembic.

### Import demo e Serie A

L'import demo offline popola per default `data/processed/fantaanalytics.db`:

```bash
make import-sample
make list-players
```

L'adapter Transfermarkt usa lo stesso database canonico e può conservare il CSV normalizzato:

```bash
make import-serie-a
python -m services.analytics.fantaanalytics.cli scrape-transfermarkt \
  --season 2026-27 --database data/processed/fantaanalytics.db \
  --output data/raw/transfermarkt_players.csv --pause 1 --retries 2
python -m services.analytics.fantaanalytics.cli list-players \
  --database data/processed/fantaanalytics.db --season 2026-27
```

Per un import riprendibile per squadra usa il checkpoint versionato (salvato di
default in `data/raw`, ignorato da Git):

```bash
python -m services.analytics.fantaanalytics.cli scrape-transfermarkt \
  --season 2026-27 --database data/processed/fantaanalytics.db \
  --resume --checkpoint data/raw/transfermarkt_2026-27_checkpoint.json \
  --continue-on-error
```

`--club` seleziona una squadra, `--start-club` riparte da una squadra inclusa,
`--retry-failed` ritenta esclusivamente le squadre fallite e `--max-clubs` /
`--max-players` limitano una sessione. Ogni squadra completata viene registrata
nel checkpoint con external ID, roster, contatori e timestamp; i fallimenti
conservano errore e numero di tentativi. La scrittura del checkpoint è atomica.
`--dry-run` non crea né aggiorna database o checkpoint; con `--output` produce
solo il CSV della sessione.

Esempi di esecuzione mirata:

```bash
# una sola squadra, identificata da nome o external ID
python -m services.analytics.fantaanalytics.cli scrape-transfermarkt \
  --season 2026-27 --database data/processed/fantaanalytics.db --club inter

# ritenta esclusivamente le squadre fallite
python -m services.analytics.fantaanalytics.cli scrape-transfermarkt \
  --season 2026-27 --database data/processed/fantaanalytics.db \
  --resume --retry-failed --continue-on-error

# preview senza persistenza, con CSV esplicito
python -m services.analytics.fantaanalytics.cli scrape-transfermarkt \
  --season 2026-27 --database /tmp/unused.db --max-clubs 1 \
  --max-players 3 --dry-run --output data/raw/transfermarkt_preview.csv
```

Con Docker, lo stesso target esegue migrazione e import dentro il container Analytics:

```bash
make stack-up
make import-serie-a IMPORT_RUNTIME=docker
```

I giocatori sono consultabili su `http://localhost:8000/api/v1/players?season=2026-27`
e tramite Laravel su `http://localhost:8081/api/v1/players?season=2026-27`.

### Interfaccia web

La prima interfaccia Vue è in `apps/web` e usa Laravel come gateway HTTP:

```bash
make web-install
make web-dev
```

Apri `http://localhost:5173/` per la landing oppure `/players` per esplorare le
rose. `VITE_API_BASE_URL` configura il gateway (default:
`http://localhost:8081/api/v1`). Le squadre vengono caricate da `/api/v1/teams`
e i giocatori vengono richiesti con il filtro `team`, senza scaricare l'intero
campionato nel browser. Per una verifica di produzione locale usa `make web-build`.

Per avviare il frontend da un altro dispositivo della rete locale, sostituisci
`<IP_DEL_MAC>` con l'indirizzo IP corrente del Mac:

```bash
export COMPOSE_PROJECT_NAME=fantaanalytics_real
export POSTGRES_PORT=55432
export ANALYTICS_API_PORT=18000
export API_PORT=18081
export CORS_ALLOWED_ORIGINS="http://localhost:5173,http://<IP_DEL_MAC>:5173"
export API_CACHE_STORE=file
docker compose up -d --force-recreate --no-deps api

cd apps/web
printf 'VITE_API_BASE_URL=http://<IP_DEL_MAC>:18081/api/v1\n' > .env.local
npm run dev -- --host 0.0.0.0 --port 5173 --strictPort
```

Il file `apps/web/.env.local` è locale e ignorato da Git. La cache API usa il
filesystem e non richiede la tabella PostgreSQL `cache`.

Nel CSV e nel contratto canonico `profile_url` è esposto come `source_url`. Viene
persistito in `player_source_mappings` insieme all'external ID, mentre non è duplicato
nella tabella `players` e non è incluso oggi nella risposta della read API. Il valore di
mercato viene normalizzato in `market_value_eur` e validato nel payload `player.v1`; la
baseline SQL corrente ne conserva il valore sorgente nei raw record, ma non mantiene
ancora una serie storica di valutazioni dedicata.

## Architettura

```text
CSV / fixture → contratto → import run + repository SQLAlchemy → query CLI/API
                                           ↓
                              score → prezzo → export
                                           ↓
                              SQLite locale / PostgreSQL Docker
```

Vedi [ARCHITECTURE.md](docs/ARCHITECTURE.md) e lo stato reale in [PROGRESS.md](docs/PROGRESS.md).

## Dati

`data/samples/demo_players.csv` contiene dati fittizi, riproducibili e versionati. I dati raw, gli export e i database locali non vengono versionati. Per le fonti esterne, rispettare licenze, termini e limiti di accesso: nessun meccanismo anti-bot deve essere aggirato. L'adapter deduplica i profili prima del fetch, usa pause configurabili e retry limitati; CAPTCHA, blocchi o modifiche HTML causano un errore leggibile. Verificare sempre che l'uso sia consentito dai termini della fonte.

## Sviluppo

```bash
make test
make lint
make format
```

Avvio dello stack applicativo:

```bash
make stack-up
make api-health
make api-seed-demo
```

`make stack-up` inizializza in ordine PostgreSQL e Analytics, applica Alembic,
avvia Laravel e applica le migrazioni del database applicativo. Il seed resta
un'operazione separata e idempotente.

Laravel è pubblicato su `http://localhost:8081` perché la porta 8080 può essere già occupata localmente. `ANALYTICS_BASE_URL=http://analytics:8000` è usato solo sulla rete Docker. Vue non è ancora iniziato.

Il dominio Laravel include utenti, leghe, regole, configurazione posti e partecipanti. Le API lega richiedono temporaneamente `X-User-ID`; è un meccanismo di sviluppo, non autenticazione di produzione. PostgreSQL ospita due database isolati: `fantaanalytics` per Python e `fantaanalytics_app` per Laravel.
