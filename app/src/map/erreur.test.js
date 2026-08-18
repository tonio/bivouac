// Vérifie les deux règles non évidentes du traitement d'erreur de
// CarteBivouac : ce qui mérite un bandeau, et ce qui l'efface.
// `node src/map/erreur.test.js` — pas de framework, les règles tiennent en
// deux lignes chacune.
import { strict as assert } from 'node:assert'
import { SRC_DATA } from './style.js'

// Répliques des conditions de CarteBivouac.vue. À garder synchrones avec elles.
const signale = (e) => !(e.sourceId && e.sourceId !== SRC_DATA)
const efface = (e) => e.sourceId === SRC_DATA && e.isSourceLoaded

// --- Ce qui se signale ---

// Le cas qui a motivé le correctif : Safari iOS perd des tuiles OpenTopoMap sur
// réseau mobile, le fond s'affiche quand même.
assert.equal(signale({ sourceId: 'fond-detail', error: { message: 'Load failed' } }), false)
assert.equal(signale({ sourceId: 'fond', error: { message: 'Load failed' } }), false)

// L'échec des protections vide la carte de son propos : il se signale.
assert.equal(signale({ sourceId: SRC_DATA, error: { message: 'Load failed' } }), true)

// Erreur sans source (style, WebGL) : on ne sait pas la classer, donc on la
// montre plutôt que de l'avaler.
assert.equal(signale({ error: { message: 'WebGL context lost' } }), true)

// --- Ce qui l'efface ---

// Les protections sont réellement revenues.
assert.equal(efface({ sourceId: SRC_DATA, isSourceLoaded: true }), true)

// Piège corrigé : un `idle` (ou un sourcedata partiel) survient aussi entre deux
// lots de tuiles en échec. Effacer là masquait un pmtiles réellement
// inaccessible — le bandeau disparaissait aussitôt affiché.
assert.equal(efface({ sourceId: SRC_DATA, isSourceLoaded: false }), false)

// Le fond qui se charge ne dit rien de l'état des protections.
assert.equal(efface({ sourceId: 'fond', isSourceLoaded: true }), false)

console.log('ok')
