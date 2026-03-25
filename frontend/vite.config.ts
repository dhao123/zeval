import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  css: {
    preprocessorOptions: {
      less: {
        javascriptEnabled: true,
      },
    },
  },
  server: {
    port: 3000,
    // AITest compatible: /api-auth/* routes proxy to company auth service
    proxy: {
      // Main API proxy - only proxy /api/v1 to backend
      '/api/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Health check proxy
      '/api/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // AITest: SSO Authentication service proxy
      '/api-auth/': {
        target: 'https://api-fe-boss-uat.zkh360.com',
        changeOrigin: true,
        secure: false,
        xfwd: true,
      },
      // AITest: Security service proxy
      '/api-security/': {
        target: 'https://api-fe-boss-uat.zkh360.com',
        changeOrigin: true,
        secure: false,
        xfwd: true,
      },
    },
  },
})
