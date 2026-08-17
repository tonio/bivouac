# app — consultation des règles de bivouac

Vue 3 + MapLibre GL, lecture directe des PMTiles du dépôt parent.

```sh
yarn install
yarn dev        # http://localhost:5173
yarn build      # dist/
```

Les données viennent de `public/bivouac.pmtiles`, un symlink vers `../../out/`.
Si la carte est vide, c'est que les tuiles n'ont pas été générées :

```sh
cd .. && ./fetch.sh && ./fetch_osm.sh && ./zones_internes.py && ./build.py --pmtiles
```

## Choix techniques

**MapLibre plutôt qu'OpenLayers** — les données sont déjà en tuiles vectorielles.
MapLibre les rend en WebGL et résout les couleurs par expression de style sur le
champ `severite` : aucune boucle JS sur les 7126 objets, et les 1355 sites Natura
2000 qui se chevauchent restent fluides. OpenLayers rend le MVT en Canvas 2D, ce
qui rame sur ce volume. OL resterait le bon choix pour des projections exotiques
ou de l'édition de géométries — pas le besoin ici.

**Pas de framework CSS** — variables CSS globales dans `src/app.css`, tout le
reste en `<style scoped>` par composant. Le markup ne porte que des classes
sémantiques (`.legende`, `.fiche`, `.pastille`), jamais d'utilitaires.

**4 dépendances** : `vue`, `maplibre-gl`, `pmtiles`, plus `vite` en dev.

## Structure

| Fichier | Rôle |
|---|---|
| `src/map/config.js` | Fonds de carte, palette, groupes de zonages. **Seul fichier à éditer** pour ajouter un fond ou un zonage. |
| `src/map/style.js` | Construction du style MapLibre (expressions de couleur). |
| `src/components/CarteBivouac.vue` | Carte, filtres, clic. |
| `src/components/LegendeCarte.vue` | Sélecteur de fond, cases de zonages, échelle de couleur. |
| `src/components/FicheZonage.vue` | Panneau d'infos : décode `regle_json` en libellés lisibles. |

Le PMTiles porte deux couches — `zones` (polygones) et `points` (refuges) — car
une couche de tuiles vectorielles ne peut contenir qu'un type de géométrie.

## Fonds de carte

| Fond | Source | Licence |
|---|---|---|
| OpenStreetMap | `tile.openstreetmap.org` | ODbL, attribution obligatoire |
| Plan IGN | `GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2` | Licence Ouverte |
| Photo aérienne | `ORTHOIMAGERY.ORTHOPHOTOS` | Licence Ouverte |

**Top25 / SCAN25 absent volontairement** : la Géoplateforme refuse la couche
(HTTP 400) sans habilitation, sa licence n'étant pas ouverte. Ne pas l'ajouter
sans avoir vérifié les droits.

Attention aux identifiants : `GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2` (sans point
avant `V2`). `PLAN.IGN` et `MAPS` renvoient 400.

## Pièges rencontrés

Trois blocages coûteux, corrigés — à ne pas réintroduire :

1. **`optimizeDeps.exclude: ['maplibre-gl']` dans `vite.config.js` est
   obligatoire.** Sans lui, le pre-bundling de Vite casse le web worker
   (`/node_modules/.vite/deps/maplibre-gl-worker.mjs` en 404) et **aucune** tuile
   n'est décodée — vectorielle comme GeoJSON. La carte reste vide *sans lever
   d'erreur*, ce qui rend le diagnostic pénible.
2. **MapLibre 6 n'a plus d'export `default`** : imports nommés uniquement
   (`import { Map, NavigationControl } from 'maplibre-gl'`).
3. **`new Protocol().tile` doit être lié** (`.bind(protocole)`) : passé détaché il
   perd son `this` et échoue sur `reading 'tiles'`. `Protocol.get()` n'est pas le
   handler mais un accesseur de cache — s'en servir ne produit rien.

En dev, la carte est exposée en `window.__carte` pour inspection console.

## Fonctionnalités

Volontairement minimal : affichage, légende, sélection de fond, filtres par
famille de zonage, fiche au clic. Le clic remonte **tous** les zonages empilés
sous le curseur, triés du plus contraignant au moins contraignant — c'est le cas
courant (un refuge dans un cœur de parc dans un site Natura 2000).

Natura 2000 et les PNR sont **décochés par défaut** : ils couvrent d'énormes
surfaces sans rien interdire, et les afficher d'emblée ferait croire à des
interdictions inexistantes.

Attribution et licences : voir `../SOURCES.md`.
