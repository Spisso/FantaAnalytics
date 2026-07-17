# Motore d'asta

La baseline `LeagueConfig` usa 10 partecipanti, 1000 crediti, offerta minima 1 e slot 3P/8D/8C/6A. Ripartisce il budget totale tra P/D/C/A secondo quote configurabili 8/15/32/45 e produce intervallo consigliato, massimo e confidenza. Con un pool completo la distribuzione somma al budget di lega; con una shortlist usa solo la quota coperta, senza assegnare denaro a giocatori assenti.

L'implementazione non include ancora stato asta, riserva obbligatoria per slot residui, alternative o undo. I prezzi sono indicativi e richiedono un pool giocatori completo per una distribuzione realistica.
