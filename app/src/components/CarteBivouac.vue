<script setup>
import { onMounted, onUnmounted, ref, shallowRef, watch } from 'vue'
// MapLibre 6 n'expose plus d'export `default` : imports nommés uniquement.
import { GeolocateControl, Map, Marker, ScaleControl, addProtocol, removeProtocol } from 'maplibre-gl'
import { Protocol } from 'pmtiles'
import 'maplibre-gl/dist/maplibre-gl.css'
import { CENTRE, ZOOM, EMPRISE, GROUPES } from '../map/config.js'
import { creerStyle, COUCHES_CLIQUABLES, SRC_DATA } from '../map/style.js'

const props = defineProps({
  fond: { type: String, required: true },
  groupesActifs: { type: Array, required: true },
})
const emit = defineEmits(['selection', 'emprise'])

const conteneur = ref(null)
const carte = shallowRef(null)
let protocole = null
// Marqueur du dernier résultat de recherche, remplacé à chaque nouvelle
// recherche et retiré à la destruction.
let repere = null
// GeolocateControl, déclenché par le bouton ⌖ de ControlesCarte.
let geoloc = null
const chargement = ref(true)
const erreur = ref('')
// Séparé de `erreur` : il ne suit pas le cycle de chargement des protections.
const erreurGeoloc = ref('')

// Servi en même-origine dans les deux cas : symlink vers ../../out/ en dev, et
// déposé dans dist/ par le workflow Pages en prod. PMTiles lit par Range
// requests, que Pages honore.
// BASE_URL, pas un chemin absolu : le site vit sous /bivouac/ pendant la bêta.
const PMTILES_URL = new URL(`${import.meta.env.BASE_URL}bivouac.pmtiles`, location.href).href

// Les types masqués sont exclus par filtre GPU, pas en retirant des couches :
// une seule expression, appliquée aux 4 couches de données.
function appliquerFiltres(map, actifs) {
  const visibles = GROUPES
    .filter((g) => actifs.includes(g.id))
    .flatMap((g) => g.types)

  const filtre = visibles.length
    ? ['in', ['get', 'type'], ['literal', visibles]]
    : ['==', ['get', 'type'], ' '] // rien de visible

  for (const id of ['zones-remplissage', 'zones-contour', 'points', 'points-etiquette']) {
    if (map.getLayer(id)) map.setFilter(id, filtre)
  }
}

onMounted(() => {
  // Le protocole pmtiles:// doit être enregistré avant la création de la carte.
  // pmtiles 4 expose `get` (async params/abortController) ; l'ancien `.tile`
  // ne renvoie rien avec MapLibre 6 et la source reste muette.
  // `tile` est le handler (get() n'est qu'un accesseur de cache), et il doit
  // être lié : passé détaché il perd son `this` et échoue sur `reading 'tiles'`.
  protocole = new Protocol({ metadata: true })
  addProtocol('pmtiles', protocole.tile.bind(protocole))

  const map = new Map({
    container: conteneur.value,
    style: creerStyle(props.fond, PMTILES_URL),
    // Cadré sur l'emprise plutôt que sur un zoom fixe : en portrait mobile un
    // zoom 5.2 coupait la Bretagne et l'Alsace. center/zoom servent de repli.
    center: CENTRE,
    zoom: ZOOM,
    bounds: EMPRISE,
    fitBoundsOptions: { padding: 16 },
    // Replié sous 640 px : déplié, l'attribution occupe deux lignes en mobile.
    attributionControl: { compact: window.innerWidth < 640 },
  })
  carte.value = map
  // Accès à la carte depuis la console en dev (diagnostic du style, des sources).
  if (import.meta.env.DEV) window.__carte = map

  // Attribution repliée dès le départ : dépliée, elle occupe trois lignes sur un
  // écran étroit et masque l'échelle.
  // MapLibre la rouvre à chaque `styledata`/`sourcedata` (son `_updateData`
  // repose `maplibregl-compact-show` en reconstruisant le contenu), donc en
  // continu pendant le chargement des zones — d'où l'attribution ouverte tout du
  // long avec l'ancien repli, posé une seule fois dans `load`. On se rebranche
  // sur les mêmes événements pour repasser derrière lui.
  // Ni le CSS ni `[open]` ne suffisent : MapLibre pose l'attribut en même temps
  // que la classe, y compris à l'ouverture automatique — rien dans le DOM ne
  // distingue « ouvert par l'utilisateur ». D'où le drapeau ci-dessous, qui
  // arrête de replier au premier clic sur ⓘ.
  const attribution = () =>
    map.getContainer().querySelector('.maplibregl-ctrl-attrib.maplibregl-compact')
  let ouvertParUtilisateur = false
  attribution()
    ?.querySelector('.maplibregl-ctrl-attrib-button')
    ?.addEventListener('click', () => { ouvertParUtilisateur = true }, { once: true })

  const replierAttribution = () => {
    if (ouvertParUtilisateur) return
    attribution()?.classList.remove('maplibregl-compact-show')
  }
  replierAttribution()
  map.on('styledata', replierAttribution)
  map.on('sourcedata', replierAttribution)

  // Pas de NavigationControl : les boutons de zoom sont des éléments de l'UI
  // flottante (ControlesCarte), pour garder une seule grammaire visuelle.
  map.addControl(new ScaleControl({ maxWidth: 120, unit: 'metric' }), 'bottom-left')

  // GeolocateControl pour le point bleu, le cercle de précision, la permission
  // et le suivi — tout ça est déjà écrit et testé. Son bouton natif est masqué
  // en CSS : c'est ⌖ de ControlesCarte qui le déclenche, pour ne pas avoir deux
  // grammaires visuelles côte à côte.
  geoloc = new GeolocateControl({
    positionOptions: { enableHighAccuracy: true },
    // En montagne le premier point GPS est souvent grossier puis s'affine :
    // le suivi laisse la position se corriger au lieu de figer l'approximation.
    trackUserLocation: true,
    showUserLocation: true,
  })
  map.addControl(geoloc)

  // Message séparé de `erreur` : celui-ci est effacé dès que les protections se
  // rechargent (`sourcedata`), ce qui arrive au premier déplacement — l'avis de
  // refus disparaissait avant d'avoir été lu. Il s'efface au clic suivant sur ⌖,
  // qui est le seul geste qui le rend obsolète.
  geoloc.on('error', (e) => {
    erreurGeoloc.value = e?.code === 1
      ? 'Localisation refusée — autorisez-la dans les réglages du navigateur.'
      : 'Position introuvable.'
  })
  geoloc.on('geolocate', () => { erreurGeoloc.value = '' })

  map.on('load', () => {
    chargement.value = false
    appliquerFiltres(map, props.groupesActifs)
  })

  map.on('error', (e) => {
    // Seul l'échec des protections mérite un message : sans elles la carte ne
    // répond plus à la question posée. Une tuile de fond ratée, non — le fond
    // s'affiche quand même, MapLibre réessaie, et Safari iOS en fait échouer
    // couramment quelques-unes (« Load failed ») sur un réseau mobile. Signaler
    // ça affichait un bandeau rouge permanent sur une carte parfaitement
    // lisible, déclenché par la dernière tuile perdue sur trois cents.
    if (e.sourceId && e.sourceId !== SRC_DATA) return
    // Message à nous, pas celui de MapLibre : « Load failed » ne dit rien à
    // l'utilisateur, et surtout pas que la carte affichée est incomplète.
    erreur.value = 'Protections indisponibles — la carte est incomplète.'
  })

  // Une coupure passagère ne doit pas laisser le bandeau à l'écran une fois les
  // protections revenues. Le signal est `sourcedata` sur la bonne source, pas
  // `idle` : `idle` ne dit que « plus rien en cours », ce qui arrive aussi
  // entre deux lots de tuiles en échec — il effaçait le bandeau aussitôt
  // affiché, y compris quand le pmtiles était réellement inaccessible.
  map.on('sourcedata', (e) => {
    if (e.sourceId === SRC_DATA && e.isSourceLoaded) erreur.value = ''
  })

  // Clic : on remonte toutes les protections empilées sous le curseur, de la
  // plus contraignante à la moins contraignante.
  map.on('click', (e) => {
    const touches = map.queryRenderedFeatures(e.point, { layers: COUCHES_CLIQUABLES })
    if (!touches.length) {
      emit('selection', null)
      return
    }

    const vus = new Set()
    const objets = []
    for (const f of touches) {
      const p = f.properties ?? {}
      const cle = `${p.type}|${p.nom}|${p.id_mnhn}`
      if (vus.has(cle)) continue
      vus.add(cle)
      objets.push(p)
    }
    objets.sort((a, b) => (b.severite ?? 0) - (a.severite ?? 0))
    emit('selection', { objets, lngLat: e.lngLat })
  })

  for (const id of COUCHES_CLIQUABLES) {
    map.on('mouseenter', id, () => { map.getCanvas().style.cursor = 'pointer' })
    map.on('mouseleave', id, () => { map.getCanvas().style.cursor = '' })
  }

  // Emprise remontée à la fin des déplacements seulement : la recherche s'en
  // sert pour trier par proximité, pas besoin de suivre chaque image.
  const publierEmprise = () => {
    const b = map.getBounds()
    emit('emprise', [[b.getWest(), b.getSouth()], [b.getEast(), b.getNorth()]])
  }
  map.on('moveend', publierEmprise)
  map.once('idle', publierEmprise)
})

onUnmounted(() => {
  repere?.remove()
  carte.value?.remove()
  removeProtocol('pmtiles')
})

// Changer de fond impose de reconstruire le style : les filtres courants sont
// réappliqués une fois le nouveau style chargé.
watch(() => props.fond, (fond) => {
  const map = carte.value
  if (!map) return
  map.setStyle(creerStyle(fond, PMTILES_URL))
  map.once('styledata', () => appliquerFiltres(map, props.groupesActifs))
})

watch(() => props.groupesActifs, (actifs) => {
  const map = carte.value
  if (map?.isStyleLoaded()) appliquerFiltres(map, actifs)
}, { deep: true })

// Pilotage depuis l'UI flottante.
defineExpose({
  zoomer: (pas) => carte.value?.zoomTo(carte.value.getZoom() + pas, { duration: 250 }),

  /** Centre sur la position de l'utilisateur (permission, point bleu et suivi
   *  gérés par GeolocateControl). */
  localiser: () => {
    erreurGeoloc.value = ''
    geoloc?.trigger()
  },

  /** Cadre sur un résultat de recherche et le marque. */
  allerA: (lieu) => {
    const map = carte.value
    if (!map || !lieu) return

    // Une emprise cadre juste une commune ou un lac ; pour un refuge ou un
    // parking, elle est minuscule — on plafonne le zoom pour garder du
    // contexte, sinon on se retrouve collé au sol.
    if (lieu.emprise) {
      map.fitBounds(lieu.emprise, { padding: 80, maxZoom: 14, duration: 900 })
    } else {
      map.flyTo({ center: [lieu.lon, lieu.lat], zoom: 14, duration: 900 })
    }

    repere?.remove()
    repere = new Marker({ color: '#c0392b' })
      .setLngLat([lieu.lon, lieu.lat])
      .addTo(map)
  },
})
</script>

<template>
  <div class="carte">
    <div ref="conteneur" class="toile"></div>
    <p v-if="chargement" class="etat surface">Chargement des protections…</p>
    <p v-else-if="erreur" class="etat surface etat--erreur">{{ erreur }}</p>
    <p v-else-if="erreurGeoloc" class="etat surface etat--erreur">{{ erreurGeoloc }}</p>
  </div>
</template>

<style scoped>
/* La carte est le fond de l'écran : elle remplit le conteneur, tout le reste
   flotte au-dessus. */
.carte {
  position: absolute;
  inset: 0;
}

.toile {
  height: 100%;
}

.etat {
  position: absolute;
  top: calc(var(--sur-haut) + 5.5rem);
  left: 50%;
  transform: translateX(-50%);
  margin: 0;
  padding: var(--pad-s) var(--pad);
  box-shadow: var(--ombre);
  font-size: 0.85rem;
}

.etat--erreur {
  color: #c0392b;
}
</style>
