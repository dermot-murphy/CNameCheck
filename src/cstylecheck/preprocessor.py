"""
preprocessor.py — Source pre-processing utilities for CStyleCheck.

Contains strip_comments, strip_strings, preprocess, build_line_map,
offset_to_line_col, _build_brace_depths, _comment_only_lines,
and extract_comments.

No internal dependencies (stdlib only).
"""
from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Source pre-processing
# ---------------------------------------------------------------------------

def strip_comments(source: str) -> str:
    """Replace comment content with spaces, preserving newlines and length."""
    def _blank_block(m: re.Match) -> str:
        return re.sub(r"[^\n]", " ", m.group())

    source = re.sub(r"/\*.*?\*/", _blank_block, source, flags=re.DOTALL)
    source = re.sub(r"//[^\n]*", lambda m: " " * len(m.group()), source)
    return source


def strip_strings(source: str) -> str:
    # Blank double-quoted string literals (preserve length for offset tracking)
    source = re.sub(
        r'"(?:[^"\\]|\\.)*"',
        lambda m: '""' + " " * (len(m.group()) - 2),
        source,
    )
    # Normalise single-quoted character literals to 'x' so tokens inside them
    # cannot trigger unsigned-suffix or other digit-sensitive checks, while
    # preserving the char-literal shape so the yoda checker still recognises
    # 'x' as a constant token (its RHS scanner skips spaces but not letters).
    source = re.sub(r"'(?:[^'\\]|\\.)'", lambda m: "'x'", source)
    return source


def preprocess(source: str) -> str:
    return strip_strings(strip_comments(source))


def _comment_only_lines(source: str) -> set:
    """Return 1-based line numbers that are pure comment/whitespace."""
    exempt: set = set()
    in_block = False
    for lineno, line in enumerate(source.splitlines(), 1):
        stripped = line.lstrip()
        if in_block:
            exempt.add(lineno)
            if "*/" in line:
                in_block = False
        elif stripped.startswith("/*"):
            exempt.add(lineno)
            if "*/" not in stripped[2:]:
                in_block = True
        elif stripped.startswith("//"):
            exempt.add(lineno)
        elif not stripped:
            exempt.add(lineno)
    return exempt


def extract_comments(source: str) -> list:
    """Return [(lineno, text)] for all comments, stripped of doxygen markers."""
    results = []
    line_map = build_line_map(source)

    for m in re.finditer(r"/\*(.*?)\*/", source, re.DOTALL):
        lineno, _ = offset_to_line_col(line_map, m.start())
        text = m.group(1)
        text = re.sub(r"[@\\]\w+", " ", text)
        text = re.sub(r"^\s*\*+", " ", text, flags=re.MULTILINE)
        results.append((lineno, text))

    for m in re.finditer(r"//([^\n]*)", source):
        lineno, _ = offset_to_line_col(line_map, m.start())
        text = re.sub(r"[@\\]\w+", " ", m.group(1))
        results.append((lineno, text))

    return results


# ---------------------------------------------------------------------------
# Brace-depth map (used for scope classification)
# ---------------------------------------------------------------------------

def _build_brace_depths(clean: str) -> list:
    """Return per-character brace depth list for *clean* (comment-free) source."""
    depth = 0
    depths = []
    for ch in clean:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        depths.append(depth)
    return depths


# ---------------------------------------------------------------------------
# Line-number mapping
# ---------------------------------------------------------------------------

def build_line_map(source: str) -> list:
    offsets = [0]
    for m in re.finditer(r"\n", source):
        offsets.append(m.end())
    return offsets


def offset_to_line_col(offsets: list, pos: int):
    lo, hi = 0, len(offsets) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if offsets[mid] <= pos:
            lo = mid
        else:
            hi = mid - 1
    return lo + 1, pos - offsets[lo] + 1
