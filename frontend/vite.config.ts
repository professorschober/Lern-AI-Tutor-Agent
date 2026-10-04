import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [react(), VitePWA({
    registerType: 'prompt',
    includeAssets: ['icon.svg', 'icon-192.png', 'icon-512.png'],
    manifest: {name: 'Lernraum · SQL Tutor', short_name: 'Lernraum', description: 'Dein lokaler SQL-Lernarbeitsplatz',
      lang: 'de', start_url: '/', display: 'standalone', background_color: '#f6f5ef', theme_color: '#164c42',
      icons: [{src: '/icon-192.png', sizes:'192x192', type:'image/png'}, {src:'/icon-512.png', sizes:'512x512', type:'image/png'}, {src:'/icon.svg',sizes:'any',type:'image/svg+xml'}]},
    workbox: {globPatterns: ['**/*.{js,css,html,svg,png,woff2}'], navigateFallbackDenylist: [/^\/api/], runtimeCaching: []}
  })],
  server: {host: '127.0.0.1', port: 5173, strictPort:true, proxy: {'/api': process.env.TUTOR_API_TARGET || 'http://127.0.0.1:8000'}}
})
