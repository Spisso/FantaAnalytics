# Modello dati

Il contratto `player.v1` rappresenta l'ingresso normalizzato: versione, fonte, ID esterno facoltativo, identità, nascita ISO, nazionalità, squadra, ruoli, piede, altezza, valore e stagione. Il validator locale applica il sottoinsieme necessario del JSON Schema e rifiuta proprietà non dichiarate. Esempi valido/non valido sono in `contracts/examples/`.

La migrazione `001_canonical_imports` crea `players`, `football_teams`, `data_sources`, `player_source_mappings`, `data_import_runs`, `data_import_errors` e `raw_records`, con chiavi esterne, indici e vincolo univoco su `data_source_id + external_source_id`. `birth_date` è la fonte di verità; `calculate_age(..., reference_date)` deriva l'età senza persisterla.

Statistiche stagionali, valori mercato storicizzati, score e prezzi persistiti sono ancora successive estensioni del modello.
