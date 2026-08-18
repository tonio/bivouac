<script setup>
defineEmits(['zoom', 'localiser'])
</script>

<template>
  <div class="surface controles">
    <button type="button" aria-label="Zoomer" @click="$emit('zoom', 1)">+</button>
    <button type="button" aria-label="Dézoomer" @click="$emit('zoom', -1)">−</button>
    <button type="button" aria-label="Me localiser" @click="$emit('localiser')">⌖</button>
  </div>
</template>

<style scoped>
/* Toujours à droite, y compris en mobile : accessible au pouce droit. */
.controles {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: var(--ombre);
}

button {
  width: var(--cible);
  height: var(--cible);
  border: 0;
  border-bottom: 1px solid var(--bord-fort);
  background: none;
  color: var(--fg);
  font: 400 1.1875rem var(--police);
  cursor: pointer;
}

button:last-child {
  border-bottom: 0;
  font-size: 1rem;
}

button:hover {
  background: var(--bg-doux);
}
</style>
