# Investor prospect explorer

An interactive view of the **Rosc Master Conservative Donor Prospect List**
(Master tab, 2,828 people, nine source lists). Open `index.html` in a browser.
It's one self-contained file: no server, no installs, no network calls.

What it does:

- Filters by priority, source list, New England tie, two-plus lists, defense or
  nat-sec link, documented giving, and free-text search.
- Cross-filters: click a state, a source-list bar, an overlap-matrix cell or an
  institution, and every other view updates.
- Opens the full 29-column record for anyone, with sources linked and
  possible-duplicate warnings shown.
- Exports the current view to CSV.

## Rebuilding after the sheet changes

1. Export the Master tab (Sheets API `values.get` on `Master!A1:AC`) to
   `data/master.json`.
2. Run:

```bash
python3 scripts/prep.py && python3 scripts/build.py
```

`build.py` lifts the state boundaries and projection code from
`lgoundenrosc/Assets` (`maps/us-base-map.html`), expected at `../Assets`.
Set `ASSETS_DIR` if it lives elsewhere.

## Files

| Path | What it is |
| --- | --- |
| `index.html` | The built explorer. This is the deliverable. |
| `docs/index.html` | The same file, served by GitHub Pages. |
| `src/template.html` | Page, styles and chart code. Edit this, not `index.html`. |
| `scripts/prep.py` | Cleans the sheet export into `data/prospects.js`. |
| `scripts/build.py` | Inlines data and map code into `index.html`. |
| `data/master.json` | Raw Master tab export, 24 Nov 2026. |

The data is private donor research. Keep this repo private.

## GitHub Pages

`docs/` holds the hosted copy: the explorer with its two tabs (All prospects and New England)
as `index.html`, plus the two data files it loads, `prospects.json` and `ne-data.json`. The raw
export in `data/` is not in `docs/`. In the repo's Settings, open Pages, set the source to
"Deploy from a branch", and pick `claude/festive-keller-yno2xw` with the `/docs` folder. The
site is then at `https://lgoundenrosc.github.io/donormap/`, and
`https://lgoundenrosc.github.io/donormap/#new-england` opens the New England tab.

`docs/` is built from the claude.ai artifact version of the explorer (which loads
`prospects.json` rather than inlining it) with the New England tab merged in by
`new-england/build/build_explorer.py`, then wrapped as a full HTML document.

A Pages site is public to anyone with the URL, even when the repo is private, unless the
organization is on GitHub Enterprise Cloud and the site's visibility is set to private. The page
carries a noindex tag, which keeps well-behaved search engines out but doesn't stop anyone who
has the link. Serving Pages from a private repo needs a paid GitHub plan.

## New England donor view (`new-england/`)

`site/index.html` plus `site/data.json` is the whole page. It fetches `data.json` by relative
path, so serve the folder (for example `python3 -m http.server`) rather than opening the file
from disk. Published as a private claude.ai artifact titled New England Donor Map.

What it shows: the 272 rows on the sheet's New England tab, assigned to the state in its
New England state column. 248 resolve to a Census town, 24 have only a state. Each person is
placed by one of three bases, and the page keeps them apart:

- **Lives or based here** (174). Home or office in the town.
- **527 filing address only** (84). The only address is from an IRS 527 filing, often old.
- **Lives elsewhere** (14). Lives outside New England or home state unconfirmed, placed at the
  town of the New England tie. Drawn as hollow rings.

### Rebuilding

1. Pull the New England tab (`'New England'!A1:AC2533`) with the Google Sheets connector and
   save the JSON response as `new-england/work/ne.json`. Pull the Master tab the same way to
   `work/master.json` (used only for the row count in the footer).
2. `cd new-england && build/geo.sh` downloads and simplifies the boundaries into `geo/`.
   Needs `pip install pyshp shapely`.
3. `python3 -I build/geocode.py .` resolves each row to a town. Village names, out-of-region
   residents and rows whose City field disagrees with their New England tie are handled in
   the `VILLAGE` and `OVERRIDE` tables at the top of the script. New rows that don't match a
   Census town name are printed under `problems`.
4. `python3 -I build/geometry.py .` then `python3 -I build/assemble.py .` write `site/data.json`.
5. `node build/shot.js site <out-dir>` renders test screenshots with Playwright.

### Explorer tab

The same view also runs as the New England tab of the Investor Prospect Explorer artifact.
`build/build_explorer.py` takes the live Explorer HTML (read it from the artifact and save as
`explorer/live.html`) plus `site/index.html`, mounts the New England view in a shadow root so the
two pages' styles and ids can't collide, and writes `explorer/index.html`. Publish that with
`site/data.json` as `ne-data.json`. `#new-england` on the Explorer link opens the tab directly.

### Things that break easily

- Town and context-land paths are stored as integer tenths of a viewBox unit with relative
  moves, and drawn inside `scale(0.1)` groups. Any new path group needs the same transform.
- Lexington, NH (M0970) is left unplaced on purpose. New Hampshire has no town of that name.
- Connecticut's county column shows the Census planning regions that replaced counties in
  2022. The Western CT planning region is close to, but not the same as, Fairfield County.
