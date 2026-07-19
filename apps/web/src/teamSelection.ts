import type { Team } from './services/api'

const preferredTeamName = 'Napoli'

export function orderTeamsForPlayers(teams: Team[]): Team[] {
  const ordered = [...teams].sort((left, right) => left.name.localeCompare(right.name, 'it-IT'))
  const preferredIndex = ordered.findIndex((team) => team.name === preferredTeamName)

  if (preferredIndex > 0) {
    const [preferred] = ordered.splice(preferredIndex, 1)
    ordered.unshift(preferred)
  }

  return ordered
}

export function selectInitialTeam(teams: Team[]): string {
  return orderTeamsForPlayers(teams)[0]?.name || ''
}
