# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.2] — 2026-05-04

### Added
- **Auto-fill on session start** — if you've already done some Anki
  reviews today before clicking Start (without logging them), the
  add-on automatically appends an untimed session covering the gap, so
  the live session begins from a clean baseline. The auto-fill is
  rollover-aware and only counts Anki time *before* the chosen start
  time, so back-dating still works correctly. A start-tooltip
  acknowledges the auto-log
- **Under-logging warning** — when adding or editing a session that
  would still leave the day's total below the actual Anki time, a
  confirmation dialog shows the gap and asks before saving. The user
  can always proceed; the warning exists to catch accidental
  under-logging
- **Live session reflected on the dashboard** — when a session is
  running, today's bar in the chart, today's row in the history table,
  and the summary cards all update once per minute to include the
  session's elapsed time. The dashboard subscribes to the tracker and
  refreshes only on integer-minute changes to avoid flicker
- **Click a session to edit it** — clicking anywhere on a session's
  label in the input dialog opens the same dialog used to add it, but
  pre-filled with that session's start, end, and minutes. Saving
  replaces the existing session in place
- **Live session shown in the input dialog** — when a session is
  running, it appears at the top of the sessions list with a blue
  "● LIVE" accent. Click the row to adjust its start time on the fly,
  or hit ⏹ to stop and save it without leaving the dialog

### Changed
- **Efficiency now capped at 100%.** If you study 60 min in Anki but
  only logged a 30 min session, the dashboard previously showed 200%.
  It now shows 100%, with the displayed "attempted" value bumped up to
  match the actual Anki time. The rule is `effective_attempted =
  max(raw_logged, actual_anki)`. Adding more sessions first "fills in"
  to that floor; only sessions logged beyond that increase the
  attempted total visibly. Days with zero logged sessions still show
  "no data" rather than a free 100%
- The dashboard's efficiency Y-axis is fixed at 100% (no more dynamic
  rescaling for outliers, since outliers are now impossible)

## [1.3.1] — 2026-05-04

### Changed
- Statusbar label now always shows **today's totals** (attempted minutes,
  Anki minutes, efficiency) instead of just the current session's stats.
  While a live session is running, its elapsed time is added to the
  saved sessions on the fly so the numbers tick up live as you study —
  no visual jump when you stop the session

## [1.3.0] — 2026-05-04

### Added
- **Live sessions** — track efficiency from a chosen moment in time and
  save the result as a regular session when you stop. Start via the
  **▶** button in Anki's bottom statusbar, the Tools menu, or
  `Ctrl+Shift+R`. The same shortcut stops a running session
- **Start-time dialog** — clicking ▶ opens a small dialog letting you
  pick the session's start time. Defaults to right now, can be
  back-dated for when you only remember to start tracking after the
  fact (also handles the "I started at 23:30 yesterday and clicked at
  00:15 today" edge case)
- **Statusbar widget** — a compact ▶ / ⏹ button always sits in Anki's
  bottom statusbar. While a session is running, a label next to it
  shows live elapsed time, Anki minutes so far, and a colour-coded
  efficiency percentage that updates every second. While idle the
  label shows a subtle "Start session" hint
- **30-minute check-in notifications** — gentle tooltip every 30 minutes
  during a live session, summarising your current efficiency.
  Configurable via the new `notify_every_30min` config key
- **Crash / shutdown recovery** — if Anki is closed (or crashes) while a
  session is running, the next time you launch Anki the session is
  auto-stopped and the tracked time is saved to the day it started.
  Stale sessions older than 24 hours are discarded

### Changed
- New `active_session.json` file in the addon directory holds the running
  session state. It's the source of truth for whether a session is active
  and is automatically removed when the session stops

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
