# Sviluppo

Prerequisito: Python 3.9+ (3.11+ consigliato). Eseguire:

```bash
make bootstrap
make test
make lint
make seed-demo
```

`make seed-demo` crea `data/exports/demo_player_scores.csv`. Non sovrascrive `.env`; le variabili di esempio sono in `.env.example`. Il vecchio `venv/` non è gestito dal Makefile: usare `.venv/` creato da bootstrap.

Persistenza e CLI locale:

```bash
make db-upgrade
make import-sample
make list-players
make db-reset-test
```

`db-reset-test` accetta solo un file con suffisso `.test.db`; non punta al database operativo. La migrazione può essere annullata con `make db-downgrade`. I comandi `db-upgrade`, `import-sample`, `list-players`, `seed-demo`, `test` e `lint` sono stati eseguiti con il `venv/` locale in questa milestone. `make bootstrap` è il percorso di installazione documentato ma non è stato eseguito qui.

Ruff verifica errori e import; `E501` è escluso perché il repository conserva fixture HTML, payload CSV e query SQL leggibili che superano la soglia tipografica senza incidere sul comportamento. Le regole di upgrade automatico sono escluse per mantenere la compatibilità con Python 3.9.
