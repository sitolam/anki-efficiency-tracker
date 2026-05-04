"""
Efficiency Tracker — Anki add-on
Compares your actual study time in Anki against the time you attempted
to study, and visualises your efficiency over time.
"""

import json
import os
from datetime import datetime, timedelta

from aqt import mw, gui_hooks
from aqt.qt import (
    QAction, QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QDoubleSpinBox, QDialogButtonBox, QDateEdit, QDate, Qt,
    QWebEngineView,
)
from aqt.utils import qconnect, tooltip, showInfo

ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(ADDON_DIR, "user_data.json")

DEFAULT_CONFIG = {
    "theme": "auto",
    "good_threshold": 70,
    "warn_threshold": 45,
    "show_toolbar_button": True,
}

# Cycle order for the in-dashboard theme toggle button.
THEME_CYCLE = ["auto", "light", "dark"]
THEME_LABELS = {"auto": "Theme: Auto 🌓", "light": "Theme: Light ☀️", "dark": "Theme: Dark 🌙"}


# ---------- Config ----------

def get_config():
    """Read the user's addon config, falling back to defaults for missing keys."""
    cfg = mw.addonManager.getConfig(__name__) or {}
    merged = dict(DEFAULT_CONFIG)
    merged.update(cfg)
    return merged


def save_config(cfg):
    mw.addonManager.writeConfig(__name__, cfg)


# ---------- Data persistence ----------

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        showInfo(f"Could not save data: {e}")


# ---------- Anki integration ----------

def get_rollover_hour():
    """Anki's day rollover hour (default 4 AM)."""
    try:
        return mw.col.get_config("rollover", 4)
    except Exception:
        try:
            return mw.col.conf.get("rollover", 4)
        except Exception:
            return 4


def get_study_minutes_for_date(date_str):
    """Actual Anki study time in minutes for a YYYY-MM-DD date."""
    if mw.col is None:
        return 0.0
    rollover = get_rollover_hour()
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return 0.0

    day_start = dt.replace(hour=rollover, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    start_ms = int(day_start.timestamp() * 1000)
    end_ms = int(day_end.timestamp() * 1000)

    try:
        total_ms = mw.col.db.scalar(
            "SELECT SUM(time) FROM revlog WHERE id >= ? AND id < ?",
            start_ms, end_ms,
        ) or 0
        return total_ms / 1000.0 / 60.0
    except Exception:
        return 0.0


# ---------- Input dialog ----------

class InputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Efficiency — enter study time")
        self.resize(420, 220)

        layout = QVBoxLayout()

        # Date
        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("Date:"))
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setMaximumDate(QDate.currentDate())
        self.date_edit.dateChanged.connect(self.update_display)
        date_row.addWidget(self.date_edit)
        layout.addLayout(date_row)

        # Attempted minutes
        time_row = QHBoxLayout()
        time_row.addWidget(QLabel("Attempted to study (min):"))
        self.spin = QDoubleSpinBox()
        self.spin.setRange(0, 1440)
        self.spin.setDecimals(0)
        self.spin.setSingleStep(5)
        time_row.addWidget(self.spin)
        layout.addLayout(time_row)

        # Info
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("padding: 8px; background: rgba(0,0,0,0.05); border-radius: 6px;")
        layout.addWidget(self.info_label)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.update_display()

    def current_date_str(self):
        return self.date_edit.date().toString("yyyy-MM-dd")

    def update_display(self):
        date_str = self.current_date_str()
        data = load_data()
        attempted = data.get(date_str, {}).get("attempted", 0)
        self.spin.blockSignals(True)
        self.spin.setValue(attempted)
        self.spin.blockSignals(False)

        actual = get_study_minutes_for_date(date_str)
        msg = f"Actual study time in Anki: <b>{actual:.1f} min</b>"
        if attempted > 0:
            eff = (actual / attempted) * 100
            msg += f"<br>Current efficiency: <b>{eff:.1f}%</b>"
        self.info_label.setText(msg)

    def save(self):
        date_str = self.current_date_str()
        data = load_data()
        if date_str not in data:
            data[date_str] = {}
        data[date_str]["attempted"] = self.spin.value()
        save_data(data)
        tooltip(f"Saved for {date_str}: {self.spin.value():.0f} min")
        self.accept()


def show_input_dialog():
    dialog = InputDialog(mw)
    dialog.exec()


# ---------- Stats dialog ----------

def _eff_class(eff, good_threshold, warn_threshold):
    if eff is None:
        return "muted"
    if eff >= good_threshold:
        return "good"
    if eff >= warn_threshold:
        return "warn"
    return "bad"


def _eff_str(eff):
    return f"{eff:.0f}%" if eff is not None else "—"


def build_stats_html(num_days=30):
    config = get_config()
    theme = config.get("theme", "auto")
    good_threshold = config.get("good_threshold", 70)
    warn_threshold = config.get("warn_threshold", 45)

    data = load_data()
    days = []
    for i in range(num_days - 1, -1, -1):
        d = datetime.now() - timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        attempted = data.get(date_str, {}).get("attempted", 0)
        actual = get_study_minutes_for_date(date_str)
        eff = (actual / attempted * 100) if attempted > 0 else None
        days.append({
            "date": date_str,
            "label": d.strftime("%d/%m"),
            "weekday": d.strftime("%a"),
            "attempted": round(attempted, 1),
            "actual": round(actual, 1),
            "efficiency": round(eff, 1) if eff is not None else None,
        })

    today = days[-1]
    valid = [d for d in days if d["efficiency"] is not None]
    avg_30 = sum(d["efficiency"] for d in valid) / len(valid) if valid else None
    last_7 = [d for d in days[-7:] if d["efficiency"] is not None]
    avg_7 = sum(d["efficiency"] for d in last_7) / len(last_7) if last_7 else None

    # SVG dimensions
    chart_w = 880
    chart_h = 280
    pad_l, pad_r, pad_t, pad_b = 50, 20, 20, 40
    inner_w = chart_w - pad_l - pad_r
    inner_h = chart_h - pad_t - pad_b

    # Bar chart data
    max_minutes = max(
        [d["attempted"] for d in days] + [d["actual"] for d in days] + [10]
    )

    def nice_max(v):
        if v <= 30: return 30
        if v <= 60: return 60
        if v <= 120: return 120
        if v <= 240: return 240
        if v <= 480: return 480
        return ((int(v) // 60) + 1) * 60
    y_max = nice_max(max_minutes)

    n = len(days)
    group_w = inner_w / n
    bar_w = group_w * 0.38

    # Generate bars
    bars_svg = []
    x_labels = []
    for i, d in enumerate(days):
        gx = pad_l + i * group_w + group_w / 2
        ah = (d["attempted"] / y_max) * inner_h if y_max > 0 else 0
        ay = pad_t + inner_h - ah
        rh = (d["actual"] / y_max) * inner_h if y_max > 0 else 0
        ry = pad_t + inner_h - rh
        bars_svg.append(
            f'<rect x="{gx - bar_w - 1:.1f}" y="{ay:.1f}" width="{bar_w:.1f}" height="{ah:.1f}" '
            f'fill="var(--warn)" rx="2"><title>{d["date"]}: {d["attempted"]} min attempted</title></rect>'
        )
        bars_svg.append(
            f'<rect x="{gx + 1:.1f}" y="{ry:.1f}" width="{bar_w:.1f}" height="{rh:.1f}" '
            f'fill="var(--accent)" rx="2"><title>{d["date"]}: {d["actual"]} min active</title></rect>'
        )
        if i % max(1, n // 10) == 0 or i == n - 1:
            x_labels.append(
                f'<text x="{gx:.1f}" y="{chart_h - 22:.0f}" text-anchor="middle" class="axis-label">{d["label"]}</text>'
            )

    # Y-axis ticks for bar chart
    y_ticks = []
    y_grid = []
    n_ticks = 4
    for k in range(n_ticks + 1):
        v = y_max * k / n_ticks
        y = pad_t + inner_h - (v / y_max) * inner_h
        y_ticks.append(
            f'<text x="{pad_l - 8:.0f}" y="{y + 4:.1f}" text-anchor="end" class="axis-label">{v:.0f}</text>'
        )
        y_grid.append(
            f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l + inner_w}" y2="{y:.1f}" class="grid"/>'
        )

    # Line chart for efficiency
    eff_chart_h = 240
    eff_inner_h = eff_chart_h - pad_t - pad_b
    eff_y_max = 100
    max_eff = max([d["efficiency"] for d in days if d["efficiency"] is not None] + [100])
    if max_eff > 100:
        eff_y_max = ((int(max_eff) // 25) + 1) * 25

    dots = []
    for i, d in enumerate(days):
        if d["efficiency"] is None:
            continue
        gx = pad_l + i * group_w + group_w / 2
        gy = pad_t + eff_inner_h - (d["efficiency"] / eff_y_max) * eff_inner_h
        eff = d["efficiency"]
        color = "#6dd97a" if eff >= good_threshold else ("#f5a557" if eff >= warn_threshold else "#ec6666")
        dots.append(
            f'<circle cx="{gx:.1f}" cy="{gy:.1f}" r="4" fill="{color}" stroke="var(--card)" stroke-width="2">'
            f'<title>{d["date"]}: {d["efficiency"]:.1f}%</title></circle>'
        )

    # Build line segments — only connect consecutive valid days
    segments = []
    current_seg = []
    for i, d in enumerate(days):
        if d["efficiency"] is None:
            if len(current_seg) > 1:
                segments.append(" ".join(f"{x:.1f},{y:.1f}" for x, y in current_seg))
            current_seg = []
        else:
            gx = pad_l + i * group_w + group_w / 2
            gy = pad_t + eff_inner_h - (d["efficiency"] / eff_y_max) * eff_inner_h
            current_seg.append((gx, gy))
    if len(current_seg) > 1:
        segments.append(" ".join(f"{x:.1f},{y:.1f}" for x, y in current_seg))
    polylines = "\n".join(
        f'<polyline points="{seg}" fill="none" stroke="var(--good)" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>'
        for seg in segments
    )

    # Eff y-ticks
    eff_y_ticks = []
    eff_y_grid = []
    for k in range(5):
        v = eff_y_max * k / 4
        y = pad_t + eff_inner_h - (v / eff_y_max) * eff_inner_h
        eff_y_ticks.append(
            f'<text x="{pad_l - 8:.0f}" y="{y + 4:.1f}" text-anchor="end" class="axis-label">{v:.0f}%</text>'
        )
        eff_y_grid.append(
            f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l + inner_w}" y2="{y:.1f}" class="grid"/>'
        )
    y_100 = pad_t + eff_inner_h - (100 / eff_y_max) * eff_inner_h
    ref_line = (
        f'<line x1="{pad_l}" y1="{y_100:.1f}" x2="{pad_l + inner_w}" y2="{y_100:.1f}" '
        f'stroke="var(--muted)" stroke-width="1" stroke-dasharray="3,3" opacity="0.6"/>'
    )

    eff_x_labels = []
    for i, d in enumerate(days):
        if i % max(1, n // 10) == 0 or i == n - 1:
            gx = pad_l + i * group_w + group_w / 2
            eff_x_labels.append(
                f'<text x="{gx:.1f}" y="{eff_chart_h - 22:.0f}" text-anchor="middle" class="axis-label">{d["label"]}</text>'
            )

    # History table (last 14 days, most recent first)
    history_rows = []
    for d in reversed(days[-14:]):
        eff_text = _eff_str(d["efficiency"])
        eff_cls = _eff_class(d["efficiency"], good_threshold, warn_threshold)
        history_rows.append(f"""
            <tr>
                <td>{d['date']} <span class="muted">({d['weekday']})</span></td>
                <td>{d['attempted']:.0f} min</td>
                <td>{d['actual']:.1f} min</td>
                <td class="{eff_cls}"><b>{eff_text}</b></td>
            </tr>
        """)

    # Theme variables (resolved server-side so we don't depend on the
    # webview's prefers-color-scheme behaviour).
    dark_vars = """
  --bg: #1e1f26;
  --card: #2a2b34;
  --text: #e8e9ed;
  --muted: #8a8d99;
  --accent: #6ba4ff;
  --good: #6dd97a;
  --warn: #f5a557;
  --bad: #ec6666;
  --grid: rgba(255,255,255,0.08);
  --border: rgba(255,255,255,0.08);
"""
    light_vars = """
  --bg: #f5f6f8;
  --card: #ffffff;
  --text: #1a1a1a;
  --muted: #6b7280;
  --accent: #6ba4ff;
  --good: #5cb86a;
  --warn: #e89545;
  --bad: #d65555;
  --grid: rgba(0,0,0,0.06);
  --border: rgba(0,0,0,0.06);
"""

    if theme == "dark":
        theme_css = f":root {{{dark_vars}}}"
    elif theme == "light":
        theme_css = f":root {{{light_vars}}}"
    else:  # auto
        theme_css = (
            f":root {{{dark_vars}}}"
            f"@media (prefers-color-scheme: light) {{ :root {{{light_vars}}} }}"
        )

    # Build legend strings dynamically from configured thresholds.
    legend_good = f"≥ {good_threshold:.0f}%"
    legend_warn = f"{warn_threshold:.0f}–{good_threshold - 1:.0f}%"
    legend_bad = f"&lt; {warn_threshold:.0f}%"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
{theme_css}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  padding: 24px;
  line-height: 1.5;
  font-size: 14px;
}}
h1 {{ font-size: 22px; font-weight: 700; margin-bottom: 4px; }}
.subtitle {{ color: var(--muted); margin-bottom: 20px; font-size: 13px; }}
.stats {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}}
.stat-card {{
  background: var(--card);
  padding: 14px 16px;
  border-radius: 10px;
  border: 1px solid var(--border);
}}
.stat-label {{
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
  font-weight: 600;
}}
.stat-value {{ font-size: 26px; font-weight: 700; }}
.stat-value .unit {{ font-size: 13px; color: var(--muted); font-weight: 500; }}
.good {{ color: var(--good); }}
.warn {{ color: var(--warn); }}
.bad {{ color: var(--bad); }}
.muted {{ color: var(--muted); }}
.chart-card {{
  background: var(--card);
  padding: 18px;
  border-radius: 10px;
  margin-bottom: 16px;
  border: 1px solid var(--border);
}}
.chart-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}}
.chart-title {{ font-size: 15px; font-weight: 600; }}
.legend {{ display: flex; gap: 14px; font-size: 12px; color: var(--muted); }}
.legend-item {{ display: flex; align-items: center; gap: 6px; }}
.legend-swatch {{ width: 10px; height: 10px; border-radius: 2px; }}
svg {{ width: 100%; height: auto; display: block; }}
.axis-label {{ fill: var(--muted); font-size: 11px; }}
.grid {{ stroke: var(--grid); stroke-width: 1; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th, td {{ padding: 8px 10px; text-align: left; border-bottom: 1px solid var(--border); }}
th {{ color: var(--muted); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }}
tr:last-child td {{ border-bottom: none; }}
</style>
</head>
<body>
<h1>📊 Efficiency Tracker</h1>
<p class="subtitle">Actual study time in Anki vs. time attempted to study — last 30 days</p>

<div class="stats">
  <div class="stat-card">
    <div class="stat-label">Today</div>
    <div class="stat-value {_eff_class(today['efficiency'], good_threshold, warn_threshold)}">{_eff_str(today['efficiency'])}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">7-day average</div>
    <div class="stat-value {_eff_class(avg_7, good_threshold, warn_threshold)}">{_eff_str(avg_7)}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">30-day average</div>
    <div class="stat-value {_eff_class(avg_30, good_threshold, warn_threshold)}">{_eff_str(avg_30)}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Active today</div>
    <div class="stat-value">{today['actual']:.0f}<span class="unit"> min</span></div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Attempted today</div>
    <div class="stat-value">{today['attempted']:.0f}<span class="unit"> min</span></div>
  </div>
</div>

<div class="chart-card">
  <div class="chart-header">
    <div class="chart-title">Study time per day</div>
    <div class="legend">
      <div class="legend-item"><div class="legend-swatch" style="background:var(--warn)"></div>Attempted</div>
      <div class="legend-item"><div class="legend-swatch" style="background:var(--accent)"></div>Active in Anki</div>
    </div>
  </div>
  <svg viewBox="0 0 {chart_w} {chart_h}" preserveAspectRatio="xMidYMid meet">
    {''.join(y_grid)}
    {''.join(bars_svg)}
    {''.join(y_ticks)}
    {''.join(x_labels)}
  </svg>
</div>

<div class="chart-card">
  <div class="chart-header">
    <div class="chart-title">Efficiency per day</div>
    <div class="legend">
      <div class="legend-item"><div class="legend-swatch" style="background:var(--good)"></div>{legend_good}</div>
      <div class="legend-item"><div class="legend-swatch" style="background:var(--warn)"></div>{legend_warn}</div>
      <div class="legend-item"><div class="legend-swatch" style="background:var(--bad)"></div>{legend_bad}</div>
    </div>
  </div>
  <svg viewBox="0 0 {chart_w} {eff_chart_h}" preserveAspectRatio="xMidYMid meet">
    {''.join(eff_y_grid)}
    {ref_line}
    {polylines}
    {''.join(dots)}
    {''.join(eff_y_ticks)}
    {''.join(eff_x_labels)}
  </svg>
</div>

<div class="chart-card">
  <div class="chart-title" style="margin-bottom: 10px;">Recent history (14 days)</div>
  <table>
    <thead>
      <tr>
        <th>Date</th>
        <th>Attempted</th>
        <th>Active</th>
        <th>Efficiency</th>
      </tr>
    </thead>
    <tbody>
      {''.join(history_rows)}
    </tbody>
  </table>
</div>
</body>
</html>"""


class StatsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Efficiency Tracker — Statistics")
        self.resize(960, 760)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.web = QWebEngineView(self)
        self.web.setMinimumHeight(600)
        self.web.setHtml(build_stats_html())
        layout.addWidget(self.web)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(12, 8, 12, 12)

        btn_input = QPushButton("➕ Enter study time")
        btn_input.clicked.connect(self.open_input)
        btn_row.addWidget(btn_input)

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.clicked.connect(self.refresh)
        btn_row.addWidget(btn_refresh)

        btn_row.addStretch()

        # Theme toggle — cycles auto → light → dark and persists to config.
        self.btn_theme = QPushButton()
        self.btn_theme.setToolTip("Cycle the dashboard theme (auto / light / dark)")
        self.btn_theme.clicked.connect(self.cycle_theme)
        self._refresh_theme_label()
        btn_row.addWidget(self.btn_theme)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)

        layout.addLayout(btn_row)
        self.setLayout(layout)

    def _refresh_theme_label(self):
        cur = get_config().get("theme", "auto")
        self.btn_theme.setText(THEME_LABELS.get(cur, THEME_LABELS["auto"]))

    def cycle_theme(self):
        cfg = get_config()
        cur = cfg.get("theme", "auto")
        try:
            nxt = THEME_CYCLE[(THEME_CYCLE.index(cur) + 1) % len(THEME_CYCLE)]
        except ValueError:
            nxt = "auto"
        cfg["theme"] = nxt
        save_config(cfg)
        self._refresh_theme_label()
        self.refresh()

    def refresh(self):
        self.web.setHtml(build_stats_html())

    def open_input(self):
        dialog = InputDialog(self)
        if dialog.exec():
            self.refresh()


def show_stats():
    dialog = StatsDialog(mw)
    dialog.exec()


# ---------- Top toolbar button ----------

def _add_toolbar_link(links, toolbar):
    """Insert an "Efficiency" link in the top toolbar, right after Stats."""
    if not get_config().get("show_toolbar_button", True):
        return

    link = toolbar.create_link(
        cmd="efficiency_tracker",
        label="Efficiency",
        func=show_stats,
        tip="Open Efficiency Tracker statistics",
        id="efficiency-tracker",
    )

    # Anki's default order is decks, add, browse, stats, sync. We want our
    # link directly after stats — that's index 4. If the toolbar layout
    # ever changes, we fall back to appending.
    insert_at = None
    for i, raw in enumerate(links):
        if 'id="qt-link-stats"' in raw or "qt-link-stats" in raw:
            insert_at = i + 1
            break
    if insert_at is None:
        insert_at = min(4, len(links))
    links.insert(insert_at, link)


gui_hooks.top_toolbar_did_init_links.append(_add_toolbar_link)


# ---------- Menu setup ----------

def setup_menu():
    menu = mw.form.menuTools.addMenu("Efficiency Tracker")

    action_input = QAction("➕ Enter study time…", mw)
    action_input.setShortcut("Ctrl+Shift+E")
    qconnect(action_input.triggered, show_input_dialog)
    menu.addAction(action_input)

    action_stats = QAction("📊 Show statistics…", mw)
    action_stats.setShortcut("Ctrl+Shift+S")
    qconnect(action_stats.triggered, show_stats)
    menu.addAction(action_stats)


setup_menu()
