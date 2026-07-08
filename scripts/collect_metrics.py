#!/usr/bin/env python3
"""
collect_metrics.py - Gather CStyleCheck trend-analysis metrics and append
a data point to the branch's JSON history file.

Usage:
    python3 scripts/collect_metrics.py --branch <main|develop> \
        [--output-dir <path>]

Output files (written to --output-dir, default: metrics/):
    <branch>.json   - cumulative data points (appended each run)

The script is idempotent: if the current commit is already recorded it
updates the existing entry rather than duplicating it.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
REPO_ROOT   = Path(__file__).resolve().parent.parent
SRC_DIR     = REPO_ROOT / "src"
EXAMPLES    = REPO_ROOT / "examples"
RULES_CFG   = REPO_ROOT / "scripts" / "metrics_rules.yml"
CHECKER     = SRC_DIR / "cstylecheck.py"


def _run(cmd, **kwargs):
    """Run a command, return stdout as a string (empty on failure)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           cwd=REPO_ROOT, **kwargs)
        return r.stdout.strip()
    except Exception:
        return ""


# --------------------------------------------------------------------------
# Git statistics
# --------------------------------------------------------------------------

def _git_commit_info():
    commit  = _run(["git", "rev-parse", "--short", "HEAD"])
    full    = _run(["git", "rev-parse", "HEAD"])
    ts_str  = _run(["git", "log", "-1", "--format=%cI"])
    try:
        ts = datetime.fromisoformat(ts_str).astimezone(timezone.utc).isoformat()
    except Exception:
        ts = datetime.now(timezone.utc).isoformat()
    return commit, full, ts


def _count_source_files():
    """Count tracked source files by category."""
    out = _run(["git", "ls-files"])
    lines = [l for l in out.splitlines() if l]
    c_h   = sum(1 for l in lines if l.endswith((".c", ".h")))
    py    = sum(1 for l in lines if l.endswith(".py"))
    total = len(lines)
    return total, c_h, py


def _git_diff_stats():
    """
    Compare HEAD to HEAD~1.
    Returns (new_files, deleted_files, lines_added, lines_deleted).
    Falls back to zeros on the initial commit.
    """
    out = _run(["git", "diff", "--numstat", "HEAD~1", "HEAD"])
    if not out:
        return 0, 0, 0, 0

    new_files = deleted_files = lines_added = lines_deleted = 0
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added_s, deleted_s = parts[0], parts[1]
        # Binary files show '-' for counts
        if added_s == "-" or deleted_s == "-":
            continue
        added   = int(added_s)
        deleted = int(deleted_s)
        lines_added   += added
        lines_deleted += deleted
        if added   > 0 and deleted == 0:
            new_files += 1
        elif deleted > 0 and added == 0:
            deleted_files += 1

    return new_files, deleted_files, lines_added, lines_deleted


def _test_and_rule_counts():
    """Return (test_count, rule_count) from pytest and rules.yml."""
    # Test count
    out = _run([sys.executable, "-m", "pytest", "tests/",
                "--collect-only", "-q", "--no-header"],
               timeout=60)
    m = re.search(r"(\d+)\s+tests?\s+collected", out)
    test_count = int(m.group(1)) if m else 0

    # Rule count from rules.yml — count top-level section entries that
    # correspond to enabled rules (heuristic: count rule keys with sub-keys)
    rule_count = 0
    try:
        import yaml
        with open(REPO_ROOT / "src" / "rules.yml") as f:
            cfg = yaml.safe_load(f)
        # Each top-level key is a rule group; count by running the checker
        # with --list-rules if available, otherwise approximate from YAML
        rule_count = _count_rule_ids(cfg)
    except Exception:
        pass

    return test_count, rule_count


def _count_rule_ids(cfg):
    """Approximate rule count from the YAML config structure."""
    known_groups = {
        "variables", "functions", "constants", "typedefs",
        "enums", "structs", "include_guards", "misc"
    }
    # A more robust approach: scan Python source for rule_id strings
    count = 0
    for py_file in (REPO_ROOT / "src" / "cstylecheck").glob("*.py"):
        try:
            src = py_file.read_text(encoding="utf-8", errors="replace")
            # Match both "rule.id" string literals and f-string patterns
            count += len(re.findall(r'"(?:variable|function|misc|constant|typedef|enum|struct|include)[a-z._]+"', src))
        except Exception:
            pass
    # Deduplicate by treating unique literal strings
    rule_ids = set()
    for py_file in (REPO_ROOT / "src" / "cstylecheck").glob("*.py"):
        try:
            src = py_file.read_text(encoding="utf-8", errors="replace")
            rule_ids.update(re.findall(
                r'"((?:variable|function|misc|constant|typedef|enum|struct|include)[a-z._]+)"',
                src))
        except Exception:
            pass
    # Add dynamically constructed ones (variable.{scope}.case / .prefix)
    dynamic = {"variable.global.case", "variable.global.prefix",
                "variable.local.case", "variable.local.prefix",
                "variable.static.case", "variable.static.prefix",
                "variable.parameter.case", "variable.parameter.prefix"}
    rule_ids.update(dynamic)
    return len(rule_ids)


# --------------------------------------------------------------------------
# CStyleCheck scan of examples/
# --------------------------------------------------------------------------

def _cstylecheck_metrics():
    """
    Run CStyleCheck on examples/*.c and examples/*.h.
    Returns dict with errors, warnings, info counts and per-rule breakdown.
    """
    c_files = sorted(EXAMPLES.glob("*.c")) + sorted(EXAMPLES.glob("*.h"))
    if not c_files:
        return {"errors": 0, "warnings": 0, "info": 0, "total": 0,
                "files_checked": 0, "rules_violated": []}

    cmd = [sys.executable, str(CHECKER),
           "--config", str(RULES_CFG),
           "--exit-zero",
           "--output-format", "json"] + [str(p) for p in c_files]

    raw = _run(cmd, timeout=120)
    # Strip the banner (first two lines) before parsing JSON
    lines = raw.splitlines()
    json_start = next(
        (i for i, l in enumerate(lines) if l.strip().startswith("{") or l.strip().startswith("[")),
        0)
    try:
        data = json.loads("\n".join(lines[json_start:]))
    except Exception:
        return {"errors": 0, "warnings": 0, "info": 0, "total": 0,
                "files_checked": 0, "rules_violated": []}

    summary    = data.get("summary", {})
    violations = data.get("violations", [])

    from collections import Counter
    by_rule = Counter(v.get("rule", "unknown") for v in violations)

    return {
        "errors":        summary.get("errors",   0),
        "warnings":      summary.get("warnings", 0),
        "info":          summary.get("info",     0),
        "total":         summary.get("total",    0),
        "files_checked": summary.get("files_checked", 0),
        "rules_violated": [{"rule": r, "count": c}
                           for r, c in by_rule.most_common()],
    }


# --------------------------------------------------------------------------
# Comment / whitespace ratios (raw scan of examples/)
# --------------------------------------------------------------------------

def _source_ratios():
    """
    Scan examples/*.c (not headers) to compute:
      - comment_ratio  : non-doxygen comment lines / total non-blank lines
      - whitespace_ratio: blank lines / total lines
    """
    c_files = sorted(EXAMPLES.glob("*.c"))
    total_lines = comment_lines = blank_lines = code_lines = 0
    in_block_comment = False

    for path in c_files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        for line in text.splitlines():
            stripped = line.strip()
            total_lines += 1

            if not stripped:
                blank_lines += 1
                continue

            # Doxygen block start — skip until end
            if stripped.startswith("/**"):
                in_block_comment = True
                # Still count as a line but NOT as a regular comment
                code_lines += 1
                if "*/" in stripped[3:]:
                    in_block_comment = False
                continue

            if in_block_comment:
                code_lines += 1
                if "*/" in stripped:
                    in_block_comment = False
                continue

            # Non-doxygen block comment
            if stripped.startswith("/*"):
                in_block_comment = stripped.count("*/") == 0 or (
                    stripped.startswith("/*") and not stripped.startswith("/**")
                    and "*/" not in stripped)
                comment_lines += 1
                if in_block_comment:
                    in_block_comment = True
                continue

            # Line comment
            if stripped.startswith("//"):
                comment_lines += 1
                continue

            # Inline comment (code line with trailing comment)
            if "//" in stripped or "/*" in stripped:
                code_lines += 1
                comment_lines += 1  # count inline comments separately? No — count as code
                comment_lines -= 1  # revert: inline ≠ comment-only line
                code_lines += 0     # (already counted above)

            code_lines += 1

    non_blank = total_lines - blank_lines
    comment_ratio   = round(comment_lines / non_blank,  4) if non_blank  else 0.0
    whitespace_ratio = round(blank_lines  / total_lines, 4) if total_lines else 0.0

    return {
        "comment_ratio":   comment_ratio,
        "whitespace_ratio": whitespace_ratio,
        "total_lines":      total_lines,
        "blank_lines":      blank_lines,
        "comment_lines":    comment_lines,
        "code_lines":       code_lines,
    }


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def _load_history(path):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {"branch": "", "data_points": []}


def _save_history(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def main():
    ap = argparse.ArgumentParser(description="Collect CStyleCheck trend metrics")
    ap.add_argument("--branch", required=True,
                    help="Branch name (main or develop)")
    ap.add_argument("--output-dir", default="metrics",
                    help="Directory to write JSON history (default: metrics/)")
    args = ap.parse_args()

    branch     = args.branch
    output_dir = REPO_ROOT / args.output_dir

    print(f"[metrics] Collecting for branch: {branch}")

    # --- gather ---
    commit, full_sha, timestamp = _git_commit_info()
    total_files, c_files_count, py_files_count = _count_source_files()
    new_files, deleted_files, lines_added, lines_deleted = _git_diff_stats()
    csc             = _cstylecheck_metrics()
    ratios          = _source_ratios()
    test_count, rule_count = _test_and_rule_counts()

    data_point = {
        "timestamp":       timestamp,
        "commit":          commit,
        "full_sha":        full_sha,
        # Repository file stats
        "total_files":     total_files,
        "c_h_files":       c_files_count,
        "py_files":        py_files_count,
        "new_files":       new_files,
        "deleted_files":   deleted_files,
        "lines_added":     lines_added,
        "lines_deleted":   lines_deleted,
        # CStyleCheck scan of examples/
        "errors":          csc["errors"],
        "warnings":        csc["warnings"],
        "info_count":      csc["info"],
        "total_violations": csc["total"],
        "files_checked":   csc["files_checked"],
        "rules_violated":  csc["rules_violated"],
        # Source ratios (examples/*.c, excluding doxygen)
        "comment_ratio":   ratios["comment_ratio"],
        "whitespace_ratio": ratios["whitespace_ratio"],
        "total_lines":     ratios["total_lines"],
        "comment_lines":   ratios["comment_lines"],
        "code_lines":      ratios["code_lines"],
        # Tool stats
        "test_count":      test_count,
        "rule_count":      rule_count,
    }

    # --- load, upsert, save ---
    hist_path = output_dir / f"{branch}.json"
    history   = _load_history(hist_path)
    history["branch"] = branch

    points = history["data_points"]
    idx = next((i for i, p in enumerate(points) if p.get("full_sha") == full_sha), None)
    if idx is not None:
        points[idx] = data_point
        print(f"[metrics] Updated existing entry for {commit}")
    else:
        points.append(data_point)
        print(f"[metrics] Appended new entry for {commit}")

    _save_history(hist_path, history)
    print(f"[metrics] Saved → {hist_path}")
    print(f"[metrics] Summary: errors={data_point['errors']}, "
          f"warnings={data_point['warnings']}, "
          f"total_files={data_point['total_files']}, "
          f"tests={data_point['test_count']}")

    # Print JSON for the workflow to capture if needed
    print(json.dumps(data_point))


if __name__ == "__main__":
    main()
