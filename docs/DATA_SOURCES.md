# Fonti dati

Il percorso supportato e verificato è il CSV UTF-8 dell'utente o il fixture fittizio in `data/samples/demo_players.csv`. Ogni riga viene conservata in `raw_records` con checksum SHA-256 di una serializzazione JSON canonica; il checksum del file è calcolato sui byte originali.

Il ciclo import è: lettura → normalizzazione → `player.v1` → matching → upsert → import run/errori. Il default è best-effort: righe invalide vengono conservate e diagnosticate, quelle valide proseguono. `--strict` conserva raw/errori ma non persiste i player di un file con errori. Stesso checksum/fonte/stagione non crea un nuovo import; `--force` abilita la rivalutazione.

Transfermarkt è soltanto un adapter sperimentale esistente. Usarlo esclusivamente quando termini, accesso e limiti lo consentono; nessun CAPTCHA, controllo d'accesso o rate limit va aggirato. Le integrazioni live non sono state verificate in questo repository.
