<script setup>
import { GROUPES } from '../map/config.js'
import LegendeSeverite from './LegendeSeverite.vue'

defineEmits(['fermer'])

const groupes = defineModel('groupes', { type: Array, required: true })

function basculer(id) {
  const i = groupes.value.indexOf(id)
  groupes.value = i === -1
    ? [...groupes.value, id]
    : groupes.value.filter((g) => g !== id)
}
</script>

<template>
  <aside class="surface panneau">
    <header>
      <h2 class="sureligne">Protections affichées</h2>
      <button type="button" aria-label="Fermer" @click="$emit('fermer')">×</button>
    </header>

    <!-- Plus de sélecteur de fond ici : il n'existait que parce que la barre
         haute masquait son segmenté en mobile. La bascule à deux états y tient,
         réduite à sa vignette. -->

    <ul class="groupes">
      <li v-for="g in GROUPES" :key="g.id">
        <label>
          <input
            type="checkbox"
            :checked="groupes.includes(g.id)"
            @change="basculer(g.id)"
          />
          <span class="case" aria-hidden="true">✓</span>
          <span class="libelle">
            {{ g.label }}
            <span v-if="g.note" class="note">{{ g.note }}</span>
          </span>
        </label>
      </li>
    </ul>

    <!-- En mobile la légende est dépliée ici : c'est le seul endroit où elle
         tient sans masquer la carte. -->
    <LegendeSeverite class="legende-integree" plate />
  </aside>
</template>

<style scoped>
.panneau {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
  overflow-y: auto;
  padding: var(--pad);
  font-size: 0.875rem;
}

header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--pad-s);
}

header button {
  border: 0;
  background: none;
  color: var(--fg-atenue);
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
}

header button:hover {
  color: var(--fg);
}

.groupes {
  display: flex;
  flex-direction: column;
  gap: 0.6875rem;
  margin: 0;
  padding: 0.75rem 0 0;
  border-top: 1px solid var(--bord);
  list-style: none;
}

label {
  display: flex;
  align-items: flex-start;
  gap: 0.6875rem;
  cursor: pointer;
}

/* La case native est masquée mais reste focusable au clavier. */
input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
}

.case {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 1.25rem;
  height: 1.25rem;
  margin-top: 0.0625rem;
  border-radius: var(--pad-xs);
  box-shadow: inset 0 0 0 1.5px #c6c2b6;
  color: transparent;
  font-size: 0.75rem;
  font-weight: 700;
}

input:checked + .case {
  background: var(--accent);
  box-shadow: none;
  color: var(--bg);
}

input:focus-visible + .case {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.libelle {
  display: flex;
  flex-direction: column;
  gap: 0.1875rem;
  font-weight: 500;
  line-height: 1.3;
}

.note {
  color: var(--fg-atenue);
  font-size: 0.75rem;
  font-weight: 400;
  line-height: 1.45;
}

.legende-integree {
  display: none;
  padding-top: 0.75rem;
  border-top: 1px solid var(--bord);
}

@media (max-width: 900px) {
  .case {
    width: 1.25rem;
    height: 1.25rem;
  }

  .legende-integree {
    display: flex;
  }
}

@media (pointer: fine) and (min-width: 901px) {
  .case {
    width: 1.125rem;
    height: 1.125rem;
  }
}
</style>
