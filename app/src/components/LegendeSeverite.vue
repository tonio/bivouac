<script setup>
import { SEVERITES } from '../map/config.js'

// `plate` : rendu sans surface propre, pour l'insertion dans un autre panneau.
defineProps({
  plate: { type: Boolean, default: false },
})
</script>

<template>
  <section :class="['legende', { 'legende--plate': plate, surface: !plate }]">
    <h2 class="sureligne">Règle applicable</h2>
    <ul>
      <li v-for="s in SEVERITES" :key="s.v">
        <span class="pastille" :style="{ background: s.couleur }"></span>
        <span>{{ s.label }}</span>
      </li>
    </ul>
    <p v-if="!plate" class="avertissement">
      Aide à la préparation, sans valeur juridique. Les arrêtés préfectoraux
      (incendie) et municipaux ne figurent pas ici et priment sur ces données.
    </p>
  </section>
</template>

<style scoped>
.legende {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: var(--pad);
  font-size: 0.8125rem;
}

.legende--plate {
  padding: 0;
}

ul {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
  color: var(--fg-doux);
  line-height: 1.3;
  list-style: none;
}

li {
  display: flex;
  align-items: center;
  gap: var(--pad-s);
}

.pastille {
  flex: 0 0 auto;
  width: 0.875rem;
  height: 0.875rem;
  border-radius: 3px;
}

.avertissement {
  margin: 0;
  color: var(--fg-atenue);
  font-size: 0.75rem;
  line-height: 1.55;
}
</style>
