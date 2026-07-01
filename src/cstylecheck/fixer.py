"""
fixer.py — Auto-fix engine for CStyleCheck.

Applies safe, mechanical source-text corrections for rules that have a
single unambiguous fix.  Works on raw source strings to preserve comments
and formatting; only modifies the specific bytes that constitute the
offending literal.

Safe fixes (--safe-only and --fix):
    misc.unsigned_suffix    — append 'U' to bare integer constant
    misc.lowercase_l_suffix — replace lowercase 'l' with 'L' in suffix

Non-safe fixes (--fix only):
    variable.pointer_prefix — rename pointer parameter/variable to add 'p_'
                              prefix in signature, body, and @param docs

All fixes are applied in reverse-offset order so earlier fixes do not
shift the positions of later ones.
"""
from __future__ import annotations

import difflib
import re
from typing import Optional

from .models import Violation
from .preprocessor import preprocess as _preprocess


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


def _fix_pointer_prefix(source: str, v: Violation) -> Optional[list]:
    """Return list of (offset, old_text, new_text) for pointer prefix rename.

    Renames the parameter/variable everywhere in its function scope:
    the signature (inside the parameter list), the function body if this
    is a definition, and any ``@param``/``\\param`` entry in the doxygen
    block immediately preceding the function.
    """
    m = re.search(
        r"Pointer (?:parameter|variable) '([^']+)' "
        r"local part should start with '([^']+)'",
        v.message,
    )
    if not m:
        return None
    old_name, pfx = m.group(1), m.group(2)
    new_name = pfx + old_name

    # Preprocess for scope-boundary detection (preserves char offsets)
    clean = _preprocess(source)
    offset = _line_col_to_offset(source, v.line, v.col)

    # Walk backward in the clean source to find the enclosing '('
    depth = 0
    paren_open = -1
    for i in range(min(offset + len(old_name), len(clean) - 1), -1, -1):
        if clean[i] == ")":
            depth += 1
        elif clean[i] == "(":
            if depth == 0:
                paren_open = i
                break
            depth -= 1
    if paren_open == -1:
        return None

    # Find the matching ')' scanning forward
    depth = 0
    paren_close = -1
    for i in range(paren_open, len(clean)):
        if clean[i] == "(":
            depth += 1
        elif clean[i] == ")":
            depth -= 1
            if depth == 0:
                paren_close = i
                break
    if paren_close == -1:
        return None

    # Find the start of the function signature (stop at the previous '}' or ';')
    sig_start = 0
    for i in range(paren_open - 1, -1, -1):
        if clean[i] in ";}":
            sig_start = i + 1
            break

    # Determine: function definition (body follows) vs declaration (ends with ;)
    rest = clean[paren_close + 1:paren_close + 30].lstrip()
    is_definition = rest.startswith("{")

    if is_definition:
        brace_open = paren_close + 1
        while brace_open < len(clean) and clean[brace_open] in " \t\n":
            brace_open += 1
        depth = 0
        scope_end = brace_open
        for i in range(brace_open, len(clean)):
            if clean[i] == "{":
                depth += 1
            elif clean[i] == "}":
                depth -= 1
                if depth == 0:
                    scope_end = i + 1
                    break
    else:
        semi = clean.find(";", paren_close)
        scope_end = (semi + 1) if semi != -1 else (paren_close + 1)

    edits: list = []

    # Rename all word-boundary occurrences within [sig_start, scope_end)
    scope_text = source[sig_start:scope_end]
    for wm in re.finditer(r"\b" + re.escape(old_name) + r"\b", scope_text):
        edits.append((sig_start + wm.start(), old_name, new_name))

    # Rename @param / \param in the nearest preceding doxygen block
    pre = source[:sig_start]
    dox_m = None
    for dm in re.finditer(r"/\*\*.*?\*/", pre, re.DOTALL):
        dox_m = dm
    if dox_m is not None and dox_m.end() >= len(pre) - 100:
        for dm in re.finditer(
                r"(?:@param|\\param)[ \t]+" + re.escape(old_name) + r"\b",
                dox_m.group()):
            idx = dm.group().index(old_name)
            edits.append((dox_m.start() + dm.start() + idx, old_name, new_name))

    return edits if edits else None


def get_fn_name_for_fix(source: str, v: Violation) -> str:
    """Return the function name containing the pointer_prefix violation."""
    clean = _preprocess(source)
    offset = _line_col_to_offset(source, v.line, v.col)
    # Scan backward from the violation position (which is inside the param
    # list) to find the '(' that opens the parameter list.
    depth = 0
    paren_open = -1
    for i in range(offset - 1, -1, -1):
        if clean[i] == ")":
            depth += 1
        elif clean[i] == "(":
            if depth == 0:
                paren_open = i
                break
            depth -= 1
    if paren_open == -1:
        return ""
    # The function name is the word immediately before '('
    fn_end = paren_open
    while fn_end > 0 and clean[fn_end - 1] in " \t":
        fn_end -= 1
    fn_s = fn_end
    while fn_s > 0 and (clean[fn_s - 1].isalnum() or clean[fn_s - 1] == "_"):
        fn_s -= 1
    return clean[fn_s:fn_end]


def fix_pointer_prefix_in_header(h_source: str, fn_name: str,
                                  old_name: str, new_name: str) -> str:
    """Rename *old_name* → *new_name* inside *fn_name* declarations in a header."""
    clean = _preprocess(h_source)
    fn_re = re.compile(r"\b" + re.escape(fn_name) + r"\b\s*\(", re.MULTILINE)
    edits: list = []
    for fn_m in fn_re.finditer(clean):
        # Find the matching ')' and the ';' that ends the declaration
        depth = 0
        paren_close = -1
        for i in range(fn_m.end() - 1, len(clean)):
            if clean[i] == "(":
                depth += 1
            elif clean[i] == ")":
                depth -= 1
                if depth == 0:
                    paren_close = i
                    break
        if paren_close == -1:
            continue
        # Only rename within declarations (ends with ;), not definitions
        after = clean[paren_close + 1:paren_close + 20].lstrip()
        if not after.startswith(";"):
            continue
        # Rename within [fn_m.start(), paren_close+1)
        decl_text = h_source[fn_m.start():paren_close + 1]
        for wm in re.finditer(r"\b" + re.escape(old_name) + r"\b", decl_text):
            edits.append((fn_m.start() + wm.start(), old_name, new_name))

    if not edits:
        return h_source

    edits.sort(key=lambda e: e[0], reverse=True)
    result = h_source
    for off, old, new in edits:
        if result[off:off + len(old)] == old:
            result = result[:off] + new + result[off + len(old):]
    return result


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

# Maps rule_id → (fix_fn, is_safe)
# is_safe=True means applied by both --fix and --fix --safe-only
_FIXERS: dict = {
    "misc.unsigned_suffix":      (_fix_unsigned_suffix,    True),
    "misc.lowercase_l_suffix":   (_fix_lowercase_l_suffix, True),
    "variable.pointer_prefix":   (_fix_pointer_prefix,     False),
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
        if edit is None:
            continue
        if isinstance(edit, list):
            edits.extend(edit)
        else:
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
