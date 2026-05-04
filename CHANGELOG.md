# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
