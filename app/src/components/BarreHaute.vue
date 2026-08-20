<script setup>
import { computed } from 'vue'
import { FONDS } from '../map/config.js'
import ChampRecherche from './ChampRecherche.vue'

defineProps({
  panneauOuvert: { type: Boolean, default: false },
  viewbox: { type: Array, default: null },
})
defineEmits(['basculer-panneau', 'aller'])

const fond = defineModel('fond', { type: String, required: true })

// Le fond vers lequel la bascule enverra. Un modulo plutôt qu'un ternaire : si
// un troisième fond revient un jour, le bouton devient un cycle sans réécriture.
const suivant = computed(() => {
  const i = FONDS.findIndex((f) => f.id === fond.value)
  return FONDS[(i + 1) % FONDS.length]
})
</script>

<template>
  <div class="barre">
    <!-- Le titre ne servait à rien : il ouvre le panneau des protections.
         `aria-label` est nécessaire car en mobile le libellé est masqué et les
         deux glyphes sont décoratifs : sans lui, plus de nom accessible. -->
    <button
      type="button"
      class="surface zones"
      :aria-expanded="panneauOuvert"
      aria-label="Zones de protection"
      @click="$emit('basculer-panneau')"
    >
      <!-- Même tente que le favicon et l'icône d'application : le bouton qui
           ouvre les zonages porte le signe du projet. Inline plutôt qu'un
           <img src="icone-mono.svg"> pour suivre `currentColor` (thème sombre,
           état survolé) sans seconde requête. -->
      <svg class="tente" viewBox="0 0 64 64" aria-hidden="true" focusable="false">
        <path
          fill="currentColor"
          fill-rule="evenodd"
          d="M32 11.5 55.5 48.5H8.5L32 11.5Zm0 14.8L23 48.5h18L32 26.3Z"
        />
        <rect x="7" y="49.5" width="50" height="4" rx="2" fill="currentColor" />
      </svg>
      <span>Zones</span>
      <!-- Burger réservé au mobile, où le libellé disparaît : voir la media query. -->
      <span class="burger" aria-hidden="true"></span>
    </button>

    <ChampRecherche class="recherche" :viewbox="viewbox" @aller="$emit('aller', $event)" />

    <!-- Deux fonds : une bascule, pas un segmenté. Le libellé annonce la
         destination et non l'état courant, sinon on ne sait pas ce que le clic
         va faire. -->
    <button
      type="button"
      class="surface bascule"
      :title="`Passer en ${suivant.label.toLowerCase()}`"
      @click="fond = suivant.id"
    >
      <span class="vignette" :class="`vignette--${suivant.id}`" aria-hidden="true"></span>
      <span>{{ suivant.court ?? suivant.label }}</span>
    </button>
  </div>
</template>

<style scoped>
.barre {
  position: absolute;
  z-index: 3;
  top: 1.5rem;
  right: 1.5rem;
  left: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

/* `:not(.surface)` est nécessaire : scopé, `button` pèse plus lourd que la
   classe `.surface` et lui volait son fond — le bouton « Zones » apparaissait
   transparent alors que les autres blocs de la barre étaient opaques. */
button:not(.surface) {
  border: 0;
  background: none;
  color: inherit;
  font: inherit;
  cursor: pointer;
}

/* On ne touche NI au fond NI à la bordure : `.surface` les porte, y compris le
   liseré du mode sombre. Remettre `border: 0` ici le supprimerait. */
button.surface {
  color: inherit;
  font: inherit;
  cursor: pointer;
}

.zones {
  display: flex;
  align-items: center;
  gap: var(--pad-s);
  height: 3rem;
  padding: 0 var(--pad);
  box-shadow: var(--ombre);
  font-size: 0.9375rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  white-space: nowrap;
}

.zones:hover {
  background: color-mix(in srgb, var(--bg) 92%, #fff);
}

.burger {
  display: none;
}

.tente {
  width: 1.125rem;
  height: 1.125rem;
  flex: 0 0 auto;
  /* La tente reprend la couleur d'accent, comme l'icône d'application. */
  color: var(--accent);
}

.bascule {
  display: flex;
  align-items: center;
  gap: var(--pad-s);
  height: 3rem;
  margin-left: auto;
  padding: 0 var(--pad) 0 0.625rem;
  box-shadow: var(--ombre);
  font-size: 0.8125rem;
  font-weight: 500;
  white-space: nowrap;
}

.bascule:hover {
  background: color-mix(in srgb, var(--bg) 92%, #fff);
}

/* Aperçu du fond visé : plus parlant qu'un mot seul quand on hésite. */
.vignette {
  width: 1.875rem;
  height: 1.875rem;
  flex: 0 0 auto;
  border: 1px solid var(--bord-fort);
  border-radius: var(--rayon-s);
  background-size: cover;
  background-position: center;
}

/* Courbes de niveau sur fond de carte topo. */
.vignette--topo {
  background-color: #f5f0e4;
  background-image:
    repeating-radial-gradient(circle at 62% 72%, #c8a678 0 1px, transparent 1px 5px);
}

/* Camaïeu de verts et de gris : forêt, pierrier, névé. */
.vignette--ign-ortho {
  background-image:
    radial-gradient(circle at 28% 30%, #6f8a52 0 40%, transparent 42%),
    radial-gradient(circle at 74% 68%, #9aa08f 0 38%, transparent 40%),
    linear-gradient(150deg, #4f6b3e, #7d8b6c);
}

@media (max-width: 900px) {
  .barre {
    top: 1rem;
    right: 0.875rem;
    left: 0.875rem;
    gap: 0.625rem;
  }

  /* Une main : la recherche prend la largeur, le bouton du panneau passe à
     droite, sous le pouce. */
  .recherche {
    order: 1;
    width: auto;
    flex: 1;
  }

  .zones {
    order: 2;
    width: var(--cible);
    height: var(--cible);
    padding: 0;
    justify-content: center;
  }

  .zones span:not(.burger) {
    display: none;
  }

  /* Le bouton devient carré et sans libellé : on repasse au burger, qui dit
     « ouvre un panneau ». La tente identifie le projet, elle n'annonce pas une
     action — elle resterait muette une fois seule dans le bouton. */
  .zones .tente {
    display: none;
  }

  .zones .burger {
    display: block;
    width: 1.0625rem;
    height: 0.125rem;
    border-radius: 1px;
    background: var(--fg);
    box-shadow: 0 -0.3125rem 0 var(--fg), 0 0.3125rem 0 var(--fg);
  }

  /* Le segmenté n'avait pas la place en barre haute ; une bascule carrée si,
     réduite à sa vignette. */
  .bascule {
    order: 3;
    width: var(--cible);
    height: var(--cible);
    margin-left: 0;
    padding: 0;
    justify-content: center;
  }

  .bascule span:not(.vignette) {
    display: none;
  }

  .vignette {
    width: 1.625rem;
    height: 1.625rem;
  }
}
</style>
