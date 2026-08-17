// Fonds de carte et sémiologie. Seul fichier à éditer pour ajouter un fond
// ou changer les couleurs.

const IGN = 'https://data.geopf.fr/wmts?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetTile' +
  '&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}'

export const FONDS = [
  {
    id: 'osm',
    label: 'OpenStreetMap',
    tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
    attribution: '© les contributeurs <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxzoom: 19,
  },
  {
    id: 'ign-plan',
    label: 'Plan IGN',
    tiles: [`${IGN}&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&FORMAT=image/png`],
    attribution: '<a href="https://www.ign.fr/">IGN</a> — Plan IGN v2',
    maxzoom: 19,
  },
  {
    id: 'ign-ortho',
    label: 'Photo aérienne',
    tiles: [`${IGN}&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&FORMAT=image/jpeg`],
    attribution: '<a href="https://www.ign.fr/">IGN</a> — Orthophotos',
    maxzoom: 19,
  },
  // SCAN25 (Top25) volontairement absent : la Géoplateforme le refuse (HTTP 400)
  // sans habilitation, sa licence n'étant pas ouverte.
]

// Couleur par sévérité (0 = libre, 5 = interdit). Palette pensée pour rester
// lisible sur photo aérienne comme sur fond clair.
export const SEVERITES = [
  { v: 0, couleur: '#7f8c9b', label: 'Droit commun — aucune règle propre' },
  { v: 1, couleur: '#2f8f4e', label: 'Autorisé sous conditions' },
  { v: 2, couleur: '#c8901a', label: 'Restreint à certaines zones' },
  { v: 3, couleur: '#b5651d', label: 'À vérifier — arrêté au cas par cas' },
  { v: 4, couleur: '#c0392b', label: 'Interdit sauf exception' },
  { v: 5, couleur: '#7d1d13', label: 'Interdit' },
]

// Familles de zonage cochables. `types` référence le champ `type` des données.
export const GROUPES = [
  {
    id: 'parcs',
    label: 'Parcs nationaux',
    types: ['pn'],
    actifDefaut: true,
  },
  {
    id: 'internes',
    label: 'Zonages internes aux parcs',
    types: ['zone_interne', 'aire_bivouac'],
    actifDefaut: true,
  },
  {
    id: 'reserves',
    label: 'Réserves naturelles et biologiques',
    types: ['rnn', 'rnr', 'rnc', 'rb'],
    actifDefaut: true,
  },
  {
    id: 'appb',
    label: 'Arrêtés de protection de biotope',
    types: ['apb'],
    actifDefaut: true,
  },
  {
    id: 'sites',
    label: 'Sites classés et littoral',
    types: ['site_classe', 'cdl'],
    actifDefaut: true,
  },
  {
    id: 'sans_regle',
    label: 'Natura 2000 et PNR',
    types: ['n2000_sic', 'n2000_zps', 'pnr'],
    actifDefaut: false,
    note: "N'interdisent pas le bivouac : gestion contractuelle, pas de pouvoir de police.",
  },
]

export const CENTRE = [2.4, 46.6]
export const ZOOM = 5.2
