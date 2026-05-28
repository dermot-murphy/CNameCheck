#!/usr/bin/env python3
"""
scripts/ci/update_readme_badge.py
===================================
Update the Naming Convention badge link in README.md.

Called by the "Update README badge and push to source branch" step in
cstylecheck_rules.yml (from inside the /tmp/main-wt git worktree):

    python scripts/ci/update_readme_badge.py /tmp/main-wt

Positional argument:
    worktree_path   Absolute path to the checked-out source-branch worktree
                    whose README.md should be updated.

Environment variables consumed:
    REPO    str   GitHub repository in "owner/reponame" format
"""

import os
import pathlib
import re
import sys

if len(sys.argv) < 2:
    print("Usage: update_readme_badge.py <worktree_path>", file=sys.stderr)
    sys.exit(1)

worktree_path = pathlib.Path(sys.argv[1])
repo          = os.environ["REPO"]
owner, reponame = repo.split("/")
pages_base = f"https://{owner}.github.io/{reponame}"
raw_base   = f"https://raw.githubusercontent.com/{owner}/{reponame}/gh-pages"
trend_url  = f"{pages_base}/cstylecheck/"
badge_url  = f"https://img.shields.io/endpoint?url={raw_base}/cstylecheck/badge.json"
badge_md   = f"[![Naming Convention]({badge_url})]({trend_url})"

readme = worktree_path / "README.md"
if not readme.exists():
    print("No README.md -- skipping")
    sys.exit(0)

text    = readme.read_text()
pattern = r"\[!\[Naming Convention\]\([^)]+\)\]\([^)]+\)"
if re.search(pattern, text):
    text = re.sub(pattern, badge_md, text, count=1)
else:
    text = re.sub(r"(^#[^\n]+\n)", rf"\1\n{badge_md}\n",
                  text, count=1, flags=re.MULTILINE)
readme.write_text(text)
print(f"README updated: {badge_md}")
