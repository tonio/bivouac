// Géocodage via Nominatim (OpenStreetMap).
//
// Pourquoi pas la BAN (api-adresse.data.gouv.fr) : elle ne connaît que des
// adresses postales. « refuge de l'Arpont » y renvoie « Le Refuge de l'Arche »
// en Mayenne. Nominatim rend le bon refuge avec son type `alpine_hut`, et
// couvre lacs, cols, sommets, hameaux et parkings — ce qu'on cherche pour un
// bivouac.
//
// Contraintes de la politique d'usage de Nominatim, à respecter :
//   - 1 requête/seconde maximum ;
//   - l'autocomplétion à chaque frappe est « strongly discouraged » ;
//   - User-Agent identifiant l'application obligatoire (impossible à définir
//     depuis un navigateur : le Referer joue ce rôle) ;
//   - attribution visible.
// D'où un debounce large, l'annulation des requêtes obsolètes et un cache.
// https://operations.osmfoundation.org/policies/nominatim/

const ENDPOINT = 'https://nominatim.openstreetmap.org/search'

export const DELAI_SAISIE = 600
const MIN_CARACTERES = 3

// Types OSM utiles au bivouac, avec leur libellé et leur priorité d'affichage.
// Un type absent d'ici reste affiché, mais après ceux-ci.
const TYPES = {
  alpine_hut: { label: 'Refuge', rang: 0 },
  wilderness_hut: { label: 'Cabane', rang: 0 },
  shelter: { label: 'Abri', rang: 1 },
  parking: { label: 'Parking', rang: 1 },
  peak: { label: 'Sommet', rang: 2 },
  saddle: { label: 'Col', rang: 2 },
  lake: { label: 'Lac', rang: 2 },
  water: { label: 'Lac', rang: 2 },
  reservoir: { label: 'Lac', rang: 2 },
  glacier: { label: 'Glacier', rang: 2 },
  hamlet: { label: 'Hameau', rang: 3 },
  isolated_dwelling: { label: 'Lieu-dit', rang: 3 },
  locality: { label: 'Lieu-dit', rang: 3 },
  village: { label: 'Village', rang: 3 },
  town: { label: 'Commune', rang: 3 },
  city: { label: 'Commune', rang: 3 },
  administrative: { label: 'Commune', rang: 4 },
  valley: { label: 'Vallée', rang: 4 },
  spring: { label: 'Source', rang: 4 },
  stream: { label: 'Cours d’eau', rang: 6 },
  river: { label: 'Cours d’eau', rang: 6 },
  guidepost: { label: 'Balise', rang: 7 },
  helipad: { label: 'Hélisurface', rang: 8 },
}

const cache = new Map()

// « Refuge de l'Arpont, Lac -auberge de Bellecombe, Termignon, Val-Cenis,
// Saint-Jean-de-Maurienne, Savoie, … » → nom + deux échelons de contexte.
function decouper(nomComplet) {
  const bouts = (nomComplet ?? '').split(',').map((s) => s.trim()).filter(Boolean)
  return { nom: bouts[0] ?? '', contexte: bouts.slice(1, 3).join(', ') }
}

function normaliser(r) {
  const { nom, contexte } = decouper(r.display_name)
  const t = TYPES[r.type] ?? TYPES[r.class]
  return {
    id: `${r.osm_type ?? ''}${r.osm_id ?? r.place_id}`,
    nom,
    contexte,
    categorie: t?.label ?? '',
    rang: t?.rang ?? 5,
    lon: Number(r.lon),
    lat: Number(r.lat),
    // boundingbox = [sud, nord, ouest, est] ; on la convertit pour fitBounds.
    emprise: r.boundingbox
      ? [
          [Number(r.boundingbox[2]), Number(r.boundingbox[0])],
          [Number(r.boundingbox[3]), Number(r.boundingbox[1])],
        ]
      : null,
  }
}

/**
 * @param {string} texte saisie de l'utilisateur
 * @param {object} opts  { signal, viewbox } — viewbox = [[o,s],[e,n]] de la vue
 *                       courante, pour privilégier les résultats proches sans
 *                       exclure le reste du pays.
 */
export async function chercher(texte, { signal, viewbox } = {}) {
  const q = texte.trim()
  if (q.length < MIN_CARACTERES) return []

  const cle = `${q}|${viewbox ? viewbox.flat().map((v) => v.toFixed(1)).join(',') : ''}`
  if (cache.has(cle)) return cache.get(cle)

  const params = new URLSearchParams({
    q,
    format: 'jsonv2',
    limit: '8',
    countrycodes: 'fr',
    'accept-language': 'fr',
  })
  if (viewbox) {
    // Sans `bounded`, la vue ne fait que remonter les résultats proches :
    // « la valette » donne la vallée en Vanoise avant l'homonyme grenoblois.
    params.set('viewbox', viewbox.flat().join(','))
  }

  const r = await fetch(`${ENDPOINT}?${params}`, { signal })
  if (!r.ok) throw new Error(`Nominatim ${r.status}`)

  const resultats = (await r.json())
    .map(normaliser)
    .sort((a, b) => a.rang - b.rang)

  cache.set(cle, resultats)
  return resultats
}
