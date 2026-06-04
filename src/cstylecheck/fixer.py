"""
fixer.py — Auto-fix engine for CStyleCheck.

Applies safe, mechanical source-text corrections for rules that have a
single unambiguous fix.  Works on raw source strings to preserve comments
and formatting; only modifies the specific bytes that constitute the
offending literal.

Safe fixes (--safe-only and --fix):
    misc.unsigned_suffix    — append 'U' to bare integer constant
    misc.lowercase_l_suffix — replace lowercase 'l' with 'L' in suffix

All fixes are applied in reverse-offset order so earlier fixes do not
shift the positions of later ones.
"""
from __future__ import annotations

import difflib
import re
from typing import Optional

from .models import Violation


# ---------------------------------------------------------------------------
# Individual fix functions
# Each receives (source: str, v: Violation) and returns the corrected source.
# They may return the original source unchanged if the fix cannot be applied.
# ---------------------------------------------------------------------------

_RE_INT_LITERAL = re.compile(r"\b(\d+)([uUlL]*)\b")
_RE_EXTRACT_QUOTED = re.compile(r"'([^']+)'")


def _line_col_to_offset(source: str, line: int, col: int) -> int:
    """Convert 1-based (line, col) to 0-based character offset."""
    lines = source.splitlines(keepends=True)
    offset = sum(len(lines[i]) for i in range(line - 1))
    return offset + col - 1


def _fix_unsigned_suffix(source: str, v: Violation) -> Optional[tuple]:
    """Return (offset, old_text, new_text) for unsigned suffix fix."""
    m = _RE_EXTRACT_QUOTED.search(v.message)
    if not m:
        return None
    literal = m.group(1)
    offset = _line_col_to_offset(source, v.line, v.col)
    # Verify the literal is actually at this offset
    snippet = source[offset: offset + len(literal) + 4]
    lm = re.match(r"(\d+)([uUlLfF]*)", snippet)
    if not lm:
        return None
    digits = lm.group(1)
    suffix = lm.group(2)
    old_text = digits + suffix
    new_text = digits + suffix.upper() + ("U" if "u" not in suffix.lower() else "")
    # Simplify: just append U if not already present
    if "u" not in suffix.lower():
        new_text = digits + suffix + "U"
    else:
        new_text = digits + suffix.upper()
    return (offset, old_text, new_text)


def _fix_lowercase_l_suffix(source: str, v: Violation) -> Optional[tuple]:
    """Return (offset, old_text, new_text) for lowercase-l suffix fix."""
    m = _RE_EXTRACT_QUOTED.search(v.message)
    if not m:
        return None
    literal = m.group(1)
    offset = _line_col_to_offset(source, v.line, v.col)
    snippet = source[offset: offset + len(literal) + 4]
    lm = re.match(r"(\d+)([uUlLfF]+)", snippet)
    if not lm:
        return None
    digits = lm.group(1)
    suffix = lm.group(2)
    new_suffix = suffix.replace("l", "L")
    if new_suffix == suffix:
        return None
    old_text = digits + suffix
    new_text = digits + new_suffix
    return (offset, old_text, new_text)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

# Maps rule_id → (fix_fn, is_safe)
# is_safe=True means applied by both --fix and --fix --safe-only
_FIXERS: dict = {
    "misc.unsigned_suffix":    (_fix_unsigned_suffix,    True),
    "misc.lowercase_l_suffix": (_fix_lowercase_l_suffix, True),
}

FIXABLE_RULES: frozenset = frozenset(_FIXERS)
SAFE_RULES: frozenset = frozenset(r for r, (_, safe) in _FIXERS.items() if safe)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply_fixes(
    source: str,
    violations: list,
    safe_only: bool = False,
) -> tuple[str, int]:
    """Apply fixes for all fixable violations to *source*.

    Returns ``(new_source, fix_count)``.  Fixes are applied in
    reverse-offset order so earlier positions are not shifted.
    """
    allowed = SAFE_RULES if safe_only else FIXABLE_RULES
    edits: list[tuple[int, str, str]] = []

    for v in violations:
        if v.rule not in allowed:
            continue
        fix_fn, _ = _FIXERS[v.rule]
        edit = fix_fn(source, v)
        if edit is not None:
            edits.append(edit)

    if not edits:
        return source, 0

    # Deduplicate by offset (same offset may appear from multiple violations)
    seen_offsets: set = set()
    unique_edits = []
    for offset, old_text, new_text in edits:
        if offset not in seen_offsets:
            seen_offsets.add(offset)
            unique_edits.append((offset, old_text, new_text))

    # Sort descending by offset so later edits don't affect earlier positions
    unique_edits.sort(key=lambda e: e[0], reverse=True)

    result = source
    applied = 0
    for offset, old_text, new_text in unique_edits:
        if result[offset: offset + len(old_text)] == old_text:
            result = result[:offset] + new_text + result[offset + len(old_text):]
            applied += 1

    return result, applied


def unified_diff(original: str, fixed: str, filepath: str) -> str:
    """Return a unified diff string between *original* and *fixed*."""
    orig_lines = original.splitlines(keepends=True)
    fixed_lines = fixed.splitlines(keepends=True)
    diff = difflib.unified_diff(
        orig_lines, fixed_lines,
        fromfile=f"a/{filepath}",
        tofile=f"b/{filepath}",
    )
    return "".join(diff)
