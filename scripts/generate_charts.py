#!/usr/bin/env python3
"""
generate_charts.py - Generate SVG trend charts from CStyleCheck metrics JSON.

Usage:
    python3 scripts/generate_charts.py --data-dir <path> \
        [--output-dir <path>] [--branch <name>]

Reads <data-dir>/<branch>.json and writes SVG files to <output-dir>/
with one chart per metric group.
"""

import argparse
import json
import math
from datetime import datetime
from pathlib import Path

# --------------------------------------------------------------------------
# Chart configuration
# --------------------------------------------------------------------------

CHART_W  = 640
CHART_H  = 280
PAD_L    = 68
PAD_R    = 20
PAD_T    = 42
PAD_B    = 56

PLOT_W   = CHART_W - PAD_L - PAD_R
PLOT_H   = CHART_H - PAD_T - PAD_B

FONT     = "ui-monospace, 'Cascadia Code', monospace"
CLR_BG   = "#0d1117"       # GitHub dark background
CLR_GRID = "#21262d"
CLR_AXIS = "#484f58"
CLR_TEXT = "#e6edf3"
CLR_MUTE = "#8b949e"

PALETTES = {
    "errors_warnings": ["#f85149", "#d29922", "#388bfd"],
    "file_stats":      ["#388bfd", "#3fb950", "#f85149", "#d29922"],
    "ratios":          ["#bc8cff", "#39d353"],
    "lines":           ["#3fb950", "#f85149"],
    "repo":            ["#388bfd", "#d29922", "#bc8cff"],
}

# --------------------------------------------------------------------------
# SVG helpers
# --------------------------------------------------------------------------

def _e(tag, attrs, content=""):
    attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    if content:
        return f"<{tag} {attr_str}>{content}</{tag}>"
    return f"<{tag} {attr_str} />"


def _text(x, y, s, **kw):
    kw.setdefault("fill", CLR_TEXT)
    kw.setdefault("font-family", FONT)
    kw.setdefault("font-size", "11")
    return _e("text", {"x": x, "y": y, **kw}, s)


def _line(x1, y1, x2, y2, stroke, width=1, dash=""):
    attrs = {"x1": x1, "y1": y1, "x2": x2, "y2": y2,
             "stroke": stroke, "stroke-width": width}
    if dash:
        attrs["stroke-dasharray"] = dash
    return _e("line", attrs)


def _polyline(points, stroke, width=2, fill="none", opacity=1.0):
    pts = " ".join(f"{x},{y}" for x, y in points)
    return _e("polyline", {"points": pts, "stroke": stroke,
                            "stroke-width": width, "fill": fill,
                            "stroke-linejoin": "round", "stroke-linecap": "round",
                            "opacity": opacity})


def _circle(cx, cy, r, fill):
    return _e("circle", {"cx": cx, "cy": cy, "r": r, "fill": fill})


def _fmt_val(v):
    if isinstance(v, float):
        return f"{v:.3f}" if abs(v) < 10 else f"{v:.1f}"
    return str(v)


# --------------------------------------------------------------------------
# Core chart builder
# --------------------------------------------------------------------------

def _make_chart(title, timestamps, series, palette, y_label="", y_min_zero=True):
    """
    series: list of (label, [values])
    timestamps: list of ISO datetime strings (same length as values)
    Returns SVG string.
    """
    n = len(timestamps)
    if n == 0:
        return ""

    # Flatten all values to determine Y range
    all_vals = [v for _, vals in series for v in vals if v is not None]
    if not all_vals:
        return ""

    raw_min = min(all_vals)
    raw_max = max(all_vals)
    if y_min_zero:
        raw_min = min(0, raw_min)

    data_range = raw_max - raw_min
    if data_range == 0:
        data_range = 1

    # Add 10 % padding on top
    y_lo = raw_min
    y_hi = raw_max + data_range * 0.12

    def px(val):
        frac = (val - y_lo) / (y_hi - y_lo)
        return PAD_T + PLOT_H - frac * PLOT_H

    def qx(i):
        if n == 1:
            return PAD_L + PLOT_W / 2
        return PAD_L + (i / (n - 1)) * PLOT_W

    # --- choose y tick values ---
    tick_count = 5
    step = (y_hi - y_lo) / tick_count
    magnitude = 10 ** math.floor(math.log10(step)) if step > 0 else 1
    nice_steps = [magnitude, 2 * magnitude, 5 * magnitude, 10 * magnitude]
    step = min(nice_steps, key=lambda s: abs(s - step))
    y_ticks = []
    t = math.floor(y_lo / step) * step
    while t <= y_hi + 1e-9:
        y_ticks.append(t)
        t = round(t + step, 10)

    # --- x tick labels (dates) ---
    dates = []
    for ts in timestamps:
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            dates.append(dt.strftime("%b %d"))
        except Exception:
            dates.append("")

    # --- build SVG ---
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{CHART_W}" height="{CHART_H}" '
        f'viewBox="0 0 {CHART_W} {CHART_H}">',
        _e("rect", {"width": CHART_W, "height": CHART_H, "fill": CLR_BG,
                    "rx": "6"}),
        # Title
        _text(PAD_L, 22, title, **{"font-size": "13", "font-weight": "600"}),
    ]

    # Grid lines (horizontal)
    for t in y_ticks:
        if y_lo <= t <= y_hi:
            y = px(t)
            parts.append(_line(PAD_L, y, PAD_L + PLOT_W, y, CLR_GRID, dash="3,3"))
            label = _fmt_val(t) if isinstance(t, float) else str(int(t))
            parts.append(_text(PAD_L - 5, y + 4, label,
                               **{"text-anchor": "end", "fill": CLR_MUTE, "font-size": "10"}))

    # Axes
    parts.append(_line(PAD_L, PAD_T, PAD_L, PAD_T + PLOT_H, CLR_AXIS))
    parts.append(_line(PAD_L, PAD_T + PLOT_H, PAD_L + PLOT_W, PAD_T + PLOT_H, CLR_AXIS))

    # Y axis label
    if y_label:
        parts.append(
            f'<text x="{14}" y="{PAD_T + PLOT_H // 2}" '
            f'fill="{CLR_MUTE}" font-family="{FONT}" font-size="10" '
            f'text-anchor="middle" '
            f'transform="rotate(-90 14 {PAD_T + PLOT_H // 2})">'
            f'{y_label}</text>'
        )

    # X tick labels (show first, mid, last or up to 6 evenly)
    tick_indices = _choose_ticks(n, max_ticks=6)
    for i in tick_indices:
        x = qx(i)
        parts.append(_line(x, PAD_T + PLOT_H, x, PAD_T + PLOT_H + 4, CLR_AXIS))
        parts.append(_text(x, PAD_T + PLOT_H + 16, dates[i],
                           **{"text-anchor": "middle", "fill": CLR_MUTE, "font-size": "10"}))

    # Series
    for idx, (label, values) in enumerate(series):
        color = palette[idx % len(palette)]
        pts   = []
        for i, v in enumerate(values):
            if v is not None:
                pts.append((qx(i), px(v)))

        if len(pts) >= 2:
            parts.append(_polyline(pts, color, width=2))
        for cx, cy in pts:
            parts.append(_circle(cx, cy, 3, color))

    # Legend
    lx = PAD_L
    ly = CHART_H - 16
    for idx, (label, _) in enumerate(series):
        color = palette[idx % len(palette)]
        parts.append(_e("rect", {"x": lx, "y": ly - 9, "width": 14, "height": 3,
                                  "fill": color, "rx": "1"}))
        parts.append(_text(lx + 18, ly, label, **{"fill": CLR_MUTE, "font-size": "10"}))
        lx += max(90, len(label) * 7 + 28)

    parts.append("</svg>")
    return "\n".join(parts)


def _choose_ticks(n, max_ticks=6):
    if n <= max_ticks:
        return list(range(n))
    step = (n - 1) / (max_ticks - 1)
    return sorted(set([0, n - 1] + [round(i * step) for i in range(1, max_ticks - 1)]))


# --------------------------------------------------------------------------
# Chart definitions
# --------------------------------------------------------------------------

def _extract(points, key):
    return [p.get(key) for p in points]


def _generate_all(points, output_dir, branch):
    ts = _extract(points, "timestamp")
    charts = []

    charts.append(("errors_warnings",
        _make_chart(
            f"Violations — {branch}",
            ts,
            [("Errors",   _extract(points, "errors")),
             ("Warnings", _extract(points, "warnings")),
             ("Info",     _extract(points, "info_count"))],
            PALETTES["errors_warnings"],
            y_label="count"
        )))

    charts.append(("file_stats",
        _make_chart(
            f"Repository files — {branch}",
            ts,
            [("Total files",   _extract(points, "total_files")),
             ("Python files",  _extract(points, "py_files")),
             ("C/H files",     _extract(points, "c_h_files"))],
            PALETTES["repo"],
            y_label="files"
        )))

    charts.append(("line_churn",
        _make_chart(
            f"Line churn per commit — {branch}",
            ts,
            [("Lines added",   _extract(points, "lines_added")),
             ("Lines deleted", _extract(points, "lines_deleted"))],
            PALETTES["lines"],
            y_label="lines"
        )))

    charts.append(("file_churn",
        _make_chart(
            f"File churn per commit — {branch}",
            ts,
            [("New files",     _extract(points, "new_files")),
             ("Deleted files", _extract(points, "deleted_files"))],
            PALETTES["file_stats"],
            y_label="files"
        )))

    charts.append(("ratios",
        _make_chart(
            f"Comment & whitespace ratios — {branch}",
            ts,
            [("Comment ratio",    _extract(points, "comment_ratio")),
             ("Whitespace ratio", _extract(points, "whitespace_ratio"))],
            PALETTES["ratios"],
            y_label="ratio",
            y_min_zero=True
        )))

    charts.append(("test_rule_counts",
        _make_chart(
            f"Test & rule counts — {branch}",
            ts,
            [("Test count", _extract(points, "test_count")),
             ("Rule count", _extract(points, "rule_count"))],
            PALETTES["file_stats"],
            y_label="count"
        )))

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, svg in charts:
        if svg:
            p = output_dir / f"{branch}_{name}.svg"
            p.write_text(svg, encoding="utf-8")
            written.append(str(p))
            print(f"[charts] Wrote {p}")

    return written


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Generate SVG trend charts")
    ap.add_argument("--data-dir",    default="metrics",
                    help="Directory containing <branch>.json files")
    ap.add_argument("--output-dir",  default="metrics/charts",
                    help="Directory to write SVG files")
    ap.add_argument("--branch",      default="main",
                    help="Branch name (main or develop)")
    args = ap.parse_args()

    repo_root  = Path(__file__).resolve().parent.parent
    data_file  = repo_root / args.data_dir / f"{args.branch}.json"

    if not data_file.exists():
        print(f"[charts] Data file not found: {data_file}")
        return 1

    history = json.loads(data_file.read_text())
    points  = history.get("data_points", [])
    if not points:
        print("[charts] No data points found, skipping chart generation")
        return 0

    print(f"[charts] {len(points)} data point(s) for branch '{args.branch}'")
    output_dir = repo_root / args.output_dir
    _generate_all(points, output_dir, args.branch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
