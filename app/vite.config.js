import { readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// MapLibre charge son worker par `new URL('./maplibre-gl-worker.mjs',
// import.meta.url)`, donc depuis assets/ à côté du bundle. optimizeDeps.exclude
// (plus bas, indispensable en dev) empêche Vite de voir cette référence : rien
// n'émet le worker au build, il part en 404, et sans lui aucune tuile
// vectorielle n'est décodée — la carte garde son fond raster et reste bloquée
// sur « Chargement des protections… », sans erreur console.
// Vérifié en prod : c'était exactement ce 404.
function workerMaplibre() {
  // Résolution par sous-chemin : le package n'expose pas de `main`, seulement
  // `./dist/*` — `resolve('maplibre-gl')` seul lève ERR_PACKAGE_PATH_NOT_EXPORTED.
  const resoudre = createRequire(import.meta.url).resolve
  // Le worker importe le module partagé à côté de lui : les deux, ou rien.
  const fichiers = ['maplibre-gl-worker.mjs', 'maplibre-gl-shared.mjs']
  return {
    name: 'maplibre-worker',
    generateBundle() {
      for (const nom of fichiers) {
        this.emitFile({
          type: 'asset',
          fileName: `assets/${nom}`,
          source: readFileSync(resoudre(`maplibre-gl/dist/${nom}`)),
        })
      }
    },
  }
}

export default defineConfig({
  // Le site est servi sous tonio.github.io/bivouac/ pendant la bêta. À remettre
  // à '/' le jour où un domaine dédié pointe dessus.
  base: '/bivouac/',
  plugins: [vue(), workerMaplibre()],
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
