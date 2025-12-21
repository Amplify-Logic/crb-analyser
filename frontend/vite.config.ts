import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: 'http://localhost:8383',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: mode !== 'production',
    // Optimize chunk splitting
    rollupOptions: {
      output: {
        manualChunks: {
          // React core
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // UI libraries
          'ui-vendor': ['framer-motion', 'lucide-react'],
          // Charts (if used)
          ...(mode === 'production' ? { 'charts': ['recharts'] } : {}),
        },
      },
    },
    // Minification settings
    minify: 'terser',
    terserOptions: {
      compress: {
        // Remove console.log in production
        drop_console: mode === 'production',
        drop_debugger: true,
      },
    },
    // Chunk size warnings
    chunkSizeWarningLimit: 500,
  },
  // Dependency pre-bundling for faster dev startup
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'framer-motion',
      'lucide-react',
    ],
  },
  // Environment variable prefix
  envPrefix: 'VITE_',
}))
