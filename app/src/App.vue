<script setup>
import { ref } from 'vue'
import CarteBivouac from './components/CarteBivouac.vue'
import LegendeCarte from './components/LegendeCarte.vue'
import FicheZonage from './components/FicheZonage.vue'
import { FONDS, GROUPES } from './map/config.js'

const fond = ref(FONDS[0].id)
const groupes = ref(GROUPES.filter((g) => g.actifDefaut).map((g) => g.id))
const selection = ref(null)
</script>

<template>
  <div class="ecran" :class="{ 'ecran--fiche': selection }">
    <LegendeCarte v-model:fond="fond" v-model:groupes="groupes" />
    <CarteBivouac
      :fond="fond"
      :groupes-actifs="groupes"
      @selection="selection = $event"
    />
    <FicheZonage :selection="selection" @fermer="selection = null" />
  </div>
</template>

<style scoped>
.ecran {
  display: grid;
  grid-template-columns: 16rem 1fr;
  height: 100%;
}

.ecran--fiche {
  grid-template-columns: 16rem 1fr 21rem;
}

/* Sous 900 px les panneaux passent au-dessus de la carte plutôt que de la
   comprimer : une carte de 200 px de large ne sert à rien. */
@media (max-width: 900px) {
  .ecran,
  .ecran--fiche {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
    overflow-y: auto;
  }

  .ecran--fiche {
    grid-template-rows: auto 60vh auto;
  }
}
</style>
