<script setup>
import { computed, onUnmounted, ref, watch } from 'vue'
import { SEVERITES, VERDICT } from '../map/config.js'

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
  lever_soleil: 'lever du soleil',
  'lever_soleil+1h': "1 h après le lever du soleil",
  tombee_nuit: 'tombée de la nuit',
  lever_jour: 'lever du jour',
}

const heure = (h) => (h ? LIB_HORAIRE[h] ?? h : null)
const couleur = (s) => SEVERITES.find((x) => x.v === s)?.couleur ?? '#7f8c9b'

// Coupe au dernier espace avant la limite, pour ne pas tronquer un mot.
const abrege = (t, max) =>
  t.length <= max ? t : t.slice(0, t.lastIndexOf(' ', max)).replace(/[,;:]$/, '') + '…'

// Le repli ne concerne que la feuille mobile, où elle masquerait la carte que
// l'on vient de toucher. En desktop, la poignée et le bouton « voir plus » sont
// masqués en CSS : replier y rendrait le détail inatteignable.
// Même borne que le @media du bloc mobile.
const feuille = window.matchMedia('(max-width: 900px)')
const enFeuille = ref(feuille.matches)
const replie = ref(feuille.matches)

const onFormat = (e) => {
  enFeuille.value = e.matches
  replie.value = e.matches
}
feuille.addEventListener('change', onFormat)

// Le bloc verdict porte ses couleurs en style inline : sans suivre le thème, un
// basculement clair/sombre le laisserait dans l'ancienne palette.
const theme = window.matchMedia('(prefers-color-scheme: dark)')
const sombre = ref(theme.matches)
const onTheme = (e) => { sombre.value = e.matches }
theme.addEventListener('change', onTheme)

onUnmounted(() => {
  feuille.removeEventListener('change', onFormat)
  theme.removeEventListener('change', onTheme)
})

// `deplie` pilote le style de la feuille : toujours vrai hors mobile.
const deplie = computed(() => !enFeuille.value || !replie.value)

watch(() => props.selection, () => {
  replie.value = enFeuille.value
})

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

    // Les aires nommées par l'acte sont l'information la plus actionnable
    // quand le bivouac n'est autorisé que là : les lister vaut mieux que le
    // seul « aires désignées » du champ contrainte.
    if (loc.aires_designees?.length) {
      detail.push(['Aires autorisées', loc.aires_designees.join(' · ')])
    }

    if (r.saison) detail.push(['Saison', r.saison])
    if (o.periode && o.periode !== 'toute l’année') detail.push(['Période', o.periode])
    // La sanction porte désormais son raisonnement juridique complet (jusqu'à
    // ~500 caractères) : on tronque à la longueur, le détail restant dans
    // regle_json pour qui lit les données. Couper sur la ponctuation ne marche
    // pas ici — « C. env. », « art. » abondent et donnent des bouts inutiles.
    if (r.sanction) detail.push(['Sanction', abrege(r.sanction, 150)])

    return {
      cle: `${o.type}|${o.nom}|${o.id_mnhn}`,
      nom: o.nom || o.libelle,
      libelle: o.libelle,
      zone: o.zone,
      resume: o.resume,
      severite: o.severite ?? 0,
      couleur: couleur(o.severite),
      detail,
      interdictions: r.interdictions_associees ?? [],
      zonesParticulieres: r.zones_particulieres ?? null,
      saisonniere: r.restriction_saisonniere ?? null,
      attention: r.attention ?? null,
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

// Les objets arrivent déjà triés par sévérité décroissante : le premier porte
// la règle qui s'applique réellement sur place.
const chef = computed(() => fiches.value[0] ?? null)
const verdict = computed(() => {
  if (!chef.value) return null
  const s = chef.value.severite
  const jeu = sombre.value ? VERDICT.sombre : VERDICT.clair
  return {
    label: SEVERITES.find((x) => x.v === s)?.label ?? '',
    nom: chef.value.nom,
    // Repli sur la sévérité 0 : une valeur hors bornes laisserait le bloc sans
    // aucune couleur.
    ...(jeu[s] ?? jeu[0]),
  }
})
</script>

<template>
  <aside v-if="selection" class="surface fiche" :class="{ 'fiche--depliee': deplie }">
    <button
      type="button"
      class="poignee"
      aria-label="Déplier ou replier la fiche"
      :aria-expanded="deplie"
      @click="replie = !replie"
    ></button>

    <header>
      <h2 class="sureligne">
        {{ fiches.length }} protection{{ fiches.length > 1 ? 's' : '' }} à cet endroit
      </h2>
      <button type="button" class="fermer" aria-label="Fermer" @click="$emit('fermer')">×</button>
    </header>

    <!-- Le verdict : la règle la plus contraignante des protections empilées.
         C'est la seule information dont le randonneur a besoin en premier. -->
    <div
      v-if="verdict"
      class="verdict"
      :style="{ background: verdict.fond, color: verdict.texte }"
    >
      <p class="sureligne" :style="{ color: verdict.accent }">Ici, la règle la plus contraignante</p>
      <p class="verdict-titre">{{ verdict.label }}</p>
      <p class="verdict-nom">{{ verdict.nom }}</p>
    </div>

    <button v-if="!deplie" type="button" class="voir-plus" @click="replie = false">
      Voir les {{ fiches.length }} protection{{ fiches.length > 1 ? 's' : '' }} et leurs règles ▴
    </button>

    <div v-show="deplie" class="liste">
      <article v-for="f in fiches" :key="f.cle">
        <div class="entete">
          <span class="pastille" :style="{ background: f.couleur }"></span>
          <span class="titres">
            <span class="nom">{{ f.nom }}</span>
            <span class="type">
              {{ f.libelle }}<template v-if="f.zone"> — {{ f.zone }}</template>
            </span>
            <span v-if="f.resume" class="resume">{{ f.resume }}</span>
          </span>
        </div>

        <div class="detail">
          <dl v-if="f.detail.length">
            <template v-for="[k, v] in f.detail" :key="k">
              <dt>{{ k }}</dt>
              <dd>{{ v }}</dd>
            </template>
          </dl>

          <p v-if="f.saisonniere" class="alerte">
            <strong>{{ f.saisonniere.periode }}</strong> — {{ f.saisonniere.regle }}
          </p>
          <p v-if="f.attention" class="alerte">{{ f.attention }}</p>

          <template v-if="f.interdictions.length">
            <h4>Également interdit</h4>
            <ul>
              <li v-for="x in f.interdictions" :key="x">{{ x }}</li>
            </ul>
          </template>

          <template v-if="f.zonesParticulieres">
            <h4>{{ f.zonesParticulieres.nom ?? 'Zones particulières' }}</h4>
            <p class="resume">
              {{ f.zonesParticulieres.regle ?? f.zonesParticulieres.liste?.join(', ') }}
            </p>
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
        </div>
      </article>

      <p class="avertissement">
        Aide à la préparation, sans valeur juridique. Les arrêtés préfectoraux
        (incendie) et municipaux ne figurent pas ici et priment sur ces données.
      </p>
    </div>
  </aside>
</template>

<style scoped>
/* Desktop : panneau flottant à droite, sous les boutons de carte pour ne pas
   les rendre incliquables. Hauteur = contenu, plafonnée. */
.fiche {
  position: absolute;
  z-index: 3;
  top: 13.75rem;
  right: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 24.5rem;
  max-height: calc(100% - 15.25rem);
  overflow-y: auto;
  padding: 1.25rem;
  box-shadow: var(--ombre-fiche);
  font-size: 0.875rem;
}

/* La poignée n'a de sens qu'en feuille mobile. */
.poignee {
  display: none;
}

header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--pad-s);
}

.fermer {
  border: 0;
  background: none;
  color: var(--fg-atenue);
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
}

.fermer:hover {
  color: var(--fg);
}

.verdict {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  padding: 1rem;
  border-radius: 6px;
}

.verdict-titre {
  margin: 0;
  font: 400 1.875rem/1.05 var(--police-titre);
}

.verdict-nom {
  margin: 0;
  font-size: 0.8125rem;
  line-height: 1.5;
  opacity: 0.85;
}

.voir-plus {
  display: none;
}

.liste {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

article {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  padding-bottom: 0.875rem;
  border-bottom: 1px solid var(--bord);
}

article:last-of-type {
  border-bottom: 0;
}

.entete {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.pastille {
  flex: 0 0 auto;
  width: 0.75rem;
  height: 0.75rem;
  margin-top: 0.25rem;
  border-radius: 3px;
}

.titres {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 0.375rem;
}

.nom {
  font-size: 0.9375rem;
  font-weight: 600;
  line-height: 1.25;
}

.type {
  color: var(--fg-atenue);
  font-size: 0.75rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.resume {
  color: var(--fg-doux);
  font-size: 0.8125rem;
  font-weight: 400;
  line-height: 1.55;
  text-wrap: pretty;
}

.detail {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  padding-left: 1.5rem;
}

dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.4375rem 0.875rem;
  margin: 0;
  font-size: 0.8125rem;
  line-height: 1.4;
}

dt {
  color: var(--fg-atenue);
}

dd {
  margin: 0;
}

h4 {
  margin: 0;
  font-size: 0.8125rem;
}

ul {
  margin: 0;
  padding-left: 1.1rem;
  font-size: 0.8125rem;
  line-height: 1.45;
}

/* Une restriction saisonnière est souvent l'information décisive : elle doit
   se distinguer du résumé. */
.alerte {
  margin: 0;
  padding: 0.6875rem 0.8125rem;
  border-radius: var(--rayon-s);
  background: color-mix(in srgb, #c8901a 13%, transparent);
  box-shadow: inset 3px 0 0 #c8901a;
  font-size: 0.75rem;
  line-height: 1.5;
}

.reserve {
  margin: 0;
  color: var(--fg-atenue);
  font-size: 0.75rem;
  font-style: italic;
}

.sources {
  display: flex;
  flex-wrap: wrap;
  gap: var(--pad-s);
  margin: 0;
  color: var(--fg-atenue);
  font-size: 0.6875rem;
}

.acte {
  font-family: var(--police-mono);
}

.avertissement {
  margin: 0;
  color: var(--fg-atenue);
  font-size: 0.75rem;
  line-height: 1.55;
}

/* Mobile : feuille du bas à deux crans. Repliée, elle ne montre que le
   verdict et laisse la carte cliquable. */
@media (max-width: 900px) {
  .fiche {
    top: auto;
    right: 0.875rem;
    bottom: 0.875rem;
    left: 0.875rem;
    width: auto;
    max-height: 33rem;
    gap: 0.875rem;
    padding: 1rem;
    border-radius: var(--rayon-feuille);
    box-shadow: var(--ombre-feuille);
  }

  .poignee {
    display: block;
    width: 3.25rem;
    height: 0.3125rem;
    align-self: center;
    border: 0;
    border-radius: 3px;
    background: #ddd6c8;
    cursor: pointer;
  }

  .verdict-titre {
    font-size: 1.6875rem;
  }

  .voir-plus {
    display: block;
    padding: 0;
    border: 0;
    background: none;
    color: var(--accent);
    font: 500 0.8125rem/1.4 var(--police);
    text-align: left;
    cursor: pointer;
  }

  .type {
    display: none;
  }

  .detail {
    padding-left: 0;
  }
}

@media (prefers-color-scheme: dark) and (max-width: 900px) {
  .poignee {
    background: #3a4247;
  }
}
</style>
