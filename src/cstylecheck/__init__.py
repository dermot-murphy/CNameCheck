"""
cstylecheck — Embedded C Style Compliance Checker.

This package exposes the full public API that was previously available
as top-level names in the monolithic ``cstylecheck.py`` module.
All names are re-exported here for backward compatibility so that:
  - ``import cstylecheck as _mod; _mod.Checker`` still works
  - The CLI entry point ``cstylecheck = "cstylecheck:main"`` still works
  - ``from _version import __version__`` is still attempted
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------
_TOOL_NAME = "CStyleCheck"

try:
    from _version import __version__ as _VERSION
except ImportError:
    try:
        from importlib.metadata import version as _pkg_version
        _VERSION = _pkg_version("cstylecheck")
    except Exception:
        _VERSION = "0.0.0.dev"

_VERSION_STRING = f"{_TOOL_NAME} {_VERSION}"

# ---------------------------------------------------------------------------
# Re-export everything from sub-modules (public API)
# ---------------------------------------------------------------------------

from .models import (                    # noqa: F401, E402
    Violation,
    CheckResult,
    _ParamSig,
    _FuncSig,
    _MISRA_ANNOTATION_RULES,
    _NAMING_ANNOTATION_PREFIXES,
    _SIGN_SIGNED,
    _SIGN_UNSIGNED,
    _SIGN_UNKNOWN,
    _SIGN_NEUTRAL,
    _SIGNED_TYPES,
    _UNSIGNED_TYPES,
)

from .preprocessor import (              # noqa: F401, E402
    strip_comments,
    strip_strings,
    preprocess,
    build_line_map,
    offset_to_line_col,
    _build_brace_depths,
    _comment_only_lines,
    extract_comments,
)

from .utils import (                     # noqa: F401, E402
    matches_case,
    matches_case_abbrev,
    to_case,
    module_name,
    is_exempt,
    _cfg,
    _strip_module_prefix,
    _github_annotation_category,
    _CASE_PATTERNS,
)

from .config import (                    # noqa: F401, E402
    _read_options_file,
    _expand_options_file,
    load_config,
    load_spell_words,
    load_alias_file,
    load_exclusions_file,
    _disabled_rules_for_file,
    load_defines_file,
    apply_defines,
    _load_dict_file,
    _data_file,
    load_banned_names_file,
    load_copyright_file,
    _build_spell_dict,
    _BUILTIN_DICT,
    C_KEYWORDS,
    C_STDLIB_NAMES,
    _COPYRIGHT_YEAR_RE,
    _COPYRIGHT_YEAR_FLEX,
    _DEFAULT_KEYWORDS_FILE,
    _DEFAULT_STDLIB_FILE,
    _DEFAULT_SPELL_DICT,
)

from .checker import (                   # noqa: F401, E402
    Checker,
    RE_DEFINE,
    RE_TYPEDEF_ENUM,
    RE_TYPEDEF_STRUCT,
    RE_TYPEDEF_SIMPLE,
    RE_FUNCTION_DEF,
    RE_FUNCTION_DECL,
    RE_VAR_DECL,
    RE_FUNCTION_PARAM,
    RE_INCLUDE_GUARD_IFNDEF,
    RE_INCLUDE_GUARD_DEFINE,
    RE_PRAGMA_ONCE,
    RE_MAGIC_NUMBER,
    RE_ARRAY_INDEX,
    RE_ENUM_MEMBER,
    RE_COMMENT_WORD,
)

from .sign_checker import (              # noqa: F401, E402
    SignChecker,
    DeclaredNotDefinedChecker,
    _classify_tokens,
    _signedness_of_type,
    _classify_arg,
    _extract_call_args,
)

from .baseline import (                  # noqa: F401, E402
    _baseline_key,
    load_baseline,
    write_baseline,
)

from .output import (                    # noqa: F401, E402
    Tee,
    _violations_to_json,
    _violations_to_sarif,
    print_summary,
)

from .cli import (                       # noqa: F401, E402
    discover_files,
    _path_matches_exclude,
    parse_args,
    _build_parser,
    main,
)
