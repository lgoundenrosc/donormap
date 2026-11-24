"""Build the self-contained two-tab explorer for GitHub Pages.

Takes docs/index.html as written by the merge step (a full HTML page that
fetches prospects.json and ne-data.json) and inlines both data files, so the
page works from the repo root, from docs/, or opened straight from disk.
Writes the result to both index.html and docs/index.html.

    python3 -I new-england/build/build_hosted.py <repo root> <prospects.json> <ne-data.json>
"""
import json, sys
from pathlib import Path

root = Path(sys.argv[1])
prospects = json.load(open(sys.argv[2]))
ne = json.load(open(sys.argv[3]))
page = (root / 'docs/index.html').read_text()

def js_json(obj):
    # Keep "</script>" and similar out of inline script text.
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

data_script = ('<script>\n/* Data inlined by new-england/build/build_hosted.py so the page needs no fetch. */\n'
               'window.PROSPECTS = ' + js_json(prospects['prospects']) + ';\n'
               'window.META = ' + js_json(prospects['meta']) + ';\n'
               'window.NE_DATA = ' + js_json(ne) + ';\n</script>\n')

# Data goes in ahead of the first script in the body.
body_at = page.index('<body>')
first_script = page.index('<script>', body_at)
page = page[:first_script] + data_script + page[first_script:]

# The New England tab uses the inlined data when present.
old = "    fetch('ne-data.json').then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })"
new = ("    (window.NE_DATA ? Promise.resolve(window.NE_DATA)\n"
       "      : fetch('ne-data.json').then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }))")
assert page.count(old) == 1
page = page.replace(old, new)

for p in (root / 'index.html', root / 'docs/index.html'):
    p.write_text(page)
print('wrote', len(page), 'bytes to index.html and docs/index.html')
