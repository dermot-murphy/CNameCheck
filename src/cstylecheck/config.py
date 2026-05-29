"""
config.py — Configuration and file-loading utilities for CStyleCheck.

Contains load_config, load_alias_file, load_exclusions_file,
_disabled_rules_for_file, load_defines_file, apply_defines,
_load_dict_file, _data_file, load_banned_names_file,
load_copyright_file, load_spell_words, _build_spell_dict,
_read_options_file, _expand_options_file, and _BUILTIN_DICT.

Imports from: preprocessor, utils, models (stdlib + pyyaml).
"""
from __future__ import annotations

import fnmatch
import re
import shlex
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")


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
            --config tools/cstylecheck/rules.yml
        or split with an = sign (standard CLI syntax):
            --config=tools/cstylecheck/rules.yml
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

def _find_default_rules() -> Path:
    """
    Locate the bundled ``src/rules.yml`` default configuration file.

    Lookup order:
    1. ``src/rules.yml`` in the source tree (source checkout / editable install).
    2. Alongside this module's package directory.
    3. ``{data_dir}/share/cstylecheck/rules.yml`` (pip install).
    """
    # Source checkout: src/cstylecheck/../rules.yml → src/rules.yml
    candidate = _HERE.parent / "rules.yml"
    if candidate.exists():
        return candidate
    # Alongside the package
    candidate2 = _HERE / "rules.yml"
    if candidate2.exists():
        return candidate2
    import sysconfig as _sysconfig
    return Path(_sysconfig.get_path("data")) / "share" / "cstylecheck" / "rules.yml"


def _deep_merge(base: dict, override: dict) -> dict:
    """
    Return a new dict that deep-merges *override* on top of *base*.

    Rules:
      - Keys present in *override* take priority.
      - Keys present only in *base* are kept (these are default values missing
        from the user's config — they will be added).
      - When both dicts have the same key and both values are dicts, merge
        recursively.  All other types use the *override* value.

    This is intentionally a pure function (no side effects on the inputs).
    """
    result = dict(base)
    for key, override_val in override.items():
        if key in result and isinstance(result[key], dict) \
                and isinstance(override_val, dict):
            result[key] = _deep_merge(result[key], override_val)
        else:
            result[key] = override_val
    return result


def _collect_paths(d: dict, prefix: str = "") -> list:
    """Return a sorted list of dotted key-paths present in *d*."""
    paths: list = []
    for k, v in d.items():
        full = f"{prefix}.{k}" if prefix else k
        paths.append(full)
        if isinstance(v, dict):
            paths.extend(_collect_paths(v, full))
    return sorted(paths)


def update_config(config_path: str) -> int:
    """
    Merge new default keys into an existing ``rules.yml`` file.

    This function implements the ``--update-config`` CLI flag.  It:

    1. Loads the user's current config from *config_path*.
    2. Loads the bundled default ``rules.yml``.
    3. Deep-merges the default **into** the user's config (user values win;
       keys missing from the user's file are added with default values).
    4. Warns about top-level keys in the user's config that are not in the
       default (may indicate renamed/removed settings).
    5. Writes the merged YAML back to *config_path* (overwrites in-place).
    6. Prints a human-readable change summary to stdout.

    Returns 0 on success, 2 on error (suitable for ``sys.exit``).

    .. note::
        YAML comments are **not** preserved — this is a limitation of
        ``yaml.safe_load`` / ``yaml.dump``.  Keep your original file in
        version control so you can diff and restore comments manually.
    """
    cfg_path = Path(config_path)
    if not cfg_path.exists():
        print(f"ERROR: Config file not found: {config_path}", file=sys.stderr)
        return 2

    # Load user config
    try:
        raw = cfg_path.read_bytes()
    except OSError as e:
        print(f"ERROR: Cannot read '{config_path}': {e}", file=sys.stderr)
        return 2
    try:
        user_cfg = yaml.safe_load(raw.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as e:
        print(f"ERROR: Cannot parse '{config_path}': {e}", file=sys.stderr)
        return 2
    if not isinstance(user_cfg, dict):
        print(f"ERROR: '{config_path}' does not contain a YAML mapping.",
              file=sys.stderr)
        return 2

    # Load bundled default
    default_path = _find_default_rules()
    if not default_path.exists():
        print(
            f"ERROR: Bundled default rules.yml not found at '{default_path}'.\n"
            "       Run from a source checkout or install via pip.",
            file=sys.stderr,
        )
        return 2
    try:
        default_cfg = yaml.safe_load(default_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        print(f"ERROR: Cannot read default rules: {e}", file=sys.stderr)
        return 2
    if not isinstance(default_cfg, dict):
        print("ERROR: Bundled rules.yml is not a YAML mapping.", file=sys.stderr)
        return 2

    # Compute what is new (in default but not in user)
    user_paths    = set(_collect_paths(user_cfg))
    default_paths = set(_collect_paths(default_cfg))
    added   = sorted(default_paths - user_paths)
    unknown = sorted(user_paths    - default_paths)

    # Deep-merge: default as the base, user values override
    merged = _deep_merge(default_cfg, user_cfg)

    # Serialise and write back
    try:
        out_text = yaml.dump(
            merged,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=True,
            width=120,
        )
        cfg_path.write_text(out_text, encoding="utf-8")
    except OSError as e:
        print(f"ERROR: Cannot write '{config_path}': {e}", file=sys.stderr)
        return 2

    # Summary
    print(f"Updated '{config_path}'")
    if added:
        print(f"  Added {len(added)} new key(s) from current defaults:")
        for p in added:
            print(f"    + {p}")
    else:
        print("  No new keys to add — config is already up to date.")
    if unknown:
        print(f"  WARNING: {len(unknown)} key(s) in your config not found in defaults")
        print("           (may be renamed or removed settings — review manually):")
        for p in unknown:
            print(f"    ? {p}")
    print(
        "\n  NOTE: YAML comments were not preserved.  Restore them from version control."
    )
    return 0


def load_config(path: str) -> dict:
    cfg_path = Path(path)
    if not cfg_path.exists():
        sys.exit(f"Config file not found: {path}")
    try:
        with cfg_path.open(encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except yaml.YAMLError as e:
        sys.exit(f"Cannot parse config file '{path}': {e}")


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
    separated words in either column order::

        alias_stem   actual_module_stem
        actual_module_stem   alias_stem

    Returns dict: {stem_lower -> [other_stem_lower, ...]}, registered
    bidirectionally so that either column order in the file is accepted.

    Example line::
        api_param  api_param_cfg

    → when checking api_param_cfg.c the prefix api_param_ is also accepted,
      and when checking api_param.c the prefix api_param_cfg_ is also accepted.
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
        stem_a, stem_b = parts[0].lower(), parts[1].lower()
        # Register bidirectionally so either column order is accepted.
        if stem_b not in aliases.get(stem_a, []):
            aliases.setdefault(stem_a, []).append(stem_b)
        if stem_a not in aliases.get(stem_b, []):
            aliases.setdefault(stem_b, []).append(stem_a)
    return aliases


# ---------------------------------------------------------------------------
# Per-file rule exclusions loader  (--exclusions)
# ---------------------------------------------------------------------------

def load_exclusions_file(path: str) -> dict:
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
        sys.exit(f"Cannot read exclusions file '{path}': {e}")
    if not isinstance(data, dict):
        return {}
    result: dict = {}
    for pattern, body in data.items():
        if not isinstance(body, dict):
            continue
        rules = body.get("disabled_rules", [])
        file_rules = frozenset(str(r) for r in rules) if isinstance(rules, list) else frozenset()
        # Per-identifier exclusions
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


def _disabled_rules_for_file(filepath: str, exclusions: dict) -> tuple:
    """
    Return (file_disabled, ident_disabled) where:
      file_disabled  frozenset of rule IDs disabled for the whole file.
      ident_disabled dict {identifier -> frozenset of rule IDs}.
    """
    basename = Path(filepath).name
    file_disabled: set = set()
    ident_disabled: dict = {}
    for pattern, body in exclusions.items():
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


# Default dictionary file paths (resolved relative to this package).
# Override any of these with the corresponding CLI flag.
_HERE = Path(__file__).resolve().parent


def _data_file(name: str) -> Path:
    """
    Resolve the path to a bundled data file.

    Lookup order
    ------------
    1. Alongside the package directory (source checkout, editable install,
       pre-commit clone).  This is the common case for development and CI.
    2. ``{data_dir}/share/cstylecheck/`` — the location used when the package
       is installed with ``pip install .`` via the ``data_files`` entry in
       ``pyproject.toml``.  ``data_dir`` is resolved via
       ``sysconfig.get_path("data")`` so that the lookup is correct for venvs,
       conda environments, system installs, and user installs alike.

    ``_load_dict_file`` handles ``FileNotFoundError`` gracefully (returns an
    empty frozenset), so callers are always safe even if neither path exists.
    """
    # Try alongside the package first (src/cstylecheck/../ = src/)
    candidate = _HERE.parent / name
    if candidate.exists():
        return candidate
    # Try alongside the package itself
    candidate2 = _HERE / name
    if candidate2.exists():
        return candidate2
    import sysconfig as _sysconfig
    return Path(_sysconfig.get_path("data")) / "share" / "cstylecheck" / name


_DEFAULT_KEYWORDS_FILE  = _data_file("c_keywords.txt")
_DEFAULT_STDLIB_FILE    = _data_file("c_stdlib_names.txt")
_DEFAULT_SPELL_DICT     = _data_file("c_spell_dict.txt")

C_KEYWORDS:    frozenset = _load_dict_file(_DEFAULT_KEYWORDS_FILE)    # type: ignore[arg-type]
C_STDLIB_NAMES: frozenset = _load_dict_file(_DEFAULT_STDLIB_FILE)   # type: ignore[arg-type]


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
    r'(\(C\)\s+copyright\s+)(\d{4}(?:[-–]\d{4})?)',
    re.IGNORECASE,
)

# Matches any year or year-range in the source file's copyright line.
_COPYRIGHT_YEAR_FLEX = r'\d{4}(?:[-–]\d{4})?'


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
# Built-in spell-check word list
# ---------------------------------------------------------------------------

_BUILTIN_DICT: frozenset = _load_dict_file(_DEFAULT_SPELL_DICT)     # type: ignore[arg-type]


def _build_spell_dict(cfg_exempt: list, extra_words: set,
                       base_dict=None) -> set:
    combined = set(base_dict if base_dict is not None else _BUILTIN_DICT)
    combined.update(w.lower() for w in cfg_exempt)
    combined.update(w.lower() for w in extra_words)
    return combined
