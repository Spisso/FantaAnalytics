# Sicurezza

- Non committare `.env`, credenziali, database locali, cache o dati raw.
- Limitare import futuri per dimensione, MIME, estensione e schema; neutralizzare formule CSV/XLSX in export.
- Non effettuare fetch arbitrari da URL forniti dall'utente.
- Le fonti live devono rispettare termini, rate limit e accesso autorizzato.
- Autenticazione, autorizzazione, CSRF/CORS e segreto tra API/analytics sono requisiti futuri e non sono ancora implementati.
- Laravel non accede alle tabelle Analytics: il confine HTTP riduce accoppiamento e privilegi condivisi.
- Gli errori upstream espongono solo codice, messaggio italiano e request ID; URL interni, stack trace e credenziali non sono restituiti.
- `ANALYTICS_BASE_URL` è configurazione controllata dall'operatore, mai input utente; i filtri proxy sono validati tramite allowlist.
- La `APP_KEY` di default nel Compose è esclusivamente locale e deve essere sostituita con un secret esterno in ambienti reali.
- `X-User-ID` non è autenticazione sicura: è limitato al milestone di sviluppo e deve essere rimosso prima di esporre le API.
- Le password sono hashate dal cast Eloquent e nascoste dalla serializzazione; il seed usa solo credenziali fittizie.
- I due database PostgreSQL condividono oggi l'utente locale del container; la produzione dovrà usare ruoli distinti con privilegi minimi.
