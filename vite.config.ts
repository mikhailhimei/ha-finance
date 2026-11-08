import { defineConfig } from 'vite';
export default defineConfig({ root: 'frontend', base: './', build: { outDir: '../custom_components/ha_finance/frontend', emptyOutDir: true, rollupOptions: { output: { entryFileNames: 'finance.js', assetFileNames: 'finance.[ext]' } } } });
