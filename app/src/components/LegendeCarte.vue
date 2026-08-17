<script setup>
import { FONDS, GROUPES, SEVERITES } from '../map/config.js'

const fond = defineModel('fond', { type: String, required: true })
const groupes = defineModel('groupes', { type: Array, required: true })

function basculer(id) {
  const i = groupes.value.indexOf(id)
  groupes.value = i === -1
    ? [...groupes.value, id]
    : groupes.value.filter((g) => g !== id)
}
</script>

<template>
  <aside class="legende">
    <h1>Bivouac en France</h1>

    <section>
      <h2>Fond de carte</h2>
      <label v-for="f in FONDS" :key="f.id" class="choix">
        <input type="radio" name="fond" :value="f.id" v-model="fond" />
        <span>{{ f.label }}</span>
      </label>
    </section>

    <section>
      <h2>Zonages affichés</h2>
      <div v-for="g in GROUPES" :key="g.id" class="groupe">
        <label class="choix">
          <input
            type="checkbox"
            :checked="groupes.includes(g.id)"
            @change="basculer(g.id)"
          />
          <span>{{ g.label }}</span>
        </label>
        <p v-if="g.note" class="note">{{ g.note }}</p>
      </div>
    </section>

    <section>
      <h2>Règle applicable</h2>
      <ul class="echelle">
        <li v-for="s in SEVERITES" :key="s.v">
          <span class="pastille" :style="{ background: s.couleur }"></span>
          <span>{{ s.label }}</span>
        </li>
      </ul>
    </section>

    <p class="avertissement">
      Aide à la préparation, sans valeur juridique. Les arrêtés préfectoraux
      (incendie) et municipaux ne figurent pas ici et priment sur ces données.
    </p>
  </aside>
</template>

<style scoped>
.legende {
  overflow-y: auto;
  padding: var(--pad);
  border-right: 1px solid var(--bord);
  background: var(--bg-doux);
  font-size: 0.85rem;
}

h1 {
  margin: 0 0 var(--pad);
  font-size: 1.05rem;
}

h2 {
  margin: 0 0 var(--pad-s);
  color: var(--fg-doux);
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

section {
  margin-bottom: var(--pad);
  padding-bottom: var(--pad);
  border-bottom: 1px solid var(--bord);
}

.choix {
  display: flex;
  align-items: center;
  gap: var(--pad-s);
  padding: 0.15rem 0;
  cursor: pointer;
}

.note {
  margin: 0 0 var(--pad-s) 1.5rem;
  color: var(--fg-doux);
  font-size: 0.74rem;
  font-style: italic;
}

.echelle {
  margin: 0;
  padding: 0;
  list-style: none;
}

.echelle li {
  display: flex;
  align-items: center;
  gap: var(--pad-s);
  padding: 0.15rem 0;
}

.pastille {
  flex: 0 0 auto;
  width: 0.9rem;
  height: 0.9rem;
  border: 1px solid rgb(0 0 0 / 0.25);
  border-radius: 2px;
}

.avertissement {
  margin: 0;
  color: var(--fg-doux);
  font-size: 0.74rem;
  line-height: 1.45;
}
</style>
