#!/usr/bin/env python3
"""
scripts/ci/generate_trend.py
=============================
Generate the gh-pages trend HTML dashboard (cstylecheck/index.html) and
shields.io badge JSON (cstylecheck/badge.json) from trend.jsonl data.

Called by the "trend" job in cstylecheck_rules.yml:
    run: python scripts/ci/generate_trend.py

Environment variables consumed (all set by the calling workflow step):
    ERRORS    int   number of naming errors in the latest run
    WARNINGS  int   number of naming warnings in the latest run
    INFOS     int   number of info-level findings in the latest run
    FILES     int   number of files checked in the latest run
    REPO      str   GitHub repository in "owner/reponame" format
"""

import json
import os
import pathlib

# ---------------------------------------------------------------------------
# Load trend data
# ---------------------------------------------------------------------------
trend_file = pathlib.Path("cstylecheck/trend.jsonl")
records = [json.loads(line) for line in trend_file.read_text().splitlines() if line.strip()]
recent = records[-60:]   # keep last 60 data points on the chart

errors   = int(os.environ["ERRORS"])
warnings = int(os.environ["WARNINGS"])
infos    = int(os.environ["INFOS"])
files    = os.environ["FILES"]
repo     = os.environ["REPO"]
owner, reponame = repo.split("/")
pages_base = f"https://{owner}.github.io/{reponame}"
raw_base   = f"https://raw.githubusercontent.com/{owner}/{reponame}/gh-pages"

# ---------------------------------------------------------------------------
# Badge JSON (served by shields.io endpoint)
# ---------------------------------------------------------------------------
total   = errors + warnings
colour  = "brightgreen" if total == 0 else "yellow" if errors == 0 else "red"
message = "clean" if total == 0 else f"{errors}E {warnings}W"
badge   = {"schemaVersion": 1, "label": "naming", "message": message, "color": colour}
pathlib.Path("cstylecheck/badge.json").write_text(json.dumps(badge, indent=2))

# ---------------------------------------------------------------------------
# Chart data
# ---------------------------------------------------------------------------
labels = [r["date"][:10] + " #" + str(r.get("run", "?")) for r in recent]
e_vals = [r["errors"]   for r in recent]
w_vals = [r["warnings"] for r in recent]
i_vals = [r["infos"]    for r in recent]

rows = "".join(
    f'<tr><td>{r["date"][:10]}</td><td>#{r.get("run","?")}</td>'
    f'<td><code>{r["sha"]}</code></td><td>{r["files"]}</td>'
    f'<td style="color:{"red" if r["errors"] else "green"}">{r["errors"]}</td>'
    f'<td style="color:{"orange" if r["warnings"] else "green"}">{r["warnings"]}</td>'
    f'<td>{r["infos"]}</td></tr>'
    for r in reversed(recent)
)

# ---------------------------------------------------------------------------
# Trend HTML page
# ---------------------------------------------------------------------------
html = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{reponame} -- Naming Convention Trend</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 960px;
         margin: 0 auto; padding: 1rem 1.5rem; color: #222; }}
  h1   {{ font-size: 1.4rem; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.85rem; }}
  th, td {{ border: 1px solid #ccc; padding: 4px 8px; text-align: right; }}
  th {{ background: #f5f5f5; text-align: center; }}
  td:nth-child(1), td:nth-child(2), td:nth-child(3) {{ text-align: left; }}
  .stat {{ display: inline-block; margin: 0 1rem; font-size: 1.1rem; }}
  canvas {{ margin: 1.5rem 0; }}
</style>
</head><body>
<h1>📋 {reponame}: Naming Convention Trend</h1>
<p>
  <span class="stat">🔴 <strong style="color:{'red' if errors else 'green'}">{errors}</strong> errors</span>
  <span class="stat">🟡 <strong style="color:{'orange' if warnings else 'green'}">{warnings}</strong> warnings</span>
  <span class="stat">📁 {files} files</span>
  <span class="stat">🔢 {len(records)} runs recorded</span>
</p>
<canvas id="chart" height="120"></canvas>
<script>
new Chart(document.getElementById('chart'), {{
  type: 'line',
  data: {{
    labels: {json.dumps(labels)},
    datasets: [
      {{ label: 'Errors',   data: {json.dumps(e_vals)}, fill: true,
         borderColor: '#d32f2f', backgroundColor: 'rgba(211,47,47,0.15)',
         tension: 0.3, pointRadius: 3 }},
      {{ label: 'Warnings', data: {json.dumps(w_vals)}, fill: true,
         borderColor: '#f57c00', backgroundColor: 'rgba(245,124,0,0.12)',
         tension: 0.3, pointRadius: 3 }},
      {{ label: 'Info',     data: {json.dumps(i_vals)}, fill: true,
         borderColor: '#1976d2', backgroundColor: 'rgba(25,118,210,0.10)',
         tension: 0.3, pointRadius: 3 }},
    ]
  }},
  options: {{
    responsive: true,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{ legend: {{ position: 'top' }},
               tooltip: {{ mode: 'index' }} }},
    scales: {{ y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }} }}
  }}
}});
</script>
<h2>Run history (last {len(recent)} runs)</h2>
<table>
<tr><th>Date</th><th>Run</th><th>SHA</th><th>Files</th>
    <th>Errors</th><th>Warnings</th><th>Info</th></tr>
{rows}
</table>
<p><small>Source: <a href="https://github.com/{repo}">{repo}</a></small></p>
</body></html>"""

pathlib.Path("cstylecheck/index.html").write_text(html)
print(f"Trend page: {pages_base}/cstylecheck/")
print(f"Badge URL:  https://img.shields.io/endpoint?url={raw_base}/cstylecheck/badge.json")
