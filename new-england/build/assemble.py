"""Combine geometry and people into site/data.json."""
import json, sys, math, re
from pathlib import Path
ROOT = Path(sys.argv[1])
geo = json.load(open(ROOT / 'work/geo.json'))
people = json.load(open(ROOT / 'work/people.json'))
master = json.load(open(ROOT / 'work/master.json'))['values']

idx = {}
for k, t in geo['towns'].items():
    idx.setdefault((t['st'], t['n'].lower()), k)
REF = {
    'CT': ['Hartford', 'New Haven', 'Bridgeport', 'Waterbury', 'New London', 'Torrington'],
    'RI': ['Providence', 'Westerly'],
    'MA': ['Worcester', 'Springfield', 'Pittsfield', 'Plymouth', 'Nantucket', 'Edgartown', 'Provincetown', 'New Bedford', 'Lowell', 'Greenfield'],
    'NH': ['Concord', 'Manchester', 'Nashua', 'Keene', 'Berlin', 'Laconia'],
    'ME': ['Portland', 'Bangor', 'Augusta', 'Lewiston', 'Presque Isle', 'Ellsworth', 'Calais', 'Rumford'],
    'VT': ['Burlington', 'Montpelier', 'Rutland', 'Brattleboro', 'St. Johnsbury', 'Bennington'],
}
ref = []
for st, names in REF.items():
    for n in names:
        k = idx.get((st, n.lower()))
        if not k:
            print('missing ref', st, n)
        else:
            ref.append(k)

# km per viewBox unit, from the projection in geometry.py
R = 6378137.0
W0 = math.radians(-77.2 + 70.3) * R * math.cos(math.radians(44))
E0 = math.radians(-63.0 + 70.3) * R * math.cos(math.radians(44))
kmPerUnit = (E0 - W0) / 1000.0 / 1000.0

# Drop empty fields to keep the file small.
slim = []
for p in people:
    slim.append({k: v for k, v in p.items() if v not in ('', None, [])})

out = dict(geo)
out.update({
    'people': slim, 'ref': ref, 'kmPerUnit': round(kmPerUnit, 5),
    'masterRows': len(master) - 1, 'neRows': len(people),
})
s = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
open(ROOT / 'site/data.json', 'w').write(s)
print('data.json bytes', len(s), 'people', len(slim), 'kmPerUnit', kmPerUnit)
