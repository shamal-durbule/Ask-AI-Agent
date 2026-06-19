import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, path.resolve(__dirname, '..'), 'VITE_')

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: parseInt(env.VITE_DEV_PORT || '3000'),
      proxy: {
        '/api': {
          target: `http://localhost:${env.VITE_API_PORT || '8000'}`,
          changeOrigin: true,
        },
      },
    },
  }
})
