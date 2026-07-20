<script setup lang="ts">
import { useRegisterSW } from 'virtual:pwa-register/vue'

const { offlineReady, needRefresh, updateServiceWorker } = useRegisterSW()

function closePrompt() {
  offlineReady.value = false
  needRefresh.value = false
}
</script>

<template>
  <aside v-if="offlineReady || needRefresh" class="pwa-prompt" role="status" aria-live="polite">
    <p v-if="offlineReady">App pronta per l'uso offline</p>
    <p v-else>Nuova versione disponibile</p>
    <div class="pwa-prompt-actions">
      <button v-if="needRefresh" class="button button-primary" type="button" @click="updateServiceWorker(true)">Aggiorna</button>
      <button class="pwa-dismiss" type="button" aria-label="Chiudi" @click="closePrompt">×</button>
    </div>
  </aside>
</template>

<style scoped>
.pwa-prompt {
  position: fixed;
  right: max(16px, env(safe-area-inset-right));
  bottom: max(16px, env(safe-area-inset-bottom));
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 14px;
  max-width: min(420px, calc(100vw - 32px));
  padding: 12px 14px 12px 16px;
  border: 1px solid #dce3ed;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 10px 30px rgb(16 27 52 / 16%);
}
.pwa-prompt p { margin: 0; color: #172033; font-size: .88rem; font-weight: 700; }
.pwa-prompt-actions { display: flex; align-items: center; gap: 8px; margin-left: auto; }
.pwa-prompt .button { min-height: 40px; padding: 9px 13px; }
.pwa-dismiss { border: 0; background: transparent; color: #718097; font-size: 1.4rem; line-height: 1; cursor: pointer; }
@media (max-width: 480px) { .pwa-prompt { align-items: flex-start; } }
</style>
