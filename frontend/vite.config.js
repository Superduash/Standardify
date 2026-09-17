import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
  },
  build: {
    // Keep an eye on bundle size as pages are added in later phases.
    chunkSizeWarningLimit: 600,
    // Never ship source maps to production — keeps source internals private.
    sourcemap: false,
  },
})
