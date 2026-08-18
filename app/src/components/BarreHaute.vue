<script setup>
import { FONDS } from '../map/config.js'

defineProps({
  panneauOuvert: { type: Boolean, default: false },
})
defineEmits(['basculer-panneau'])

const fond = defineModel('fond', { type: String, required: true })
</script>

<template>
  <div class="barre">
    <!-- Le titre ne servait à rien : il ouvre le panneau des protections. -->
    <button
      type="button"
      class="surface zones"
      :aria-expanded="panneauOuvert"
      @click="$emit('basculer-panneau')"
    >
      <span class="point"></span>
      <span>Zones</span>
    </button>

    <label class="surface recherche">
      <span class="loupe" aria-hidden="true">⌕</span>
      <input type="search" placeholder="Rechercher un lieu, un massif, un refuge…" />
    </label>

    <div class="surface fonds" role="radiogroup" aria-label="Fond de carte">
      <button
        v-for="f in FONDS"
        :key="f.id"
        type="button"
        role="radio"
        :aria-checked="fond === f.id"
        :class="{ actif: fond === f.id }"
        :title="f.label"
        @click="fond = f.id"
      >
        {{ f.court ?? f.label }}
      </button>
    </div>
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

.point {
  width: 0.5625rem;
  height: 0.5625rem;
  border-radius: 50%;
  background: var(--repere);
}

.recherche {
  display: flex;
  align-items: center;
  gap: 0.5625rem;
  width: 22.5rem;
  height: 3rem;
  padding: 0 1rem;
  box-shadow: var(--ombre);
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

/* Le focus est porté par la surface entière plutôt que par le champ, sinon
   l'outline se dessine à l'intérieur du bloc et se lit mal. */
.recherche:focus-within {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.recherche input:focus-visible {
  outline: none;
}

.fonds {
  display: flex;
  gap: var(--pad-xs);
  height: 3rem;
  margin-left: auto;
  padding: 0.3125rem;
  box-shadow: var(--ombre);
}

.fonds button {
  padding: 0 1rem;
  border-radius: var(--rayon-s);
  color: var(--fg-secondaire);
  font-size: 0.8125rem;
  font-weight: 500;
}

.fonds button.actif {
  background: var(--bg-doux);
  color: var(--fg);
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

  .zones span:not(.point) {
    display: none;
  }

  .zones .point {
    width: 1.0625rem;
    height: 0.125rem;
    border-radius: 1px;
    background: var(--fg);
    box-shadow: 0 -0.3125rem 0 var(--fg), 0 0.3125rem 0 var(--fg);
  }

  /* Le segmenté de fond rejoint le panneau : pas de place en barre haute. */
  .fonds {
    display: none;
  }
}
</style>
