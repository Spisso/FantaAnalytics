# Deployment

Non esiste ancora un deployment supportato: API, web, PostgreSQL e Docker Compose sono milestone successive. Per ora il servizio analytics è un processo offline e senza segreti. Un futuro deployment dovrà usare container separati, PostgreSQL, variabili ambiente segrete esterne a Git, health/readiness checks e migrazioni reversibili.
