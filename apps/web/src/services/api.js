const baseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081/api/v1').replace(/\/$/, '');
async function request(path) {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 8000);
    try {
        const response = await fetch(`${baseUrl}${path}`, {
            headers: { Accept: 'application/json' },
            signal: controller.signal,
        });
        const body = await response.json().catch(() => null);
        if (!response.ok || !body) {
            throw new Error('Impossibile caricare i dati. Verifica che lo stack backend sia avviato.');
        }
        return body;
    }
    catch (error) {
        if (error instanceof DOMException && error.name === 'AbortError') {
            throw new Error('La richiesta ha impiegato troppo tempo. Riprova tra poco.');
        }
        throw error instanceof Error ? error : new Error('Impossibile caricare i dati.');
    }
    finally {
        window.clearTimeout(timer);
    }
}
export const api = {
    teams: (season) => request(`/teams?season=${encodeURIComponent(season)}`),
    players: (season, team) => request(`/players?season=${encodeURIComponent(season)}&team=${encodeURIComponent(team)}&limit=200`),
};
