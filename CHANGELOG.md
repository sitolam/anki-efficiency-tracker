# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] — 2026-05-04

### Fixed
- The "today" used by the input dialog and the dashboard now honours
  Anki's day rollover hour (default 4 AM). Before this fix, a study
  session logged at 02:30 was attributed to that calendar day's row
  while Anki itself counted reviews from the same moment against the
  previous day, leading to mismatched efficiency totals around the
  rollover boundary.

## [1.2.0] — 2026-05-04

### Added
- **Session-based time tracking** — log study time as one or more
  sessions per day (e.g., 09:00 → 10:00 + 14:30 → 15:00) instead of a
  single total. The redesigned input dialog shows a per-day list of
  sessions with add / remove buttons. Each session can be either timed
  (start + end time) or untimed ("just minutes"). Total attempted time
  is computed automatically from the sessions

### Changed
- Input dialog redesigned around the session list — changes save
  immediately on add / remove (no separate Save button)
- Data format gained a `sessions` field on each day. Legacy entries with
  only `attempted` still work, and are auto-shown as a single untimed
  session when opened for editing
- Import accepts both the new `sessions` format and the legacy `attempted`
  format

## [1.1.0] — 2026-05-04

### Added
- **Configurable time range** — view the last 7, 30, 90, or 365 days from
  a new dropdown in the dashboard. The choice persists via the new
  `range_days` config key
- **Export data** (Tools → Efficiency Tracker → Export data…) — save your
  attempted-time entries to a JSON file
- **Import data** (Tools → Efficiency Tracker → Import data…) — load
  entries from a JSON export, with a confirmation prompt showing how many
  entries are new vs. overwritten

### Changed
- History table size now scales with the selected range (caps at 30)
- Bar widths and gaps adapt to the range so 90- and 365-day views remain
  legible
- Dashboard subtitle reflects the current range ("last N days")

## [1.0.0] — 2026-05-04

Initial release.

### Features
- **Dashboard** — full-window statistics view with summary cards (today,
  7-day average, 30-day average, active and attempted minutes for today),
  a bar chart comparing attempted vs. actual minutes per day, a colour-coded
  efficiency line chart, and a 14-day history table
- **Daily input** — dialog for logging how much time you attempted to study
  on a given day, with a date picker for back-filling earlier days
- **Top-toolbar button** — "Efficiency" link placed right next to Anki's
  "Stats" button for one-click access to the dashboard
- **Theme support** — automatic / light / dark, cycleable from the
  dashboard's "Theme" button or settable permanently via the addon config
- **Configurable thresholds** — defaults are 70 % (green) and 45 % (red),
  fully tweakable via the addon config; the dashboard legend reflects
  whatever values you pick
- **Keyboard shortcuts** — `Ctrl+Shift+E` to enter time, `Ctrl+Shift+S`
  for the dashboard
- **Pure-SVG visualisations** — no external dependencies, works fully offline
- **Day rollover** — honours Anki's own `rollover` setting (default 4 AM)
- **Per-user JSON storage** — `user_data.json` inside the addon directory
