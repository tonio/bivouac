// Construction du style MapLibre. Les couleurs sont résolues côté GPU par
// expression sur `severite` : aucune boucle JS sur les 7126 objets.
import { FONDS, SEVERITES } from './config.js'

const SRC_FOND = 'fond'
const SRC_DETAIL = 'fond-detail'
const SRC_DATA = 'bivouac'

// ['match', ['get','severite'], 0, '#...', 1, '#...', ..., defaut]
const couleurParSeverite = [
  'match', ['get', 'severite'],
  ...SEVERITES.flatMap(({ v, couleur }) => [v, couleur]),
  '#7f8c9b',
]

export function creerStyle(fondId, pmtilesUrl) {
  const fond = FONDS.find((f) => f.id === fondId) ?? FONDS[0]

  return {
    version: 8,
    // Police bitmap hébergée par MapLibre : évite un serveur de glyphes local.
    glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
    sources: {
      [SRC_FOND]: {
        type: 'raster',
        tiles: fond.tiles,
        tileSize: 256,
        maxzoom: fond.maxzoom,
        attribution: fond.attribution,
      },
      // Second palier du même fond, s'il en déclare un : deux sources
      // superposées plutôt qu'un setStyle au franchissement du seuil, qui
      // ferait clignoter la carte et rechargerait tout le style.
      ...(fond.detail && {
        [SRC_DETAIL]: {
          type: 'raster',
          tiles: fond.detail.tiles,
          tileSize: 256,
          maxzoom: fond.detail.maxzoom,
          attribution: fond.detail.attribution,
        },
      }),
      [SRC_DATA]: {
        type: 'vector',
        url: `pmtiles://${pmtilesUrl}`,
        attribution:
          'Zonages <a href="https://data.geopf.fr/">IGN/PatriNat</a> · ' +
          'règles <a href="https://www.parcsnationaux.fr/">parcs nationaux</a> · ' +
          'zonages internes <a href="https://github.com/PnCevennes/data_reglementation">PN Cévennes</a> (ODbL)',
      },
    },
    layers: [
      { id: 'fond', type: 'raster', source: SRC_FOND },

      // Fondu croisé sur un niveau de zoom : le palier de détail apparaît au
      // seuil sans coupure visible, par-dessus le fond sobre qui reste chargé.
      ...(fond.detail
        ? [{
            id: 'fond-detail',
            type: 'raster',
            source: SRC_DETAIL,
            paint: {
              'raster-opacity': [
                'interpolate', ['linear'], ['zoom'],
                fond.detail.seuil - 1, 0,
                fond.detail.seuil, 1,
              ],
            },
          }]
        : []),

      {
        id: 'zones-remplissage',
        type: 'fill',
        source: SRC_DATA,
        'source-layer': 'zones',
        paint: {
          'fill-color': couleurParSeverite,
          // Les zonages se superposent beaucoup : opacité faible pour que le
          // cumul reste lisible plutôt que d'écraser le fond.
          'fill-opacity': 0.28,
        },
      },
      {
        id: 'zones-contour',
        type: 'line',
        source: SRC_DATA,
        'source-layer': 'zones',
        paint: {
          'line-color': couleurParSeverite,
          // Le contour porte la lecture des limites : sur un fond topographique
          // très texturé, un remplissage à 28 % se noie mais un liseré net reste
          // visible sans masquer les courbes de niveau.
          'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.6, 10, 2, 14, 3],
          'line-opacity': 0.95,
        },
      },
      {
        id: 'points',
        type: 'circle',
        source: SRC_DATA,
        'source-layer': 'points',
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['zoom'], 6, 3.5, 12, 7],
          'circle-color': couleurParSeverite,
          'circle-stroke-width': 1.5,
          'circle-stroke-color': '#ffffff',
        },
      },
      {
        id: 'points-etiquette',
        type: 'symbol',
        source: SRC_DATA,
        'source-layer': 'points',
        minzoom: 9,
        layout: {
          'text-field': ['get', 'nom'],
          'text-font': ['Noto Sans Regular'],
          'text-size': 11,
          'text-offset': [0, 1.1],
          'text-anchor': 'top',
        },
        paint: {
          'text-color': '#1b1f23',
          'text-halo-color': '#ffffff',
          'text-halo-width': 1.5,
        },
      },
    ],
  }
}

export const COUCHES_CLIQUABLES = ['points', 'zones-remplissage']
export { SRC_DATA }
