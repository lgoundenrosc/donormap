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

`docs/` holds a copy of `index.html` and nothing else, so Pages can serve
the explorer without publishing the raw export in `data/`. In the repo's
Settings, open Pages, set the source to "Deploy from a branch", and pick
this branch with the `/docs` folder.

A Pages site is public to anyone with the URL, even when the repo is
private, unless the organization is on GitHub Enterprise Cloud and the
site's visibility is set to private. The page carries a noindex tag, which
keeps well-behaved search engines out but doesn't stop anyone who has the
link.
