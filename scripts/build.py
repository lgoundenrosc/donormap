"""Assemble index.html from src/template.html, data/prospects.js and the map
code in lgoundenrosc/Assets (maps/us-base-map.html). Run after prep.py:
    python3 scripts/prep.py && python3 scripts/build.py
Set ASSETS_DIR if the Assets checkout is not at ../Assets."""
import os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assets = os.environ.get('ASSETS_DIR', os.path.join(os.path.dirname(ROOT), 'Assets'))
base = open(os.path.join(assets, 'maps', 'us-base-map.html')).read()
# Take US_STATES through insetStates: data plus projection helpers, verbatim.
start = base.index('var US_STATES = {')
end = base.index('(function () {', start)
mapjs = base[start:end].rstrip()
tpl = open(os.path.join(ROOT, 'src', 'template.html')).read()
data = open(os.path.join(ROOT, 'data', 'prospects.js')).read()
html = tpl.replace('/*MAPJS*/', mapjs)
html = html.replace('/*DATA*/', data.replace('</', '<\\/'))
open(os.path.join(ROOT, 'index.html'), 'w').write(html)
print('index.html', len(html) // 1024, 'KB')
