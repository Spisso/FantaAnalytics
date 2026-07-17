# Repository audit — 2026-07-17

## Stato Git

- Branch: `main`, allineato a `origin/main` al commit `75a3eec` durante l'audit.
- Remote: `origin https://github.com/Spisso/FantaAnalytics.git` (fetch/push).
- Working tree iniziale: pulito; nessun commit locale avanti rispetto al remote.
- Il database locale `database/transfermarkt.db` era tracciato; è un artefatto generato da rimuovere dall'indice senza cancellarlo localmente.
- `venv/` è ignorato e non tracciato.

## Architettura esistente e codice preservato

Il checkout contiene un prototipo Python: `main.py` coordina `TransfermarktScraper`, fallback CSV, `CsvService` e `DatabaseService` SQLite. `Player.get_age()` deriva correttamente l'età dalla data di nascita. Il metodo `TransfermarktScraper.get_players()` esiste: l'errore storico di attributo non è riproducibile.

Sono stati preservati tutti i moduli e i test originari. Il nuovo servizio `services/analytics/` è un confine indipendente e non rompe le importazioni esistenti.

## Dipendenze e comandi

- Runtime rilevato: Python 3.9.6; PHP 8.4.14 è disponibile, Node non è rilevato.
- Dipendenze runtime: Requests, BeautifulSoup, lxml, pandas; il virtualenv storico non contiene pytest.
- Test originari verificati con `venv/bin/python -m unittest discover -s tests -v`: 5/5 superati prima delle modifiche.
- Il comando standard è ora `make test`; `make bootstrap` crea un `.venv` separato e installa anche gli strumenti di qualità.

## Rischi e difetti osservati

- Il live scraper dipende dalla struttura HTML e da accesso consentito a Transfermarkt; non deve essere il percorso necessario per l'app.
- `main.py` riduce i record al sottoinsieme di cinque campi e SQLite è un archivio locale non canonico; nessuna provenienza/import run è ancora persistita.
- È emesso un warning LibreSSL da urllib3 sul Python di sistema: i test passano, ma un ambiente Python moderno è consigliato.
- README era vuoto; mancavano contratti, documentazione, tool di lint e dati demo versionati.

## Migrazione sicura

1. Conservare il prototipo come adapter di compatibilità e usare fixture/CSV per lo sviluppo offline.
2. Consolidare la logica in `services/analytics`, con contratti versionati e test puri.
3. Aggiungere in seguito API Laravel, PostgreSQL e Vue come confini nuovi, senza rimuovere i percorsi di import manuali.
4. Migrare il database SQLite solo tramite export/import e migrazioni PostgreSQL reversibili.
