# Development guide

## Layout

```
efficiency-tracker/
├── src/efficiency_tracker/   ← actual add-on source (this is what gets zipped)
│   ├── __init__.py           ← entry point — Anki imports this
│   └── manifest.json         ← add-on metadata
├── scripts/
│   ├── build.sh              ← bash build (macOS/Linux)
│   └── build.py              ← cross-platform build (any OS with Python)
├── docs/                     ← screenshots & docs
├── dist/                     ← build output (gitignored)
└── .github/workflows/        ← CI: builds + attaches to releases on tag push
```

## Local development loop

The fastest iteration loop is to symlink the source directly into Anki's
addons folder so changes show up after a restart of Anki.

### macOS / Linux

```bash
ANKI_ADDONS=~/Library/Application\ Support/Anki2/addons21    # macOS
# ANKI_ADDONS=~/.local/share/Anki2/addons21                  # Linux
ln -s "$(pwd)/src/efficiency_tracker" "$ANKI_ADDONS/efficiency_tracker"
```

### Windows (PowerShell, admin)

```powershell
New-Item -ItemType SymbolicLink `
    -Path "$env:APPDATA\Anki2\addons21\efficiency_tracker" `
    -Target "$(pwd)\src\efficiency_tracker"
```

After editing `__init__.py`, restart Anki to pick up changes. (Anki only
loads add-on Python at startup.)

## Building a release artefact

```bash
./scripts/build.sh        # bash
python scripts/build.py   # cross-platform
```

Either produces `dist/efficiency_tracker.ankiaddon`, which is just a zip with
`__init__.py` and `manifest.json` at its root. You can install it via
**Tools → Add-ons → Install from file…**.

## Tagging a release

```bash
git tag v1.0.1
git push origin v1.0.1
```

The GitHub Actions workflow in `.github/workflows/build.yml` will build the
`.ankiaddon` and attach it to a release for that tag.

## Where data lives

Two persistence layers, both managed for you:

1. **Anki review log** (`revlog` table in the collection) — read-only here.
   Used to compute "actual study minutes" via a SQL query against
   `mw.col.db`. Honours `mw.col.get_config("rollover", 4)` for day boundaries.
2. **`user_data.json`** in the add-on directory — written by the input
   dialog, read by the stats view. Schema:

   ```json
   {
     "2026-05-04": { "attempted": 60 },
     "2026-05-03": { "attempted": 90 }
   }
   ```

   Date keys are local-date `YYYY-MM-DD` strings (matched to the same
   rollover-based day boundary used for the SQL query).

## Anki API touchpoints

- `aqt.mw` — main window; entry to everything else
- `mw.col.db.scalar(sql, *args)` — direct SQL against the collection
- `mw.col.get_config(key, default)` — read collection config (rollover hour
  lives here in modern Anki; falls back to `mw.col.conf.get` on older)
- `mw.form.menuTools.addMenu(name)` — adds the top-level menu we hang our
  actions on
- `aqt.webview.AnkiWebView` — the embedded webview used for the stats page;
  inherits Anki's CSS niceties (font, dark mode handling) for free
