import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    // Makes "@/components/Button" work as a path alias.
    // Must match tsconfig.json "paths" setting.
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',  // Required inside Docker to accept connections from host
    // Proxy /api/* requests to the FastAPI backend.
    // This means the frontend can call `/api/health` and it hits
    // `http://backend:8000/api/health` without CORS issues in development.
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})
