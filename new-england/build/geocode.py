"""Resolve each New England tab row to a Census town (county subdivision).

Reads work/ne.json (Sheets dump) and geo/towns.json (projected, simplified
towns from mapshaper). Writes work/people.json and work/places.json.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(sys.argv[1])
ne = json.load(open(ROOT / 'work/ne.json'))['values']
H = ne[0]
rows = [dict(zip(H, r + [''] * (len(H) - len(r)))) for r in ne[1:]]
towns = json.load(open(ROOT / 'geo/towns.json'))['features']

NE = ('CT', 'ME', 'MA', 'NH', 'RI', 'VT')

# (state, lowercase name) -> GEOID. Where Vermont and Maine repeat a name
# (city and town of St. Albans, Lincoln town and plantation), prefer the city
# or the town over the plantation.
index = {}
rank = {'city': 0, 'town': 1, 'plantation': 2}
for f in towns:
    p = f['properties']
    nm = re.sub(r' Town$', '', p['NAME']).lower()
    key = (p['STUSPS'], nm)
    kind = p['NAMELSAD'].rsplit(' ', 1)[-1]
    r = rank.get(kind, 3)
    if key not in index or r < index[key][1]:
        index[key] = (p['GEOID'], r)
index = {k: v[0] for k, v in index.items()}

# Villages and neighbourhoods that are not Census towns, placed in the town
# that contains them. Matches the Massachusetts map's choices where they overlap.
VILLAGE = {
    ('MA', 'south hamilton'): 'hamilton', ('MA', 'east falmouth'): 'falmouth',
    ('MA', 'osterville'): 'barnstable', ('MA', 'waban'): 'newton',
    ('MA', 'chestnut hill'): 'newton', ('MA', 'charlestown'): 'boston',
    ('MA', 'manchester'): 'manchester-by-the-sea',
    ('CT', 'old greenwich'): 'greenwich', ('CT', 'riverside'): 'greenwich',
    ('CT', 'w  hartford'): 'west hartford', ('CT', 'w hartford'): 'west hartford',
    ('CT', 'yalesville'): 'wallingford',
    ('NH', 'etna'): 'hanover',
    ('ME', 'port clyde'): 'st. george',
    ('VT', 'st. albans area'): 'st. albans',
}

# Rows whose City field does not name the New England town. Each entry gives
# the town to use and why. Town None means state only, no town.
OVERRIDE = {
    'M0005': ('greenwich', 'Lives in Boca Raton, FL. Placed at Greenwich, the 527 filing address through 2019.'),
    'M0031': ('greenwich', 'Lives in Nashville, TN. Placed at Greenwich, the 527 filing address through 2023 and the base of Teamworthy Ventures.'),
    'M0029': ('boston', 'Lives in Palm Beach, FL. Placed at Boston, a former home.'),
    'M0042': ('greenwich', 'Based in New York. Placed at Greenwich, the 527 filing address 2009-18.'),
    'M0048': ('boston', 'Based in Menlo Park, CA. Placed at Boston, the 527 filing address through 2025.'),
    'M0059': ('boston', 'Foundation address in Boston.'),
    'M0058': ('boston', 'Foundation address in Boston.'),
    'M0067': ('boston', 'Lives in Vero Beach, FL. Placed at Boston, a former home.'),
    'M0116': ('greenwich', 'Lives in Palm Beach, FL. Placed at Greenwich, where Interactive Brokers is based.'),
    'M0239': ('norwalk', ''),
    'M0274': ('peterborough', 'City field reads Boston. Placed at Peterborough per the New England tie.'),
    'M2543': ('boston', 'Home state not confirmed. Placed at Boston, base of the New England Legal Foundation, which this person chairs.'),
    'M0299': ('manchester', 'City field reads New Hampshire / Boston. Placed at Manchester per the New England tie.'),
    'M2767': (None, 'Lives in Florida. Second home in Maine, town not given.'),
    'M0387': ('greenwich', 'Lives in Oakville, CA. Placed at Greenwich, the 527 filing address 2010-18.'),
    'M0412': ('scituate', 'Lives in Evanston, IL. Placed at Scituate, where this person keeps a home.'),
    'M0426': (None, 'No town given.'),
    'M0429': ('providence', ''),
    'M0443': ('wellesley', ''),
    'M0921': (None, 'Foundation filing gives Massachusetts only.'),
    'M2686': ('boston', 'Home state not confirmed. Placed at Boston, the Jones Day office this person leads.'),
    'M0847': (None, 'No town given.'),
    'M2696': ('boston', 'Home state not confirmed. Placed at Boston, the Jones Day office.'),
    'M0895': (None, 'Foundation filing gives Massachusetts only.'),
    'M2691': ('boston', 'Works in New York. Placed at Boston, the Jones Day office this person formerly led.'),
    'M0970': (None, 'Listed as Lexington, NH. New Hampshire has no town of that name, so left unplaced. Check whether Lexington, MA is meant.'),
    'M0985': (None, 'No town given.'),
    'M0990': (None, 'Firm based in Maine, home town not stated.'),
    'M2092': (None, 'No town given.'),
}

def money(s):
    s = (s or '').strip()
    if not s or s == '-':
        return None
    m = re.sub(r'[^0-9.]', '', s)
    return float(m) if m else None

def first_place(city):
    c = re.sub(r'\(.*?\)', '', city or '').strip()
    return re.split(r'\s*/\s*|\s*,\s*| and ', c)[0].strip()

out, problems = [], []
for r in rows:
    mid = r['Master ID']
    st = r['New England state']
    home = r['State']
    tie = r['New England tie']
    note = ''
    if mid in OVERRIDE:
        tname, note = OVERRIDE[mid]
    else:
        tname = first_place(r['City or region']).lower()
        tname = VILLAGE.get((st, tname), tname)
        if not tname:
            tname = None
    if tname is not None:
        tname = VILLAGE.get((st, tname), tname)
    geoid = index.get((st, tname)) if tname else None
    if tname and not geoid:
        problems.append((mid, r['City or region'], st))
    if mid not in OVERRIDE and tname:
        raw = first_place(r['City or region'])
        if raw.lower() != tname:
            note = f'{raw} is placed in its Census town.'

    # Basis for the placement.
    if home not in NE:
        basis = 'tie'
    elif tie.startswith('Filed 527 gifts from') or tie.startswith('Gave an Augusta'):
        basis = 'filing'
    else:
        basis = 'home'
    m = re.search(r'last in (\d{4})', tie)
    lastFiled = int(m.group(1)) if m else None

    g = {
        'g527_2526': money(r['527 giving 2025-26 ($)']),
        'g527_2124': money(r['527 giving 2021-24 ($)']),
        'statePac': money(r['State PAC giving ($)']),
        'irs527Total': money(r['IRS 527 total, all years, NE list ($)']),
        'knownMoney': money(r['Known political money, all sources, NE list ($)']),
        'giftBandFloor': money(r['Largest published gift band, floor ($)']),
    }
    vals = [v for v in g.values() if v]
    rec = {
        'id': mid, 'name': r['Name'], 'type': r['Type'], 'city': r['City or region'],
        'home': home, 'st': st, 'tie': tie, 'basis': basis, 'lastFiled': lastFiled,
        'priority': r['Priority'], 'nLists': int(r['Number of our lists'] or 0),
        'listArr': [x.strip() for x in r['Lists'].split(';') if x.strip()],
        'matchBasis': r['Match basis'], 'possibleMatches': r['Possible matches to check'],
        **g, 'top': max(vals) if vals else None,
        'foundation': r['Linked foundation'], 'title': r['Title or organization'],
        'affiliations': r['Affiliations'], 'defense': r['Defense or national security link'],
        'wealth': r['Wealth or investor signal'], 'sourcePriority': r['Priority on source lists'],
        'whereFound': r['Where found on source sheets'], 'contact': r['Contact or LinkedIn'],
        'notes': r['Notes'], 'sources': r['Sources'],
        'town': geoid, 'placeNote': note,
    }
    out.append(rec)

print('rows', len(out), 'placed', sum(1 for o in out if o['town']), 'unplaced', sum(1 for o in out if not o['town']))
print('problems', problems)
import collections
print(collections.Counter(o['basis'] for o in out))
print(collections.Counter(o['priority'] for o in out))
json.dump(out, open(ROOT / 'work/people.json', 'w'), ensure_ascii=False)
