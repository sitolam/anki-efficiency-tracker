# Efficiency Tracker — Anki add-on

Tracks how **efficiently** you studied: compares your actual study time in
Anki against the time you *attempted* to study, and visualises the history
across the last 30 days.

![Screenshot — dark mode](docs/screenshot-dark.png)

<details>
<summary>Light mode</summary>

![Screenshot — light mode](docs/screenshot-light.png)

</details>

## What does it do?

Anki already shows how long you actually spent doing reviews. But that isn't
the same as how long you *tried* to study. You may have spent two hours at
your desk, but Anki only counted 45 minutes — the rest was scrolling, getting
distracted, or staring at one card.

This add-on lets you log how much time you attempted to study each day, and
then computes your efficiency:

```
efficiency = actual study time in Anki / time attempted to study
```

The result is a dashboard with a bar chart, a line chart, and a table of
your recent history.

## Features

- ➕ **Log study time as sessions** — add multiple time blocks per day
  (09:00 → 10:00, 14:30 → 15:00, etc.) or just a duration in minutes
- 📊 Dashboard with today's efficiency, 7-day average, and 30-day average
- 🔘 Toolbar button right next to Anki's built-in "Stats" — one click to
  open the dashboard
- 📈 Bar chart per day (attempted vs. active in Anki)
- 📉 Line chart of efficiency, colour-coded by threshold (defaults: ≥ 70%
  green, 45–69% amber, < 45% red — fully configurable)
- 🗂️ History table of recent days
- 📅 Configurable time range — view the last **7, 30, 90, or 365 days**
- 📤 **Export / 📥 Import** your attempted-time data as JSON, for
  back-ups or rough cross-device sync
- ⌨️ Keyboard shortcuts: `Ctrl+Shift+E` to log time, `Ctrl+Shift+S` for
  statistics
- 🌓 Theme cycle button in the dashboard (auto / light / dark) — also
  settable via the add-on config
- 📦 Zero external dependencies — all charts in pure SVG, ~9 KB total
- 🔌 Works fully offline

## Installation

### Option 1: from a release file

1. Download the latest `efficiency_tracker.ankiaddon` from the
   [Releases](../../releases) page
2. Open Anki → **Tools → Add-ons → Install from file…**
3. Select the downloaded file
4. Restart Anki

### Option 2: build from source

```bash
git clone https://github.com/sitolam/efficiency-tracker.git
cd efficiency-tracker
./scripts/build.sh
# → produces dist/efficiency_tracker.ankiaddon
```

Then install via **Tools → Add-ons → Install from file…**.

### Option 3: copy manually (for development)

Copy the `src/efficiency_tracker/` folder into your Anki addons directory:

- **macOS**: `~/Library/Application Support/Anki2/addons21/`
- **Windows**: `%APPDATA%\Anki2\addons21\`
- **Linux**: `~/.local/share/Anki2/addons21/`

## Usage

After installing, a new menu **Tools → Efficiency Tracker** appears with
these actions:

| Action                       | Shortcut         | What it does                                                |
|------------------------------|------------------|-------------------------------------------------------------|
| ➕ Enter study time…        | `Ctrl+Shift+E`   | Open the per-day session log (add/remove timed sessions)   |
| 📊 Show statistics…         | `Ctrl+Shift+S`   | Open the dashboard                                          |
| 📤 Export data…             |                  | Save your attempted-time entries to a JSON file             |
| 📥 Import data…             |                  | Load entries from a JSON export (merged with existing data) |

### Logging a session

Open **Enter study time…** and click **➕ Add session**. Two modes:

- **Timed** — enter a *from* and *to* time (e.g., 09:00 → 10:30). The
  duration is computed automatically. Sessions that cross midnight are
  detected and marked as overnight.
- **Just minutes** — enter a duration without specific times. Useful for
  back-filling old data when you don't remember exactly when you studied.

Add as many sessions as you want for the same day — they all add up to
the day's total attempted time. Remove individual sessions with the ✕
button. Changes are saved immediately.

The dialog has a date picker so you can also back-fill earlier days, and
shows your actual Anki time and live efficiency for the selected date.

## Configuration

Open **Tools → Add-ons → Efficiency Tracker → Config** to tune:

| Key | Default | Description |
|-----|---------|-------------|
| `theme` | `"auto"` | `"auto"` (follow system), `"dark"`, or `"light"`. Also cycleable from the dashboard. |
| `good_threshold` | `70` | Efficiency % at which the indicator turns green |
| `warn_threshold` | `45` | Below this %, indicator turns red. Between this and `good_threshold` it's amber |
| `range_days` | `30` | Time window for the dashboard. One of `7`, `30`, `90`, or `365`. Also changeable from the range dropdown in the dashboard. |
| `show_toolbar_button` | `true` | Show the "Efficiency" link in Anki's top toolbar (restart Anki after changing) |

## Cross-device sync (export / import)

Anki itself doesn't sync the addon's `user_data.json`, so attempted-time
entries stay local to each machine. To copy data between devices:

1. On device A: **Tools → Efficiency Tracker → Export data…** — saves a
   JSON file you can put in Dropbox / iCloud / a USB drive
2. On device B: **Tools → Efficiency Tracker → Import data…** — pick the
   file. Existing entries with matching dates are overwritten by the
   imported values; entries that exist only locally are kept.

The export format is a simple JSON object with a `data` field, so you can
also hand-edit it or generate it from scripts if you want to.

## How it works

- **Actual study time** comes straight from Anki's `revlog` table (the same
  data Anki's own statistics use). The day boundary follows your Anki
  rollover setting (4 AM by default).
- **Attempted time** is also bucketed into Anki-days that follow the same
  rollover. So a session you log at 02:30 with the default 4 AM rollover
  counts toward the *previous* calendar date — exactly how Anki itself
  groups reviews from that moment. This keeps the efficiency calculation
  honest around the night boundary.
- **Storage**: `user_data.json` inside the add-on folder. Each day is
  either a list of sessions
  (`{"sessions": [{"start": "09:00", "end": "10:00", "minutes": 60}, …]}`)
  or, for entries from older versions, a plain `{"attempted": N}`. Both
  formats are read transparently.
- **Visualisation** is generated as pure SVG inside an Anki webview. No
  Chart.js, no CDN, no tracking — works offline.

## Compatibility

- Anki 2.1.50+ (Qt6)
- Tested on macOS, Windows, and Linux

## Known limitations

- Very long ranges (365 days) render daily bars at high density — use the
  efficiency line chart for trends in that mode.
- No automatic cross-device sync — use **Export data / Import data** in the
  Tools menu, or sync the add-on folder via iCloud / Dropbox manually.

## Contributing

Issues and pull requests are welcome. Some ideas on the roadmap:

- Note field per day (why was efficiency low?)
- Streak counter for consecutive days at ≥ X% efficiency
- Per-week or per-month efficiency targets
- Aggregated views (weekly / monthly bars) for very long ranges

## License

[MIT](LICENSE)
