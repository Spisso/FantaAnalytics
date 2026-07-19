<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api, type Team } from '../services/api'

const season = '2026-27'
const teams = ref<Team[]>([])
const loading = ref(true)
const error = ref('')

async function loadSummary() {
  loading.value = true
  error.value = ''
  try {
    teams.value = (await api.teams(season)).data
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Impossibile caricare i dati.'
  } finally {
    loading.value = false
  }
}

onMounted(loadSummary)
</script>

<template>
  <section class="hero page-shell">
    <div class="hero-copy">
      <p class="eyebrow">SERIE A · {{ season }}</p>
      <h1>Fanta<span>Analytics</span></h1>
      <p class="hero-text">Analizza i giocatori della Serie A e prepara la tua prossima asta.</p>
      <RouterLink class="button button-primary" to="/players">Esplora i giocatori <span>→</span></RouterLink>
    </div>
    <div class="hero-mark" aria-hidden="true"><span>FA</span><i></i><i></i><i></i></div>
  </section>

  <section class="stats page-shell" aria-label="Statistiche stagione">
    <div class="stat-card"><span>Stagione selezionata</span><strong>{{ season }}</strong></div>
    <div class="stat-card"><span>Squadre</span><strong v-if="!loading">{{ teams.length }}</strong><strong v-else>—</strong></div>
    <div class="stat-card"><span>Giocatori disponibili</span><strong v-if="!loading">{{ teams.reduce((total, team) => total + team.player_count, 0) }}</strong><strong v-else>—</strong></div>
  </section>

  <section v-if="loading" class="page-shell state-message">Caricamento squadre...</section>
  <section v-else-if="error" class="page-shell state-message error-state">
    <p>{{ error }}</p><button class="button button-muted" @click="loadSummary">Riprova</button>
  </section>
  <section class="features page-shell">
    <article><span class="feature-number">01</span><h2>Esplora per squadra</h2><p>Scorri le rose della Serie A con un solo gesto.</p></article>
    <article><span class="feature-number">02</span><h2>Confronta i profili</h2><p>Ruolo, età e nazionalità per orientare le tue scelte.</p></article>
    <article><span class="feature-number">03</span><h2>Dati aggiornabili</h2><p>Una pipeline Analytics pronta a seguire la stagione.</p></article>
  </section>
</template>
