import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'icons/*.png'],
      manifest: {
        name: 'FantaAnalytics',
        short_name: 'FantaAnalytics',
        description: "Analizza i giocatori della Serie A e prepara la tua asta.",
        start_url: '/players',
        display: 'standalone',
        orientation: 'portrait-primary',
        theme_color: '#101b34',
        background_color: '#f5f7fb',
        lang: 'it-IT',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icons/maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        navigateFallbackDenylist: [/^\/api\//],
        // API responses are intentionally not cached: stale player data is misleading.
        runtimeCaching: [],
      },
    }),
  ],
})
