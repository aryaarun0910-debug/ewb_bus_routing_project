import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // 127.0.0.1, not localhost: on Windows `localhost` resolves to IPv6 (::1)
      // first, but uvicorn binds IPv4 only, adding a ~2s connection-timeout delay
      // to every proxied API call. Forcing IPv4 keeps the dashboard snappy.
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
