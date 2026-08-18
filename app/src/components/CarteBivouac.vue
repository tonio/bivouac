<script setup>
import { onMounted, onUnmounted, ref, shallowRef, watch } from 'vue'
// MapLibre 6 n'expose plus d'export `default` : imports nommés uniquement.
import { Map, Marker, ScaleControl, addProtocol, removeProtocol } from 'maplibre-gl'
import { Protocol } from 'pmtiles'
import 'maplibre-gl/dist/maplibre-gl.css'
import { CENTRE, ZOOM, EMPRISE, GROUPES } from '../map/config.js'
import { creerStyle, COUCHES_CLIQUABLES } from '../map/style.js'

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
const chargement = ref(true)
const erreur = ref('')

const PMTILES_URL = new URL('/bivouac.pmtiles', location.href).href

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

  // Pas de NavigationControl : les boutons de zoom sont des éléments de l'UI
  // flottante (ControlesCarte), pour garder une seule grammaire visuelle.
  map.addControl(new ScaleControl({ maxWidth: 120, unit: 'metric' }), 'bottom-left')

  map.on('load', () => {
    chargement.value = false
    appliquerFiltres(map, props.groupesActifs)

    // En compact, MapLibre ouvre l'attribution au démarrage : sur un écran
    // étroit elle occupe trois lignes et masque l'échelle. On la replie au
    // bouton ⓘ, que l'utilisateur reste libre d'ouvrir.
    document
      .querySelector('.maplibregl-ctrl-attrib.maplibregl-compact')
      ?.classList.remove('maplibregl-compact-show')
  })

  map.on('error', (e) => {
    // Une tuile manquante ne doit pas masquer la carte : on signale sans casser.
    erreur.value = e.error?.message ?? 'Erreur de chargement des tuiles'
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
  recentrer: () => carte.value?.fitBounds(EMPRISE, { padding: 16, duration: 700 }),

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
  top: 5.5rem;
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
