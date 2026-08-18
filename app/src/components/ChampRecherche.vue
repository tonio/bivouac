<script setup>
import { onUnmounted, ref, watch } from 'vue'
import { chercher, DELAI_SAISIE } from '../map/recherche.js'

const props = defineProps({
  // Emprise de la vue courante, [[o,s],[e,n]] : sert à privilégier les
  // résultats proches de ce que l'utilisateur regarde.
  viewbox: { type: Array, default: null },
})
const emit = defineEmits(['aller'])

const texte = ref('')
const resultats = ref([])
const ouvert = ref(false)
const enCours = ref(false)
const erreur = ref('')
const actif = ref(-1)

let minuteur = null
let requete = null
// Choisir un résultat réécrit le champ, ce qui relancerait le watch et
// rouvrirait la liste juste après l'avoir fermée.
let ignorerProchaineSaisie = false

function annuler() {
  clearTimeout(minuteur)
  requete?.abort()
  requete = null
}

// Debounce large et non 1 frappe = 1 requête : Nominatim plafonne à 1 req/s et
// décourage explicitement l'autocomplétion.
watch(texte, (q) => {
  annuler()
  if (ignorerProchaineSaisie) {
    ignorerProchaineSaisie = false
    return
  }
  erreur.value = ''
  actif.value = -1

  if (q.trim().length < 3) {
    resultats.value = []
    ouvert.value = false
    enCours.value = false
    return
  }

  enCours.value = true
  minuteur = setTimeout(async () => {
    const ctrl = new AbortController()
    requete = ctrl
    try {
      resultats.value = await chercher(q, { signal: ctrl.signal, viewbox: props.viewbox })
      ouvert.value = true
    } catch (e) {
      if (e.name !== 'AbortError') {
        erreur.value = 'Recherche indisponible'
        resultats.value = []
      }
    } finally {
      if (requete === ctrl) {
        enCours.value = false
        requete = null
      }
    }
  }, DELAI_SAISIE)
})

// Fermeture au clic ailleurs : sans ça la liste reste posée sur la carte.
const enveloppe = ref(null)
const auClicDehors = (e) => {
  if (ouvert.value && !enveloppe.value?.contains(e.target)) ouvert.value = false
}
document.addEventListener('pointerdown', auClicDehors)

onUnmounted(() => {
  annuler()
  document.removeEventListener('pointerdown', auClicDehors)
})

function choisir(r) {
  emit('aller', r)
  ignorerProchaineSaisie = true
  texte.value = r.nom
  ouvert.value = false
  enCours.value = false
  actif.value = -1
}

function auClavier(e) {
  if (e.key === 'Escape') {
    ouvert.value = false
    actif.value = -1
    return
  }
  if (!resultats.value.length) return

  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    e.preventDefault()
    ouvert.value = true
    const n = resultats.value.length
    const pas = e.key === 'ArrowDown' ? 1 : -1
    actif.value = (actif.value + pas + n) % n
  } else if (e.key === 'Enter') {
    e.preventDefault()
    choisir(resultats.value[Math.max(0, actif.value)])
  }
}

function vider() {
  annuler()
  texte.value = ''
  resultats.value = []
  ouvert.value = false
}
</script>

<template>
  <div ref="enveloppe" class="enveloppe">
    <label class="surface champ" :class="{ 'champ--ouvert': ouvert && resultats.length }">
      <span class="loupe" aria-hidden="true">⌕</span>
      <input
        v-model="texte"
        type="search"
        role="combobox"
        aria-label="Rechercher un lieu"
        :aria-expanded="ouvert && resultats.length > 0"
        aria-autocomplete="list"
        aria-controls="resultats-recherche"
        placeholder="Refuge, lac, col, parking, hameau…"
        autocomplete="off"
        @keydown="auClavier"
        @focus="ouvert = resultats.length > 0"
      />
      <span v-if="enCours" class="fileur" aria-label="Recherche en cours"></span>
      <button v-else-if="texte" type="button" class="vider" aria-label="Effacer" @click="vider">×</button>
    </label>

    <ul
      v-if="ouvert && resultats.length"
      id="resultats-recherche"
      class="surface liste"
      role="listbox"
    >
      <li
        v-for="(r, i) in resultats"
        :key="r.id"
        role="option"
        :aria-selected="i === actif"
        :class="{ actif: i === actif }"
        @mouseenter="actif = i"
        @mousedown.prevent="choisir(r)"
      >
        <span class="nom">{{ r.nom }}</span>
        <span v-if="r.categorie" class="categorie">{{ r.categorie }}</span>
        <span v-if="r.contexte" class="contexte">{{ r.contexte }}</span>
      </li>
      <li class="mention" aria-hidden="true">
        Recherche <a href="https://nominatim.openstreetmap.org/" target="_blank" rel="noopener">Nominatim</a> · données OpenStreetMap
      </li>
    </ul>

    <p v-else-if="erreur" class="surface message">{{ erreur }}</p>
    <p v-else-if="ouvert && texte.trim().length >= 3 && !enCours" class="surface message">
      Aucun lieu trouvé
    </p>
  </div>
</template>

<style scoped>
.enveloppe {
  position: relative;
  display: flex;
  width: 22.5rem;
  flex-direction: column;
}

.champ {
  display: flex;
  align-items: center;
  gap: 0.5625rem;
  height: 3rem;
  padding: 0 1rem;
  box-shadow: var(--ombre);
}

/* Liste ouverte : le champ et la liste ne forment qu'un bloc. */
.champ--ouvert {
  border-bottom-right-radius: 0;
  border-bottom-left-radius: 0;
}

.champ:focus-within {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.loupe {
  color: var(--fg-secondaire);
}

input {
  width: 100%;
  border: 0;
  background: none;
  color: var(--fg);
  font: 400 0.875rem var(--police);
}

input::placeholder {
  color: var(--fg-atenue);
}

input:focus-visible {
  outline: none;
}

/* Masque la croix native de <input type="search">, doublon de notre bouton. */
input::-webkit-search-cancel-button {
  display: none;
}

.vider {
  border: 0;
  background: none;
  color: var(--fg-atenue);
  font-size: 1.125rem;
  line-height: 1;
  cursor: pointer;
}

.vider:hover {
  color: var(--fg);
}

.fileur {
  width: 0.875rem;
  height: 0.875rem;
  flex: 0 0 auto;
  border: 2px solid var(--bord-fort);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: tourne 0.7s linear infinite;
}

@keyframes tourne {
  to { transform: rotate(1turn); }
}

@media (prefers-reduced-motion: reduce) {
  .fileur {
    animation-duration: 2s;
  }
}

.liste,
.message {
  position: absolute;
  z-index: 1;
  top: calc(3rem - 1px);
  right: 0;
  left: 0;
  margin: 0;
  border-top-left-radius: 0;
  border-top-right-radius: 0;
  box-shadow: var(--ombre-panneau);
}

.liste {
  max-height: 21rem;
  overflow-y: auto;
  padding: 0.375rem;
  list-style: none;
}

.message {
  padding: 0.75rem 1rem;
  color: var(--fg-secondaire);
  font-size: 0.8125rem;
}

.liste li:not(.mention) {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0 0.5rem;
  padding: 0.5rem 0.625rem;
  border-radius: var(--rayon-s);
  cursor: pointer;
}

.liste li.actif {
  background: var(--bg-doux);
}

.nom {
  font-size: 0.875rem;
  font-weight: 500;
}

.categorie {
  align-self: center;
  color: var(--fg-secondaire);
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  white-space: nowrap;
}

.contexte {
  grid-column: 1 / -1;
  color: var(--fg-secondaire);
  font-size: 0.75rem;
}

/* Attribution requise par la politique d'usage de Nominatim. */
.mention {
  padding: 0.5rem 0.625rem 0.25rem;
  color: var(--fg-atenue);
  font-size: 0.6875rem;
}

@media (max-width: 900px) {
  .enveloppe {
    order: 1;
    width: auto;
    flex: 1;
  }
}
</style>
