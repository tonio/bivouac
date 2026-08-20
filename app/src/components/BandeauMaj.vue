<script setup>
// Mise à jour du service worker, proposée et non imposée : les règles affichées
// ont une portée juridique, un rechargement surprise en pleine lecture d'une
// fiche est le mauvais moment. D'où registerType: 'prompt' côté vite.config.
import { ref } from 'vue'
import { registerSW } from 'virtual:pwa-register'

const dispo = ref(false)
const horsLigne = ref(false)

const majSW = registerSW({
  onNeedRefresh: () => (dispo.value = true),
  // Précache terminé : la coquille est disponible hors ligne. La donnée, non —
  // le libellé le dit explicitement plutôt que de laisser croire à un mode
  // hors-ligne complet.
  onOfflineReady: () => {
    horsLigne.value = true
    setTimeout(() => (horsLigne.value = false), 6000)
  },
})
</script>

<template>
  <div v-if="dispo || horsLigne" class="bandeau surface" role="status">
    <template v-if="dispo">
      <span>Une nouvelle version est disponible.</span>
      <button type="button" class="actualiser" @click="majSW(true)">Actualiser</button>
      <button type="button" class="plus-tard" @click="dispo = false">Plus tard</button>
    </template>
    <template v-else>
      <span>Application disponible hors ligne — la carte, elle, a besoin du réseau.</span>
      <button type="button" class="plus-tard" @click="horsLigne = false">OK</button>
    </template>
  </div>
</template>

<style scoped>
.bandeau {
  position: absolute;
  /* Au-dessus de la marge sûre : en PWA plein écran, le bas de l'écran est
     occupé par la barre de gestes. */
  bottom: calc(env(safe-area-inset-bottom, 0px) + var(--pad));
  left: 50%;
  transform: translateX(-50%);
  z-index: 5;
  display: flex;
  gap: var(--pad-s);
  align-items: center;
  max-width: min(30rem, calc(100vw - 2 * var(--pad)));
  padding: var(--pad-s) var(--pad);
  border-radius: var(--rayon);
  box-shadow: var(--ombre-panneau);
  font-size: 0.875rem;
  line-height: 1.35;
}

button {
  flex: none;
  min-height: var(--cible);
  padding: 0 var(--pad-s);
  border: 0;
  border-radius: var(--rayon-s);
  background: none;
  color: var(--accent);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.plus-tard {
  color: var(--fg-secondaire);
  font-weight: 500;
}

button:hover {
  background: var(--bg-doux);
}

@media (pointer: fine) {
  button {
    min-height: 2.5rem;
  }
}
</style>
