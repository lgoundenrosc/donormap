"""Turn mapshaper output (metres, equirectangular at 44N) into SVG path data.

Writes work/geo.json with towns, state outlines, context land, label points
and zoom boxes, all in one viewBox coordinate space.
"""
import json, re, sys, math
from pathlib import Path
from shapely.geometry import shape, box, mapping
from shapely.ops import unary_union

ROOT = Path(sys.argv[1])
G = ROOT / 'geo'

R = 6378137.0
LAT_TS = math.radians(44)
LON0 = -70.3

def proj(lon, lat):
    return (math.radians(lon - LON0) * R * math.cos(LAT_TS), math.radians(lat - 44) * R)

# Extent of the drawable world: wide enough that a landscape screen showing all
# of New England still has land or sea at the edges.
W0, S0 = proj(-77.2, 39.6)
E0, N0 = proj(-63.0, 48.4)
SCALE = 1000.0 / (E0 - W0)          # viewBox units per metre
VBW, VBH = 1000.0, (N0 - S0) * SCALE

def xy(x, y):
    return ((x - W0) * SCALE, (N0 - y) * SCALE)

def ring_d(coords):
    """Integer tenths of a viewBox unit, relative moves. Drawn inside a
    scale(0.1) group, so the browser sees the same geometry at a third of
    the bytes."""
    pts = [xy(x, y) for x, y in coords]
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    q = []
    for x, y in pts:
        t = (round(x * 10), round(y * 10))
        if not q or t != q[-1]:
            q.append(t)
    if len(q) < 3:
        return ''
    def pair(a, b):
        return f'{a}' + (f'{b}' if b < 0 else f' {b}')
    out = ['M' + pair(*q[0])]
    seg = []
    for (x0, y0), (x1, y1) in zip(q, q[1:]):
        dx, dy = x1 - x0, y1 - y0
        seg.append(pair(dx, dy))
    body = ''
    for sgm in seg:
        body += sgm if (body and sgm.startswith('-')) else (' ' + sgm if body else sgm)
    return out[0] + 'l' + body + 'z'

def geom_d(g):
    polys = [g] if g.geom_type == 'Polygon' else list(getattr(g, 'geoms', []))
    parts = []
    for p in polys:
        if p.geom_type != 'Polygon' or p.is_empty:
            continue
        parts.append(ring_d(p.exterior.coords))
        for h in p.interiors:
            parts.append(ring_d(h.coords))
    return ''.join(x for x in parts if x)

def vpt(pt):
    x, y = xy(pt.x, pt.y)
    return [round(x, 1), round(y, 1)]

towns_fc = json.load(open(G / 'towns.json'))['features']
states_fc = json.load(open(G / 'states.json'))['features']

towns = {}
for f in towns_fc:
    p = f['properties']
    g = shape(f['geometry'])
    if g.is_empty:
        continue
    big = max(g.geoms, key=lambda q: q.area) if g.geom_type == 'MultiPolygon' else g
    c = big.centroid
    if not big.contains(c):
        c = big.representative_point()
    county = p['NAMELSADCO']
    if p['STUSPS'] == 'CT':
        county = county.replace(' Planning Region', ' planning region')
    towns[p['GEOID']] = {
        'n': re.sub(r' Town$', '', p['NAME']),
        'st': p['STUSPS'],
        'co': county,
        'd': geom_d(g),
        'c': vpt(c),
    }

states = {}
for f in states_fc:
    g = shape(f['geometry'])
    minx, miny, maxx, maxy = g.bounds
    x0, y1 = xy(minx, miny)
    x1, y0 = xy(maxx, maxy)
    states[f['properties']['STUSPS']] = {'d': geom_d(g), 'bb': [round(x0, 1), round(y0, 1), round(x1 - x0, 1), round(y1 - y0, 1)]}
region = unary_union([shape(f['geometry']) for f in states_fc])
minx, miny, maxx, maxy = region.bounds
x0, y1 = xy(minx, miny); x1, y0 = xy(maxx, maxy)
regionBB = [round(x0, 1), round(y0, 1), round(x1 - x0, 1), round(y1 - y0, 1)]

clip = box(W0, S0, E0, N0)
context = []
for fn in ('ny.json', 'can.json'):
    for f in json.load(open(G / fn))['features']:
        g = shape(f['geometry']).buffer(0).intersection(clip)
        if not g.is_empty:
            context.append(geom_d(g))

def bb(lon0, lat0, lon1, lat1):
    xa, ya = xy(*proj(lon0, lat1))
    xb, yb = xy(*proj(lon1, lat0))
    return [round(xa, 1), round(ya, 1), round(xb - xa, 1), round(yb - ya, 1)]

def pt(lon, lat):
    x, y = xy(*proj(lon, lat))
    return [round(x, 1), round(y, 1)]

out = {
    'vb': [round(VBW, 1), round(VBH, 1)],
    'towns': towns,
    'states': states,
    'region': regionBB,
    'context': context,
    'boxes': {
        'boston': bb(-71.42, 42.18, -70.86, 42.62),
        'fairfield': bb(-73.74, 40.98, -72.98, 41.36),
        'seacoast': bb(-71.55, 42.82, -70.6, 43.72),
    },
    'stateLabels': {
        'ME': pt(-69.25, 45.35), 'NH': pt(-71.62, 43.95), 'VT': pt(-72.72, 44.05),
        'MA': pt(-72.55, 42.36), 'CT': pt(-72.7, 41.62), 'RI': pt(-71.28, 41.27),
    },
    'contextLabels': [
        ['NEW YORK', pt(-74.6, 43.3)], ['QUEBEC', pt(-71.4, 46.45)],
        ['NEW BRUNSWICK', pt(-66.3, 46.55)], ['NOVA SCOTIA', pt(-64.6, 44.95)],
        ['Atlantic Ocean', pt(-68.4, 41.9)],
    ],
}
s = json.dumps(out, separators=(',', ':'))
open(ROOT / 'work/geo.json', 'w').write(s)
print('viewBox', out['vb'], 'region', regionBB, 'towns', len(towns), 'bytes', len(s))
print('town path bytes', sum(len(t['d']) for t in towns.values()), 'context bytes', sum(len(c) for c in context))
