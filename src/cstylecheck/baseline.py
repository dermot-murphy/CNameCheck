"""
baseline.py — Baseline suppression for CStyleCheck.

Contains load_baseline, write_baseline, and _baseline_key.

Imports from: models.
"""
from __future__ import annotations

import sys
from pathlib import Path

from .models import Violation


# ---------------------------------------------------------------------------
# Baseline suppression
# ---------------------------------------------------------------------------

def _baseline_key(v: Violation) -> str:
    """Stable string key identifying a violation for baseline matching."""
    return f"{v.filepath}:{v.line}:{v.rule}:{v.message}"


def load_baseline(path: str) -> frozenset:
    """Load a baseline JSON file and return a frozenset of violation keys."""
    import json
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"Cannot read baseline file '{path}': {e}")
    keys: set = set()
    for entry in data.get("violations", []):
        key = (f"{entry.get('file','')}:{entry.get('line','')}:"
               f"{entry.get('rule','')}:{entry.get('message','')}")
        keys.add(key)
    return frozenset(keys)


def write_baseline(violations: list, path: str) -> None:
    """Write *violations* as a JSON baseline file to *path*."""
    import json
    data = {
        "violations": [
            {
                "file":    v.filepath,
                "line":    v.line,
                "rule":    v.rule,
                "message": v.message,
            }
            for v in violations
        ]
    }
    try:
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as e:
        sys.exit(f"Cannot write baseline file '{path}': {e}")
