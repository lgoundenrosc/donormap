#!/usr/bin/env bash
# Download Census 2023 town boundaries (county subdivisions, 1:500k) for the six
# New England states plus New York, and Natural Earth provinces for Canada, then
# project and simplify with mapshaper. Run from the folder that holds geo/.
set -euo pipefail
mkdir -p geo && cd geo
for f in 09 23 25 33 44 50; do
  curl -sSO "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_${f}_cousub_500k.zip"
  unzip -oq "cb_2023_${f}_cousub_500k.zip" -d "cb_2023_${f}_cousub_500k"
done
curl -sSO https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_state_500k.zip
unzip -oq cb_2023_us_state_500k.zip -d cb_2023_us_state_500k
curl -sS -o ne10.geojson https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson
python3 -I - <<'PY'
import json
g = json.load(open('ne10.geojson'))
keep = [f for f in g['features'] if f['properties'].get('admin') == 'Canada' and f['properties'].get('name') in ('Québec', 'New Brunswick', 'Nova Scotia', 'Prince Edward Island')]
json.dump({'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'name': f['properties']['name']}, 'geometry': f['geometry']} for f in keep]}, open('canada.geojson', 'w'))
PY
P="+proj=eqc +lat_ts=44 +lat_0=44 +lon_0=-70.3 +units=m +ellps=GRS80"
npx -y mapshaper@0.6.102 -i combine-files cb_2023_{09,23,25,33,44,50}_cousub_500k/*.shp -merge-layers force name=towns \
  -filter 'ALAND > 0' -filter-fields GEOID,NAME,NAMELSAD,STUSPS,NAMELSADCO -proj "$P" \
  -simplify interval=90 keep-shapes -clean -o towns.json format=geojson precision=1 \
  -dissolve STUSPS name=states -o states.json format=geojson precision=1
npx -y mapshaper@0.6.102 -i cb_2023_us_state_500k/cb_2023_us_state_500k.shp -filter 'NAME=="New York"' -filter-fields NAME \
  -proj "$P" -simplify interval=250 keep-shapes -o ny.json format=geojson precision=1
npx -y mapshaper@0.6.102 -i canada.geojson -proj "$P" -simplify interval=250 keep-shapes -o can.json format=geojson precision=1
