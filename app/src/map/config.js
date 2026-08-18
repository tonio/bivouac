// Fonds de carte et sémiologie. Seul fichier à éditer pour ajouter un fond
// ou changer les couleurs.

const IGN = 'https://data.geopf.fr/wmts?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetTile' +
  '&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}'

// Zoom à partir duquel OpenTopoMap devient lisible sous les zonages. Mesuré, pas
// estimé : la saturation moyenne d'une tuile alpine reste à ~0,73 jusqu'à z10
// (teinte hypsométrique, sommets en brun-rouge) puis tombe à ~0,18 à z11, quand
// le rendu passe aux courbes de niveau sur fond clair.
export const SEUIL_TOPO = 11

// Deux fonds seulement, tous deux utiles à la préparation d'un bivouac : la topo
// pour le relief et les sentiers, la photo pour la nature du terrain (pierrier,
// herbe, forêt). OSM standard et le Plan IGN ont été retirés : plats, sans
// courbes de niveau, ils n'apportaient rien ici.
export const FONDS = [
  {
    // Un seul fond dans l'interface, deux sources selon l'échelle : l'utilisateur
    // n'a pas à choisir, il voit « Topo » et la carte reste lisible partout.
    // SCAN25 (la vraie Top25) reste hors de portée : la Géoplateforme le refuse
    // sans habilitation, sa licence n'étant pas ouverte.
    id: 'topo',
    label: 'Carte topographique',
    // Libellé court pour la bascule de la barre haute, où la place manque.
    court: 'Topo',

    // Vue large : fond sobre (beige-gris), sans relief coloré, pour que les
    // zonages ressortent. Style « HOT » d'OSM-France, en ODbL.
    tiles: [
      'https://a.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
      'https://b.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
    ],
    attribution:
      '© les contributeurs <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> | ' +
      'rendu <a href="https://www.hotosm.org/">HOT</a>, hébergé par <a href="https://openstreetmap.fr/">OSM-France</a>',
    maxzoom: 19,

    // Vue rapprochée : courbes de niveau cotées, ombrage, sentiers et éboulis —
    // le rendu le plus proche d'une Top25 disponible librement.
    detail: {
      seuil: SEUIL_TOPO,
      tiles: [
        'https://a.tile.opentopomap.org/{z}/{x}/{y}.png',
        'https://b.tile.opentopomap.org/{z}/{x}/{y}.png',
        'https://c.tile.opentopomap.org/{z}/{x}/{y}.png',
      ],
      // Attribution imposée telle quelle par la licence CC-BY-SA d'OpenTopoMap.
      attribution:
        'Données : © les contributeurs <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, SRTM | ' +
        'rendu : © <a href="https://opentopomap.org/">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
      // OpenTopoMap s'arrête à 17 ; au-delà MapLibre sur-zoome la dernière tuile.
      maxzoom: 17,
    },
  },
  {
    id: 'ign-ortho',
    label: 'Photo aérienne',
    court: 'Photo',
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

// Habillage du bloc « verdict » en tête de fiche, indexé par sévérité : la plus
// contraignante des protections empilées colore le bloc entier. Deux jeux, le
// thème sombre ne se déduit pas du clair par simple opacité sans perdre le
// contraste.
// La couleur d'accent se nomme `accent` et non `label` : SEVERITES.label est un
// libellé texte, et les deux clés se sont déjà écrasées dans un spread — la
// couleur s'affichait à la place du mot.
export const VERDICT = {
  clair: [
    { fond: '#eef1f3', accent: '#5e6b78', texte: '#243039' },
    { fond: '#e7f2ea', accent: '#3c7a55', texte: '#123b25' },
    { fond: '#f7eedc', accent: '#8a6413', texte: '#4a360a' },
    { fond: '#f6e9dc', accent: '#8a4c15', texte: '#43230a' },
    { fond: '#fbe9e5', accent: '#93291f', texte: '#4a130c' },
    { fond: '#f6e2de', accent: '#7d1d13', texte: '#3a0d07' },
  ],
  sombre: [
    { fond: '#212a2f', accent: '#9fb0bd', texte: '#e6edf2' },
    { fond: '#17301f', accent: '#7fc79b', texte: '#e4f4ea' },
    { fond: '#33270e', accent: '#e0b45c', texte: '#f7ecd6' },
    { fond: '#33210f', accent: '#dda169', texte: '#f6e6d8' },
    { fond: '#3a1a15', accent: '#e3a79e', texte: '#fbe9e5' },
    { fond: '#31130e', accent: '#d99286', texte: '#f7dfda' },
  ],
}

// Familles de protection cochables. `types` référence le champ `type` des données.
export const GROUPES = [
  {
    id: 'parcs',
    label: 'Parcs nationaux',
    types: ['pn'],
    actifDefaut: true,
  },
  {
    id: 'internes',
    label: 'Secteurs réglementés des parcs',
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

// Emprise de la France métropolitaine. Préférée au couple centre/zoom au
// chargement : un zoom fixe coupe la Bretagne et l'Alsace sur un écran
// portrait. fitBounds s'adapte au format réel.
export const EMPRISE = [[-5.3, 41.3], [9.7, 51.2]]
