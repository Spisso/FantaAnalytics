export interface Team {
  name: string
  player_count: number
}

export interface Player {
  id: number
  canonical_full_name: string
  effective_fantasy_role: string
  team: string
  season: string
  birth_date?: string | null
  nationality?: string | null
  source_role?: string | null
  market_value_eur?: number | null
  source_url?: string | null
}

const baseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081/api/v1').replace(/\/$/, '')

async function request<T>(path: string): Promise<T> {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), 8000)
  try {
    const response = await fetch(`${baseUrl}${path}`, {
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    })
    const body = await response.json().catch(() => null)
    if (!response.ok || !body) {
      throw new Error('Impossibile caricare i dati. Verifica che lo stack backend sia avviato.')
    }
    return body as T
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('La richiesta ha impiegato troppo tempo. Riprova tra poco.')
    }
    throw error instanceof Error ? error : new Error('Impossibile caricare i dati.')
  } finally {
    window.clearTimeout(timer)
  }
}

export const api = {
  teams: (season: string) => request<{ data: Team[]; count: number; season: string }>(`/teams?season=${encodeURIComponent(season)}`),
  players: (season: string, team: string) => request<{ data: Player[]; count: number }>(`/players?season=${encodeURIComponent(season)}&team=${encodeURIComponent(team)}&limit=200`),
}
