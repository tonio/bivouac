<script setup>
import { ref } from 'vue'
import CarteBivouac from './components/CarteBivouac.vue'
import BarreHaute from './components/BarreHaute.vue'
import PanneauProtections from './components/PanneauProtections.vue'
import LegendeSeverite from './components/LegendeSeverite.vue'
import ControlesCarte from './components/ControlesCarte.vue'
import FicheZonage from './components/FicheZonage.vue'
import BandeauMaj from './components/BandeauMaj.vue'
import { FONDS, GROUPES } from './map/config.js'

const fond = ref(FONDS[0].id)
const groupes = ref(GROUPES.filter((g) => g.actifDefaut).map((g) => g.id))
const selection = ref(null)

// Le panneau des protections est masqué au chargement : la carte est l'écran,
// tout le reste se demande.
const panneau = ref(false)
const carte = ref(null)

// Emprise courante, transmise à la recherche pour privilégier les résultats
// proches de ce que l'utilisateur regarde (« la valette » → celle de Vanoise
// si la carte est sur la Vanoise).
const viewbox = ref(null)
</script>

<template>
  <div class="ecran">
    <CarteBivouac
      ref="carte"
      :fond="fond"
      :groupes-actifs="groupes"
      @selection="selection = $event"
      @emprise="viewbox = $event"
    />

    <BarreHaute
      v-model:fond="fond"
      :panneau-ouvert="panneau"
      :viewbox="viewbox"
      @basculer-panneau="panneau = !panneau"
      @aller="carte?.allerA($event)"
    />

    <PanneauProtections
      v-if="panneau"
      v-model:groupes="groupes"
      class="panneau"
      @fermer="panneau = false"
    />

    <!-- En mobile la légende vit dans le panneau : ici on n'affiche que la
         version flottante permanente du desktop. -->
    <LegendeSeverite class="legende" />

    <ControlesCarte
      class="controles"
      @zoom="carte?.zoomer($event)"
      @localiser="carte?.localiser()"
    />

    <FicheZonage :selection="selection" @fermer="selection = null" />

    <BandeauMaj />
  </div>
</template>

<style scoped>
/* La carte occupe tout : les panneaux flottent au-dessus et leur hauteur suit
   leur contenu. Aucune colonne fixe ne comprime plus la carte. */
.ecran {
  position: relative;
  height: 100%;
  overflow: hidden;
}

/* Les 5.5rem se comptent SOUS la barre haute, elle-même décalée des marges
   sûres : les panneaux flottants héritent donc du même décalage. */
.panneau {
  position: absolute;
  z-index: 2;
  top: calc(var(--sur-haut) + 5.5rem);
  left: calc(var(--sur-gauche) + 1.5rem);
  width: 18.5rem;
  max-height: calc(100% - var(--sur-haut) - var(--sur-bas) - 12rem);
}

.legende {
  position: absolute;
  z-index: 1;
  bottom: calc(var(--sur-bas) + 3.5rem);
  left: calc(var(--sur-gauche) + 1.5rem);
  width: 18.5rem;
}

.controles {
  position: absolute;
  z-index: 2;
  top: calc(var(--sur-haut) + 5.5rem);
  right: calc(var(--sur-droite) + 1.5rem);
}

@media (max-width: 900px) {
  .panneau {
    top: calc(var(--sur-haut) + 4.875rem);
    left: calc(var(--sur-gauche) + 0.875rem);
    width: 18.75rem;
    max-width: calc(100% - var(--sur-gauche) - var(--sur-droite) - 1.75rem);
    max-height: calc(100% - var(--sur-haut) - var(--sur-bas) - 7rem);
  }

  .controles {
    top: calc(var(--sur-haut) + 4.875rem);
    right: calc(var(--sur-droite) + 0.875rem);
  }

  /* La légende n'est plus permanente : elle est dépliée dans le panneau. */
  .legende {
    display: none;
  }
}
</style>
