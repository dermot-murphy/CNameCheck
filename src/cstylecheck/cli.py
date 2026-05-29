"""
cli.py — CLI argument parsing and main() entry point for CStyleCheck.

Contains discover_files, _path_matches_exclude, parse_args,
_build_parser, and main.

Imports from: all submodules.
"""
from __future__ import annotations

import argparse
import fnmatch
import glob as glob_mod
import os
import sys
from pathlib import Path
from typing import Generator

from .config import (
    load_config, load_alias_file, load_exclusions_file,
    _disabled_rules_for_file, load_defines_file,
    load_banned_names_file, load_copyright_file, load_spell_words,
    _build_spell_dict, _load_dict_file, _expand_options_file,
    C_KEYWORDS, C_STDLIB_NAMES,
)
from .utils import module_name, _cfg
from .checker import Checker
from .sign_checker import SignChecker, DeclaredNotDefinedChecker
from .baseline import load_baseline, write_baseline, _baseline_key
from .output import Tee, _violations_to_json, _violations_to_sarif, print_summary
from . import _TOOL_NAME, _VERSION, _VERSION_STRING


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
    p.add_argument("--config", default="rules.yml",
                   help="YAML config file (default: rules.yml)")
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
    p.add_argument("--exclusions", metavar="FILE",
                   help="YAML file specifying per-file rule exclusions.  Keys are "
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
                        "handled via --exclusions (disable reserved_name rule).")
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
    # Build local overrides from CLI flags without mutating module-level globals
    # (mutating globals is not thread-safe — issue #79).
    keywords_set = (
        _load_dict_file(args.keywords_file)
        if getattr(args, "keywords_file", None) else C_KEYWORDS
    )
    stdlib_set = (
        _load_dict_file(args.stdlib_file)
        if getattr(args, "stdlib_file", None) else C_STDLIB_NAMES
    )
    spell_base = None
    if getattr(args, "spell_dict", None):
        spell_base = _load_dict_file(args.spell_dict)

    spell_words = None
    sp_cfg = cfg.get("spell_check", {})
    if sp_cfg.get("enabled", False):
        cfg_exempt  = sp_cfg.get("exempt_values", [])
        extra_words = load_spell_words(args.spell_words) if args.spell_words else set()
        spell_words = _build_spell_dict(cfg_exempt, extra_words, base_dict=spell_base)
    elif getattr(args, "spell_words", None):
        # spell_check is disabled but the user passed --spell-words; warn rather
        # than silently discarding the file (issue #90).
        print(
            f"WARNING: --spell-words '{args.spell_words}' supplied but "
            "spell_check.enabled is false in config — words file ignored.",
            file=sys.stderr,
        )

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

    # Per-file rule exclusions: {basename_glob: frozenset_of_rule_ids}
    exclusions_map: dict = (
        load_exclusions_file(args.exclusions) if args.exclusions else {}
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
    files: list = []
    for _fp in discover_files(
        args.files,
        args.include,
        args.exclude,
        cfg.get("ignore", {}),
    ):
        files.append(_fp)
        if getattr(args, "verbose", False) and sys.stderr.isatty():
            _msg = f"Discovering: {_fp}"
            print(f"{_msg:<79}", end="\r",
                  file=sys.stderr, flush=True)

    if not files:
        print("No C files to check.", file=sys.stderr)
        tee.close()
        return 0

    if getattr(args, "verbose", False):
        _n = len(files)
        _msg = f"Found {_n} file(s) - starting analysis..."
        print(f"{_msg:<79}", file=sys.stderr, flush=True)

    output_format  = getattr(args, "output_format", "text")
    all_violations: list = []
    # Cache source text keyed by filepath to avoid reading each file twice
    # (once for Checker, once for SignChecker).
    source_cache: dict = {}

    for filepath in files:
        if getattr(args, "verbose", False):
            _msg = f"Scanning: {filepath}"
            if sys.stderr.isatty():
                print(f"{_msg:<79}", end="\r", file=sys.stderr, flush=True)
            else:
                print(_msg, file=sys.stderr, flush=True)
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
        _file_disabled, _ident_disabled = _disabled_rules_for_file(filepath, exclusions_map)

        checker = Checker(
            filepath, source, cfg,
            spell_words=spell_words,
            alias_prefixes=alias_pfxs,
            disabled_rules=_file_disabled,
            ident_disabled_rules=_ident_disabled,
            defines=defines,
            extra_banned=extra_banned,
            copyright_header=copyright_header,
            c_keywords=keywords_set,
            c_stdlib_names=stdlib_set,
        )
        result  = checker.run_all()
        all_violations.extend(result.violations)

        if output_format == "text":
            for v in sorted(result.violations, key=lambda x: (x.line, x.col)):
                if args.github_actions:
                    tee.print(v.github_annotation())
                else:
                    tee.print(v)

    if getattr(args, "verbose", False) and sys.stderr.isatty():
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

    # Cross-file declared-but-not-defined check (needs all files ingested first).
    dnd_cfg = cfg.get("misc", {}).get("declared_not_defined", {})
    if dnd_cfg.get("enabled", False):
        dndc = DeclaredNotDefinedChecker(cfg, defines=defines)
        for filepath in files:
            src = source_cache.get(filepath)
            if src is not None:
                dndc.ingest(filepath, src)
        dnd_violations = dndc.check()
        all_violations.extend(dnd_violations)
        if output_format == "text":
            for v in sorted(dnd_violations, key=lambda x: (x.filepath, x.line, x.col)):
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
    try:
        sys.exit(main())
    except SystemExit as _e:
        # sys.exit("message") uses a string code → exit 1 by default.
        # Re-emit as exit 2 so callers can distinguish config errors (2)
        # from naming violations (1) and clean runs (0).
        if isinstance(_e.code, str):
            print(_e.code, file=sys.stderr)
            sys.exit(2)
        raise
