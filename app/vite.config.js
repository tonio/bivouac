import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  optimizeDeps: {
    // Le pre-bundling casse le web worker de MapLibre :
    // /node_modules/.vite/deps/maplibre-gl-worker.mjs renvoie 404, et sans
    // worker aucune tuile n'est décodée (la carte reste vide, sans erreur).
    exclude: ['maplibre-gl'],
  },
  server: {
    fs: {
      // public/bivouac.pmtiles est un symlink vers ../../out/ : sans cette
      // autorisation Vite refuse de servir hors de la racine du projet.
      allow: ['..'],
    },
  },
})
