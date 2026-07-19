<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <header class="site-header">
    <nav class="nav-shell" aria-label="Navigazione principale">
      <RouterLink class="brand" to="/">Fanta<span>Analytics</span></RouterLink>
      <div class="nav-links">
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/players">Giocatori</RouterLink>
      </div>
    </nav>
  </header>
  <main><RouterView /></main>
  <footer class="site-footer">Dati e pipeline Analytics · stagione 2026-27</footer>
</template>
