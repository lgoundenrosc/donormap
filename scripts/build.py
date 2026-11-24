"""Assemble the explorer from src/template.html, data/prospects.js and the map
code in lgoundenrosc/Assets (maps/us-base-map.html). Run after prep.py:
    python3 scripts/prep.py && python3 scripts/build.py
Writes two builds:
  index.html          standalone file with the data inlined (open locally)
  dist/page.html      hosted build for the claude.ai artifact, which loads
  dist/prospects.json the data from this file beside it
Set ASSETS_DIR if the Assets checkout is not at ../Assets."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assets = os.environ.get('ASSETS_DIR', os.path.join(os.path.dirname(ROOT), 'Assets'))
base = open(os.path.join(assets, 'maps', 'us-base-map.html')).read()
# US_STATES through insetStates: boundary data plus projection helpers, verbatim.
start = base.index('var US_STATES = {')
end = base.index('(function () {', start)
mapjs = base[start:end].rstrip()
tpl = open(os.path.join(ROOT, 'src', 'template.html')).read().replace('/*MAPJS*/', mapjs)
data = open(os.path.join(ROOT, 'data', 'prospects.js')).read()

# 1. standalone
html = tpl.replace('/*DATA*/', data.replace('</', '<\\/'))
open(os.path.join(ROOT, 'index.html'), 'w').write(html)
print('index.html', len(html) // 1024, 'KB')

# 2. hosted: the host supplies doctype, head and body, and the data is fetched
head_end = tpl.index('<title>')
page = tpl[head_end:]
page = page.replace('</head>\n<body>\n', '').replace('</body>\n</html>\n', '').replace('</body>\n</html>', '')
page = page.replace('<title>Investor Prospect Explorer</title>',
                    '<title>Investor Prospect Explorer</title>\n<meta name="claude:viewport-fit-sides" content="cover">', 1)
page = page.replace('<script>\n/*DATA*/\n</script>\n', '')
os.makedirs(os.path.join(ROOT, 'dist'), exist_ok=True)
open(os.path.join(ROOT, 'dist', 'page.html'), 'w').write(page)
recs = json.loads(data[len('window.PROSPECTS='):data.index(';\nwindow.META=')])
meta = json.loads(data[data.index('window.META=') + len('window.META='):].rstrip().rstrip(';'))
with open(os.path.join(ROOT, 'dist', 'prospects.json'), 'w') as f:
    f.write('{"meta":' + json.dumps(meta) + ',"prospects":[\n' + ',\n'.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) for r in recs) + '\n]}\n')
print('dist/page.html', len(page) // 1024, 'KB; dist/prospects.json', os.path.getsize(os.path.join(ROOT, 'dist', 'prospects.json')) // 1024, 'KB')
