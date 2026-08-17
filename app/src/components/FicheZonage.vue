<script setup>
import { computed } from 'vue'
import { SEVERITES } from '../map/config.js'

const props = defineProps({
  selection: { type: Object, default: null },
})
defineEmits(['fermer'])

const LIB_TENTE = {
  aucune_restriction: 'Sans restriction de type',
  legere_sans_station_debout: 'Tente légère, sans station debout',
  sans_tente_uniquement: 'Sans tente uniquement',
  interdite: 'Tente interdite',
}

const LIB_HORAIRE = {
  coucher_soleil: 'coucher du soleil',
  'coucher_soleil-1h': '1 h avant le coucher du soleil',
  'lever_soleil+1h': "1 h après le lever du soleil",
  tombee_nuit: 'tombée de la nuit',
  lever_jour: 'lever du jour',
}

const heure = (h) => (h ? LIB_HORAIRE[h] ?? h : null)
const couleur = (s) => SEVERITES.find((x) => x.v === s)?.couleur ?? '#7f8c9b'

// Le champ regle_json porte la règle complète : les tuiles vectorielles
// n'acceptant pas d'attributs imbriqués, elle est sérialisée à la construction.
function regle(objet) {
  try {
    return JSON.parse(objet.regle_json ?? '{}')
  } catch {
    return {}
  }
}

const fiches = computed(() =>
  (props.selection?.objets ?? []).map((o) => {
    const r = regle(o)
    const loc = r.localisation ?? {}
    const detail = []

    if (r.tente?.type) detail.push(['Tente', LIB_TENTE[r.tente.type] ?? r.tente.type])

    const d = heure(r.horaires?.debut)
    const f = heure(r.horaires?.fin)
    if (d && f) detail.push(['Horaires', `de ${d} à ${f}`])

    if (loc.refuge_obligatoire) detail.push(['Emplacement', 'À proximité immédiate d’un refuge'])
    else if (loc.corridor_m) detail.push(['Emplacement', `À ${loc.corridor_m} m maximum du sentier balisé`])
    else if (loc.distance_min_acces_routier) {
      detail.push(['Emplacement', `À plus de ${loc.distance_min_acces_routier} d’un accès routier`])
    }

    if (r.duree?.nuits_max) detail.push(['Durée', `${r.duree.nuits_max} nuit maximum`])

    if (r.cout?.payant) {
      const montant = r.cout.montant_eur ? `${r.cout.montant_eur} € / ${r.cout.unite ?? 'nuit'}` : 'payant'
      const resa = r.cout.reservation_obligatoire ? ', réservation obligatoire' : ''
      detail.push(['Coût', montant + resa])
    } else if (r.cout && r.cout.payant === false) {
      detail.push(['Coût', 'Gratuit' + (r.cout.reservation_obligatoire ? ', réservation requise' : '')])
    }

    if (r.feu) {
      detail.push(['Feu', r.feu.rechaud_portatif
        ? 'Feu au sol interdit, réchaud portatif autorisé'
        : 'Feu et réchaud interdits'])
    }

    if (r.saison) detail.push(['Saison', r.saison])
    if (o.periode && o.periode !== 'toute l’année') detail.push(['Période', o.periode])
    if (r.sanction) detail.push(['Sanction', r.sanction])

    return {
      cle: `${o.type}|${o.nom}|${o.id_mnhn}`,
      nom: o.nom || o.libelle,
      libelle: o.libelle,
      zone: o.zone,
      resume: o.resume,
      couleur: couleur(o.severite),
      detail,
      interdictions: r.interdictions_associees ?? [],
      zonesParticulieres: r.zones_particulieres ?? null,
      acte: o.acte,
      fiche: o.fiche_inpn,
      source: o.source_url,
      sourceNom: o.source_nom,
      licence: o.source_licence,
      precision: o.precision_geo,
      fiabilite: r.fiabilite,
    }
  }),
)
</script>

<template>
  <aside v-if="selection" class="fiche">
    <header>
      <h2>{{ fiches.length }} zonage{{ fiches.length > 1 ? 's' : '' }} à cet endroit</h2>
      <button type="button" @click="$emit('fermer')" aria-label="Fermer">×</button>
    </header>

    <article v-for="f in fiches" :key="f.cle">
      <h3><span class="pastille" :style="{ background: f.couleur }"></span>{{ f.nom }}</h3>
      <p class="type">
        {{ f.libelle }}<template v-if="f.zone"> — {{ f.zone }}</template>
      </p>

      <p v-if="f.resume" class="resume">{{ f.resume }}</p>

      <dl v-if="f.detail.length">
        <template v-for="[k, v] in f.detail" :key="k">
          <dt>{{ k }}</dt>
          <dd>{{ v }}</dd>
        </template>
      </dl>

      <template v-if="f.interdictions.length">
        <h4>Également interdit</h4>
        <ul>
          <li v-for="i in f.interdictions" :key="i">{{ i }}</li>
        </ul>
      </template>

      <template v-if="f.zonesParticulieres">
        <h4>{{ f.zonesParticulieres.nom ?? 'Zones particulières' }}</h4>
        <p class="resume">{{ f.zonesParticulieres.regle ?? f.zonesParticulieres.liste?.join(', ') }}</p>
      </template>

      <p v-if="f.fiabilite" class="reserve">Fiabilité : {{ f.fiabilite }}</p>
      <p v-if="f.precision" class="reserve">Précision géométrique : {{ f.precision }}</p>

      <p class="sources">
        <span v-if="f.acte" class="acte">{{ f.acte }}</span>
        <a v-if="f.fiche" :href="f.fiche" target="_blank" rel="noopener">Fiche INPN</a>
        <a v-if="f.source" :href="f.source" target="_blank" rel="noopener">
          {{ f.sourceNom ?? 'Source' }}<template v-if="f.licence"> ({{ f.licence }})</template>
        </a>
      </p>
    </article>
  </aside>
</template>

<style scoped>
.fiche {
  overflow-y: auto;
  padding: var(--pad);
  border-left: 1px solid var(--bord);
  background: var(--bg);
  font-size: 0.85rem;
}

header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--pad-s);
  margin-bottom: var(--pad);
}

header h2 {
  margin: 0;
  color: var(--fg-doux);
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

button {
  border: 0;
  background: none;
  color: var(--fg-doux);
  font-size: 1.4rem;
  line-height: 1;
  cursor: pointer;
}

button:hover {
  color: var(--fg);
}

article {
  padding-bottom: var(--pad);
  margin-bottom: var(--pad);
  border-bottom: 1px solid var(--bord);
}

article:last-child {
  border-bottom: 0;
}

h3 {
  display: flex;
  align-items: center;
  gap: var(--pad-s);
  margin: 0 0 0.15rem;
  font-size: 0.95rem;
}

.pastille {
  flex: 0 0 auto;
  width: 0.75rem;
  height: 0.75rem;
  border: 1px solid rgb(0 0 0 / 0.25);
  border-radius: 2px;
}

.type {
  margin: 0 0 var(--pad-s);
  color: var(--fg-doux);
  font-size: 0.76rem;
}

.resume {
  margin: 0 0 var(--pad-s);
  line-height: 1.45;
}

h4 {
  margin: var(--pad-s) 0 0.2rem;
  font-size: 0.78rem;
}

dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.15rem var(--pad-s);
  margin: 0 0 var(--pad-s);
}

dt {
  color: var(--fg-doux);
  font-size: 0.76rem;
}

dd {
  margin: 0;
  font-size: 0.8rem;
}

ul {
  margin: 0 0 var(--pad-s);
  padding-left: 1.1rem;
  font-size: 0.8rem;
  line-height: 1.4;
}

.reserve {
  margin: 0 0 0.2rem;
  color: var(--fg-doux);
  font-size: 0.74rem;
  font-style: italic;
}

.sources {
  display: flex;
  flex-wrap: wrap;
  gap: var(--pad-s);
  margin: var(--pad-s) 0 0;
  font-size: 0.74rem;
}

.acte {
  color: var(--fg-doux);
  font-family: var(--police-mono);
}
</style>
