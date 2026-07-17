# Sicurezza

- Non committare `.env`, credenziali, database locali, cache o dati raw.
- Limitare import futuri per dimensione, MIME, estensione e schema; neutralizzare formule CSV/XLSX in export.
- Non effettuare fetch arbitrari da URL forniti dall'utente.
- Le fonti live devono rispettare termini, rate limit e accesso autorizzato.
- Autenticazione, autorizzazione, CSRF/CORS e segreto tra API/analytics sono requisiti futuri e non sono ancora implementati.
