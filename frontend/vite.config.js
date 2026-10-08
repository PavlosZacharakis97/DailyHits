import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Same-origin API: the browser calls /api on the Vite server, which proxies to Django.
    // Keep the browser's Host header so Django sees the same origin as the browser.
    proxy: {
      '/api': {
        target: process.env.API_PROXY_TARGET ?? 'http://localhost:8000',
        changeOrigin: false,
      },
    },
    watch: {
      usePolling: process.env.VITE_USE_POLLING === 'true',
    },
  },
})
