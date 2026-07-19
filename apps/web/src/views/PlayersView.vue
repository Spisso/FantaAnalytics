<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api, type Player, type Team } from '../services/api'

const season = '2026-27'
const teams = ref<Team[]>([])
const selectedTeam = ref('')
const players = ref<Player[]>([])
const search = ref('')
const loadingTeams = ref(true)
const loadingPlayers = ref(false)
const error = ref('')
const playerError = ref('')

const visiblePlayers = computed(() => {
  const needle = search.value.trim().toLocaleLowerCase('it-IT')
  return needle ? players.value.filter((player) => player.canonical_full_name.toLocaleLowerCase('it-IT').includes(needle)) : players.value
})

function ageFromBirthDate(date?: string | null) {
  if (!date) return '—'
  const birth = new Date(`${date}T00:00:00`)
  if (Number.isNaN(birth.getTime())) return '—'
  const now = new Date()
  let age = now.getFullYear() - birth.getFullYear()
  if (now < new Date(now.getFullYear(), birth.getMonth(), birth.getDate())) age -= 1
  return age
}

function formatDate(date?: string | null) {
  if (!date) return '—'
  const parsed = new Date(`${date}T00:00:00`)
  return Number.isNaN(parsed.getTime()) ? date : parsed.toLocaleDateString('it-IT')
}

async function loadTeams() {
  loadingTeams.value = true; error.value = ''
  try {
    teams.value = (await api.teams(season)).data
    selectedTeam.value = teams.value[0]?.name || ''
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Impossibile caricare i dati.'
  } finally { loadingTeams.value = false }
}

async function loadPlayers() {
  if (!selectedTeam.value) { players.value = []; return }
  loadingPlayers.value = true; playerError.value = ''
  try { players.value = (await api.players(season, selectedTeam.value)).data }
  catch (reason) { playerError.value = reason instanceof Error ? reason.message : 'Impossibile caricare i giocatori.' }
  finally { loadingPlayers.value = false }
}

watch(selectedTeam, loadPlayers)
onMounted(loadTeams)
</script>

<template>
  <section class="page-shell players-page">
    <div class="section-heading"><div><p class="eyebrow">DATABASE CANONICO</p><h1>Giocatori Serie A</h1><p>Stagione {{ season }} · seleziona una squadra per esplorare la rosa.</p></div><span class="result-pill">{{ visiblePlayers.length }} giocatori</span></div>
    <div v-if="loadingTeams" class="state-message">Caricamento squadre...</div>
    <div v-else-if="error" class="state-message error-state"><p>{{ error }}</p><button class="button button-muted" @click="loadTeams">Riprova</button></div>
    <template v-else>
      <div class="team-tabs" role="tablist" aria-label="Squadre">
        <button v-for="team in teams" :key="team.name" :class="['team-tab', { active: selectedTeam === team.name }]" role="tab" :aria-selected="selectedTeam === team.name" @click="selectedTeam = team.name">{{ team.name }} <small>{{ team.player_count }}</small></button>
      </div>
      <div class="toolbar"><label class="search-box"><span>⌕</span><input v-model="search" type="search" placeholder="Cerca per nome..." aria-label="Cerca giocatore" /></label><span class="selected-team">{{ selectedTeam }}</span></div>
      <div v-if="loadingPlayers" class="state-message">Caricamento giocatori...</div>
      <div v-else-if="playerError" class="state-message error-state"><p>{{ playerError }}</p><button class="button button-muted" @click="loadPlayers">Riprova</button></div>
      <div v-else-if="!visiblePlayers.length" class="state-message">Nessun giocatore trovato per questa ricerca.</div>
      <div v-else class="player-table-wrap"><table class="player-table"><thead><tr><th>Giocatore</th><th>Ruolo</th><th>Età</th><th>Nazionalità</th><th>Data di nascita</th></tr></thead><tbody><tr v-for="player in visiblePlayers" :key="player.id"><td><strong>{{ player.canonical_full_name }}</strong><small>{{ player.team }}</small></td><td><span class="role-badge">{{ player.effective_fantasy_role }}</span><small v-if="player.source_role">{{ player.source_role }}</small></td><td>{{ ageFromBirthDate(player.birth_date) }}</td><td>{{ player.nationality || '—' }}</td><td>{{ formatDate(player.birth_date) }}</td></tr></tbody></table></div>
    </template>
    <!-- TODO: aggiungere serie_a_since o seasons_in_serie_a tramite una fonte storica. -->
  </section>
</template>
