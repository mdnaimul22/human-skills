import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

export default defineConfig({
  base: './',  // Chrome Extensions require relative asset paths
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    sourcemap: 'inline', // Prevents eval and conforms to Chrome MV3 CSP
    rollupOptions: {
      input: {
        panel: path.resolve(__dirname, 'panel.html'),
        popup: path.resolve(__dirname, 'popup.html'),
        sidepanel: path.resolve(__dirname, 'sidepanel.html'),
        options: path.resolve(__dirname, 'options.html'),
        background: path.resolve(__dirname, 'src/background/index.ts'),
        content: path.resolve(__dirname, 'src/content/index.ts'),
      },
      output: {
        entryFileNames: (chunkInfo) => {
          if (chunkInfo.name === 'background' || chunkInfo.name === 'content') {
            return '[name].js';
          }
          return 'assets/[name]-[hash].js';
        },
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
      },
    },
    outDir: 'dist',
  },
});
