# Piano di implementazione

| Fase | Stato | Risultato verificabile |
|---|---|---|
| 0 — Audit e stabilizzazione | Completata | Audit, ignore sicuro, test caratterizzazione e comandi base |
| 1 — Fondazione monorepo | In corso | Servizio analytics installabile e vertical slice offline; API/web/compose restano da realizzare |
| 2 — Modello canonico | Da fare | Migrazioni PostgreSQL/Laravel, relazioni e seed |
| 3 — Ingestion | In corso | CSV normalizzato e fixture demo; adapter source completo da estendere |
| 4–5 — Import ed esplorazione | Da fare | API/UI e import transazionale |
| 6–7 — Score, proiezioni, prezzi | In corso | Baseline score/prezzo spiegabile; proiezioni e calibrazione restano da fare |
| 8–11 — Lega, asta, rosa, coach | Da fare | Flussi applicativi completi |
| 12 — Hardening | Da fare | CI, E2E, Docker e release readiness |

La prossima slice è l'adozione del contratto `player.v1` in un import run persistente, prima di introdurre una UI.
