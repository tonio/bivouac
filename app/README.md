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

Deux fonds, tous deux utiles à la préparation : la topo pour le relief et les
sentiers, la photo pour la nature du terrain (pierrier, herbe, forêt).

| Fond | Source | Licence | Zoom max |
|---|---|---|---|
| Carte topographique (défaut) | `tile.opentopomap.org` | CC-BY-SA, attribution imposée mot pour mot | 17 |
| Photo aérienne | `ORTHOIMAGERY.ORTHOPHOTOS` (Géoplateforme) | Licence Ouverte | 19 |

**OpenTopoMap** est le fond « rando » : courbes de niveau cotées, ombrage du
relief, sentiers et éboulis figurés — le rendu disponible librement le plus
proche d'une Top25. CC-BY-SA autorise l'usage commercial ; en contrepartie
l'attribution est imposée telle quelle et le partage à l'identique s'applique.

**OSM standard et le Plan IGN ont été retirés** : plats, sans courbes de niveau,
ils n'apportaient rien pour préparer un bivouac. CyclOSM a été écarté aussi —
orienté vélo, sans variante rando.

Serveur bénévole, sans garantie de disponibilité et sans limite chiffrée mais
avec une clause anti-téléchargement massif : les trois sous-domaines `a/b/c` sont
déclarés pour répartir la charge. Ne pas préchauffer de cache dessus.

**Top25 / SCAN25 reste hors de portée** : la Géoplateforme refuse la couche
(HTTP 400) sans habilitation, sa licence n'étant pas ouverte. Ne pas l'ajouter
sans avoir vérifié les droits.

`maxzoom: 17` sur le fond topo est mesuré, pas supposé : z18 renvoie une tuile
unie (une seule couleur). MapLibre sur-zoome donc la dernière tuile réelle au
lieu d'afficher du blanc.

Attention aux identifiants Géoplateforme : `ORTHOIMAGERY.ORTHOPHOTOS` fonctionne,
`PLAN.IGN` et `MAPS` renvoient 400 (le plan s'appelait
`GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2`, sans point avant `V2`).

Le contour des protections s'épaissit jusqu'à 3 px en zoom fort : sur un fond
topographique texturé, un remplissage à 28 % se noie alors qu'un liseré net
délimite sans masquer les courbes.

## Recherche de lieu

Géocodage via **Nominatim** (OpenStreetMap), pas la BAN : `api-adresse.data.gouv.fr`
ne connaît que des adresses postales et renvoie « Le Refuge de l'Arche » en
Mayenne pour « refuge de l'Arpont ». Nominatim rend le bon refuge avec son type
`alpine_hut`, et couvre lacs, cols, sommets, hameaux et parkings.

`src/map/recherche.js` classe les résultats par pertinence bivouac (refuge et
cabane d'abord, cours d'eau et hélisurfaces en dernier) et transmet l'emprise de
la vue courante : « la valette » donne la vallée en Vanoise si la carte y est,
l'homonyme grenoblois sinon.

La politique d'usage de Nominatim plafonne à **1 requête/seconde** et décourage
explicitement l'autocomplétion. D'où un debounce de 600 ms, l'annulation des
requêtes obsolètes (`AbortController`) et un cache par requête : une saisie de
18 caractères ne déclenche qu'un seul appel, vérifié. L'attribution Nominatim
apparaît en pied de liste, comme la politique l'exige.

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

### Pièges CSS

4. **Un `button` scopé bat `.surface`.** Vue compile `button { … }` en
   `button[data-v-xxx]` (0-1-1), plus spécifique que la classe `.surface`
   (0-1-0) : un reset `background: none` volait donc son fond au seul bouton
   portant `.surface`. D'où le `button:not(.surface)` dans `BarreHaute.vue`.
   Corollaire : ne pas remettre `border: 0` sur un `button.surface`, la bordure
   porte le liseré du mode sombre.
5. **Le liseré sombre passe par `border`, pas par un `inset` de box-shadow.**
   Plusieurs composants redéfinissent `box-shadow` pour ajuster l'élévation, ce
   qui effaçait un liseré posé en `inset` — les surfaces se fondaient dans la
   carte.
6. **Les contrôles MapLibre ne suivent pas le thème.** Ils reposent sur les
   tuiles, toujours claires : leur palette est figée en clair dans `app.css`,
   sinon on obtient du texte clair sur fond blanc. Égaler leur spécificité
   demande deux classes (`.maplibregl-ctrl.maplibregl-ctrl-attrib`).

### Accessibilité

Focus clavier global (`:focus-visible`, 2 px `--accent`) déclaré une seule fois
dans `app.css` — le champ de recherche délègue à sa surface via
`:focus-within`, l'outline d'un input se lisant mal à l'intérieur du bloc.

Contrastes vérifiés au ratio WCAG dans les deux thèmes : `--fg-atenue` porte
l'avertissement juridique et les placeholders en 12-14 px, d'où un ton assez
sombre pour tenir 4.5:1 (4.73 en clair, 5.60 en sombre). L'assombrir moins
casse la conformité.

## Fonctionnalités

Volontairement minimal : affichage, légende, sélection de fond, filtres par
famille de zonage, fiche au clic. Le clic remonte **tous** les zonages empilés
sous le curseur, triés du plus contraignant au moins contraignant — c'est le cas
courant (un refuge dans un cœur de parc dans un site Natura 2000).

Natura 2000 et les PNR sont **décochés par défaut** : ils couvrent d'énormes
surfaces sans rien interdire, et les afficher d'emblée ferait croire à des
interdictions inexistantes.

Attribution et licences : voir `../SOURCES.md`.
