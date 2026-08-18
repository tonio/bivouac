// Vérifie la seule règle non évidente du handler d'erreur de CarteBivouac :
// ce qui mérite un bandeau et ce qui doit passer en silence.
// `node src/map/erreur.test.js` — pas de framework, la règle tient en 3 lignes.
import { strict as assert } from 'node:assert'
import { SRC_DATA } from './style.js'

// Réplique de la condition de CarteBivouac.vue. Gardée synchrone avec elle :
// si le handler change, ce fichier doit changer aussi.
const signale = (e) => !(e.sourceId && e.sourceId !== SRC_DATA)

// Le cas qui a motivé le correctif : Safari iOS perd des tuiles OpenTopoMap sur
// réseau mobile, le fond s'affiche quand même.
assert.equal(signale({ sourceId: 'fond-detail', error: { message: 'Load failed' } }), false)
assert.equal(signale({ sourceId: 'fond', error: { message: 'Load failed' } }), false)

// L'échec des protections vide la carte de son propos : il se signale.
assert.equal(signale({ sourceId: SRC_DATA, error: { message: 'Load failed' } }), true)

// Erreur sans source (style, WebGL) : on ne sait pas la classer, donc on la
// montre plutôt que de l'avaler.
assert.equal(signale({ error: { message: 'WebGL context lost' } }), true)

console.log('ok')
