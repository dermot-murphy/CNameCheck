"""
conftest.py / harness.py
========================
Shared test infrastructure for CStyleCheck tests.

Import from any test file:
    from harness import Checker, run, rules, count, messages, CFG
"""

import sys
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Locate checker
# ---------------------------------------------------------------------------
# Checker lives in src/ which is a sibling of tests/
# Layout:  repo-root/src/cnamecheck.py
#          repo-root/tests/harness.py
_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(_SRC_DIR))

import cnamecheck as _mod  # noqa: E402

Checker   = _mod.Checker
Violation = _mod.Violation
load_defines_file       = _mod.load_defines_file
load_copyright_file     = _mod.load_copyright_file
_build_spell_dict       = _mod._build_spell_dict
_BUILTIN_DICT           = _mod._BUILTIN_DICT
_load_dict_file         = _mod._load_dict_file
SignChecker             = _mod.SignChecker


# ---------------------------------------------------------------------------
# Config builders
# ---------------------------------------------------------------------------

_ALL_OFF: dict = {
    "file_prefix":    {"enabled": False},
    "variables":      {"enabled": False},
    "functions":      {"enabled": False},
    "typedefs":       {"enabled": False},
    "enums":          {"enabled": False},
    "structs":        {"enabled": False},
    "include_guards": {"enabled": False},
    "misc": {
        "line_length":           {"enabled": False},
        "indentation":           {"enabled": False},
        "magic_numbers":         {"enabled": False},
        "unsigned_suffix":       {"enabled": False},
        "block_comment_spacing": {"enabled": False},
        "copyright_header":      {"enabled": False},
        "eof_comment":           {"enabled": False},
        "yoda_conditions":       {"enabled": False},
    },
    "reserved_names":    {"enabled": False},
    "sign_compatibility":{"enabled": False},
    "spell_check":       {"enabled": False},
}


def cfg_only(**overrides) -> dict:
    """
    Return a config where every rule is disabled except those in *overrides*.
    Deep-merges the 'misc' sub-dict.
    """
    import copy
    base = copy.deepcopy(_ALL_OFF)
    for k, v in overrides.items():
        if k == "misc":
            base["misc"].update(v)
        else:
            base[k] = v
    return base


# ---------------------------------------------------------------------------
# Runner helpers
# ---------------------------------------------------------------------------

def run(source: str,
        cfg: dict,
        filepath: str = "test_module.c",
        spell_words=None,
        alias_prefixes: list = None,
        disabled_rules: frozenset = frozenset(),
        defines: list = None,
        extra_banned: frozenset = frozenset(),
        copyright_header=None) -> list:
    """Run checker on *source* and return Violation list."""
    c = Checker(
        filepath, source, cfg,
        spell_words=spell_words,
        alias_prefixes=alias_prefixes,
        disabled_rules=disabled_rules,
        defines=defines,
        extra_banned=extra_banned,
        copyright_header=copyright_header,
    )
    return c.run_all().violations


def rules(source: str, cfg: dict, **kw) -> list:
    """Return list of rule ID strings."""
    return [v.rule for v in run(source, cfg, **kw)]


def messages(source: str, cfg: dict, **kw) -> list:
    """Return list of violation message strings."""
    return [v.message for v in run(source, cfg, **kw)]


def count(source: str, cfg: dict, rule_id: str, **kw) -> int:
    """Count occurrences of *rule_id* in violations."""
    return sum(1 for r in rules(source, cfg, **kw) if r == rule_id)


def has(source: str, cfg: dict, rule_id: str, **kw) -> bool:
    """True if *rule_id* appears in violations."""
    return rule_id in rules(source, cfg, **kw)


def clean(source: str, cfg: dict, **kw) -> bool:
    """True if there are zero violations."""
    return len(run(source, cfg, **kw)) == 0


# ---------------------------------------------------------------------------
# Convenience configs used across multiple test modules
# ---------------------------------------------------------------------------

# File-prefix only
PREFIX_CFG = cfg_only(
    file_prefix={"enabled": True, "severity": "error",
                 "separator": "_", "case": "lower",
                 "exempt_main": True, "exempt_patterns": []},
)

# Full variables block
VARS_CFG = cfg_only(
    variables={
        "enabled": True, "severity": "error",
        "case": "lower_snake", "min_length": 2, "max_length": 40,
        "allow_single_char_loop_vars": True,
        "allowed_abbreviations": [],
        "global":    {"severity": "error", "case": "lower_snake",
                      "require_module_prefix": True,
                      "g_prefix": {"enabled": True, "severity": "warning",
                                   "prefix": "g_"}},
        "static":    {"severity": "error", "case": "lower_snake",
                      "require_module_prefix": True,
                      "s_prefix": {"enabled": True, "severity": "warning",
                                   "prefix": "s_"}},
        "local":     {"severity": "error", "case": "lower_snake",
                      "require_module_prefix": False},
        "parameter": {"severity": "warning", "case": "lower_snake",
                      "require_module_prefix": False},
        "pointer_prefix": {"enabled": True, "severity": "warning",
                           "prefix": "p_"},
        "pp_prefix":  {"enabled": True, "severity": "warning",
                       "prefix": "pp_"},
        "bool_prefix":{"enabled": True, "severity": "warning",
                       "prefix": "b_"},
    },
)
