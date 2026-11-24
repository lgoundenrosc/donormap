"""Merge the New England view into the Investor Prospect Explorer as a second tab.

Inputs:  explorer/live.html (the live Explorer, with the publish skeleton)
         site/index.html    (the standalone New England page)
Output:  explorer/index.html, ready to publish with ne-data.json beside it.

The New England view mounts in a shadow root, so its class names, ids and
styles cannot collide with the Explorer's. Colour tokens are shared: the
Explorer's :root blocks already define the Rosc palette, and the map-only
tokens are added to them with an --ne- prefix.
"""
import re, sys
from pathlib import Path

ROOT = Path(sys.argv[1])
live = (ROOT / 'explorer/live.html').read_text()
ne = (ROOT / 'site/index.html').read_text()

# ---- strip the publish skeleton from the live Explorer
start = live.index('<title>')
end = live.rindex('</body></html>')
ex = live[start:end].rstrip() + '\n'

# ---- pieces of the New England page
css = ne[ne.index('<style>') + 7: ne.index('</style>')]
body = ne[ne.index('<div class="wrap">'): ne.index('<script>')].rstrip()
js = ne[ne.index('<script>') + 8: ne.rindex('</script>')]

MAP_TOKENS = ['water', 'land', 'land-has', 'land-sel', 'land-hover', 'land-off', 'ctx', 'ctx-line',
              'town-line', 'state-line', 'ref', 'st-lbl']
def grab(block_css, name):
    m = re.search(r'--' + re.escape(name) + r':\s*([^;]+);', block_css)
    return m.group(1).strip()
# token values from the NE page's own dark (bare :root) and light blocks
dark_block = css[css.index(':root {'): css.index('@media (prefers-color-scheme: light)')]
light_block = css[css.index(':root[data-theme="light"] {'):]
light_block = light_block[:light_block.index('}')]
dark_tokens = ' '.join(f'--ne-{t}: {grab(dark_block, t)};' for t in MAP_TOKENS)
light_tokens = ' '.join(f'--ne-{t}: {grab(light_block, t)};' for t in MAP_TOKENS)

# shadow CSS: drop the token blocks, page-level rules and masthead, rename map tokens
css = css[css.index('* { box-sizing: border-box; }'):]
drop = [r'^body \{.*$', r'^\.wrap \{.*$', r'^/\* Masthead.*$', r'^\.mast[ .].*$', r'^\s*\.mast h1 \{.*$']
css = '\n'.join(l for l in css.split('\n') if not any(re.match(p, l) for p in drop))
css = re.sub(r'var\(--(' + '|'.join(map(re.escape, MAP_TOKENS)) + r')\)', r'var(--ne-\1)', css)
css = (':host { display: block; color: var(--ink); font-family: var(--font-body); font-size: 15px; line-height: 1.55; }\n'
       '[hidden] { display: none !important; }\n'
       '.ne-root { margin-top: 16px; }\n' + css)

# shadow markup: no masthead, own root class
body = re.sub(r'\s*<header class="mast">.*?</header>', '', body, count=1, flags=re.S)
body = body.replace('<div class="wrap">', '<div class="ne-root">', 1)

# script: boot(D) becomes bootNE(D, root), lookups go through the shadow root
js = js[js.index('function boot(D) {'):]
js = js.replace('function boot(D) {', 'function bootNE(D, root) {', 1)
js = js.replace("function $(id) { return document.getElementById(id); }", "function $(id) { return root.getElementById(id); }")
js = js.replace('document.querySelectorAll(', 'root.querySelectorAll(').replace('document.querySelector(', 'root.querySelector(')
js = re.sub(r'var\(--(' + '|'.join(map(re.escape, MAP_TOKENS)) + r')\)', r'var(--ne-\1)', js)
tail = """  render();
}"""
assert js.rstrip().endswith(tail), js.rstrip()[-80:]
js = js.rstrip()[:-len(tail)] + """  render();
  return {
    refresh: function () {
      var r = svg.getBoundingClientRect();
      if (!r.width) return;
      var atHome = Math.abs(vb[2] - homeW) < 1e-6;
      lastW = r.width; homeW = home()[2];
      setVB(atHome ? home() : vb.slice());
    }
  };
}
"""
assert 'document.' not in re.sub(r'document\.createElement(NS)?\(', '', js), [m.start() for m in re.finditer(r'document\.', js)]

# ---- edit the Explorer
# 1. map tokens into the three :root blocks
ex = ex.replace('  --font-body: "Source Serif 4"', '  ' + dark_tokens + '\n  --font-body: "Source Serif 4"', 1)
n_light = ex.count('  --tip-bg: #182042; --tip-fg: #f5f0e4;\n')
assert n_light == 2, n_light
ex = ex.replace('  --tip-bg: #182042; --tip-fg: #f5f0e4;\n', '  --tip-bg: #182042; --tip-fg: #f5f0e4;\n  ' + light_tokens + '\n')

# 2. tab styles
TAB_CSS = """
/* view tabs */
.tabs { display: flex; flex-wrap: wrap; gap: 0 4px; margin: 14px 0 0; border-bottom: 1px solid var(--line); }
.tab { font-family: var(--font-label); font-weight: 600; font-size: 15px; letter-spacing: .1em; text-transform: uppercase; background: none; border: 0; border-bottom: 3px solid transparent; color: var(--ink-3); padding: 8px 14px 6px; margin-bottom: -1px; cursor: pointer; }
.tab:hover { color: var(--ink); }
.tab[aria-selected="true"] { color: var(--ink); border-bottom-color: var(--gold); }
.tab .n { font-weight: 500; letter-spacing: .02em; color: var(--ink-3); margin-left: 7px; }
.tab:focus-visible { outline: 2px solid var(--gold); outline-offset: -2px; }
.ne-loading { color: var(--ink-3); font-size: 15px; padding: 28px 0; }
"""
ex = ex.replace('\n/* masthead */', TAB_CSS + '\n/* masthead */', 1)

# 3. tab bar after the masthead, panels around the existing content
ex = ex.replace('''      <p class="eyebrow">Rosc &middot; Investor prospects &middot; All lists</p>''',
                '''      <p class="eyebrow" id="mastEyebrow">Rosc &middot; Investor prospects &middot; All lists</p>''', 1)
ex = ex.replace('''      <p class="sub">All 2,828 people''', '''      <p class="sub" id="mastSub">All 2,828 people''', 1)
hdr_end = ex.index('  </header>\n') + len('  </header>\n')
ex = ex[:hdr_end] + '''
  <div class="tabs" role="tablist" aria-label="Views">
    <button type="button" class="tab" role="tab" id="tab-all" aria-controls="panel-all" aria-selected="true">All prospects<span class="n">2,828</span></button>
    <button type="button" class="tab" role="tab" id="tab-ne" aria-controls="panel-ne" aria-selected="false" tabindex="-1">New England<span class="n">272</span></button>
  </div>

  <div id="panel-all" role="tabpanel" aria-labelledby="tab-all">
''' + ex[hdr_end:]
notes_end = ex.index('  </section>\n</div>\n\n<aside class="drawer"')
ex = ex[:notes_end] + '''  </section>
  </div>

  <div id="panel-ne" role="tabpanel" aria-labelledby="tab-ne" hidden>
    <div id="ne-host"><p class="ne-loading">Loading the New England view.</p></div>
  </div>
</div>

<template id="ne-tpl"><style>
''' + css.strip() + '''
</style>
''' + body + '''
</template>

<aside class="drawer"''' + ex[notes_end + len('  </section>\n</div>\n\n<aside class="drawer"'):]

# 4. pointer from the all-prospects notes to the new tab
ex = ex.replace('''      <li>Source: Rosc Master Conservative Donor Prospect List, Master tab''',
                '''      <li>The <a href="#new-england">New England tab</a> places the 272 people with a New England home or tie by town, with state, town and person drill-down.</li>
      <li>Source: Rosc Master Conservative Donor Prospect List, Master tab''', 1)

# 5. the New England script and the tab controller, after the Explorer's own scripts
TAB_JS = """
<script>
/* New England view. Mounted in a shadow root on first open. */
""" + js.strip() + """

(function () {
  'use strict';
  var TABS = { all: document.getElementById('tab-all'), 'new-england': document.getElementById('tab-ne') };
  var PANELS = { all: document.getElementById('panel-all'), 'new-england': document.getElementById('panel-ne') };
  var MAST = {
    all: ['Rosc &middot; Investor prospects &middot; All lists', document.getElementById('mastSub').innerHTML],
    'new-england': ['Rosc &middot; Investor prospects &middot; New England',
      'The 272 people on the New England tab of the master list, placed by town of record across Connecticut, Maine, ' +
      'Massachusetts, New Hampshire, Rhode Island and Vermont. Click a state card, town or circle to drill in, and a name ' +
      'for the full record. Matches and figures unverified, confirm before outreach.']
  };
  var ne = null, neStarted = false;
  function startNE() {
    if (neStarted) return;
    neStarted = true;
    var host = document.getElementById('ne-host');
    var loading = host.querySelector('.ne-loading');
    fetch('ne-data.json').then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (D) {
        if (loading) loading.remove();
        var root = host.attachShadow({ mode: 'open' });
        root.appendChild(document.getElementById('ne-tpl').content.cloneNode(true));
        ne = bootNE(D, root);
      })
      .catch(function (e) {
        neStarted = false;
        if (loading) loading.textContent = 'The New England data did not load (' + String(e && e.message || e) + '). Open the tab again to retry.';
      });
  }
  function show(name, focus) {
    if (!TABS[name]) name = 'all';
    Object.keys(TABS).forEach(function (k) {
      var on = k === name;
      TABS[k].setAttribute('aria-selected', on ? 'true' : 'false');
      TABS[k].tabIndex = on ? 0 : -1;
      PANELS[k].hidden = !on;
    });
    document.getElementById('mastEyebrow').innerHTML = MAST[name][0];
    document.getElementById('mastSub').innerHTML = MAST[name][1];
    if (focus) TABS[name].focus();
    if (name === 'new-england') { startNE(); if (ne) ne.refresh(); }
  }
  function go(name) {
    var h = name === 'all' ? '' : '#' + name;
    if (location.hash !== h) {
      try { history.replaceState(null, '', h || location.pathname + location.search); } catch (e) { location.hash = h; }
    }
    show(name);
  }
  TABS.all.onclick = function () { go('all'); };
  TABS['new-england'].onclick = function () { go('new-england'); };
  Object.keys(TABS).forEach(function (k) {
    TABS[k].addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      e.preventDefault();
      var next = k === 'all' ? 'new-england' : 'all';
      go(next); TABS[next].focus();
    });
  });
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href="#new-england"]');
    if (a) { e.preventDefault(); go('new-england'); window.scrollTo(0, 0); }
  });
  window.addEventListener('hashchange', function () { show(location.hash === '#new-england' ? 'new-england' : 'all'); });
  show(location.hash === '#new-england' ? 'new-england' : 'all');
})();
</script>
"""
ex = ex.rstrip() + '\n' + TAB_JS
(ROOT / 'explorer/index.html').write_text(ex)
print('index.html bytes', len(ex))
