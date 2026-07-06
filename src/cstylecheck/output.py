"""
output.py — Output helpers for CStyleCheck.

Contains Tee, _violations_to_json, _violations_to_sarif, and print_summary.

Imports from: models.
"""
from __future__ import annotations

from collections import Counter


# ---------------------------------------------------------------------------
# Output helper — tee to stdout and optional log file
# ---------------------------------------------------------------------------

class Tee:
    """Write to stdout and optionally a log file simultaneously."""

    def __init__(self, log_fh=None):
        self._log = log_fh

    def print(self, *args, **kwargs) -> None:
        # Always write to stdout
        kwargs.pop("file", None)
        print(*args, **kwargs)
        if self._log:
            print(*args, file=self._log, **kwargs)

    def close(self) -> None:
        if self._log:
            self._log.close()
            self._log = None


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def _violations_to_json(violations: list, files_checked: int) -> str:
    """Serialise *violations* to a JSON string."""
    import json
    errors   = sum(1 for v in violations if v.severity == "error")
    warnings = sum(1 for v in violations if v.severity == "warning")
    infos    = sum(1 for v in violations if v.severity == "info")
    return json.dumps({
        "summary": {
            "files_checked": files_checked,
            "errors": errors,
            "warnings": warnings,
            "info": infos,
            "total": len(violations),
        },
        "violations": [
            {
                "file":     v.filepath,
                "line":     v.line,
                "col":      v.col,
                "severity": v.severity,
                "rule":     v.rule,
                "message":  v.message,
            }
            for v in violations
        ],
    }, indent=2)


# ---------------------------------------------------------------------------
# SARIF output  (SARIF 2.1.0 — consumed by GitHub Code Scanning)
# ---------------------------------------------------------------------------

def _violations_to_sarif(violations: list, tool_version: str) -> str:
    """Serialise *violations* to a SARIF 2.1.0 JSON string."""
    import json

    # Collect unique rule IDs
    rule_ids = list(dict.fromkeys(v.rule for v in violations))
    rules = [
        {"id": rid, "name": rid.replace(".", "_"),
         "shortDescription": {"text": rid}}
        for rid in rule_ids
    ]

    # Map severity → SARIF level
    _sev_map = {"error": "error", "warning": "warning", "info": "note"}

    results = []
    for v in violations:
        results.append({
            "ruleId": v.rule,
            "level": _sev_map.get(v.severity, "note"),
            "message": {"text": v.message},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": v.filepath.replace("\\", "/")},
                    "region": {"startLine": v.line, "startColumn": v.col},
                }
            }],
        })

    # _TOOL_NAME imported lazily to avoid circular import
    from . import _TOOL_NAME
    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/"
                   "master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": _TOOL_NAME,
                    "version": tool_version,
                    "rules": rules,
                }
            },
            "results": results,
        }],
    }
    return json.dumps(sarif, indent=2)


# ---------------------------------------------------------------------------
# HTML output  (self-contained, no external dependencies)
# ---------------------------------------------------------------------------

_HTML_CSS = """
body{font-family:system-ui,sans-serif;margin:0;background:#f5f5f5;color:#222}
header{background:#1a1a2e;color:#fff;padding:1rem 2rem}
header h1{margin:0;font-size:1.4rem;letter-spacing:.04em}
header p{margin:.3rem 0 0;font-size:.85rem;opacity:.8}
.summary{display:flex;gap:1rem;padding:1rem 2rem;background:#fff;
  border-bottom:1px solid #ddd;flex-wrap:wrap}
.card{border-radius:6px;padding:.6rem 1.2rem;min-width:100px;text-align:center;
  font-weight:bold;font-size:1.1rem}
.card span{display:block;font-size:.72rem;font-weight:normal;margin-top:.2rem}
.card.error{background:#fde8e8;color:#c0392b}
.card.warning{background:#fff3cd;color:#856404}
.card.info{background:#d1ecf1;color:#0c5460}
.card.total{background:#e2e3e5;color:#383d41}
.card.files{background:#d4edda;color:#155724}
main{padding:1.5rem 2rem}
.file-section{background:#fff;border-radius:8px;margin-bottom:1.2rem;
  box-shadow:0 1px 3px rgba(0,0,0,.1);overflow:hidden}
.file-header{background:#2d3436;color:#fff;padding:.6rem 1rem;
  font-family:monospace;font-size:.9rem;display:flex;
  justify-content:space-between;align-items:center}
.file-header .badge{background:#636e72;border-radius:12px;
  padding:.1rem .6rem;font-size:.78rem}
table{width:100%;border-collapse:collapse;font-size:.88rem}
th{background:#ecf0f1;text-align:left;padding:.45rem .7rem;
  font-size:.78rem;text-transform:uppercase;letter-spacing:.04em;
  color:#636e72;border-bottom:2px solid #ddd}
td{padding:.4rem .7rem;border-bottom:1px solid #f0f0f0;vertical-align:top}
tr:last-child td{border-bottom:none}
tr.error td{background:#fff5f5}
tr.warning td{background:#fffdf0}
tr.info td{background:#f0faff}
.sev{border-radius:4px;padding:.1rem .45rem;font-size:.76rem;
  font-weight:bold;white-space:nowrap}
.sev.error{background:#fde8e8;color:#c0392b}
.sev.warning{background:#fff3cd;color:#856404}
.sev.info{background:#d1ecf1;color:#0c5460}
.rule{font-family:monospace;font-size:.82rem;color:#2980b9}
.loc{font-family:monospace;font-size:.82rem;white-space:nowrap}
.clean{padding:.8rem 1rem;color:#27ae60;font-size:.88rem}
footer{text-align:center;padding:1rem;font-size:.78rem;color:#888}
"""


def _h(text: str) -> str:
    """HTML-escape *text*."""
    import html
    return html.escape(str(text))


def _violations_to_html(violations: list, files_checked: int,
                         version: str) -> str:
    """Generate a self-contained HTML report from *violations*."""
    import datetime
    from collections import defaultdict

    errors   = sum(1 for v in violations if v.severity == "error")
    warnings = sum(1 for v in violations if v.severity == "warning")
    infos    = sum(1 for v in violations if v.severity == "info")

    # Group violations by filepath, preserving order
    by_file: dict = defaultdict(list)
    for v in violations:
        by_file[v.filepath].append(v)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    from . import _VERSION_STRING

    lines = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        f"<title>CStyleCheck Report — {now}</title>",
        f"<style>{_HTML_CSS}</style>",
        "</head>",
        "<body>",
        "<header>",
        "<h1>CStyleCheck Report</h1>",
        f"<p>Generated {now} &nbsp;|&nbsp; {_h(_VERSION_STRING)}</p>",
        "</header>",
        '<div class="summary">',
        f'<div class="card files">{files_checked}<span>files checked</span></div>',
        f'<div class="card error">{errors}<span>errors</span></div>',
        f'<div class="card warning">{warnings}<span>warnings</span></div>',
        f'<div class="card info">{infos}<span>info</span></div>',
        f'<div class="card total">{len(violations)}<span>total</span></div>',
        "</div>",
        "<main>",
    ]

    if not violations:
        lines.append('<p style="color:#27ae60;font-size:1.1rem">'
                     "&#10003; No violations found.</p>")
    else:
        for filepath, file_viols in by_file.items():
            count = len(file_viols)
            lines += [
                '<div class="file-section">',
                '<div class="file-header">',
                f'<span>{_h(filepath)}</span>',
                f'<span class="badge">{count} violation{"s" if count != 1 else ""}</span>',
                "</div>",
                "<table>",
                "<thead><tr>"
                "<th>Line</th><th>Col</th><th>Severity</th>"
                "<th>Rule</th><th>Message</th>"
                "</tr></thead>",
                "<tbody>",
            ]
            for v in sorted(file_viols, key=lambda x: (x.line, x.col)):
                sev = _h(v.severity)
                lines.append(
                    f'<tr class="{sev}">'
                    f'<td class="loc">{v.line}</td>'
                    f'<td class="loc">{v.col}</td>'
                    f'<td><span class="sev {sev}">{sev}</span></td>'
                    f'<td><span class="rule">{_h(v.rule)}</span></td>'
                    f'<td>{_h(v.message)}</td>'
                    "</tr>"
                )
            lines += ["</tbody>", "</table>", "</div>"]

    lines += [
        "</main>",
        f'<footer>Generated by {_h(_VERSION_STRING)}</footer>',
        "</body>",
        "</html>",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(all_violations: list, files_checked: int, tee: Tee) -> None:
    errors   = sum(1 for v in all_violations if v.severity == "error")
    warnings = sum(1 for v in all_violations if v.severity == "warning")
    infos    = sum(1 for v in all_violations if v.severity == "info")
    tee.print("\n" + "=" * 60)
    tee.print("  Errors & Warnings:")
    tee.print(f"  Errors        : {errors}")
    tee.print(f"  Warnings      : {warnings}")
    tee.print(f"  Info          : {infos}")
    tee.print(f"  {chr(8211) * 36}")
    tee.print(f"  Total         : {errors + warnings + infos}")
    tee.print("=" * 60)
    rule_counts: Counter = Counter(v.rule for v in all_violations)
    if rule_counts:
        tee.print("  Top violated rules:")
        for rule, count in rule_counts.most_common(10):
            tee.print(f"    {rule:<45} {count}")
    tee.print("=" * 60)

    # Per-file breakdown: bucket each file into errors / warnings / info / ok
    files_with_errors:   set = set()
    files_with_warnings: set = set()
    files_with_infos:    set = set()
    for v in all_violations:
        if v.severity == "error":
            files_with_errors.add(v.filepath)
        elif v.severity == "warning":
            files_with_warnings.add(v.filepath)
        elif v.severity == "info":
            files_with_infos.add(v.filepath)
    files_with_issues = (
        files_with_errors | files_with_warnings | files_with_infos
    )
    # Count unique files per bucket (a file counts in the highest bucket only)
    files_error_only   = len(files_with_errors)
    files_warning_only = len(files_with_warnings - files_with_errors)
    files_info_only    = len(files_with_infos - files_with_errors - files_with_warnings)
    files_clean        = files_checked - len(files_with_issues)
    if files_checked > 0:
        tee.print("  Files:")
        tee.print(f"    Files checked       : {files_checked}")
        tee.print(f"    Files with errors   : {files_error_only}")
        tee.print(f"    Files with warnings : {files_warning_only}")
        tee.print(f"    Files with info     : {files_info_only}")
        tee.print(f"    Files clean         : {files_clean}")
        tee.print("=" * 60)
