#!/usr/bin/env bash
# Refuges du massif de la Vanoise depuis OpenStreetMap (Overpass).
# Sert à positionner les aires de bivouac que le parc ne publie qu'en PDF.
# ponytail: bbox du massif en dur — les refuges ne bougent pas.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p data

curl -sS -m 180 -A "bivouac-data/1.0 (+usage non commercial)" \
  --data-binary '
[out:json][timeout:120];
// nwr = nodes + ways + relations : certains refuges sont des relations,
// que node/way seuls laissent passer (ex. Fond des Fours).
nwr["tourism"~"alpine_hut|wilderness_hut"](45.10,6.45,45.70,7.40);
out center tags;' \
  -o data/osm_refuges_vanoise.json \
  "https://overpass-api.de/api/interpreter"

python3 -c "
import json
n=len(json.load(open('data/osm_refuges_vanoise.json'))['elements'])
print(f'{n} refuges OSM -> data/osm_refuges_vanoise.json')
"
