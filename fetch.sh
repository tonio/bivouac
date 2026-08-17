#!/usr/bin/env bash
# Télécharge les zonages de protection depuis la Géoplateforme IGN (couches PatriNat/INPN).
# ponytail: WFS -> GeoJSON via ogr2ogr, pas de cache ni de reprise. Relancer = retélécharger.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p data

WFS="WFS:https://data.geopf.fr/wfs/ows?VERSION=2.0.0"

# clé_sortie=couche_wfs
LAYERS=(
  pn=patrinat_pn:parc_national
  pnr=patrinat_pnr:pnr
  n2000_zps=patrinat_zps:zps
  n2000_sic=patrinat_sic:sic
  rnn=patrinat_rnn:rnn
  rnr=patrinat_rnr:rnr
  rnc=patrinat_rnc:pnm
  apb=patrinat_apb:apb
  rb=patrinat_rb:rb
  site_classe=patrinat_sc:sc
  cdl=patrinat_cdl:conservatoire_littoral
)

for entry in "${LAYERS[@]}"; do
  key=${entry%%=*}; layer=${entry#*=}
  echo "→ $key ($layer)"
  ogr2ogr -f GeoJSON "data/$key.geojson" "$WFS" "$layer" \
    -t_srs EPSG:4326 -nlt PROMOTE_TO_MULTI -lco RFC7946=YES -overwrite
done

echo "OK"
ls -lh data/
