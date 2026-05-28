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
# Summary
# ---------------------------------------------------------------------------

def print_summary(all_violations: list, files_checked: int, tee: Tee) -> None:
    errors   = sum(1 for v in all_violations if v.severity == "error")
    warnings = sum(1 for v in all_violations if v.severity == "warning")
    infos    = sum(1 for v in all_violations if v.severity == "info")
    tee.print("\n" + "=" * 60)
    tee.print(f"  Files checked : {files_checked}")
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
