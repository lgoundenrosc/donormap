"""Turn the Master tab export (data/master.json, Sheets values API shape) into
the compact record set the explorer embeds. Run: python3 scripts/prep.py"""
import json, re, os, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw = json.load(open(os.path.join(ROOT, 'data', 'master.json')))['values']
H = raw[0]
rows = [r + [''] * (len(H) - len(r)) for r in raw[1:]]
col = {h: i for i, h in enumerate(H)}

LISTS = ['527s', 'State PACs', 'Foundation donors', 'BENS', 'NE campaign ties',
         'Trump officials', 'Ambassadors', 'Lawyers', 'Trump business']
INST = ['Hudson Institute', 'Pioneer Institute', 'Hoover Institution',
        'Center for Strategic and International Studies', 'Center for a New American Security',
        'Claremont Institute', 'Navy SEAL Foundation', 'U.S. Naval Academy Foundation',
        'Hillsdale College', 'American Enterprise Institute', 'Special Operations Warrior Foundation',
        'Manhattan Institute', 'Foundation for Defense of Democracies',
        'Ronald Reagan Presidential Foundation and Institute',
        'Jewish Institute for National Security of America', 'Heritage Foundation',
        'West Point Association of Graduates', 'Cato Institute', 'Foundation for American Innovation',
        'Institute for the Study of War', 'Green Beret Foundation', 'America First Policy Institute',
        'American Compass']
STATES = set('AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY PR'.split())

def money(s):
    s = (s or '').strip()
    if s in ('', '-'):
        return None
    d = re.sub(r'[^0-9.]', '', s)
    return float(d) if d else None

def blank(s):
    s = (s or '').strip()
    return '' if s in ('-',) else s

def g(r, name):
    return blank(r[col[name]])

out = []
issues = collections.Counter()
for r in rows:
    st = g(r, 'State')[:2].upper()
    if st not in STATES:
        if st: issues['state not recognised: ' + g(r, 'State')] += 1
        st = ''
    if not st and g(r, 'New England state'):
        st = g(r, 'New England state')
    lists = [x.strip() for x in g(r, 'Lists').split(';') if x.strip()]
    mask = 0
    for x in lists:
        if x in LISTS: mask |= 1 << LISTS.index(x)
        else: issues['unknown list ' + x] += 1
    aff = g(r, 'Affiliations')
    inst = [i for i, n in enumerate(INST) if n + ':' in aff]
    m = {k: money(g(r, k)) for k in ['527 giving 2025-26 ($)', '527 giving 2021-24 ($)', 'State PAC giving ($)',
         'IRS 527 total, all years, NE list ($)', 'Known political money, all sources, NE list ($)',
         'Largest published gift band, floor ($)']}
    a, b, c, dne, kne, band = m.values()
    # Best available documented political money. The NE-list totals already
    # span all years, so take the larger of the summed fields and those totals
    # rather than adding them (adding would double count).
    summed = (a or 0) + (b or 0) + (c or 0)
    best = max(summed, dne or 0, kne or 0)
    defense = g(r, 'Defense or national security link')
    out.append({
        'id': g(r, 'Master ID'), 'n': g(r, 'Name'), 'ty': g(r, 'Type'),
        'ci': g(r, 'City or region'), 'st': st, 'stRaw': g(r, 'State'),
        'ne': g(r, 'New England tie'), 'nes': g(r, 'New England state'),
        'p': g(r, 'Priority'), 'nl': int(g(r, 'Number of our lists') or 1), 'lm': mask,
        'mb': g(r, 'Match basis'), 'pm': g(r, 'Possible matches to check'),
        'g1': a, 'g2': b, 'gp': c, 'gn': dne, 'gk': kne, 'gb': band, 'gt': best or None,
        'lf': g(r, 'Linked foundation'), 't': g(r, 'Title or organization'), 'af': aff,
        'in': inst, 'd': defense, 'w': g(r, 'Wealth or investor signal'),
        'ps': g(r, 'Priority on source lists'), 'wf': g(r, 'Where found on source sheets'),
        'co': g(r, 'Contact or LinkedIn'), 'no': g(r, 'Notes'), 'so': g(r, 'Sources'),
    })
# drop empty keys to save bytes
for o in out:
    for k in [k for k, v in o.items() if v in ('', None, []) ]:
        del o[k]
meta = {'lists': LISTS, 'inst': INST, 'n': len(out)}
js = 'window.PROSPECTS=' + json.dumps(out, separators=(',', ':'), ensure_ascii=False) + ';\nwindow.META=' + json.dumps(meta) + ';'
open(os.path.join(ROOT, 'data', 'prospects.js'), 'w').write(js)
print(len(out), 'records,', len(js) // 1024, 'KB')
for k, v in issues.most_common(): print(' ', v, k)
