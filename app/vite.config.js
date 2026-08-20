import { readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

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

// Service worker : on précache la coquille (1,6 Mo de bundle, polices, icônes),
// PAS la donnée. Le pmtiles fait 93 Mo et pmtiles.js le lit par requêtes Range
// sur des tranches d'octets ; le précacher téléchargerait le fichier entier, et
// un cache Workbox standard ne sait de toute façon pas resservir une tranche.
// Conséquence assumée : hors ligne, l'app démarre et son interface répond, mais
// la carte reste vide. Le mode « télécharger une zone » est un autre chantier.
function pwa() {
  return VitePWA({
    registerType: 'prompt',
    // Le manifeste est écrit à la main dans public/ (chemins relatifs, indispensables
    // sous /bivouac/) : le plugin ne doit pas en générer un second.
    manifest: false,
    workbox: {
      globPatterns: ['**/*.{js,mjs,css,html,svg,png,woff2}'],
      // 93 Mo : à exclure explicitement, sinon le build échoue sur la limite de
      // taille et, si on la relevait, l'installation mangerait le forfait data.
      globIgnores: ['**/bivouac.pmtiles'],
      navigateFallback: 'index.html',
      // La donnée ne passe jamais par le SW : laisser le réseau (et donc les
      // requêtes Range) opérer sans interception.
      navigateFallbackDenylist: [/\.pmtiles$/],
      // Sans ça, le SW fraîchement activé ne prend pas la main sur les pages
      // déjà ouvertes : « Actualiser » rechargeait l'ancien index.html servi
      // par l'ancien SW. Constaté en vrai — les balises Apple ajoutées pour le
      // plein écran iOS n'arrivaient pas, il a fallu désinstaller l'app.
      clientsClaim: true,
      runtimeCaching: [
        {
          // Les tuiles du fond de carte restent en ligne, mais un aller-retour
          // évité est un aller-retour gagné pendant une session de préparation.
          // Plafonné en nombre et en durée : le cache ne doit pas grossir sans fin.
          urlPattern: ({ url }) =>
            /tile\.openstreetmap\.fr|tile\.opentopomap\.org|data\.geopf\.fr/.test(url.href),
          handler: 'NetworkFirst',
          options: {
            cacheName: 'tuiles-fond',
            expiration: { maxEntries: 600, maxAgeSeconds: 7 * 24 * 3600 },
            cacheableResponse: { statuses: [0, 200] },
          },
        },
        {
          // Glyphes MapLibre : quelques fichiers, jamais modifiés.
          urlPattern: ({ url }) => url.href.startsWith('https://demotiles.maplibre.org/font/'),
          handler: 'CacheFirst',
          options: {
            cacheName: 'glyphes',
            expiration: { maxEntries: 40, maxAgeSeconds: 30 * 24 * 3600 },
            cacheableResponse: { statuses: [0, 200] },
          },
        },
      ],
    },
  })
}

export default defineConfig({
  // Le site est servi sous tonio.github.io/bivouac/ pendant la bêta. À remettre
  // à '/' le jour où un domaine dédié pointe dessus.
  base: '/bivouac/',
  plugins: [vue(), workerMaplibre(), pwa()],
  optimizeDeps: {
    // Le pre-bundling casse le web worker de MapLibre :
    // /node_modules/.vite/deps/maplibre-gl-worker.mjs renvoie 404, et sans
    // worker aucune tuile n'est décodée (la carte reste vide, sans erreur).
    exclude: ['maplibre-gl'],
  },
  server: {
    fs: {
      // public/bivouac.pmtiles est un symlink vers ../../pipeline/out/ : sans cette
      // autorisation Vite refuse de servir hors de la racine du projet.
      allow: ['..'],
    },
  },
})
