import type { Player } from './services/api'

const roleOrder: Record<string, number> = { P: 0, D: 1, C: 2, A: 3 }
const surnameParticles = new Set([
  'da', 'dal', 'dalla', 'de', 'degli', 'dei', 'del', 'della', 'di', 'do', 'dos', 'du',
  'la', 'le', 'van', 'von',
])
const collator = new Intl.Collator('it-IT', { sensitivity: 'base', usage: 'sort' })

export function extractPlayerNameParts(fullName: string): { givenName: string; surname: string } {
  const words = fullName.trim().split(/\s+/).filter(Boolean)
  if (words.length === 0) return { givenName: '', surname: '' }
  if (words.length === 1) return { givenName: words[0], surname: '' }

  let surnameStart = words.length - 1
  if (surnameStart > 1 && surnameParticles.has(words[surnameStart - 1].toLocaleLowerCase('it-IT'))) {
    surnameStart -= 1
  }

  return {
    givenName: words.slice(0, surnameStart).join(' '),
    surname: words.slice(surnameStart).join(' '),
  }
}

export function sortPlayersByRoleSurnameAndName(players: Player[]): Player[] {
  return [...players].sort((left, right) => {
    const leftRole = roleOrder[left.effective_fantasy_role?.toUpperCase()] ?? 4
    const rightRole = roleOrder[right.effective_fantasy_role?.toUpperCase()] ?? 4
    if (leftRole !== rightRole) return leftRole - rightRole

    const leftName = extractPlayerNameParts(left.canonical_full_name)
    const rightName = extractPlayerNameParts(right.canonical_full_name)
    const leftSurname = leftName.surname || leftName.givenName
    const rightSurname = rightName.surname || rightName.givenName
    const surnameComparison = collator.compare(leftSurname, rightSurname)
    if (surnameComparison !== 0) return surnameComparison

    const givenNameComparison = collator.compare(leftName.givenName, rightName.givenName)
    if (givenNameComparison !== 0) return givenNameComparison

    return collator.compare(left.canonical_full_name, right.canonical_full_name)
  })
}
