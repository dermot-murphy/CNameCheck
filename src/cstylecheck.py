#!/usr/bin/env python3
"""
cstylecheck.py
====================
Embedded C Style Compliance Checker for GitHub Actions / pre-commit hooks.

Usage
-----
  python cstylecheck.py [OPTIONS] <file1.c> [file2.h ...]
  python cstylecheck.py --options-file cstylecheck.options [overrides ...]
  python cstylecheck.py --version
  python cstylecheck.py --help

  Key options (see --help for the full list):
    --config PATH          YAML config file (default: cstylecheck_rules.yaml)
    --options-file FILE    Read options from FILE (one per line, # = comment)
    --defines FILE         Project macro/type substitution file
    --aliases FILE         Module alias prefix file
    --cstylecheck_exclusions FILE      Per-file rule exclusion YAML
    --include GLOB         Glob pattern to scan (repeatable)
    --exclude GLOB         Glob pattern to exclude (repeatable)
    --output-format FORMAT Output format: text (default), json, or sarif
    --baseline-file FILE   Suppress violations present in a saved baseline
    --write-baseline FILE  Write all current violations to FILE, exit 0
    --github-actions       Emit GitHub Actions ::error/::warning annotations
    --warnings-as-errors   Promote all warnings and info to errors
    --summary              Print violation summary table (text mode only)
    --log FILE             Write all output to FILE as well as stdout
    --version              Print tool name and version then exit 0
    --help                 Print this help text then exit 0

Exit codes
----------
  0  Clean (or --version / --help / --write-baseline)
  1  One or more errors found (or warnings promoted by --warnings-as-errors)
  2  Configuration / invocation error

Checks performed (driven by cstylecheck_rules.yaml)
----------------------------------------------------
  Variables
    - Scope-aware: global (g_ prefix), file-static (s_ prefix), local,
      parameter — each with independent case and module-prefix rules.
    - Pointer variables:  single *  → local part must start with p_
    - Double pointers:    **        → local part must start with pp_
    - Boolean variables:  bool/_Bool → local part must start with b_
    - Handle variables:   configured types → local part must start with h_
    - Prefix ordering:    [g_][p_|pp_][b_|h_] when multiple prefixes apply
    - No embedded numbers in variable names (configurable, default off)
    - Min-length and max-length enforcement (YAML configurable).

  Functions
    - Module prefix required on all public definitions.
    - Body style: object_verb (e.g. uart_BufferRead), configurable to
      verb_object or lower_snake; single-word verb also accepted.
    - Static functions may require a configured prefix (e.g. prv_) via
      functions.static_prefix when enabled.
    - Allowed abbreviations and object-exclusion lists in YAML.
    - Min-length and max-length enforcement (YAML configurable).

  Constants and macros
    - UPPER_SNAKE_CASE required; configurable exempt_patterns for RTOS
      names, leading-__ compiler macros, etc.
    - Module prefix required.
    - Min-length and max-length enforcement.

  Types
    - Enum type: lower_snake + _t suffix.
    - Enum members: UPPER_SNAKE, prefixed with the type name (minus suffix),
      converted to member case.
    - Typedef: UPPER_SNAKE + _T suffix.  Multi-token base types (e.g.
      typedef unsigned int UINT_T) are correctly detected.
    - Struct tag: lower_snake + _s suffix; members lower_snake.

  Include guards
    - Pattern {FILENAME_UPPER}_{EXT_UPPER}_ or #pragma once accepted.

  Yoda conditions (BARR-C)
    - In == and != comparisons the constant must be on the left:
      if (NULL == p_buf) is correct; if (p_buf == NULL) is a violation.

  Reserved names (BARR-C 6.1.a / 7.1.a-b)
    - No identifier may shadow a C/C++ keyword or C standard library name.
    - Extended via --banned-names FILE for project-specific banned names.
    - Per-file exceptions via --cstylecheck_exclusions (disable rule 'reserved_name').

  Miscellaneous
    - Magic numbers flagged; #define RHS, array indices, return values exempt.
    - Unsigned literal suffix (U/u) required on numeric constants.
    - Line length and indentation style checked on non-comment lines.
    - Comment spell-check (opt-in, disabled by default).

  Cross-file sign compatibility
    - Unsigned literals (e.g. 100U) passed to signed-typed parameters,
      and signed literals passed to unsigned parameters, are flagged.
    - typedef chains resolved (typedef signed char int8_t → signed).
    - plain_char_is_signed option controls char treatment (default: signed).
"""

from __future__ import annotations

import argparse
import fnmatch
import glob as glob_mod
import os
import re
import shlex
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, List

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------
# The authoritative version string lives in _version.py, which is generated
# by the build/CI system using:
#
#   git describe --tags --dirty --always > _version.txt
#   python -c "
#   import pathlib
#   v = pathlib.Path('_version.txt').read_text().strip()
#   pathlib.Path('_version.py').write_text(f'__version__ = {v!r}\n')
#   "
#
# If _version.py is absent (e.g. during development without a git tag) the
# fallback string "1.0.0.dev" is used instead.
_TOOL_NAME = "CStyleCheck"

try:
    from _version import __version__ as _VERSION
except ImportError:
    _VERSION = "1.0.0.dev"

_VERSION_STRING = f"{_TOOL_NAME} {_VERSION}"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Violation:
    filepath: str
    line: int
    col: int
    severity: str          # error | warning | info
    rule: str
    message: str

    def github_annotation(self) -> str:
        level = self.severity if self.severity in ("error", "warning", "notice") else "notice"
        return (
            f"::{level} file={self.filepath},line={self.line},"
            f"col={self.col},title=NamingConvention[{self.rule}]::"
            f"{self.message}"
        )

    def __str__(self) -> str:
        return (
            f"{self.filepath}:{self.line}:{self.col}: "
            f"{self.severity.upper()} [{self.rule}] {self.message}"
        )


@dataclass
class CheckResult:
    violations: List[Violation] = field(default_factory=list)

    def add(self, v: Violation) -> None:
        self.violations.append(v)

    def has_errors(self) -> bool:
        return any(v.severity == "error" for v in self.violations)


# ---------------------------------------------------------------------------
# Options file expansion  (--options-file)
# ---------------------------------------------------------------------------

def _read_options_file(path: str) -> list:
    """
    Read an options file and return a flat list of CLI tokens.

    Format rules:
      - One option (or option + value) per line.
      - Blank lines and lines starting with # are ignored.
      - Shell quoting rules apply (via shlex), so paths containing spaces
        must be quoted:  --log "output path/results.txt"
      - Options that take a value may be on the same line:
            --config tools/cstylecheck/cstylecheck_rules.yaml
        or split with an = sign (standard CLI syntax):
            --config=tools/cstylecheck/cstylecheck_rules.yaml
    """
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        sys.exit(f"Cannot read options file '{path}': {e}")
    tokens: list = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            tokens.extend(shlex.split(line))
        except ValueError as e:
            print(f"WARNING: options file '{path}' line {lineno}: {e}",
                  file=sys.stderr)
    return tokens


def _expand_options_file(argv: list) -> list:
    """
    Scan *argv* for --options-file PATH tokens and expand them in-place.

    Tokens from the file are inserted at the position of the flag so that
    any arguments that appear AFTER the flag on the real command line
    override file defaults when argparse uses last-wins semantics.

    Multiple --options-file flags are processed left-to-right.  The flag
    and its path argument are consumed and do not appear in the result.
    """
    result: list = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--options-file":
            i += 1
            if i >= len(argv):
                sys.exit("ERROR: --options-file requires a path argument")
            result.extend(_read_options_file(argv[i]))
        elif arg.startswith("--options-file="):
            result.extend(_read_options_file(arg[len("--options-file="):]))
        else:
            result.append(arg)
        i += 1
    return result


# ---------------------------------------------------------------------------
# Configuration loader
# ---------------------------------------------------------------------------

def load_config(path: str) -> dict:
    cfg_path = Path(path)
    if not cfg_path.exists():
        sys.exit(f"Config file not found: {path}")
    with cfg_path.open() as fh:
        return yaml.safe_load(fh)


def load_spell_words(path: str) -> set:
    """Load a plain-text file of exempt spell-check words (one per line)."""
    result: set = set()
    try:
        for raw in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
            word = raw.strip()
            if word and not word.startswith("#"):
                result.add(word.lower())
    except OSError as e:
        sys.exit(f"Cannot read spell-words file '{path}': {e}")
    return result


# ---------------------------------------------------------------------------
# Alias file loader  (--aliases)
# ---------------------------------------------------------------------------

def load_alias_file(path: str) -> dict:
    """
    Load the module-alias plain-text file.

    Each non-blank, non-comment line must contain exactly two whitespace-
    separated words::

        alias_stem   actual_module_stem

    Returns dict: {actual_module_stem_lower -> [alias_stem_lower, ...]}.

    Example line::
        api_param  api_param_cfg

    → when checking api_param_cfg.c the prefix api_param_ is also accepted.
    """
    aliases: dict = {}
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        sys.exit(f"Cannot read alias file '{path}': {e}")
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            print(f"WARNING: alias file line {lineno}: expected 2 words, "
                  f"got {parts!r}", file=sys.stderr)
            continue
        alias_stem, actual_stem = parts[0].lower(), parts[1].lower()
        aliases.setdefault(actual_stem, []).append(alias_stem)
    return aliases


# ---------------------------------------------------------------------------
# Per-file rule cstylecheck_exclusions loader  (--cstylecheck_exclusions)
# ---------------------------------------------------------------------------

def load_cstylecheck_exclusions_file(path: str) -> dict:
    """
    Load the per-file rule exclusion YAML.

    Each top-level key is a :func:`fnmatch` pattern matched against the
    **basename** of the file being checked.  Each value must have a
    ``disabled_rules`` list of rule IDs (strings exactly as they appear in
    violation messages, e.g. ``function.prefix``).

    Returns dict: {basename_glob -> frozenset_of_disabled_rule_ids}.

    Example YAML::

        "ascii.*":
          disabled_rules:
            - function.prefix
            - function.style

        "util_string.c":
          disabled_rules:
            - variable.global.prefix
    """
    try:
        data = yaml.safe_load(
            Path(path).read_text(encoding="utf-8", errors="replace"))
    except OSError as e:
        sys.exit(f"Cannot read cstylecheck_exclusions file '{path}': {e}")
    if not isinstance(data, dict):
        return {}
    result: dict = {}
    for pattern, body in data.items():
        if not isinstance(body, dict):
            continue
        rules = body.get("disabled_rules", [])
        file_rules = frozenset(str(r) for r in rules) if isinstance(rules, list) else frozenset()
        # Per-identifier cstylecheck_exclusions
        ident_rules: dict = {}
        for ident, ibody in (body.get("identifiers") or {}).items():
            if isinstance(ibody, dict):
                irules = ibody.get("disabled_rules", [])
                if isinstance(irules, list):
                    ident_rules[str(ident)] = frozenset(str(r) for r in irules)
        result[str(pattern)] = {
            "file_rules":  file_rules,
            "ident_rules": ident_rules,
        }
    return result


def _disabled_rules_for_file(filepath: str, cstylecheck_exclusions: dict) -> tuple:
    """
    Return (file_disabled, ident_disabled) where:
      file_disabled  frozenset of rule IDs disabled for the whole file.
      ident_disabled dict {identifier -> frozenset of rule IDs}.
    """
    basename = Path(filepath).name
    file_disabled: set = set()
    ident_disabled: dict = {}
    for pattern, body in cstylecheck_exclusions.items():
        if not fnmatch.fnmatch(basename, pattern):
            continue
        if isinstance(body, frozenset):
            file_disabled |= body
        elif isinstance(body, dict):
            file_disabled |= body.get("file_rules", frozenset())
            for ident, rules in body.get("ident_rules", {}).items():
                ident_disabled.setdefault(ident, set())
                ident_disabled[ident] |= rules
    return (
        frozenset(file_disabled),
        {k: frozenset(v) for k, v in ident_disabled.items()},
    )


# ---------------------------------------------------------------------------
# Defines file loader  (--defines)
# ---------------------------------------------------------------------------

def load_defines_file(path: str) -> list:
    """
    Load a project defines plain-text file.

    Each non-blank, non-comment line must contain a token followed by its
    expansion (separated by one or more spaces)::

        STATIC          static
        CONST           const
        uint8_t         unsigned char
        LOCAL_INLINE    static inline

    Returns a list of ``(compiled_pattern, replacement_str)`` tuples in
    file order.  Substitution is whole-word (\\b boundaries) so that a
    shorter token such as ``CONST`` does not corrupt ``CONSTANT``.

    Multi-word expansions are supported:  ``uint8_t  unsigned char``
    expands every bare ``uint8_t`` token to two tokens.

    The file is processed by :func:`apply_defines` on the comment- and
    string-stripped source (``self.clean``) so that tokens appearing inside
    comments or string literals are never substituted.
    """
    result: list = []
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        sys.exit(f"Cannot read defines file '{path}': {e}")
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)   # split on first whitespace run only
        if len(parts) < 2:
            print(f"WARNING: defines file '{path}' line {lineno}: "
                  f"expected 'TOKEN expansion', got {parts!r}",
                  file=sys.stderr)
            continue
        token, expansion = parts[0], parts[1].strip()
        try:
            pattern = re.compile(r'\b' + re.escape(token) + r'\b')
        except re.error as e:
            print(f"WARNING: defines file '{path}' line {lineno}: "
                  f"bad token {token!r}: {e}", file=sys.stderr)
            continue
        result.append((pattern, expansion))
    return result


def apply_defines(text: str, defines: list) -> str:
    """
    Apply each ``(pattern, replacement)`` pair from *defines* to *text*
    using whole-word substitution, returning the result.

    Call this on the preprocessed (comment/string-stripped) source so that
    comment content is never accidentally substituted.
    """
    for pattern, replacement in defines:
        text = pattern.sub(replacement, text)
    return text


# ---------------------------------------------------------------------------
# Reserved / banned name sets  (BARR-C 6.1.a, 7.1.a, 7.1.b)
# ---------------------------------------------------------------------------

def _load_dict_file(path: str) -> frozenset:
    """Load a plain-text dictionary file (one token per line, # = comment)."""
    tokens = set()
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    tokens.add(line)
    except FileNotFoundError:
        pass  # missing dict files are silently ignored
    return frozenset(tokens)


# Default dictionary file paths (resolved relative to this script).
# Override any of these with the corresponding CLI flag.
_HERE = Path(__file__).resolve().parent


def _data_file(name: str) -> Path:
    """
    Resolve the path to a bundled data file.

    Lookup order
    ------------
    1. Alongside ``__file__`` (source checkout, editable install, pre-commit
       clone).  This is the common case for development and CI.
    2. ``{data_dir}/share/cstylecheck/`` — the location used when the package
       is installed with ``pip install .`` via the ``data_files`` entry in
       ``pyproject.toml``.  ``data_dir`` is resolved via
       ``sysconfig.get_path("data")`` so that the lookup is correct for venvs,
       conda environments, system installs, and user installs alike.

    ``_load_dict_file`` handles ``FileNotFoundError`` gracefully (returns an
    empty frozenset), so callers are always safe even if neither path exists.
    """
    candidate = _HERE / name
    if candidate.exists():
        return candidate
    import sysconfig as _sysconfig
    return Path(_sysconfig.get_path("data")) / "share" / "cstylecheck" / name

_DEFAULT_KEYWORDS_FILE  = _data_file("c_keywords.txt")
_DEFAULT_STDLIB_FILE    = _data_file("c_stdlib_names.txt")
_DEFAULT_SPELL_DICT     = _data_file("c_spell_dict.txt")

C_KEYWORDS:    frozenset = _load_dict_file(_DEFAULT_KEYWORDS_FILE)
C_STDLIB_NAMES: frozenset = _load_dict_file(_DEFAULT_STDLIB_FILE)



def load_banned_names_file(path: str) -> frozenset:
    """
    Load a plain-text file of additional banned identifier names.

    Format: one name per line.  Lines starting with # are comments.
    Names are case-sensitive (as C identifiers are).
    """
    result: set = set()
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        sys.exit(f"Cannot read banned-names file '{path}': {e}")
    for raw in text.splitlines():
        name = raw.strip()
        if name and not name.startswith("#"):
            result.add(name)
    return frozenset(result)


# ---------------------------------------------------------------------------
# Copyright header loader  (--copyright)
# ---------------------------------------------------------------------------

# Matches the year (or year range) that follows "(C) Copyright" on a
# copyright line, case-insensitive for the word "copyright".
# Handles:  2024  ·  2020-2024  ·  2020–2024 (en-dash U+2013)
_COPYRIGHT_YEAR_RE = re.compile(
    r'(\(C\)\s+copyright\s+)(\d{4}(?:[-\u2013]\d{4})?)',
    re.IGNORECASE,
)

# Matches any year or year-range in the source file's copyright line.
_COPYRIGHT_YEAR_FLEX = r'\d{4}(?:[-\u2013]\d{4})?'


def load_copyright_file(path: str) -> tuple:
    """
    Parse a copyright header template file and return
    ``(template_text, match_re)`` where:

    * ``template_text`` – the raw ``/* ... */`` block comment string exactly
      as it appears in *path* (CRLF normalised to LF).
    * ``match_re``      – a compiled regex anchored to ``\\A`` (start of
      file) that matches the header with a *flexible* year on the
      ``(C) Copyright`` line, so any 4-digit year or ``YYYY-YYYY`` range is
      accepted in the files being checked.

    The copyright file must contain at least one block comment
    (``/* ... */``).  The first such comment is used as the template.
    """
    try:
        raw = Path(path).read_text(encoding='utf-8', errors='replace')
    except OSError as e:
        sys.exit(f"Cannot read copyright file '{path}': {e}")

    text = raw.replace('\r\n', '\n').replace('\r', '\n')

    m = re.search(r'/\*.*?\*/', text, re.DOTALL)
    if not m:
        sys.exit(
            f"Copyright file '{path}' contains no block comment (/* ... */)."
        )

    template = m.group(0)
    lines    = template.split('\n')

    # Build a regex by escaping every line literally, then replacing the
    # year token on the (C) Copyright line with a flexible pattern.
    pattern_parts: list = []
    found_year = False
    for line in lines:
        ym = _COPYRIGHT_YEAR_RE.search(line)
        if ym and not found_year:
            found_year = True
            before = line[:ym.start(2)]
            after  = line[ym.end(2):]
            pattern_parts.append(
                re.escape(before) + _COPYRIGHT_YEAR_FLEX + re.escape(after)
            )
        else:
            pattern_parts.append(re.escape(line))

    pattern_str = '\n'.join(pattern_parts)
    compiled    = re.compile(r'\A' + pattern_str)

    if not found_year:
        print(
            f"WARNING: copyright file '{path}': no '(C) Copyright YEAR' "
            "line found — year will be matched literally.",
            file=sys.stderr,
        )

    return template, compiled


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

_CASE_PATTERNS = {
    "lower_snake": re.compile(r"^[a-z][a-z0-9_]*$"),
    "upper_snake": re.compile(r"^[A-Z][A-Z0-9_]*$"),
    "camel":       re.compile(r"^[a-z][a-zA-Z0-9]*$"),
    "pascal":      re.compile(r"^[A-Z][a-zA-Z0-9]*$"),
    "lower":       re.compile(r"^[a-z][a-z0-9_]*$"),
    "upper":       re.compile(r"^[A-Z][A-Z0-9_]*$"),
}


def matches_case(name: str, style: str) -> bool:
    pat = _CASE_PATTERNS.get(style)
    return pat.match(name) is not None if pat else True


def matches_case_abbrev(name: str, style: str, abbrevs: set) -> bool:
    """
    Like matches_case() but for lower_snake / lower styles, each
    underscore-delimited segment is also accepted if it appears (in any
    case) in *abbrevs* (the set of allowed uppercase abbreviations).

    Example:  read_FIFO_registers  passes lower_snake when FIFO is in abbrevs.
    For all other styles the function behaves identically to matches_case().
    """
    if style not in ("lower_snake", "lower") or not abbrevs:
        return matches_case(name, style)
    segments = name.split("_")
    for seg in segments:
        if not seg:
            continue
        if seg.upper() in abbrevs:
            continue   # allowed abbreviation — any capitalisation
        if not re.match(r"^[a-z][a-z0-9]*$", seg):
            return False
    return True


def to_case(name: str, style: str) -> str:
    """Convert *name* to *style* — used to derive enum member prefixes."""
    if style in ("upper_snake", "upper"):
        return name.upper()
    if style in ("lower_snake", "lower", "camel"):
        return name.lower()
    return name    # pascal / as_is — unchanged


def module_name(filepath: str) -> str:
    return Path(filepath).stem.lower()


def is_exempt(name: str, patterns: list) -> bool:
    for p in patterns:
        try:
            if re.match(p, name):
                return True
        except re.error:
            pass
    return False


def _cfg(cfg: dict, *keys, default=None):
    node = cfg
    for k in keys:
        if not isinstance(node, dict):
            return default
        node = node.get(k, default)
        if node is None:
            return default
    return node


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
    return re.sub(
        r'"(?:[^"\\]|\\.)*"',
        lambda m: '""' + " " * (len(m.group()) - 2),
        source,
    )


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
# Regex patterns
# ---------------------------------------------------------------------------

RE_DEFINE = re.compile(
    r"^\s*#\s*define\s+([A-Za-z_]\w*)(\()?",
    re.MULTILINE,
)

RE_TYPEDEF_ENUM = re.compile(
    r"typedef\s+enum\s*\w*\s*\{([^}]*)\}\s*([A-Za-z_]\w*)\s*;",
    re.DOTALL,
)

RE_TYPEDEF_STRUCT = re.compile(
    r"typedef\s+struct\s*([A-Za-z_]\w*)?\s*\{([^}]*)\}\s*([A-Za-z_]\w*)\s*;",
    re.DOTALL,
)

RE_TYPEDEF_SIMPLE = re.compile(
    # Each word in the base type is followed by whitespace, so the last word
    # (the typedef name itself, followed by ';') is never consumed by the base
    # type group — avoiding the backtracking bug where 'INT32_' was matched as
    # the base type and 'T' captured as the name.
    r"typedef\s+"
    r"(?:(?:struct|union|enum)\s+\w+\s+|(?:\w+\s+)+)"  # base: each word has trailing space
    r"\*?\s*"                                             # optional pointer
    r"([A-Za-z_]\w*)\s*;",                               # typedef name
)

# Control-flow keywords that must never be mistaken for a return type.
_CFKW = (
    r"if|else|while|for|do|switch|case|return|goto|break|continue"
    r"|sizeof|typeof|__typeof__|__attribute__|defined|assert"
)

RE_FUNCTION_DEF = re.compile(
    # Safe against catastrophic backtracking: no [\w\s]+ constructs.
    # [^;{}] matches newlines so multiline parameter lists work correctly.
    # (?!_CFKW\b) prevents matching "if (...) {" as a function definition.
    r"(?:^|\n)[ \t]*"
    r"(?:(?:static|inline|extern|STATIC|INLINE|EXTERN|LOCAL_INLINE)[ \t]+)*"
    r"(?:(?:const|volatile|CONST)[ \t]+)?"
    r"(?:(?:unsigned|signed)[ \t]+)?"
    r"(?:(?:long[ \t]+long|long|short)[ \t]+)?"
    r"(?!(?:" + _CFKW + r")\b)"         # return type must NOT be a keyword
    r"\w+"                              # return type (one token)
    r"[ \t]*\*?[ \t]*"
    r"([A-Za-z_]\w*)"                  # FUNCTION NAME — group 1
    r"[ \t]*\([^;{}]*\)"              # param list — [^;{}] matches newlines
    r"[ \t\n]*\{",                    # allow newline before opening brace
    re.MULTILINE,
)

# RE_FUNCTION_DECL: matches function *prototypes* (ending with ;).
# Used to collect sig_ranges for multiline parameter lists in headers.
RE_FUNCTION_DECL = re.compile(
    r"(?:^|\n)[ \t]*"
    r"(?:(?:static|inline|extern|STATIC|INLINE|EXTERN|LOCAL_INLINE)[ \t]+)*"
    r"(?:(?:const|volatile|CONST)[ \t]+)?"
    r"(?:(?:unsigned|signed)[ \t]+)?"
    r"(?:(?:long[ \t]+long|long|short)[ \t]+)?"
    r"(?!(?:" + _CFKW + r")\b)"
    r"\w+"                              # return type
    r"[ \t]*\*?[ \t]*"
    r"([A-Za-z_]\w*)"                  # FUNCTION NAME — group 1
    r"[ \t]*\([^;{}]*\)"              # param list — [^;{}] matches newlines
    r"[ \t\n]*;",                     # ends with semicolon (declaration)
    re.MULTILINE,
)

# group 1 = qualifier string (may contain "static")
# group 2 = type token (e.g. bool, uint8_t, MY_TYPE_T)
# group 3 = pointer stars (empty, "*", or "**")
# group 4 = variable name
RE_VAR_DECL = re.compile(
    r"(?:^|[;{}\n])[ \t]*"
    r"((?:(?:static|extern|volatile|const)[ \t]+)*)"   # group 1: qualifiers
    r"(?:(?:unsigned|signed)[ \t]+)?"
    r"(?:(?:long[ \t]+long|long|short)[ \t]+)?"
    r"(int|char|float|double|uint\w+|int\w+|bool|_Bool|size_t"
    r"|[A-Z_]\w+_[Tt])[ \t]*"                        # group 2: type token
    r"(\*{0,2})[ \t]*"                                 # group 3: pointer stars
    r"([a-z_]\w*)"                                      # group 4: variable name
    r"[ \t]*(?:=|;|\[|,)",
    re.MULTILINE,
)

# Match one parameter: type tokens  *?  name  followed by , or ) or [
RE_FUNCTION_PARAM = re.compile(
    r"(?:(?:const|volatile|unsigned|signed|long|short|int|char|float|double"
    r"|uint\w+|int\w+|bool|_Bool|size_t|[A-Z_]\w+_[Tt])[ \t]+)+"
    r"\*?[ \t]*([a-z_]\w*)[ \t]*(?:,|\)|\[)",
)

RE_INCLUDE_GUARD_IFNDEF = re.compile(r"^\s*#\s*ifndef\s+([A-Za-z_]\w*)", re.MULTILINE)
RE_INCLUDE_GUARD_DEFINE = re.compile(r"^\s*#\s*define\s+([A-Za-z_]\w*)\s*$", re.MULTILINE)
RE_PRAGMA_ONCE          = re.compile(r"^\s*#\s*pragma\s+once", re.MULTILINE)

RE_MAGIC_NUMBER = re.compile(r"(?<![.\w])(\d{2,})(?![.\w])")
RE_ARRAY_INDEX  = re.compile(r"\[\s*\d+\s*\]")   # matches  [2]  or  [ 10 ]

RE_ENUM_MEMBER  = re.compile(r"\b([A-Za-z_]\w*)\s*(?:=|,|\})")

RE_COMMENT_WORD = re.compile(r"[A-Za-z][A-Za-z']{2,}")


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


# ---------------------------------------------------------------------------
# Built-in spell-check word list
# ---------------------------------------------------------------------------

_BUILTIN_DICT: frozenset = _load_dict_file(_DEFAULT_SPELL_DICT)


def _build_spell_dict(cfg_exempt: list, extra_words: set,
                       base_dict=None) -> set:
    combined = set(base_dict if base_dict is not None else _BUILTIN_DICT)
    combined.update(w.lower() for w in cfg_exempt)
    combined.update(w.lower() for w in extra_words)
    return combined


# ---------------------------------------------------------------------------
# Checker class
# ---------------------------------------------------------------------------


class Checker:
    def __init__(
        self,
        filepath: str,
        source: str,
        cfg: dict,
        spell_words=None,
        alias_prefixes: list = None,
        disabled_rules: frozenset = None,
        ident_disabled_rules: dict = None,
        defines: list = None,
        extra_banned: frozenset = None,
        copyright_header=None,
    ):
        self.filepath      = filepath
        self.source        = source
        # Step 1: strip comments and string literals
        self.clean         = preprocess(source)
        # Track positions of "}" that close a typedef struct/union/enum
        # body so _check_variables can exclude them from RE_VAR_DECL.
        _RE_TYPEDEF_CLOSE = re.compile(
            r"\btypedef\b[^{]*\{[^}]*\}\s*\w+\s*;",
            re.DOTALL,
        )
        self._typedef_close_positions: set = set()
        for _tc in _RE_TYPEDEF_CLOSE.finditer(self.clean):
            # Mark the "}" position so RE_VAR_DECL hits after it are skipped
            _close_brace = self.clean.rfind("}", _tc.start(), _tc.end())
            if _close_brace >= 0:
                self._typedef_close_positions.add(_close_brace)
        # Step 2: substitute project-defined keyword/type aliases so that
        # all subsequent regexes see only canonical C keywords and types.
        # e.g. STATIC→static, uint8_t→unsigned char
        if defines:
            self.clean     = apply_defines(self.clean, defines)
        self.cfg           = cfg
        self.module        = module_name(filepath)
        self.result        = CheckResult()
        self._line_map     = build_line_map(source)
        self._is_header    = filepath.endswith(".h")
        self._comment_only = _comment_only_lines(source)
        self._brace_depths = _build_brace_depths(self.clean)
        self._spell_dict   = spell_words   # set or None
        # List of accepted prefix strings for this file (canonical + aliases).
        # e.g. ["api_param_cfg_", "api_param_"]
        self._alias_prefixes: list = alias_prefixes or []
        # Set of rule IDs that are suppressed for this file.
        self._disabled_rules: frozenset = disabled_rules or frozenset()
        self._ident_disabled: dict = ident_disabled_rules or {}
        # Extra banned identifier names (from --banned-names file + builtins)
        self._extra_banned: frozenset = extra_banned or frozenset()
        # tuple (template_text, compiled_re) from --copyright, or None
        self._copyright = copyright_header

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _violation(self, pos: int, sev: str, rule: str, msg: str) -> Violation:
        line, col = offset_to_line_col(self._line_map, pos)
        return Violation(self.filepath, line, col, sev, rule, msg)

    def _v(self, pos: int, sev: str, rule: str, msg: str) -> None:
        if self._ident_disabled:
            import re as _re
            _m = _re.search(r"'([^']+)'", msg)
            if _m and rule in self._ident_disabled.get(_m.group(1), frozenset()):
                return
        self.result.add(self._violation(pos, sev, rule, msg))

    def _prefix(self) -> str:
        sep  = _cfg(self.cfg, "file_prefix", "separator", default="_")
        case = _cfg(self.cfg, "file_prefix", "case", default="lower")
        pfx  = self.module.upper() if case == "upper" else self.module
        return pfx + sep

    def _require_module_prefix(self, name: str, pos: int, rule: str) -> None:
        """Emit a violation if *name* does not carry the module prefix or any alias prefix."""
        if not _cfg(self.cfg, "file_prefix", "enabled", default=True):
            return
        sev         = _cfg(self.cfg, "file_prefix", "severity", default="error")
        exempt_main = _cfg(self.cfg, "file_prefix", "exempt_main", default=True)
        exempt_pats = _cfg(self.cfg, "file_prefix", "exempt_patterns", default=[])

        if exempt_main and self.module == "main":
            return
        if is_exempt(name, exempt_pats):
            return

        # Build the full list of accepted prefixes: canonical + any aliases
        sep = _cfg(self.cfg, "file_prefix", "separator", default="_")
        accepted = list(self._alias_prefixes)  # already includes canonical
        if not accepted:
            accepted = [self._prefix()]

        name_lower = name.lower()
        if any(name_lower.startswith(p.lower()) for p in accepted):
            return   # at least one prefix matched

        # Report using the canonical prefix in the message
        pfx = accepted[0]
        alias_hint = (
            f" (or alias prefix(es): "
            + ", ".join(f"'{a}'" for a in accepted[1:])
            + ")"
            if len(accepted) > 1 else ""
        )
        self._v(pos, sev, rule,
                f"'{name}' must be prefixed with '{pfx}'{alias_hint} (module prefix)")

    def _depth_at(self, pos: int) -> int:
        if pos <= 0:
            return 0
        return self._brace_depths[min(pos, len(self._brace_depths) - 1)]

    def _strip_any_prefix(self, name: str) -> str:
        """Strip the longest matching module prefix (canonical or alias) from *name*."""
        name_lower = name.lower()
        best = name   # fallback: return name unchanged
        for pfx in self._alias_prefixes:
            if name_lower.startswith(pfx.lower()):
                remainder = name[len(pfx):]
                if len(remainder) < len(best):
                    best = remainder
        # If no alias prefix matched, try the canonical prefix
        if best is name:
            best = _strip_module_prefix(name, self._prefix())
        return best

    # -----------------------------------------------------------------------
    # Public entry point
    # -----------------------------------------------------------------------

    def run_all(self) -> CheckResult:
        self._check_copyright_header()
        self._check_defines()
        self._check_variables()
        self._check_functions()
        self._check_typedefs()
        self._check_enums()
        self._check_structs()
        if self._is_header:
            self._check_include_guard()
        self._check_misc()
        self._check_yoda()
        self._check_reserved_names()
        if self._spell_dict is not None:
            self._check_spelling()
        # Remove violations for rules that are disabled for this file
        if self._disabled_rules:
            self.result.violations = [
                v for v in self.result.violations
                if v.rule not in self._disabled_rules
            ]
        return self.result

    # -----------------------------------------------------------------------
    # 1. Constants and macros (#define)
    # -----------------------------------------------------------------------

    def _check_defines(self) -> None:
        macro_cfg = self.cfg.get("macros", {})
        const_cfg = self.cfg.get("constants", {})

        for m in RE_DEFINE.finditer(self.clean):
            name      = m.group(1)
            is_fn     = m.group(2) == "("

            # Bare guard define: #define FOO  with nothing after on the line
            rest = self.clean[m.end():].split("\n")[0].strip()
            if not rest:
                continue

            cfg_node   = macro_cfg if is_fn else const_cfg
            if not cfg_node.get("enabled", True):
                continue

            sev           = cfg_node.get("severity", "error")
            expected_case = cfg_node.get("case", "upper_snake")
            exempt_pats   = cfg_node.get("exempt_patterns", [])
            label         = "Macro" if is_fn else "Constant"
            rule_pfx      = "macro" if is_fn else "constant"

            if is_exempt(name, exempt_pats):
                continue

            if not matches_case(name, expected_case):
                self._v(m.start(), sev, f"{rule_pfx}.case",
                        f"{label} '{name}' must be {expected_case}")

            max_len = cfg_node.get("max_length")
            if max_len and len(name) > max_len:
                self._v(m.start(), sev, f"{rule_pfx}.max_length",
                        f"{label} '{name}' length {len(name)} exceeds "
                        f"maximum {max_len} characters")

            min_len = cfg_node.get("min_length")
            if min_len and len(name) < min_len:
                self._v(m.start(), sev, f"{rule_pfx}.min_length",
                        f"{label} '{name}' length {len(name)} is below "
                        f"minimum {min_len} characters")

            self._require_module_prefix(name, m.start(), f"{rule_pfx}.prefix")

    # -----------------------------------------------------------------------
    # 2. Variable declarations — scope-aware
    # -----------------------------------------------------------------------

    def _check_variables(self) -> None:
        """
        Classify every variable declaration by scope and apply per-scope rules.

        Scope classification (from brace depth + qualifiers):
          global    depth == 0, no 'static'  -> module prefix + g_ required
          static    depth == 0, has 'static' -> module prefix + s_ required
          local     depth >  0, not a param  -> case check only
          parameter appears in a fn signature -> case check only

        Parameters are identified by scanning function signatures before the
        main declaration loop so we can distinguish them from locals.
        """
        var_cfg = self.cfg.get("variables", {})
        if not var_cfg.get("enabled", True):
            return

        # Per-scope configuration sub-nodes
        sc_global = var_cfg.get("global",    {})
        sc_static = var_cfg.get("static",    {})
        sc_local  = var_cfg.get("local",     {})
        sc_param  = var_cfg.get("parameter", {})

        # Collect parameter names AND the character positions of every
        # function signature (from '(' up to the opening '{').
        # A VAR_DECL match inside a signature range is always a parameter,
        # regardless of brace depth — this handles multiline param lists
        # where the parameters appear before the first '{' and therefore
        # have brace_depth == 0.
        param_names: set = set()
        sig_ranges:  list = []   # list of (start, end) char ranges

        # RE for a parameter with explicit star(s) captured
        _RE_PARAM_STARS = re.compile(
            r"(?:(?:const|volatile|unsigned|signed|long|short|int|char|float|double"
            r"|uint\w+|int\w+|bool|_Bool|size_t|[A-Z_]\w+_[Tt])[ \t]+)+"
            r"(\*{1,2})[ \t]*"      # group 1: star(s)
            r"([a-z_]\w*)"           # group 2: name
            r"[ \t]*(?:,|\)|\[)",
        )
        # RE for a single-token typed parameter (for handle and bool checks)
        _RE_PARAM_TYPED = re.compile(
            r"(?:^|,|\()[ \t]*"
            r"(?:(?:const|volatile)[ \t]+)?"
            r"([A-Za-z_]\w*)[ \t]+"   # group 1: type token
            r"(\*{0,2})[ \t]*"          # group 2: optional stars
            r"([a-z_]\w*)"              # group 3: name
            r"[ \t]*(?:,|\)|\[)",
        )
        _h_cfg_early    = var_cfg.get("handle_prefix", {})
        _h_types_early  = {t.strip() for t in _h_cfg_early.get("handle_types", [])}
        _h_pfx_early    = _h_cfg_early.get("prefix", "h_")
        _h_sev_early    = _h_cfg_early.get("severity", "warning")
        _h_en_early     = _h_cfg_early.get("enabled", True)
        _b_cfg_early    = var_cfg.get("bool_prefix", {})
        _b_pfx_early    = _b_cfg_early.get("prefix", "b_")
        _b_sev_early    = _b_cfg_early.get("severity", "warning")
        _b_en_early     = _b_cfg_early.get("enabled", True)
        # Parameter p_ prefix (variable.parameter.p_prefix rule)
        _pp_param_cfg   = var_cfg.get("parameter", {}).get("p_prefix", {})
        _pp_param_en    = _pp_param_cfg.get("enabled", False)
        _pp_param_pfx   = _pp_param_cfg.get("prefix", "p_")
        _pp_param_sev   = _pp_param_cfg.get("severity", "warning")

        def _collect_sig(fn_m, end_char):
            """Extract param names, ranges, and pointer-depth info."""
            paren_open = self.clean.find("(", fn_m.start())
            end_pos    = self.clean.find(end_char, fn_m.start())
            if paren_open != -1 and end_pos != -1 and paren_open < end_pos:
                sig_text = self.clean[paren_open:end_pos]
                sig_ranges.append((paren_open, end_pos))
                for pm in RE_FUNCTION_PARAM.finditer(sig_text):
                    p_name_raw = pm.group(1)
                    param_names.add(p_name_raw)
                    # variable.parameter.p_prefix: all params must start with p_
                    if _pp_param_en:
                        _stripped = self._strip_any_prefix(p_name_raw)
                        if not _stripped.startswith(_pp_param_pfx):
                            self._v(
                                paren_open + pm.start(),
                                _pp_param_sev,
                                "variable.parameter.p_prefix",
                                f"Parameter '{p_name_raw}' must start with "
                                f"'{_pp_param_pfx}' (parameter prefix)")
                # Additionally check pp_ / b_ prefix in params here
                # because RE_VAR_DECL doesn't cover signature positions.
                for pm in _RE_PARAM_STARS.finditer(sig_text):
                    p_stars = pm.group(1)
                    p_name  = pm.group(2)
                    p_local = self._strip_any_prefix(p_name)
                    abs_pos = paren_open + pm.start()
                    if p_stars == "**":
                        if pp_cfg_early.get("enabled", True):
                            pp_pfx = pp_cfg_early.get("prefix", "pp_")
                            pp_sev = pp_cfg_early.get("severity", "warning")
                            if not p_local.startswith(pp_pfx):
                                self._v(abs_pos, pp_sev,
                                        "variable.pp_prefix",
                                        f"Double-pointer parameter '{p_name}' "
                                        f"local part should start with '{pp_pfx}' "
                                        f"(BARR-C 7.1.l)")
                    elif p_stars == "*":
                        if ptr_cfg_early.get("enabled", True):
                            p_pfx = ptr_cfg_early.get("prefix", "p_")
                            p_sev = ptr_cfg_early.get("severity", "warning")
                            if not p_local.startswith(p_pfx):
                                self._v(abs_pos, p_sev,
                                        "variable.pointer_prefix",
                                        f"Pointer parameter '{p_name}' "
                                        f"local part should start with '{p_pfx}' "
                                        f"(BARR-C 7.1.k)")
                # Handle-type and bool parameters (via typed RE)
                for pm in _RE_PARAM_TYPED.finditer(sig_text):
                    p_type  = pm.group(1)
                    p_stars = pm.group(2)
                    p_name  = pm.group(3)
                    p_local = self._strip_any_prefix(p_name)
                    abs_pos = paren_open + pm.start()
                    if p_stars:   # pointer params already handled above
                        continue
                    if _h_en_early and _h_types_early and p_type in _h_types_early:
                        if not p_local.startswith(_h_pfx_early):
                            self._v(abs_pos, _h_sev_early,
                                    "variable.handle_prefix",
                                    f"Handle parameter '{p_name}' (type '{p_type}') "
                                    f"local part should start with '{_h_pfx_early}' "
                                    f"(BARR-C 7.1.n)")
                    if _b_en_early and p_type in ("bool", "_Bool"):
                        if not p_local.startswith(_b_pfx_early):
                            self._v(abs_pos, _b_sev_early,
                                    "variable.bool_prefix",
                                    f"Boolean parameter '{p_name}' "
                                    f"local part should start with '{_b_pfx_early}' "
                                    f"(BARR-C 7.1.m)")

        # Hoist ptr_cfg / pp_cfg lookups so _collect_sig can use them
        ptr_cfg_early = var_cfg.get("pointer_prefix", {})
        pp_cfg_early  = var_cfg.get("pp_prefix",      {})

        # Definitions (end with {) — covers .c file bodies
        for fn_m in RE_FUNCTION_DEF.finditer(self.clean):
            _collect_sig(fn_m, "{")
        # Declarations (end with ;) — covers .h prototypes with multiline params
        for fn_m in RE_FUNCTION_DECL.finditer(self.clean):
            _collect_sig(fn_m, ";")

        ptr_cfg  = var_cfg.get("pointer_prefix", {})
        min_len  = var_cfg.get("min_length", 2)
        allow_sc = var_cfg.get("allow_single_char_loop_vars", True)
        allow_loop_short = var_cfg.get("allow_loop_vars_short", False)

        # Collect names that appear only inside for/while loop initialisers.
        # These are typically i, ii, idx — short loop counters.
        loop_only_vars: set = set()
        if allow_loop_short:
            _RE_FOR_INIT = re.compile(
                r"\bfor\s*\(\s*(?:(?:int|uint\w+|size_t)\s+)?"
                r"([a-z_]\w*)\s*=",
                re.MULTILINE,
            )
            _all_var_uses = set(re.findall(r"\b([a-z_]\w*)\b", self.clean))
            for fm in _RE_FOR_INIT.finditer(self.clean):
                vname = fm.group(1)
                # Consider it loop-only if it only appears in loop constructs.
                # Simple heuristic: name has ≤ 3 chars (typical loop counters)
                if len(vname) <= 3:
                    loop_only_vars.add(vname)

        # Allowed uppercase abbreviations for variable names
        var_abbrevs = {a.upper() for a in var_cfg.get("allowed_abbreviations", [])}

        bool_cfg = var_cfg.get("bool_prefix",   {})
        pp_cfg   = var_cfg.get("pp_prefix",     {})

        # Collect typedef struct/union/enum alias names so that RE_VAR_DECL
        # matches on "} AliasName ;" are not treated as global variables.
        # Pattern matches body with semicolons (member declarations).
        _RE_TYPEDEF_ALIAS = re.compile(
            r"\btypedef\s+(?:struct|union|enum)\b[^{]*\{[^}]*\}"
            r"\s*([A-Za-z_]\w*)\s*;",
            re.DOTALL,
        )
        _typedef_alias_names: set = {
            _ta.group(1)
            for _ta in _RE_TYPEDEF_ALIAS.finditer(self.clean)
        }

        _typedef_close = getattr(self, "_typedef_close_positions", set())
        for m in RE_VAR_DECL.finditer(self.clean):
            # Skip matches where the trigger char is a typedef-closing "}"
            if self.clean[m.start():m.start()+1] == "}" and \
                    m.start() in _typedef_close:
                continue
            qualifiers  = m.group(1).lower()
            type_token  = m.group(2)          # e.g. "bool", "uint8_t"
            stars       = m.group(3)          # "", "*", or "**"
            name        = m.group(4)

            if not name:
                continue

            # Minimum length check (BARR-C 7.1.e)
            if len(name) < min_len:
                _exempt = ((allow_sc and len(name) == 1) or
                           (allow_loop_short and name in loop_only_vars))
                if not _exempt:
                    self._v(m.start(), var_cfg.get("severity", "warning"),
                            "variable.min_length",
                            f"Variable '{name}' length {len(name)} is below "
                            f"minimum {min_len} characters (BARR-C 7.1.e)")
                continue  # skip further checks on very short names

            # Skip names that are typedef struct/union/enum aliases —
            # they appear as "} TypeName ;" and match RE_VAR_DECL by accident.
            if name in _typedef_alias_names:
                continue

            # extern declarations are references to symbols defined elsewhere;
            # they are never variable definitions and must not be checked.
            if "extern" in qualifiers:
                continue

            depth     = self._depth_at(m.start())
            is_static = "static" in qualifiers
            # A variable is a parameter if its name was found in a signature
            # AND (it is inside a function body OR its position falls within
            # a signature range — the latter catches multiline param lists
            # which precede the opening brace and therefore have depth == 0).
            in_sig = any(s <= m.start() < e for s, e in sig_ranges)
            is_param  = (name in param_names) and (depth > 0 or in_sig)

            # in_sig (position inside a function signature) takes priority
            # over depth == 0 because multiline param lists have depth == 0
            # but are unambiguously parameters, not globals or statics.
            if in_sig:
                scope  = "parameter"
                sc     = sc_param
                # variable.parameter.p_prefix via in_sig path
                if _pp_param_en:
                    _p_stripped = self._strip_any_prefix(name)
                    if not _p_stripped.startswith(_pp_param_pfx):
                        self._v(m.start(), _pp_param_sev,
                                "variable.parameter.p_prefix",
                                f"Parameter '{name}' must start with "
                                f"'{_pp_param_pfx}' (parameter prefix)")
            elif depth == 0 and is_static:
                scope  = "static"
                sc     = sc_static
            elif depth == 0:
                scope  = "global"
                sc     = sc_global
            elif is_param:
                scope  = "parameter"
                sc     = sc_param
                # variable.parameter.p_prefix via RE_VAR_DECL path
                if _pp_param_en:
                    _p_stripped = self._strip_any_prefix(name)
                    if not _p_stripped.startswith(_pp_param_pfx):
                        self._v(m.start(), _pp_param_sev,
                                "variable.parameter.p_prefix",
                                f"Parameter '{name}' must start with "
                                f"'{_pp_param_pfx}' (parameter prefix)")
            else:
                scope  = "local"
                sc     = sc_local

            sev           = sc.get("severity",      var_cfg.get("severity", "error"))
            expected_case = sc.get("case",           var_cfg.get("case", "lower_snake"))
            req_mod_pfx   = sc.get("require_module_prefix", scope in ("global", "static"))

            if not matches_case_abbrev(name, expected_case, var_abbrevs):
                self._v(m.start(), sev, f"variable.{scope}.case",
                        f"{scope.capitalize()} variable '{name}' must be "
                        f"{expected_case}")

            max_len = var_cfg.get("max_length")
            if max_len and len(name) > max_len:
                self._v(m.start(), sev, "variable.max_length",
                        f"Variable '{name}' length {len(name)} exceeds "
                        f"maximum {max_len} characters")

            if req_mod_pfx:
                self._require_module_prefix(
                    name, m.start(), f"variable.{scope}.prefix")

            # g_ prefix — globals only
            if scope == "global":
                g_cfg = sc.get("g_prefix", {})
                if g_cfg.get("enabled", True):
                    g_pfx = g_cfg.get("prefix", "g_")
                    g_sev = g_cfg.get("severity", "warning")
                    local = self._strip_any_prefix(name)
                    if not local.startswith(g_pfx):
                        self._v(m.start(), g_sev, "variable.global.g_prefix",
                                f"Global variable '{name}' local part should "
                                f"start with '{g_pfx}'")

            # s_ prefix — file-scope statics only
            if scope == "static":
                s_cfg = sc.get("s_prefix", {})
                if s_cfg.get("enabled", True):
                    s_pfx = s_cfg.get("prefix", "s_")
                    s_sev = s_cfg.get("severity", "warning")
                    local = self._strip_any_prefix(name)
                    if not local.startswith(s_pfx):
                        self._v(m.start(), s_sev, "variable.static.s_prefix",
                                f"Static variable '{name}' local part should "
                                f"start with '{s_pfx}'")

            # Pointer prefixes (BARR-C 7.1.k / 7.1.l)
            # Single pointer (*) → local part must start with p_
            # Double pointer (**) → local part must start with pp_
            # The stars are captured directly in RE_VAR_DECL (group 3).
            if stars == "**":
                if pp_cfg.get("enabled", True):
                    pp_pfx = pp_cfg.get("prefix", "pp_")
                    pp_sev = pp_cfg.get("severity", "warning")
                    local  = self._strip_any_prefix(name)
                    if not local.startswith(pp_pfx):
                        self._v(m.start(), pp_sev, "variable.pp_prefix",
                                f"Double-pointer variable '{name}' local part "
                                f"should start with '{pp_pfx}' (BARR-C 7.1.l)")
            elif stars == "*":
                if ptr_cfg.get("enabled"):
                    p_pfx = ptr_cfg.get("prefix", "p_")
                    p_sev = ptr_cfg.get("severity", "warning")
                    local = self._strip_any_prefix(name)
                    if not local.startswith(p_pfx):
                        self._v(m.start(), p_sev, "variable.pointer_prefix",
                                f"Pointer variable '{name}' local part should "
                                f"start with '{p_pfx}' (BARR-C 7.1.k)")

            # Boolean prefix (BARR-C 7.1.m)
            # Variables of type bool or _Bool must have local part starting
            # with b_ and should be phrased as a question they answer.
            if bool_cfg.get("enabled", True) and type_token in ("bool", "_Bool"):
                b_pfx = bool_cfg.get("prefix", "b_")
                b_sev = bool_cfg.get("severity", "warning")
                local = self._strip_any_prefix(name)
                if not local.startswith(b_pfx):
                    self._v(m.start(), b_sev, "variable.bool_prefix",
                            f"Boolean variable '{name}' local part should "
                            f"start with '{b_pfx}' (BARR-C 7.1.m)")

            # Handle prefix (BARR-C 7.1.n)
            # Non-pointer handle variables (file handles, OS object handles)
            # must start with h_.  The set of handle types is configured via
            # variables.handle_prefix.handle_types in the YAML.
            h_cfg   = var_cfg.get("handle_prefix", {})
            h_types = {t.strip() for t in h_cfg.get("handle_types", [])}
            if h_cfg.get("enabled", True) and h_types and type_token in h_types:
                h_pfx = h_cfg.get("prefix", "h_")
                h_sev = h_cfg.get("severity", "warning")
                local = self._strip_any_prefix(name)
                if not local.startswith(h_pfx):
                    self._v(m.start(), h_sev, "variable.handle_prefix",
                            f"Handle variable '{name}' (type '{type_token}') "
                            f"local part should start with '{h_pfx}' (BARR-C 7.1.n)")

            # Embedded numeric values (BARR-C 7.1.g)
            # No variable name shall contain any numeric value that is called
            # out elsewhere (e.g. buffer32, array8, gpio3). Exempt patterns
            # may be configured for deliberate hardware-numbered names.
            num_cfg = var_cfg.get("no_numeric_in_name", {})
            if num_cfg.get("enabled", False):
                num_sev     = num_cfg.get("severity", "warning")
                num_exempt  = num_cfg.get("exempt_patterns", [])
                # Built-in exemption: digit followed immediately by a letter
                # unit suffix (e.g. 24hour, 8bit, 16mhz, 32khz).  These are
                # descriptive unit qualifiers, not type-width magic numbers.
                _has_unit_digit = bool(re.search(r'\d+[a-z]', name))
                if re.search(r'\d', name) and not _has_unit_digit and not is_exempt(name, num_exempt):
                    self._v(m.start(), num_sev, "variable.no_numeric_in_name",
                            f"Variable '{name}' contains an embedded numeric "
                            f"value — use a descriptive name (BARR-C 7.1.g)")

            # Prefix ordering (BARR-C 7.1.o)
            # When multiple prefixes are required they must appear in the order
            # [g_][p_|pp_][b_|h_]. Checked only when prefix-order is enabled.
            po_cfg = var_cfg.get("prefix_order", {})
            if po_cfg.get("enabled", False):
                po_sev    = po_cfg.get("severity", "warning")
                local     = self._strip_any_prefix(name)
                is_bool_t = type_token in ("bool", "_Bool")
                is_hdl_t  = bool(h_types) and type_token in h_types
                expected  = ""
                if scope == "global":
                    expected += var_cfg.get("global", {}).get(
                        "g_prefix", {}).get("prefix", "g_")
                if stars == "**":
                    expected += var_cfg.get("pp_prefix", {}).get("prefix", "pp_")
                elif stars == "*":
                    expected += var_cfg.get("pointer_prefix", {}).get("prefix", "p_")
                if is_bool_t:
                    expected += var_cfg.get("bool_prefix", {}).get("prefix", "b_")
                elif is_hdl_t:
                    expected += var_cfg.get("handle_prefix", {}).get("prefix", "h_")
                if expected and not local.startswith(expected):
                    self._v(m.start(), po_sev, "variable.prefix_order",
                            f"Variable '{name}': expected prefix order "
                            f"'{expected}', got local part '{local}' "
                            f"(BARR-C 7.1.o)")

    # -----------------------------------------------------------------------
    # 3. Function definitions
    # -----------------------------------------------------------------------

    # Helper: check whether a function body string satisfies object_verb.
    # Extracted so verb_object can reuse the same logic.
    @staticmethod
    def _body_is_object_verb(body: str, cstylecheck_exclusions: set, abbrevs: set) -> bool:
        """
        Return True when *body* (text after the module prefix) satisfies the
        object_verb (or verb_object) convention:

          * If any underscore-delimited segment of *body* appears in
            *cstylecheck_exclusions*, the rule is waived entirely.
          * Otherwise every segment must be PascalCase or an entry in
            *abbrevs*.  A single segment (verb only, no explicit object)
            is also accepted.

        Examples that pass:
          BufferRead          — classic ObjectVerb
          Init                — single verb, no object required
          LiveDataRead_X_Start — multi-segment; last = verb, rest = object
          Wr_Mode_Transit     — Wr is in cstylecheck_exclusions → waived
        """
        segments = [s for s in body.split("_") if s]
        if not segments:
            return False
        # Rule 1: exclusion list waives the entire check
        for seg in segments:
            if seg in cstylecheck_exclusions or seg.upper() in {e.upper() for e in cstylecheck_exclusions}:
                return True
        # Rule 2: every segment must be PascalCase or a known abbreviation
        for seg in segments:
            if seg.upper() in {a.upper() for a in abbrevs}:
                continue
            if not re.match(r"^[A-Z][a-zA-Z0-9]*$", seg):
                return False
        return True

    def _check_functions(self) -> None:
        fn_cfg     = self.cfg.get("functions", {})
        if not fn_cfg.get("enabled", True):
            return
        sev        = fn_cfg.get("severity", "error")
        style      = fn_cfg.get("style", "object_verb")
        isr_cfg    = fn_cfg.get("isr_suffix", {})
        cstylecheck_exclusions = set(fn_cfg.get("object_cstylecheck_exclusions", []))
        abbrevs    = set(fn_cfg.get("allowed_abbreviations", []))
        sp_cfg     = fn_cfg.get("static_prefix", {})

        # Pre-compile a regex to detect 'static' qualifier before the function
        # return type on the same line (or within a short preceding window).
        _RE_STATIC_FN = re.compile(
            r"(?:^|\n)[ \t]*static[ \t]+",
            re.MULTILINE,
        )

        for m in RE_FUNCTION_DEF.finditer(self.clean):
            name = m.group(1)
            if not name:
                continue

            if (isr_cfg.get("enabled")
                    and name.endswith(isr_cfg.get("suffix", "_IRQHandler"))):
                continue

            # Skip all checks for functions that are exempt from prefix rules.
            # (exempt_main covers main.c helpers; exempt_patterns covers ISR
            # stubs and other project-wide exceptions.)
            _fp_cfg = self.cfg.get("file_prefix", {})
            if _fp_cfg.get("exempt_main", True) and self.module == "main":
                continue
            if is_exempt(name, _fp_cfg.get("exempt_patterns", [])):
                continue

            # Detect whether this is a static function definition by inspecting
            # the text immediately before the match (up to 120 chars back).
            window_start = max(0, m.start())
            window_text  = self.clean[window_start: m.start() + 60]
            is_static_fn = bool(re.match(
                r"(?:^|\n)[ \t]*(?:static[ \t]+|(?:inline|const|volatile)[ \t]+)*static[ \t]+",
                window_text,
                re.MULTILINE,
            )) or "static" in self.clean[max(0, m.start()):m.start() + 60].split("\n")[0]

            # static_prefix rule: static functions must start with configured prefix
            if sp_cfg.get("enabled", False) and is_static_fn:
                sp_pfx = sp_cfg.get("prefix", "prv_")
                sp_sev = sp_cfg.get("severity", "warning")
                if not name.startswith(sp_pfx):
                    self._v(m.start(), sp_sev, "function.static_prefix",
                            f"Static function '{name}' must start with "
                            f"'{sp_pfx}' (static function prefix)")

            self._require_module_prefix(name, m.start(), "function.prefix")

            fn_max = fn_cfg.get("max_length")
            if fn_max and len(name) > fn_max:
                self._v(m.start(), sev, "function.max_length",
                        f"Function '{name}' length {len(name)} exceeds "
                        f"maximum {fn_max} characters")

            fn_min = fn_cfg.get("min_length")
            if fn_min and len(name) < fn_min:
                self._v(m.start(), sev, "function.min_length",
                        f"Function '{name}' length {len(name)} is below "
                        f"minimum {fn_min} characters")

            pfx = self._prefix()
            if not name.lower().startswith(pfx.lower()):
                continue
            body = name[len(pfx):]

            if style in ("object_verb", "verb_object"):
                if not self._body_is_object_verb(body, cstylecheck_exclusions, abbrevs):
                    self._v(m.start(), sev, "function.style",
                            f"Function '{name}' body '{body}' should be "
                            f"ObjectVerb segments separated by '_' "
                            f"(e.g. {pfx}BufferRead or {pfx}LiveData_Read)")
            elif style == "lower_snake":
                if not matches_case(body, "lower_snake"):
                    self._v(m.start(), sev, "function.style",
                            f"Function '{name}' body '{body}' should be "
                            f"lower_snake")

    # -----------------------------------------------------------------------
    # 4. Typedefs
    # -----------------------------------------------------------------------

    def _check_typedefs(self) -> None:
        td_cfg = self.cfg.get("typedefs", {})
        if not td_cfg.get("enabled", True):
            return
        sev        = td_cfg.get("severity", "warning")
        suffix_cfg = td_cfg.get("suffix", {})
        suffix     = suffix_cfg.get("suffix", "_T") if suffix_cfg.get("enabled") else None

        for m in RE_TYPEDEF_SIMPLE.finditer(self.clean):
            name = m.group(1)
            if not name:
                continue
            if not matches_case(name, td_cfg.get("case", "upper_snake")):
                self._v(m.start(), sev, "typedef.case",
                        f"Typedef '{name}' must be "
                        f"{td_cfg.get('case', 'upper_snake')}")
            if suffix and not name.endswith(suffix):
                self._v(m.start(), sev, "typedef.suffix",
                        f"Typedef '{name}' must end with '{suffix}'")

    # -----------------------------------------------------------------------
    # 5. Enums — fixed member-prefix derivation
    # -----------------------------------------------------------------------

    def _check_enums(self) -> None:
        """
        Derive the expected enum member prefix correctly when the type_case
        and member_case differ.

        Algorithm:
          1. Take the type name as it appears in the source (e.g. uart_status_t).
          2. Strip the type suffix case-insensitively (e.g. remove _t -> uart_status).
          3. Convert to the member case  (e.g. upper_snake -> UART_STATUS).
          4. Each member must start with <result>_ (e.g. UART_STATUS_OK).

        This is correct regardless of whether type_case is lower_snake or
        upper_snake and regardless of suffix capitalisation.
        """
        enum_cfg = self.cfg.get("enums", {})
        if not enum_cfg.get("enabled", True):
            return

        type_sev        = enum_cfg.get("severity", "error")
        type_case       = enum_cfg.get("type_case", "upper_snake")
        type_suffix_cfg = enum_cfg.get("type_suffix", {})
        type_suffix     = (type_suffix_cfg.get("suffix", "_T")
                           if type_suffix_cfg.get("enabled") else None)
        member_case     = enum_cfg.get("member_case", "upper_snake")
        member_pfx_cfg  = enum_cfg.get("member_prefix_from_type", {})

        for m in RE_TYPEDEF_ENUM.finditer(self.clean):
            body_str, type_name = m.group(1), m.group(2)

            # --- type name checks ---
            if not matches_case(type_name, type_case):
                self._v(m.start(), type_sev, "enum.type_case",
                        f"Enum type '{type_name}' must be {type_case}")
            if type_suffix and not type_name.endswith(type_suffix):
                self._v(m.start(), type_sev, "enum.type_suffix",
                        f"Enum type '{type_name}' must end with '{type_suffix}'")

            # --- derive member prefix ---
            # Strip suffix case-insensitively, then convert to member case.
            raw_base = type_name
            if type_suffix and raw_base.lower().endswith(type_suffix.lower()):
                raw_base = raw_base[: -len(type_suffix)]
            member_pfx = to_case(raw_base, member_case)

            # --- member checks ---
            for mm in RE_ENUM_MEMBER.finditer(body_str):
                mname = mm.group(1)
                if not matches_case(mname, member_case):
                    self._v(m.start(), type_sev, "enum.member_case",
                            f"Enum member '{mname}' must be {member_case}")
                if (member_pfx_cfg.get("enabled")
                        and not mname.upper().startswith(
                            member_pfx.upper() + "_")):
                    self._v(m.start(),
                            member_pfx_cfg.get("severity", "warning"),
                            "enum.member_prefix",
                            f"Enum member '{mname}' should start with "
                            f"'{member_pfx}_'")

    # -----------------------------------------------------------------------
    # 6. Struct tags and members
    # -----------------------------------------------------------------------

    def _check_structs(self) -> None:
        st_cfg = self.cfg.get("structs", {})
        if not st_cfg.get("enabled", True):
            return
        sev            = st_cfg.get("severity", "warning")
        tag_case       = st_cfg.get("tag_case", "lower_snake")
        tag_suffix_cfg = st_cfg.get("tag_suffix", {})
        tag_suffix     = (tag_suffix_cfg.get("suffix", "_s")
                          if tag_suffix_cfg.get("enabled") else None)
        member_case    = st_cfg.get("member_case", "lower_snake")
        # Uppercase abbreviations allowed in member names (same concept as
        # variables.allowed_abbreviations).  E.g. FIFO, CRC, SPI.
        st_abbrevs = {a.upper() for a in
                      st_cfg.get("allowed_abbreviations", [])}

        for m in RE_TYPEDEF_STRUCT.finditer(self.clean):
            tag      = m.group(1)
            body_str = m.group(2)

            if tag:
                if not matches_case(tag, tag_case):
                    self._v(m.start(), sev, "struct.tag_case",
                            f"Struct tag '{tag}' must be {tag_case}")
                if tag_suffix and not tag.endswith(tag_suffix):
                    self._v(m.start(), sev, "struct.tag_suffix",
                            f"Struct tag '{tag}' must end with '{tag_suffix}'")

            # Members: no module prefix required
            for mm in re.finditer(r"\b([a-zA-Z_]\w*)\s*(?:;|\[)", body_str):
                mname = mm.group(1)
                if not matches_case_abbrev(mname, member_case, st_abbrevs):
                    self._v(m.start(), sev, "struct.member_case",
                            f"Struct member '{mname}' must be {member_case}")

    # -----------------------------------------------------------------------
    # 0. Copyright block comment header
    # Checks that the file begins with the configured copyright block
    # comment template, followed by exactly one blank line.
    # Activated only when --copyright FILE was supplied on the CLI.
    # -----------------------------------------------------------------------

    def _check_copyright_header(self) -> None:
        cr_cfg = self.cfg.get("misc", {}).get("copyright_header", {})
        if not cr_cfg.get("enabled", True):
            return
        if self._copyright is None:
            return   # no --copyright file supplied — check not active

        sev              = cr_cfg.get("severity", "error")
        template, pattern = self._copyright

        # Normalise line endings so the regex (built from the template,
        # which was also normalised) can match reliably.
        source = self.source.replace('\r\n', '\n').replace('\r', '\n')

        m = pattern.match(source)

        if m is None:
            # ----------------------------------------------------------------
            # Header mismatch
            # ----------------------------------------------------------------
            if not source.lstrip('\ufeff').startswith('/*'):
                # No opening /* at the top of the file at all.
                self.result.add(Violation(
                    self.filepath, 1, 1, sev, "misc.copyright_header",
                    "File must begin with the copyright block comment header; "
                    "no '/*' found at start of file"))
            else:
                # There is a block comment at the top, but it doesn't match.
                # Try to find the first differing line for a helpful message.
                tpl_lines = template.split('\n')
                src_lines = source.split('\n')
                diff_line = None
                for idx, (tl, sl) in enumerate(
                        zip(tpl_lines, src_lines), start=1):
                    # On the (C) Copyright line accept any year/range.
                    ym = _COPYRIGHT_YEAR_RE.search(tl)
                    if ym:
                        # Replace the year in the source line too, then compare
                        sl_norm = _COPYRIGHT_YEAR_RE.sub(
                            lambda mo: mo.group(1) + '0000', sl)
                        tl_norm = _COPYRIGHT_YEAR_RE.sub(
                            lambda mo: mo.group(1) + '0000', tl)
                        if sl_norm != tl_norm:
                            diff_line = idx
                            break
                    elif sl != tl:
                        diff_line = idx
                        break
                else:
                    # zip stopped early — source has fewer lines than template
                    if len(src_lines) < len(tpl_lines):
                        diff_line = len(src_lines) + 1

                if diff_line is not None:
                    self.result.add(Violation(
                        self.filepath, diff_line, 1, sev,
                        "misc.copyright_header",
                        f"Copyright header mismatch at line {diff_line}: "
                        f"file does not match the required template"))
                else:
                    self.result.add(Violation(
                        self.filepath, 1, 1, sev, "misc.copyright_header",
                        "Copyright header does not match the required template"))
            return

        # --------------------------------------------------------------------
        # Header matched — check exactly one blank line follows the closing */
        # --------------------------------------------------------------------
        after      = source[m.end():]
        # splitlines(keepends=True) handles all cases cleanly:
        #   '\n\ncode'   → ['\n', '\n', 'code']  → 1 blank ✓
        #   '\nvoid'     → ['\n', 'void']         → 0 blanks ✗
        #   '\n\n\ncode' → ['\n','\n','\n','code']→ 2 blanks ✗
        after_lines  = after.splitlines(keepends=True)
        # [0] is the tail of the */ line itself; skip it.
        blank_count  = 0
        for al in after_lines[1:]:
            if al.strip():
                break
            blank_count += 1

        if blank_count != 1:
            # Line number of the */ closing line
            header_end_line = source[:m.end()].count('\n') + 1
            report_line     = header_end_line + 1
            if blank_count == 0:
                msg = ("Copyright header must be followed by exactly one "
                       "blank line; found none")
            else:
                msg = (f"Copyright header must be followed by exactly one "
                       f"blank line; found {blank_count}")
            self.result.add(Violation(
                self.filepath, report_line, 1, sev,
                "misc.copyright_header", msg))

    # -----------------------------------------------------------------------
    # 7. Include guards
    # -----------------------------------------------------------------------

    def _check_include_guard(self) -> None:
        ig_cfg = self.cfg.get("include_guards", {})
        if not ig_cfg.get("enabled", True):
            return
        sev = ig_cfg.get("severity", "error")

        if ig_cfg.get("allow_pragma_once") and RE_PRAGMA_ONCE.search(self.clean):
            return

        stem     = Path(self.filepath).stem.upper()
        ext      = Path(self.filepath).suffix.lstrip(".").upper()
        template = ig_cfg.get("pattern", "{FILENAME_UPPER}_{EXT_UPPER}_")
        expected = (template
                    .replace("{FILENAME_UPPER}", stem)
                    .replace("{EXT_UPPER}", ext))

        ifndef_m = RE_INCLUDE_GUARD_IFNDEF.search(self.clean)
        define_m = RE_INCLUDE_GUARD_DEFINE.search(self.clean)

        if not ifndef_m or not define_m:
            self._v(0, sev, "include_guard.missing",
                    f"Header '{self.filepath}' has no include guard or #pragma once")
            return

        guard = ifndef_m.group(1)
        if not guard.startswith(expected.rstrip("_")):
            self._v(ifndef_m.start(), sev, "include_guard.format",
                    f"Include guard '{guard}' should match '{expected}*'")

    # -----------------------------------------------------------------------
    # 8. Miscellaneous
    # -----------------------------------------------------------------------

    def _check_misc(self) -> None:
        misc = self.cfg.get("misc", {})

        # Line length — skip comment/blank lines
        ll_cfg = misc.get("line_length", {})
        if ll_cfg.get("enabled", True):
            sev    = ll_cfg.get("severity", "warning")
            maxlen = ll_cfg.get("max", 120)
            for lineno, line in enumerate(self.source.splitlines(), 1):
                if lineno in self._comment_only:
                    continue
                if len(line) > maxlen:
                    self.result.add(Violation(
                        self.filepath, lineno, maxlen + 1, sev,
                        "misc.line_length",
                        f"Line length {len(line)} exceeds maximum {maxlen}"))

        # Indentation — skip comment/blank lines
        ind_cfg = misc.get("indentation", {})
        if ind_cfg.get("enabled", True):
            sev   = ind_cfg.get("severity", "info")
            style = ind_cfg.get("style", "spaces")
            for lineno, line in enumerate(self.source.splitlines(), 1):
                if lineno in self._comment_only:
                    continue
                if style == "spaces" and line.startswith("\t"):
                    self.result.add(Violation(
                        self.filepath, lineno, 1, sev, "misc.indentation",
                        "Tab used for indentation; expected spaces"))
                elif style == "tabs" and re.match(r"^ +", line):
                    self.result.add(Violation(
                        self.filepath, lineno, 1, sev, "misc.indentation",
                        "Spaces used for indentation; expected tabs"))

        # Pre-compute exempt positions for magic-number and unsigned-suffix checks:
        #
        #   1. Array subscripts:    array[2]  — the index literal is not magic.
        #   2. #define RHS:         #define FOO 1000  — already named, not magic.
        #   3. return statements:   return 0;  — return codes need no U suffix.
        #   4. Negative sign:       -1  — handled per-literal below (not position).
        exempt_positions: set = set()
        # Array subscripts
        for ai in RE_ARRAY_INDEX.finditer(self.clean):
            exempt_positions.update(range(ai.start(), ai.end()))
        # #define lines and preprocessor conditionals (#if/#elif/#ifdef/#ifndef)
        # Constants in preprocessor expressions need no U suffix — the
        # preprocessor treats all integer tokens as signed by default.
        _RE_PREPROC_LINE = re.compile(
            r"^[ \t]*#[ \t]*(?:define|if|elif|ifdef|ifndef|undef)[^\n]*",
            re.MULTILINE,
        )
        for dl in _RE_PREPROC_LINE.finditer(self.clean):
            exempt_positions.update(range(dl.start(), dl.end()))
        # return statements:  "return <expr>;"  — return codes are not constants
        _RE_RETURN_STMT = re.compile(r"\breturn\b[^;]*;", re.MULTILINE)
        for rs in _RE_RETURN_STMT.finditer(self.clean):
            exempt_positions.update(range(rs.start(), rs.end()))

        # const-qualified variable declarations:  const TYPE NAME = LITERAL;
        # The literal IS the named constant — no magic-number warning needed.
        # Covers: const T name = val;  and  static const T name = val;
        # Match both scalar and aggregate (brace-initialised) const decls:
        #   const uint16_t POLY_A0 = 1735;
        #   static const int LUT[] = {10, 20, 30};
        _RE_CONST_DECL = re.compile(
            r"\b(?:static\s+)?const\s+\w[\w\s\[\]*]*\s*=\s*"  # lhs
            r"(?:\{[^}]*\}|[^;]+)"                                    # rhs
            r"\s*;",
            re.MULTILINE,
        )
        for cd in _RE_CONST_DECL.finditer(self.clean):
            exempt_positions.update(range(cd.start(), cd.end()))

        # Arguments to functions whose parameters are known signed integers
        # (e.g. memset, printf) are exempt from the unsigned_suffix rule.
        # These are configured in misc.unsigned_suffix.exempt_function_args.
        _DEFAULT_EXEMPT_FNS = [
            # C string/memory functions with signed "int c" parameter
            "memset", "memcmp", "memchr",
            # C stdio — format functions accept int args
            "printf", "fprintf", "sprintf", "snprintf",
            "vprintf", "vfprintf", "vsprintf", "vsnprintf",
            # C stdio character functions
            "fputc", "putc", "putchar", "ungetc",
            # POSIX / socket
            "setsockopt",
        ]
        _us_fn_cfg = misc.get("unsigned_suffix", {})
        _exempt_fns = _us_fn_cfg.get(
            "exempt_function_args", _DEFAULT_EXEMPT_FNS
        )
        for _fn in _exempt_fns:
            _fn_pat = re.compile(
                r"\b" + re.escape(_fn) + r"\s*\(", re.MULTILINE
            )
            for _fm in _fn_pat.finditer(self.clean):
                _depth = 0
                _pos   = _fm.end() - 1
                _start = _pos
                while _pos < len(self.clean):
                    if self.clean[_pos] == "(":
                        _depth += 1
                    elif self.clean[_pos] == ")":
                        _depth -= 1
                        if _depth == 0:
                            break
                    _pos += 1
                exempt_positions.update(range(_start, _pos + 1))

        # Magic numbers
        mn_cfg = misc.get("magic_numbers", {})
        if mn_cfg.get("enabled", True):
            sev    = mn_cfg.get("severity", "warning")
            exempt = {str(v) for v in mn_cfg.get("exempt_values", [])}
            for m in RE_MAGIC_NUMBER.finditer(self.clean):
                if m.start() in exempt_positions:
                    continue
                val = m.group(1)
                if val not in exempt:
                    line, col = offset_to_line_col(self._line_map, m.start())
                    self.result.add(Violation(
                        self.filepath, line, col, sev, "misc.magic_number",
                        f"Magic number {val} should be a named constant"))

        # Unsigned suffix
        us_cfg = misc.get("unsigned_suffix", {})
        if us_cfg.get("enabled") and us_cfg.get("require_on_unsigned_constants"):
            sev              = us_cfg.get("severity", "info")
            zero_is_neutral  = us_cfg.get("zero_is_neutral", True)

            # Build a set of variable names that have a signed type so that
            # integer literals assigned to them do not require a U suffix.
            signed_vars: set = set()
            for dm in RE_VAR_DECL.finditer(self.clean):
                qualifiers = dm.group(1).lower()
                type_tok   = dm.group(2)
                var_name   = dm.group(4)
                if "unsigned" not in qualifiers and type_tok in _SIGNED_TYPES:
                    signed_vars.add(var_name)

            # Build a set of char offsets that are in a signed-variable
            # assignment context:  <signed_var> = <literal>
            _RE_SIGNED_ASSIGN = re.compile(
                r"\b([a-z_]\w*)\s*(?:[+\-*/%&|^]=|=)\s*([0-9]+)\b"
            )
            signed_assign_positions: set = set()
            for am in _RE_SIGNED_ASSIGN.finditer(self.clean):
                if am.group(1) in signed_vars:
                    lit_start = am.start(2)
                    lit_end   = am.end(2)
                    signed_assign_positions.update(range(lit_start, lit_end))

            for m in re.finditer(r"\b([0-9]+)\b", self.clean):
                if m.start() in exempt_positions:
                    continue
                # Skip float literals: digit followed by . or e/E,
                # or preceded by . (e.g. 2.0, 1.5e3, .5f, 3.14f)
                _after  = self.clean[m.end():m.end()+2]
                _before = self.clean[m.start()-1:m.start()] if m.start() > 0 else ""
                if (_after[:1] in (".", "e", "E", "f", "F") or
                        _before == "."):
                    continue
                # Skip the digit inside a negative literal like -1
                if m.start() > 0 and self.clean[m.start() - 1] == "-":
                    continue
                val = m.group(1)
                # 0 is assignment-neutral when zero_is_neutral is enabled
                if zero_is_neutral and val == "0":
                    continue
                # Skip literals assigned to signed-typed variables
                if m.start() in signed_assign_positions:
                    continue
                # Skip literals used as part of a declaration initialiser
                # for a signed variable:  int x = <literal>
                decl_ctx = self.clean[max(0, m.start()-60):m.start()]
                if re.search(
                    r"\b(?:int|char|short|long|float|double|int\w+_t|ptrdiff_t|ssize_t)\b"
                    r"(?:\s+\w+)?\s*=\s*$",
                    decl_ctx
                ):
                    continue
                after = self.clean[m.end(): m.end() + 1]
                if after not in ("u", "U", "l", "L"):
                    line, col = offset_to_line_col(self._line_map, m.start())
                    self.result.add(Violation(
                        self.filepath, line, col, sev, "misc.unsigned_suffix",
                        f"Unsigned constant '{val}' should have "
                        f"'U' or 'u' suffix (or assign to a signed type)"))

    # -----------------------------------------------------------------------
    # 9. Block-comment spacing
    # Checks that the number of blank lines between the closing */ of a
    # multi-line block comment and the next non-blank line is within the
    # configured [min, max] range.
    # -----------------------------------------------------------------------
        bcs_cfg = misc.get("block_comment_spacing", {})
        if bcs_cfg.get("enabled", False):
            bcs_sev = bcs_cfg.get("severity", "warning")
            bcs_min = bcs_cfg.get("min_blank_lines", 1)
            bcs_max = bcs_cfg.get("max_blank_lines", 2)
            _RE_BLOCK_CMT = re.compile(r'/\*.*?\*/', re.DOTALL)
            for _bc in _RE_BLOCK_CMT.finditer(self.source):
                # Only check multi-line block comments
                if "\n" not in _bc.group(0):
                    continue
                _rest   = self.source[_bc.end():]
                _lines  = _rest.split("\n")
                # Count blank lines after the closing */ line
                _blanks = 0
                _found_next = False
                for _li, _ln in enumerate(_lines):
                    if _li == 0:
                        # Remainder of the */ line — skip
                        continue
                    if _ln.strip() == "":
                        _blanks += 1
                    else:
                        _found_next = True
                        break
                if not _found_next:
                    continue  # comment at end of file
                _bc_line = self.source[:_bc.end()].count("\n") + 1
                if _blanks < bcs_min:
                    self.result.add(Violation(
                        self.filepath, _bc_line, 1, bcs_sev,
                        "misc.block_comment_spacing",
                        f"Block comment has {_blanks} blank line(s) after '*/'; "
                        f"minimum is {bcs_min}"))
                elif _blanks > bcs_max:
                    self.result.add(Violation(
                        self.filepath, _bc_line, 1, bcs_sev,
                        "misc.block_comment_spacing",
                        f"Block comment has {_blanks} blank line(s) after '*/'; "
                        f"maximum is {bcs_max}"))

        # EOF comment
        # The last non-blank line must equal the configured template string
        # (with {filename} replaced by the file's base name, case-adjusted).
        # Exactly one blank line must follow it as the final line of the file.
        eof_cfg = misc.get("eof_comment", {})
        if eof_cfg.get("enabled", False):
            sev      = eof_cfg.get("severity", "warning")
            template = eof_cfg.get("template", "/* EOF: {filename} */")
            fn_case  = eof_cfg.get("filename_case", "lower")

            basename = Path(self.filepath).name
            if fn_case == "lower":
                basename = basename.lower()
            elif fn_case == "upper":
                basename = basename.upper()
            # "preserve" → leave as-is

            expected = template.replace("{filename}", basename)

            # splitlines() gives logical lines without a phantom trailing
            # entry for the terminal \n, but does include a trailing ''
            # element when the file ends with \n\n (one blank line) or
            # \n\n\n (two blank lines), which is exactly what we need.
            lines = self.source.splitlines()

            # Locate last non-blank line
            last_nb = None
            for _i in range(len(lines) - 1, -1, -1):
                if lines[_i].strip():
                    last_nb = _i
                    break

            if last_nb is None:
                # Entirely blank / empty file
                self.result.add(Violation(
                    self.filepath, 1, 1, sev, "misc.eof_comment",
                    f"File is empty or blank; expected EOF comment "
                    f"'{expected}' as last non-blank line"))
            else:
                lineno_nb = last_nb + 1          # 1-based
                actual    = lines[last_nb]

                # Check 1: last non-blank line matches expected string
                if actual != expected:
                    self.result.add(Violation(
                        self.filepath, lineno_nb, 1, sev, "misc.eof_comment",
                        f"Last non-blank line must be '{expected}'; "
                        f"found '{actual}'"))

                # Check 2: exactly one blank line follows (the last line)
                after = lines[last_nb + 1:]      # lines after EOF comment
                n_after = len(after)
                if n_after == 0:
                    # Nothing after the comment — missing trailing blank line
                    self.result.add(Violation(
                        self.filepath, lineno_nb, 1, sev, "misc.eof_comment",
                        "EOF comment must be followed by exactly one blank line"))
                elif n_after == 1:
                    # Exactly one line follows — it must be blank
                    if after[0].strip():
                        self.result.add(Violation(
                            self.filepath, lineno_nb + 1, 1, sev,
                            "misc.eof_comment",
                            "Line after EOF comment must be blank"))
                    # else: perfect — one blank line, done
                else:
                    # More than one line follows the last non-blank line;
                    # all of them are blank (otherwise last_nb would be later),
                    # so we have multiple trailing blank lines.
                    self.result.add(Violation(
                        self.filepath, lineno_nb + 1, 1, sev,
                        "misc.eof_comment",
                        f"EOF comment must be followed by exactly one blank "
                        f"line; found {n_after}"))

    # -----------------------------------------------------------------------
    # 10. Comment spell-check
    # -----------------------------------------------------------------------

    def _check_spelling(self) -> None:
        sp_cfg = self.cfg.get("spell_check", {})
        if not sp_cfg.get("enabled", True):
            return
        sev = sp_cfg.get("severity", "info")

        for lineno, text in extract_comments(self.source):
            for wm in RE_COMMENT_WORD.finditer(text):
                word = re.sub(r"'s$", "", wm.group(0).lower())
                if word not in self._spell_dict:
                    self.result.add(Violation(
                        self.filepath, lineno, 1, sev, "spell_check",
                        f"Unknown word in comment: '{wm.group(0)}'"))


    # -----------------------------------------------------------------------
    # 10. Yoda conditions  (constant on the LHS of == and !=)
    # -----------------------------------------------------------------------

    def _check_yoda(self) -> None:
        """
        Flag comparisons where a variable is on the LHS and a constant on the
        RHS of == or !=.  The Barr-C / MISRA-friendly style puts the constant
        first so that a mistyped = instead of == becomes a compile-time error:

            if (NULL == p_buf)     ← correct (Yoda style)
            if (p_buf == NULL)     ← violation

        Only == and != are checked.  Directional operators (< > <= >=) are
        excluded because reversing them changes meaning and is not idiomatic.
        """
        yoda_cfg = self.cfg.get("misc", {}).get("yoda_conditions", {})
        if not yoda_cfg.get("enabled", True):
            return
        sev = yoda_cfg.get("severity", "warning")

        # Build exempt positions: #define RHS and return statements
        skip: set = set()
        for m in re.finditer(r"^[ \t]*#[ \t]*define[^\n]*",
                              self.clean, re.MULTILINE):
            skip.update(range(m.start(), m.end()))
        for m in re.finditer(r"\breturn\b[^;]*;", self.clean, re.MULTILINE):
            skip.update(range(m.start(), m.end()))

        _RE_CMP = re.compile(r"(?<![<>=!])([=!]=)(?!=)")

        for m in _RE_CMP.finditer(self.clean):
            if m.start() in skip:
                continue

            op = m.group(1)

            # Extract token immediately to the LEFT of the operator
            lhs_end = m.start()
            while lhs_end > 0 and self.clean[lhs_end - 1] in " \t":
                lhs_end -= 1
            lhs_s = lhs_end
            while lhs_s > 0 and (self.clean[lhs_s - 1].isalnum()
                                   or self.clean[lhs_s - 1] == "_"):
                lhs_s -= 1
            lhs = self.clean[lhs_s:lhs_end]

            # Extract token immediately to the RIGHT of the operator
            rhs_start = m.end()
            while rhs_start < len(self.clean) and self.clean[rhs_start] in " \t":
                rhs_start += 1
            rhs_end = rhs_start
            while rhs_end < len(self.clean) and (
                    self.clean[rhs_end].isalnum()
                    or self.clean[rhs_end] in "_'xXuUlL"):
                rhs_end += 1
            rhs = self.clean[rhs_start:rhs_end]

            if self._is_variable_token(lhs) and self._is_constant_token(rhs):
                self._v(m.start(), sev, "misc.yoda_condition",
                        f"Constant '{rhs}' should be on the left of '{op}': "
                        f"write '{rhs} {op} {lhs}'")

    @staticmethod
    def _is_constant_token(tok: str) -> bool:
        """True if *tok* is recognisably a constant (literal, keyword, ALL_CAPS)."""
        t = tok.strip()
        if not t:
            return False
        if re.fullmatch(r"[0-9]+[uUlL]*", t):             return True  # decimal
        if re.fullmatch(r"0[xX][0-9A-Fa-f]+[uUlL]*", t): return True  # hex
        if re.fullmatch(r"'[^']*'", t):                    return True  # char
        if t in {"true", "false", "TRUE", "FALSE",
                 "NULL", "nullptr"}:                       return True  # bool/null
        if re.fullmatch(r"[A-Z_][A-Z0-9_]+", t):          return True  # ALL_CAPS ≥ 2 chars
        return False

    @staticmethod
    def _is_variable_token(tok: str) -> bool:
        """True if *tok* is a plain variable identifier (starts with lowercase/underscore)."""
        t = tok.strip()
        if not t:
            return False
        return bool(re.fullmatch(r"[a-z_][a-zA-Z0-9_]*", t))

    # -----------------------------------------------------------------------
    # 11. Reserved / banned name check
    # -----------------------------------------------------------------------

    def _is_reserved(self, name: str) -> tuple:
        """Return (True, category_string) if *name* is a reserved identifier."""
        if name in C_KEYWORDS:
            return True, "C/C++ keyword"
        if name in C_STDLIB_NAMES:
            return True, "C standard library name"
        if name in self._extra_banned:
            return True, "project-banned name"
        return False, ""

    def _check_name_reserved(self, name: str, pos: int, sev: str) -> None:
        """Emit a violation if *name* shadows a C keyword or stdlib identifier."""
        banned, category = self._is_reserved(name)
        if banned:
            self._v(pos, sev, "reserved_name",
                    f"'{name}' shadows a {category} and must not be used "
                    f"as an identifier (BARR-C 6.1.a / 7.1.a)")

    def _check_reserved_names(self) -> None:
        """
        Check that no declared identifier shadows a C/C++ keyword, a C standard
        library name, or a project-banned name (from --banned-names FILE).

        Checks all scopes: variables, function definitions, and macro/constant
        names.  Per-file exceptions are handled via --cstylecheck_exclusions by adding
        'reserved_name' to the disabled_rules list for that file pattern.
        """
        rn_cfg = self.cfg.get("reserved_names", {})
        if not rn_cfg.get("enabled", True):
            return
        sev = rn_cfg.get("severity", "error")

        # Variables (all scopes) — group(4) is the variable name after the
        # RE_VAR_DECL upgrade that added type (group 2) and stars (group 3).
        for m in RE_VAR_DECL.finditer(self.clean):
            name = m.group(4)
            if name:
                self._check_name_reserved(name, m.start(), sev)

        # Function definitions
        for m in RE_FUNCTION_DEF.finditer(self.clean):
            name = m.group(1)
            if name:
                self._check_name_reserved(name, m.start(), sev)

        # Macros and object-like #defines
        for m in RE_DEFINE.finditer(self.clean):
            name = m.group(1)
            rest = self.clean[m.end():].split("\n")[0].strip()
            if not rest:   # bare include-guard define — skip
                continue
            if name:
                self._check_name_reserved(name, m.start(), sev)


# ---------------------------------------------------------------------------
# Type-signedness resolution and cross-file call-site checking
# ---------------------------------------------------------------------------
#
# This sub-system works in three stages, all driven across the full set of
# files passed to the checker in a single run:
#
#   Stage 1 — typedef resolution
#     Parse every typedef declaration from all .h and .c files.
#     Build a map: typedef_name -> SIGNED | UNSIGNED | UNKNOWN.
#     Follow chains (typedef A = B; typedef B = signed char) up to 8 hops.
#
#   Stage 2 — function signature extraction
#     Parse function *declarations* (ending in ';') from header files.
#     For each parameter record its type string and resolved signedness.
#
#   Stage 3 — call-site checking
#     For every function call in a .c file whose name matches a known
#     signature, extract the actual argument expressions and classify each
#     one as SIGNED (e.g. -1, (int8_t)x), UNSIGNED (e.g. 100U, 0xFFU),
#     NEUTRAL (plain positive integer literal — allowed for either side),
#     or UNKNOWN (variable / complex expression — skipped conservatively).
#     Emit a violation when an argument's signedness is known and conflicts
#     with the parameter's resolved signedness.

_SIGN_SIGNED   = "signed"
_SIGN_UNSIGNED = "unsigned"
_SIGN_UNKNOWN  = "unknown"
_SIGN_NEUTRAL  = "neutral"   # plain positive integer literal: no flag

# Type names that are intrinsically unsigned (without needing the keyword)
_UNSIGNED_TYPES: set = {
    "uint8_t",  "uint16_t",  "uint32_t",  "uint64_t",
    "uint8",    "uint16",    "uint32",    "uint64",
    "bool", "_Bool", "size_t", "uintptr_t", "uintmax_t",
}

# Type names that are intrinsically signed (without needing the keyword)
_SIGNED_TYPES: set = {
    "int8_t",   "int16_t",   "int32_t",   "int64_t",
    "int8",     "int16",     "int32",     "int64",
    "sint8",    "sint16",    "sint32",    "sint64",
    "int", "short", "long",
    # plain char: implementation-defined, but most embedded compilers make
    # it signed; we treat it as signed by default (configurable via YAML)
    "char",
}


@dataclass
class _ParamSig:
    """Signedness information for one function parameter."""
    name:       str
    type_str:   str   # as written in the source
    signedness: str   # _SIGN_SIGNED | _SIGN_UNSIGNED | _SIGN_UNKNOWN


@dataclass
class _FuncSig:
    """Resolved signature of a declared function."""
    name:   str
    params: list      # list[_ParamSig]


# --- Regex patterns for sign analysis ---

_RE_TYPEDEF_SCALAR = re.compile(
    r"\btypedef\b"
    r"((?:[ \t]+(?:const|volatile|signed|unsigned|long|short"
    r"|int|char|float|double|\w+))+)"
    r"[ \t]+(\w+)\s*;",
)

_RE_FUNC_DECL = re.compile(
    # Function prototype (ends with ; not {).  No backtracking hazard because
    # each keyword group uses [ \t]+ and there is no \s inside the type tokens.
    r"(?:^|\n)[ \t]*"
    r"(?:(?:extern|static|inline|const|volatile)[ \t]+)*"
    r"(?:(?:unsigned|signed)[ \t]+)?"
    r"(?:(?:long[ \t]+long|long|short)[ \t]+)?"
    r"\w+[ \t]*\*?[ \t]*"
    r"([A-Za-z_]\w*)"                     # function name  — group 1
    r"[ \t]*\(([^)]*)\)"                # param list     — group 2
    r"[ \t]*;",
    re.MULTILINE,
)

_RE_ONE_PARAM = re.compile(
    r"((?:(?:const|volatile|signed|unsigned|long|short|int|char|float|double"
    r"|bool|_Bool|uint\w*|int\w*|sint\w*|size_t|[A-Za-z_]\w*)[ \t]+)+)"
    r"\*?[ \t]*"
    r"([A-Za-z_]\w*)"
    r"[ \t]*(?:,|$|\[)",
)

_RE_CALL       = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
_RE_UINT_LIT   = re.compile(r"^\s*(?:0[xX][0-9A-Fa-f]+|[0-9]+)[uU][lL]?\s*$")
_RE_NEG_LIT    = re.compile(r"^\s*-\s*[0-9]+\s*$")
_RE_PLAIN_INT  = re.compile(r"^\s*(?:0[xX][0-9A-Fa-f]+|[0-9]+)[lL]?\s*$")
_RE_CHAR_LIT   = re.compile(r"^\s*'[^']*'\s*$")
_RE_UINT_CAST  = re.compile(r"^\s*\(\s*(?:unsigned|uint\w+)\s*\)")
_RE_SINT_CAST  = re.compile(r"^\s*\(\s*(?:signed|int\w+|sint\w+)\s*\)")


def _classify_tokens(tokens: list) -> str:
    """Return sign classification from a list of type/qualifier tokens."""
    tset = set(tokens)
    if "unsigned" in tset:
        return _SIGN_UNSIGNED
    if "signed" in tset:
        return _SIGN_SIGNED
    for t in tokens:
        if t in _UNSIGNED_TYPES:
            return _SIGN_UNSIGNED
        if t in _SIGNED_TYPES:
            return _SIGN_SIGNED
    return _SIGN_UNKNOWN


def _signedness_of_type(type_str: str, tmap: dict) -> str:
    """Resolve a full type string (e.g. 'int8_t' or 'unsigned short') to a sign."""
    tokens = type_str.split()
    result = _classify_tokens(tokens)
    if result != _SIGN_UNKNOWN:
        return result
    # Fall back: look each token up in the typedef map
    for t in tokens:
        if t in tmap and tmap[t] != _SIGN_UNKNOWN:
            return tmap[t]
    return _SIGN_UNKNOWN


def _classify_arg(expr: str) -> str:
    """Classify one call-site argument expression."""
    e = expr.strip()
    if _RE_UINT_LIT.match(e)  or _RE_UINT_CAST.match(e): return _SIGN_UNSIGNED
    if _RE_SINT_CAST.match(e) or _RE_NEG_LIT.match(e):   return _SIGN_SIGNED
    if _RE_PLAIN_INT.match(e) or _RE_CHAR_LIT.match(e):  return _SIGN_NEUTRAL
    return _SIGN_UNKNOWN


def _extract_call_args(source: str, paren_pos: int):
    """
    Extract comma-separated argument strings from a function call starting
    at *paren_pos* (the position of '(').  Returns a list of strings or
    None if the call cannot be parsed.
    """
    if paren_pos >= len(source) or source[paren_pos] != "(":
        return None
    depth = 0
    buf: list = []
    parts: list = []
    i = paren_pos + 1
    while i < len(source):
        ch = source[i]
        if ch in "([":
            depth += 1; buf.append(ch)
        elif ch in ")]":
            if depth == 0:
                parts.append("".join(buf).strip())
                return parts
            depth -= 1; buf.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(buf).strip()); buf = []
        else:
            buf.append(ch)
        i += 1
    return None


class SignChecker:
    """
    Cross-file sign-compatibility checker.

    Usage:
        sc = SignChecker(cfg)
        for filepath, source in all_files:
            sc.ingest(filepath, source)
        violations = sc.check()
    """

    def __init__(self, cfg: dict):
        self._cfg       = cfg
        self._sources:  list = []   # (filepath, raw_source, clean_source)
        self._tmap:     dict = {}   # typedef_name -> sign string
        self._sigs:     dict = {}   # function_name -> _FuncSig
        self._built     = False

    def ingest(self, filepath: str, source: str) -> None:
        self._sources.append((filepath, source, preprocess(source)))

    def check(self) -> list:
        """Build type/signature tables then check every .c call site."""
        sc_cfg = self._cfg.get("sign_compatibility", {})
        if not sc_cfg.get("enabled", True):
            return []

        sev = sc_cfg.get("severity", "error")
        # Temporarily remove 'char' from the module-level signed-types set if
        # the project treats plain char as unsigned.  try/finally guarantees
        # the set is restored even if an exception occurs mid-run, so calling
        # check() multiple times (or from multiple tests) gives consistent results.
        _char_removed  = False
        _char_unsigned = False
        if not sc_cfg.get("plain_char_is_signed", True):
            if "char" in _SIGNED_TYPES:
                _SIGNED_TYPES.discard("char")
                _char_removed = True
            if "char" not in _UNSIGNED_TYPES:
                _UNSIGNED_TYPES.add("char")
                _char_unsigned = True
        try:
            self._build_typedef_map()
            self._build_signatures()
            return self._check_calls(sev)
        finally:
            if _char_removed:
                _SIGNED_TYPES.add("char")
            if _char_unsigned:
                _UNSIGNED_TYPES.discard("char")

    # --- Stage 1: typedef resolution ---

    def _build_typedef_map(self) -> None:
        raw: dict = {}
        pattern = re.compile(
            r"\btypedef\b"
            r"((?:[ \t]+(?:const|volatile|signed|unsigned|long|short"
            r"|int|char|float|double|\w+))+)"
            r"[ \t]+(\w+)\s*;",
        )
        for _fp, _src, clean in self._sources:
            for m in pattern.finditer(clean):
                tokens = m.group(1).split()
                name   = m.group(2)
                # Skip if name looks like a pointer typedef (handled elsewhere)
                if "*" not in m.group(0):
                    raw[name] = tokens

        resolved: dict = {}

        def resolve(name: str, depth: int = 0) -> str:
            if name in resolved:
                return resolved[name]
            if depth > 8 or name not in raw:
                return _SIGN_UNKNOWN
            tokens   = raw[name]
            non_qual = [t for t in tokens
                        if t not in ("const", "volatile", "restrict")]
            if len(non_qual) == 1 and non_qual[0] in raw:
                result = resolve(non_qual[0], depth + 1)
            else:
                result = _classify_tokens(tokens)
            resolved[name] = result
            return result

        for n in raw:
            resolve(n)
        self._tmap = resolved

    # --- Stage 2: function signature extraction ---

    def _build_signatures(self) -> None:
        pattern_decl  = re.compile(
            r"(?:^|\n)[ \t]*"
            r"(?:(?:extern|static|inline|const|volatile)[ \t]+)*"
            r"(?:(?:unsigned|signed)[ \t]+)?"
            r"(?:(?:long[ \t]+long|long|short)[ \t]+)?"
            r"\w+[ \t]*\*?[ \t]*"
            r"([A-Za-z_]\w*)"
            r"[ \t]*\(([^)]*)\)"
            r"[ \t]*;",
            re.MULTILINE,
        )
        pattern_param = re.compile(
            r"((?:(?:const|volatile|signed|unsigned|long|short|int|char"
            r"|float|double|bool|_Bool|uint\w*|int\w*|sint\w*|size_t"
            r"|[A-Za-z_]\w*)[ \t]+)+)"
            r"\*?[ \t]*"
            r"([A-Za-z_]\w*)"
            r"[ \t]*(?:,|$|\[)",
        )

        for fp, _src, clean in self._sources:
            # Parse declarations from both .h and .c (extern declarations)
            for m in pattern_decl.finditer(clean):
                fname = m.group(1)
                plist = m.group(2).strip()
                if plist in ("void", ""):
                    self._sigs[fname] = _FuncSig(fname, [])
                    continue
                params = []
                for pm in pattern_param.finditer(plist + ","):
                    type_str = pm.group(1).strip()
                    pname    = pm.group(2)
                    sign     = _signedness_of_type(type_str, self._tmap)
                    params.append(_ParamSig(pname, type_str, sign))
                # Prefer the first (header) declaration if already seen
                if fname not in self._sigs:
                    self._sigs[fname] = _FuncSig(fname, params)

    # --- Stage 3: call-site sign checking ---

    def _check_calls(self, sev: str) -> list:
        call_re = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
        violations: list = []

        for filepath, _src, clean in self._sources:
            # Only check .c files for call sites
            if not filepath.endswith(".c"):
                continue
            line_map = build_line_map(clean)

            for cm in call_re.finditer(clean):
                fn_name = cm.group(1)
                if fn_name not in self._sigs:
                    continue
                sig = self._sigs[fn_name]
                if not sig.params:
                    continue

                args = _extract_call_args(clean, cm.end() - 1)
                if not args:
                    continue

                for idx, (arg, param) in enumerate(zip(args, sig.params)):
                    arg_sign = _classify_arg(arg)
                    if arg_sign in (_SIGN_UNKNOWN, _SIGN_NEUTRAL):
                        continue
                    if param.signedness == _SIGN_UNKNOWN:
                        continue
                    if arg_sign != param.signedness:
                        line, col = offset_to_line_col(line_map, cm.start())
                        violations.append(Violation(
                            filepath, line, col, sev,
                            "sign_compatibility",
                            f"Argument {idx + 1} '{arg.strip()}' is "
                            f"{arg_sign} but parameter '{param.name}' "
                            f"('{param.type_str}') expects {param.signedness}; "
                            f"call to '{fn_name}'",
                        ))
        return violations


# ---------------------------------------------------------------------------
# Module-prefix stripping helper (used in variable checks)
# ---------------------------------------------------------------------------

def _strip_module_prefix(name: str, prefix: str) -> str:
    """Return *name* with the module prefix removed (case-insensitive)."""
    if name.lower().startswith(prefix.lower()):
        return name[len(prefix):]
    return name


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def _path_matches_exclude(filepath: str, exclude_globs: list) -> bool:
    """
    Return True when *filepath* is covered by any entry in *exclude_globs*.

    Correctly handles two categories of exclude pattern:

    Whole-subtree patterns (prune entire directory tree):
      source/cots/           trailing slash
      source/cots/**         recursive glob
      source/cots/**/*.*     deep wildcard
      source/cots/**/*.c     extension-filtered subtree

    Specific-file patterns (match only named files):
      **/sdk_config.h        named file anywhere under a directory
      *.pb.h                 filename glob
      sdk_config.h           exact filename
      cots                   bare directory name in any path segment
    """
    p = filepath.replace("\\", "/")

    for raw_pat in exclude_globs:
        pat = raw_pat.replace("\\", "/")

        # ── Trailing slash: everything under this directory ──────────────────
        if pat.endswith("/"):
            dir_pfx = pat.rstrip("/")
            if p == dir_pfx or p.startswith(dir_pfx + "/"):
                return True
            if ("/" + dir_pfx + "/") in ("/" + p + "/"):
                return True
            continue

        # ── Classify the pattern as subtree vs specific-file ────────────────
        # A whole-subtree pattern ends with /**, or its final segment is a
        # pure wildcard with no specific filename (*, *.*, **).
        # A specific-file pattern has a concrete filename after the last /.
        _last_seg = pat.rsplit("/", 1)[-1] if "/" in pat else pat
        _is_subtree = (
            pat.endswith("/**")
            or _last_seg in ("*", "*.*", "**")
            or (_last_seg.startswith("*") and "." not in _last_seg)
        )

        if _is_subtree:
            # Use the fixed prefix (before first wildcard) for directory pruning
            _first_wild = len(pat)
            for _wc in ("*", "?", "["):
                _wi = pat.find(_wc)
                if 0 <= _wi < _first_wild:
                    _first_wild = _wi
            _dir_pfx = pat[:_first_wild].rstrip("/")
            if _dir_pfx:
                if p == _dir_pfx or p.startswith(_dir_pfx + "/"):
                    return True
                if "/" not in _dir_pfx:
                    if ("/" + _dir_pfx + "/") in ("/" + p + "/"):
                        return True
                    if p.startswith(_dir_pfx + "/"):
                        return True
            continue

        # ── Specific-file pattern: fnmatch ───────────────────────────────────
        if fnmatch.fnmatch(p, pat):
            return True
        # Also match just the filename (e.g. "sdk_config.h" or "*.pb.h")
        if fnmatch.fnmatch(os.path.basename(p), _last_seg):
            return True
        # Bare name with no slashes or wildcards: match any path segment
        if "/" not in pat and not any(c in pat for c in "*?["):
            if ("/" + pat + "/") in ("/" + p + "/") or p.startswith(pat + "/"):
                return True

    return False

def discover_files(
    explicit: list,
    include_globs: list,
    exclude_globs: list,
    ignore_cfg: dict,
) -> Generator:
    ignore_paths = ignore_cfg.get("paths", [])
    ignore_files = ignore_cfg.get("files", [])

    def is_ignored(p: str) -> bool:
        # Check CLI --exclude globs first
        if _path_matches_exclude(p, exclude_globs):
            return True
        name = os.path.basename(p)
        for pat in ignore_files:
            if fnmatch.fnmatch(name, pat):
                return True
        for pat in ignore_paths:
            if fnmatch.fnmatch(p, pat) or fnmatch.fnmatch(
                    p.replace("\\", "/"), pat):
                return True
        return False

    seen: set = set()

    def emit(p: str):
        # os.path.abspath() is pure string arithmetic (no stat call).
        # Path.resolve() makes a stat() syscall per file — on Docker
        # network mounts that costs ~100 ms per call and causes a
        # silent delay that looks like a hang.
        abs_p = os.path.abspath(p)
        if abs_p not in seen and not is_ignored(p):
            seen.add(abs_p)
            yield p

    for f in explicit:
        yield from emit(f)

    for pattern in include_globs:
        # Use glob for simple patterns; fall back to os.walk for
        # recursive (**) patterns which block until fully expanded.
        if "**" in pattern:
            # Split at the ** and walk from the base directory
            parts = pattern.replace("\\", "/").split("**")
            base  = parts[0].rstrip("/") or "."
            tail  = parts[-1].lstrip("/")
            for root, _dirs, fnames in os.walk(base):
                # Prune excluded directories so os.walk does not
                # descend into them.  This is critical when an exclude
                # path (e.g. /repo/source/cots/) contains thousands of
                # subdirectories — without pruning, os.walk visits every
                # one and emit() runs is_ignored() on every file inside,
                # causing the silent delay the user observes.
                _dirs[:] = [
                    d for d in _dirs
                    if not _path_matches_exclude(
                        os.path.join(root, d), exclude_globs
                    )
                ]
                # Also skip the root directory itself if excluded
                if _path_matches_exclude(root, exclude_globs):
                    continue
                for fname in fnames:
                    if fname.endswith((".c", ".h")):
                        if not tail or fnmatch.fnmatch(fname, tail):
                            yield from emit(os.path.join(root, fname))
        else:
            for f in glob_mod.glob(pattern, recursive=True):
                if f.endswith((".c", ".h")):
                    yield from emit(f)


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
    from collections import OrderedDict

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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = _build_parser()
    return p.parse_args()


def _build_parser() -> argparse.ArgumentParser:
    """Return the fully configured ArgumentParser (used by both parse_args and --help)."""
    p = argparse.ArgumentParser(
        prog=_TOOL_NAME,
        description=(
            "Embedded C Style Compliance Checker for GitHub Actions / pre-commit.\n"
            f"Version: {_VERSION_STRING}\n\n"
            "Checks source files against a configurable YAML rule set and reports\n"
            "violations with file, line, and column information.  Optionally emits\n"
            "GitHub Actions inline annotations (--github-actions) and records a\n"
            "machine-readable log (--log).\n\n"
            "Selected rule highlights:\n"
            "  misc.copyright_header  File must begin with the copyright block comment\n"
            "                         template (--copyright FILE); year may differ.\n"
            "  misc.eof_comment       Last non-blank line must be '/* EOF: filename */'\n"
            "                         followed by exactly one blank line.\n\n"
            "Exit codes:\n"
            "  0  Clean — no violations (or --version/--help)\n"
            "  1  One or more errors found\n"
            "  2  Configuration or invocation error"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,   # we add our own so we can guarantee exit code 0
    )
    # --- Help and version (always exit 0) ---
    p.add_argument("-h", "--help", action="store_true",
                   help="Show this help message and exit (exit code 0)")
    p.add_argument("--version", action="store_true",
                   help=f"Print '{_VERSION_STRING}' and exit (exit code 0)")
    p.add_argument("--verbose", action="store_true",
                   help="Show the directory being scanned — useful for "
                        "large filesets so the tool does not appear to hang")
    # --- Positional ---
    p.add_argument("files", nargs="*",
                   help="C source / header files to check")
    p.add_argument("--config", default="cstylecheck_rules.yaml",
                   help="YAML config file (default: cstylecheck_rules.yaml)")
    p.add_argument("--github-actions", action="store_true",
                   help="Emit ::error/::warning GitHub Actions annotations")
    p.add_argument("--output-format", choices=["text", "json", "sarif"],
                   default="text",
                   help="Output format: text (default), json, or sarif. "
                        "json and sarif write to --log if given, else stdout. "
                        "Implies --exit-zero is unaffected.")
    p.add_argument("--summary", action="store_true",
                   help="Print summary table after all files are checked")
    p.add_argument("--baseline-file", metavar="FILE",
                   help="JSON baseline file produced by --write-baseline. "
                        "Violations present in the baseline are suppressed "
                        "so that CI only fails on new violations.")
    p.add_argument("--write-baseline", metavar="FILE",
                   help="Write all current violations to FILE as a JSON "
                        "baseline and exit 0. Use once on an existing "
                        "codebase to silence legacy noise.")
    p.add_argument("--exit-zero", action="store_true",
                   help="Always exit 0 (useful for warning-only CI steps)")
    p.add_argument("--include", action="append", default=[],
                   metavar="GLOB",
                   help="Additional glob pattern(s) to scan (repeatable)")
    p.add_argument("--exclude", action="append", default=[],
                   metavar="GLOB",
                   help="Glob pattern(s) to exclude (repeatable)")
    p.add_argument("--log", metavar="FILE",
                   help="Write all output to FILE in addition to stdout")
    p.add_argument("--spell-words", metavar="FILE",
                   help="Plain-text file of project-specific words exempt from "
                        "spell-checking (one word per line, # = comment)")
    p.add_argument("--keywords-file", metavar="FILE",
                   help="Replace the built-in C keyword list "
                        "(default: src/c_keywords.txt)")
    p.add_argument("--stdlib-file", metavar="FILE",
                   help="Replace the built-in C stdlib name list "
                        "(default: src/c_stdlib_names.txt)")
    p.add_argument("--spell-dict", metavar="FILE",
                   help="Replace the built-in spell-check dictionary "
                        "(default: src/c_spell_dict.txt)")
    p.add_argument("--aliases", metavar="FILE",
                   help="Plain-text file mapping module alias prefixes to actual "
                        "module names.  Each line: 'alias_stem  actual_stem'. "
                        "Identifiers with the alias prefix are then accepted in "
                        "files whose stem is actual_stem.")
    p.add_argument("--cstylecheck_exclusions", metavar="FILE",
                   help="YAML file specifying per-file rule cstylecheck_exclusions.  Keys are "
                        "fnmatch patterns matched against the file basename; values "
                        "list rule IDs to disable for that file.")
    p.add_argument("--warnings-as-errors", action="store_true",
                   help="Promote all warnings (and info) to errors regardless of "
                        "severity assigned in the config.  The exit code becomes 1 "
                        "if any violation exists, not just errors.")
    p.add_argument("--options-file", metavar="FILE",
                   help="Read additional command-line options from FILE (one "
                        "option per line, shell quoting supported, # = comment). "
                        "Options in FILE are applied before any options that "
                        "follow this flag on the command line, so explicit "
                        "arguments always take priority.")
    p.add_argument("--defines", metavar="FILE",
                   help="Plain-text file of project macro/type definitions used "
                        "to expand tokens before analysis. Each line: "
                        "'TOKEN  expansion'  e.g. 'STATIC static' or "
                        "'uint8_t unsigned char'. Applied after comment "
                        "stripping so comment content is never substituted.")
    p.add_argument("--banned-names", metavar="FILE",
                   help="Plain-text file of additional identifier names that "
                        "must not be used in any source file (one name per "
                        "line, # = comment). Added to the built-in C keyword "
                        "and C stdlib name lists. Per-file exceptions are "
                        "handled via --cstylecheck_exclusions (disable reserved_name rule).")
    p.add_argument("--copyright", metavar="FILE",
                   help="Plain-text file containing the copyright block "
                        "comment template that must appear at the top of "
                        "every C source file, followed by exactly one blank "
                        "line.  The template is matched exactly except that "
                        "the year on the '(C) Copyright YEAR' line may "
                        "differ (any 4-digit year or YYYY-YYYY range is "
                        "accepted).  Enables the misc.copyright_header rule.")
    return p


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    # Fast-path: --version and --help must work even if every other arg is
    # broken, so check for them before options-file expansion or config loading.
    raw_argv = sys.argv[1:]
    if "--version" in raw_argv:
        print(_VERSION_STRING)
        return 0
    if "-h" in raw_argv or "--help" in raw_argv:
        # Re-parse with a temporary parser just to print help, then exit 0
        _tmp = argparse.ArgumentParser(
            prog=_TOOL_NAME,
            description=parse_args.__doc__ or "",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=False,
        )
        # Reconstruct args list from parse_args so help text is complete
        _real_parser = _build_parser()
        _real_parser.print_help()
        return 0

    # Expand --options-file tokens into sys.argv before parsing.
    # This must happen before parse_args() so that every option in the
    # file is visible to argparse as if it had been typed on the command line.
    sys.argv[1:] = _expand_options_file(sys.argv[1:])
    args = parse_args()
    # Handle --help/--version that appeared inside an options file
    if getattr(args, "help", False):
        _build_parser().print_help()
        return 0
    if getattr(args, "version", False):
        print(_VERSION_STRING)
        return 0
    cfg  = load_config(args.config)

    # Spell-check word set — None means the check is entirely disabled
    # Override dictionary files from CLI if provided
    global C_KEYWORDS, C_STDLIB_NAMES, _BUILTIN_DICT
    if getattr(args, "keywords_file", None):
        C_KEYWORDS = _load_dict_file(args.keywords_file)
    if getattr(args, "stdlib_file", None):
        C_STDLIB_NAMES = _load_dict_file(args.stdlib_file)
    spell_base = None
    if getattr(args, "spell_dict", None):
        spell_base = _load_dict_file(args.spell_dict)
        _BUILTIN_DICT = spell_base

    spell_words = None
    sp_cfg = cfg.get("spell_check", {})
    if sp_cfg.get("enabled", False):
        cfg_exempt  = sp_cfg.get("exempt_values", [])
        extra_words = load_spell_words(args.spell_words) if args.spell_words else set()
        spell_words = _build_spell_dict(cfg_exempt, extra_words, base_dict=spell_base)

    # Project defines map: list of (pattern, replacement) for token substitution
    defines: list = load_defines_file(args.defines) if args.defines else []

    # Extra banned identifier names (from --banned-names file)
    extra_banned: frozenset = (
        load_banned_names_file(getattr(args, 'banned_names'))
        if getattr(args, 'banned_names', None) else frozenset()
    )

    # Copyright header template (from --copyright file)
    copyright_header = (
        load_copyright_file(args.copyright)
        if getattr(args, 'copyright', None) else None
    )

    # Module alias map: {actual_stem_lower: [alias_stem_lower, ...]}
    alias_map: dict = load_alias_file(args.aliases) if args.aliases else {}

    # Per-file rule cstylecheck_exclusions: {basename_glob: frozenset_of_rule_ids}
    cstylecheck_exclusions_map: dict = (
        load_cstylecheck_exclusions_file(args.cstylecheck_exclusions) if args.cstylecheck_exclusions else {}
    )

    # Open optional log file
    log_fh = None
    if args.log:
        try:
            log_fh = open(args.log, "w", encoding="utf-8")
        except OSError as e:
            sys.exit(f"Cannot open log file '{args.log}': {e}")

    tee = Tee(log_fh)

    # Discover files
    # Discover files lazily — emit progress immediately rather than
    # blocking until the entire glob tree is walked.
    _vb_prev_dir = ""
    files: list = []
    for _fp in discover_files(
        args.files,
        args.include,
        args.exclude,
        cfg.get("ignore", {}),
    ):
        files.append(_fp)
        if getattr(args, "verbose", False):
            _msg = f"Discovering: {_fp}"
            print(f"{_msg:<79}", end="\r",
                  file=sys.stderr, flush=True)

    if not files:
        print("No C files to check.", file=sys.stderr)
        tee.close()
        return 2

    if getattr(args, "verbose", False):
        _n = len(files)
        _msg = f"Found {_n} file(s) - starting analysis..."
        print(f"{_msg:<79}", file=sys.stderr, flush=True)

    output_format  = getattr(args, "output_format", "text")
    all_violations: list = []
    _vb_prev_dir = ""
    # Cache source text keyed by filepath to avoid reading each file twice
    # (once for Checker, once for SignChecker).
    source_cache: dict = {}

    for filepath in files:
        if getattr(args, "verbose", False):
            _msg = f"Scanning: {filepath}"
            print(f"{_msg:<79}", end="\r",
                  file=sys.stderr, flush=True)
        try:
            source = Path(filepath).read_text(encoding="utf-8", errors="replace")
            source_cache[filepath] = source
        except OSError as e:
            tee.print(f"ERROR: Cannot read {filepath}: {e}")
            continue

        # Build accepted prefix list for this file (canonical + aliases)
        mod   = module_name(filepath)
        sep   = _cfg(cfg, "file_prefix", "separator", default="_")
        case  = _cfg(cfg, "file_prefix", "case", default="lower")
        canon = (mod.upper() if case == "upper" else mod.lower()) + sep
        alias_pfxs = [canon] + [
            a.lower() + sep for a in alias_map.get(mod.lower(), [])
        ]

        # Collect disabled rules for this specific file
        _file_disabled, _ident_disabled = _disabled_rules_for_file(filepath, cstylecheck_exclusions_map)

        checker = Checker(
            filepath, source, cfg,
            spell_words=spell_words,
            alias_prefixes=alias_pfxs,
            disabled_rules=_file_disabled,
            ident_disabled_rules=_ident_disabled,
            defines=defines,
            extra_banned=extra_banned,
            copyright_header=copyright_header,
        )
        result  = checker.run_all()
        all_violations.extend(result.violations)

        if output_format == "text":
            for v in sorted(result.violations, key=lambda x: (x.line, x.col)):
                if args.github_actions:
                    tee.print(v.github_annotation())
                else:
                    tee.print(v)

    if getattr(args, "verbose", False):
        print(" " * 80, end="\r",
              file=sys.stderr)  # erase last progress line
    # Cross-file sign-compatibility check (needs all files ingested first).
    # Uses the source cache so no file is read from disk a second time.
    sign_cfg = cfg.get("sign_compatibility", {})
    if sign_cfg.get("enabled", True):
        sc = SignChecker(cfg)
        for filepath in files:
            src = source_cache.get(filepath)
            if src is not None:
                sc.ingest(filepath, src)
        sign_violations = sc.check()
        all_violations.extend(sign_violations)
        if output_format == "text":
            for v in sorted(sign_violations, key=lambda x: (x.filepath, x.line, x.col)):
                if args.github_actions:
                    tee.print(v.github_annotation())
                else:
                    tee.print(v)

    # --write-baseline: dump all violations and exit 0 (no further checks).
    if getattr(args, "write_baseline", None):
        write_baseline(all_violations, args.write_baseline)
        tee.print(f"Baseline written to '{args.write_baseline}' "
                  f"({len(all_violations)} violation(s)).")
        tee.close()
        return 0

    # --baseline-file: suppress violations that match the saved baseline.
    if getattr(args, "baseline_file", None):
        baseline = load_baseline(args.baseline_file)
        before   = len(all_violations)
        all_violations = [
            v for v in all_violations
            if _baseline_key(v) not in baseline
        ]
        suppressed = before - len(all_violations)
        if suppressed and output_format == "text":
            tee.print(f"(Baseline suppressed {suppressed} known violation(s))")

    # --warnings-as-errors: promote every warning and info to error.
    # We do this AFTER collecting and printing all violations so that the
    # original severity is visible in the output, but the summary and exit
    # code reflect the promoted level.
    if getattr(args, "warnings_as_errors", False):
        for v in all_violations:
            if v.severity in ("warning", "info"):
                v.severity = "error"

    # --output-format json / sarif: emit structured output to stdout or --log.
    if output_format == "json":
        json_text = _violations_to_json(all_violations, len(files))
        tee.print(json_text)
    elif output_format == "sarif":
        sarif_text = _violations_to_sarif(all_violations, _VERSION)
        tee.print(sarif_text)

    if args.summary and output_format == "text":
        print_summary(all_violations, len(files), tee)

    tee.close()

    if args.exit_zero:
        return 0
    return 1 if any(v.severity == "error" for v in all_violations) else 0


if __name__ == "__main__":
    sys.exit(main())
