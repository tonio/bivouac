# app — consultation des règles de bivouac

Vue 3 + MapLibre GL, lecture directe des PMTiles du dépôt parent.

```sh
yarn install
yarn dev        # http://localhost:5173
yarn build      # dist/
```

En dev, les données viennent de `public/bivouac.pmtiles`, un symlink vers
`../../pipeline/out/` (en prod, voir [Déploiement](#déploiement)). Si la carte est vide,
c'est que les tuiles n'ont pas été générées :

```sh
cd ../pipeline && ./fetch.sh && ./fetch_osm.sh && ./zones_internes.py && ./build.py --pmtiles
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
| `src/components/BarreHaute.vue` | Bascule de fond, bouton « Zones », recherche. |
| `src/components/ChampRecherche.vue` | Autocomplétion Nominatim. |
| `src/components/PanneauProtections.vue` | Cases à cocher par famille de zonage. |
| `src/components/LegendeSeverite.vue` | Échelle de couleur et avertissement juridique. |
| `src/components/ControlesCarte.vue` | Zoom et recadrage. |
| `src/components/FicheZonage.vue` | Panneau d'infos : décode `regle_json` en libellés lisibles. |

Le PMTiles porte deux couches — `zones` (polygones) et `points` (refuges) — car
une couche de tuiles vectorielles ne peut contenir qu'un type de géométrie.

## Fonds de carte

Deux fonds dans l'interface, une bascule à deux états dans la barre haute (le
libellé annonce la destination, pas l'état courant).

| Fond | Source | Licence | Zoom max |
|---|---|---|---|
| **Carte topographique** (défaut), vue large | `tile.openstreetmap.fr/hot` | ODbL, hébergé par OSM-France | 19 |
| **Carte topographique**, à partir de z11 | `tile.opentopomap.org` | CC-BY-SA, attribution imposée mot pour mot | 17 |
| **Photo aérienne** | `ORTHOIMAGERY.ORTHOPHOTOS` (Géoplateforme) | Licence Ouverte | 19 |

### Un fond, deux paliers de zoom

« Topo » sert deux jeux de tuiles selon l'échelle, sans que l'utilisateur ait à
choisir — il voit un seul fond, la carte reste lisible partout :

- **Sous z11** : style HOT, beige-gris sobre. OpenTopoMap y applique une teinte
  hypsométrique (plaines vert vif, sommets brun-rouge) qui rend les zonages
  illisibles à l'échelle de la France.
- **À partir de z11** : OpenTopoMap, pour les courbes de niveau cotées, l'ombrage,
  les sentiers et les éboulis — le rendu le plus proche d'une Top25 disponible
  librement.

Le seuil est **mesuré, pas estimé** : la saturation moyenne d'une tuile alpine
d'OpenTopoMap reste à ~0,73 jusqu'à z10, puis tombe à ~0,18 à z11, quand le style
abandonne l'hypsométrie. Voir `SEUIL_TOPO` dans `config.js`.

Techniquement, deux sources raster superposées avec un fondu croisé sur un niveau
de zoom (`raster-opacity` interpolée), et non un `setStyle` au franchissement qui
ferait clignoter la carte et rechargerait tout le style.

**Écartés** : OSM standard, le Plan IGN et OSM-FR (plats, sans courbes de niveau),
CyclOSM (orienté vélo, sans variante rando), CARTO Positron et Voyager (licence
Enterprise requise pour un usage commercial), Esri Gray Canvas et Wikimedia
(conditions floues, Wikimedia réservant ses tuiles à ses propres projets).
SCAN25 — la vraie Top25 — reste hors de portée : la Géoplateforme la refuse sans
habilitation, sa licence n'étant pas ouverte.

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

1. **Le web worker de MapLibre casse des deux côtés, pour des raisons opposées.**
   Sans erreur console dans un cas comme dans l'autre : la carte reste sur
   « Chargement des protections… », fond raster visible et zonages absents, parce
   que les tuiles raster n'ont pas besoin du worker et les vectorielles si. Le
   404 n'apparaît que dans l'onglet réseau.
   - **En dev**, `optimizeDeps.exclude: ['maplibre-gl']` est obligatoire : le
     pre-bundling de Vite sert `/node_modules/.vite/deps/maplibre-gl-worker.mjs`
     en 404.
   - **Au build**, cet `exclude` occulte le worker : MapLibre le résout par
     `new URL('./maplibre-gl-worker.mjs', import.meta.url)`, donc depuis
     `assets/`, où rien ne l'émet. D'où le plugin `workerMaplibre()` dans
     `vite.config.js`, qui l'y copie avec son module partagé (les deux, ou rien —
     le worker importe le second).

   Corollaire : retirer l'`exclude` casse le dev, retirer le plugin casse la
   prod. Les deux sont nécessaires.
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

## PWA et hors ligne

Installable, avec un service worker généré par `vite-plugin-pwa`. Ce qu'il
précache : la coquille — bundle, polices, icônes, `index.html`, soit ~1,7 Mo en
17 entrées. Ce qu'il ne précache **pas** : `bivouac.pmtiles`.

Cette exclusion est le point central. Le pmtiles fait 93 Mo et `pmtiles.js` le
lit par **requêtes Range** sur des tranches d'octets. Le précacher
téléchargerait le fichier entier (mesuré : une requête sans en-tête `Range`
renvoie les 96 694 171 octets), et un cache Workbox standard ne sait de toute
façon pas resservir une tranche à partir d'une réponse complète. D'où
`globIgnores` sur le fichier et `navigateFallbackDenylist` sur `.pmtiles`.

Conséquence assumée, à connaître : **hors ligne, l'app démarre et son interface
répond, mais la carte n'a pas ses protections.** Le fond de carte peut réapparaître
si les tuiles sont encore dans le cache runtime (`NetworkFirst`, 600 tuiles /
7 jours) ; les zonages, non.

⚠️ Limite connue, non résolue : dans ce cas la carte s'affiche vide **avec sa
légende** (« Interdit », « Autorisé sous conditions »…), ce qui peut se lire
« rien d'interdit ici » au lieu de « données manquantes ». Le bandeau
« Protections indisponibles » existe et fonctionne quand la source tombe en
cours de route, mais pas au démarrage hors ligne : `pmtiles.js` avale l'échec du
fetch de l'en-tête, et MapLibre n'émet alors aucun `error` portant un
`sourceId`. `isSourceLoaded()` renvoie même `true` dans ce cas (vérifié en
navigateur), donc le tester ne suffit pas. À reprendre avant de communiquer sur
un usage hors ligne.

Mise à jour en `prompt` et non `autoUpdate` : les règles affichées ont une portée
juridique, un rechargement surprise en pleine lecture d'une fiche est le mauvais
moment. `BandeauMaj.vue` propose « Actualiser » et signale la disponibilité hors
ligne.

Les polices sont auto-hébergées (`src/polices.css` + `src/polices/`) : plus de
requête vers `fonts.googleapis.com`, qui bloquait le premier rendu et exposait
l'IP des visiteurs. Elles vivent dans `src/` et non `public/` pour que Vite les
hache et réécrive leur URL selon `base`.

## Déploiement

En ligne sur **https://tonio.github.io/bivouac/**, déployé par
`.github/workflows/pages.yml` à chaque push sur `main`.

Le pmtiles fait 93 Mo et n'est pas dans git — c'est un dérivé reproductible par
`pipeline/build.py`. Il vit dans la release `data-v1`, et le workflow le dépose dans
`dist/` au build. Pages le sert donc **en même-origine** que l'app.

Mettre à jour la donnée sans toucher au code — le tag est fixe, on remplace son
asset :

```sh
cd ../pipeline && ./build.py --pmtiles
gh release upload data-v1 out/bivouac.pmtiles --clobber
```

Le workflow ne régénère pas la donnée : `pipeline/fetch.sh` télécharge ~300 Mo pour des
zonages qui bougent quelques fois par an.

**`base: '/bivouac/'`** tant que le site vit sous un sous-chemin. À remettre à
`'/'` le jour où un domaine dédié pointe dessus — et l'URL du pmtiles suit
d'elle-même, elle passe par `import.meta.env.BASE_URL` plutôt que par un chemin
absolu, qui viserait la racine du domaine.

### Pourquoi pas l'URL de la release directement

Testé, inutilisable : un release asset redirige vers
`release-assets.githubusercontent.com` avec une URL **signée qui expire en ~1 h**,
et **sans en-tête CORS**. Les Range requests passent (206), mais le navigateur
refuse la réponse. D'où la copie dans `dist/` : en même-origine, la question du
CORS ne se pose plus, et Pages honore `Range` (vérifié, `206` +
`content-range`) — ce dont PMTiles dépend entièrement.

Une alternative si la donnée dépasse un jour la limite de 2 Go des releases, ou
si le trafic justifie un CDN : Cloudflare R2 (10 Go gratuits, egress gratuit,
CORS et Range configurables). Ce n'est qu'un changement d'URL.

## Fonctionnalités

Volontairement minimal : affichage, légende, sélection de fond, filtres par
famille de zonage, fiche au clic. Le clic remonte **tous** les zonages empilés
sous le curseur, triés du plus contraignant au moins contraignant — c'est le cas
courant (un refuge dans un cœur de parc dans un site Natura 2000).

Natura 2000 et les PNR sont **décochés par défaut** : ils couvrent d'énormes
surfaces sans rien interdire, et les afficher d'emblée ferait croire à des
interdictions inexistantes.

Attribution et licences : voir `../SOURCES.md`.
