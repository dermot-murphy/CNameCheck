#!/usr/bin/env python3
"""
scripts/ci/append_trend_record.py
==================================
Append a single CI run record to cstylecheck/trend.jsonl.

Called by the "trend" job in cstylecheck_rules.yml:
    run: python scripts/ci/append_trend_record.py

Environment variables consumed (all set by the calling workflow step):
    RUN_NUMBER  int   GitHub Actions run number
    SHA         str   full commit SHA (truncated to 8 chars internally)
    ERRORS      int   number of naming errors
    WARNINGS    int   number of naming warnings
    INFOS       int   number of info-level findings
    FILES       int   number of files checked
"""

import datetime
import json
import os
import pathlib

record = {
    "date":     datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "run":      int(os.environ["RUN_NUMBER"]),
    "sha":      os.environ["SHA"][:8],
    "errors":   int(os.environ["ERRORS"]),
    "warnings": int(os.environ["WARNINGS"]),
    "infos":    int(os.environ["INFOS"]),
    "files":    int(os.environ["FILES"]),
}

trend_file = pathlib.Path("cstylecheck/trend.jsonl")
with trend_file.open("a") as fh:
    fh.write(json.dumps(record) + "\n")

print(f"Appended: {record}")
