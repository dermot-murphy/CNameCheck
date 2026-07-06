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


_RE_SUPPRESS = re.compile(
    r"(?://|/\*)\s*cstylecheck\s*:\s*"
    r"(disable-next-line|disable|enable)"
    r"(?:=([^\n*/]+))?",
    re.IGNORECASE,
)


def parse_inline_suppressions(source: str) -> dict:
    """Parse inline suppression comments and return {1-based-line → frozenset(rule_ids)}.

    Supported syntax:
      // cstylecheck: disable=rule.id, rule.id2   → suppress those rules on this line
      // cstylecheck: disable                      → suppress all rules on this line
      // cstylecheck: disable-next-line=rule.id   → suppress rule on the next line
      // cstylecheck: disable-next-line            → suppress all rules on next line
      // cstylecheck: disable=rule.id              → begin block suppression (until enable)
      // cstylecheck: enable=rule.id               → end block suppression for that rule

    Block disable/enable pairs work per rule ID; "disable" (no rule list) opens an
    all-rules block that "enable" (no rule list) closes.
    """
    lines = source.splitlines()
    suppressed: dict = {}   # line → set[str]; "*" means "all rules"

    # block_rules: rule_id → set of lines added so far (we update as we scan)
    # Simpler to track active-block rules as a running set then stamp each line.
    active_block: set = set()   # rule IDs currently in a block-disable; "*" for all

    def _add(lineno: int, rules) -> None:
        if lineno < 1:
            return
        s = suppressed.setdefault(lineno, set())
        if "*" in rules:
            s.add("*")
        else:
            s.update(rules)

    def _parse_rules(rule_text) -> frozenset:
        if not rule_text or not rule_text.strip():
            return frozenset({"*"})
        return frozenset(r.strip() for r in rule_text.split(",") if r.strip())

    for lineno, line in enumerate(lines, 1):
        m = _RE_SUPPRESS.search(line)
        if not m:
            # Still apply any active block suppressions to this line
            if active_block:
                _add(lineno, active_block)
            continue

        directive = m.group(1).lower().replace("-", "_")   # disable_next_line | disable | enable
        rules = _parse_rules(m.group(2))

        if directive == "disable_next_line":
            _add(lineno + 1, rules)
            # Also carry through any active block suppressions on THIS line
            if active_block:
                _add(lineno, active_block)

        elif directive == "disable":
            # Check whether this is a standalone line suppression or a block opener.
            # Heuristic: if the non-comment portion of the line has code, it's a
            # same-line suppression; otherwise it opens a block.
            non_comment = line[:m.start()].strip()
            if non_comment:
                # Same-line: suppress the code on this line
                _add(lineno, rules)
                if active_block:
                    _add(lineno, active_block)
            else:
                # Block opener: suppress from the NEXT line until enable
                active_block.update(rules)
                # Don't suppress the directive line itself

        elif directive == "enable":
            if "*" in rules:
                active_block.clear()
            else:
                active_block.difference_update(rules)
            # Don't suppress the enable line itself

        else:
            if active_block:
                _add(lineno, active_block)

    return {ln: frozenset(s) for ln, s in suppressed.items()}


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
            depths.append(depth)
        elif ch == "}":
            depths.append(depth)
            depth = max(0, depth - 1)
        else:
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
