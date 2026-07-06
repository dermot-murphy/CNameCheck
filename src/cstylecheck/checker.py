"""
checker.py — Checker class and all rule-check methods for CStyleCheck.

Contains all RE_* regex patterns, the Checker class, and all _check_* methods.

Imports from: models, preprocessor, utils, config.
"""
from __future__ import annotations

import re
from pathlib import Path

from .models import (
    Violation, CheckResult,
    _SIGNED_TYPES,
)
from .preprocessor import (
    preprocess, build_line_map, offset_to_line_col,
    _build_brace_depths, _comment_only_lines, extract_comments,
    parse_inline_suppressions,
)
from .utils import (
    matches_case, matches_case_abbrev, to_case, module_name,
    is_exempt, _cfg, _strip_module_prefix,
)
from .config import (
    apply_defines,
    C_KEYWORDS, C_STDLIB_NAMES,
    _COPYRIGHT_YEAR_RE,
)


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

# Standard C (C89–C17) and POSIX.1-2017 header names (CERT PRE04-C).
# Source files must not be named after any of these headers.
_STANDARD_C_HEADERS: frozenset = frozenset({
    # C standard headers
    "assert.h", "complex.h", "ctype.h", "errno.h", "fenv.h", "float.h",
    "inttypes.h", "iso646.h", "limits.h", "locale.h", "math.h", "setjmp.h",
    "signal.h", "stdalign.h", "stdarg.h", "stdatomic.h", "stdbool.h",
    "stddef.h", "stdint.h", "stdio.h", "stdlib.h", "stdnoreturn.h",
    "string.h", "tgmath.h", "threads.h", "time.h", "uchar.h", "wchar.h",
    "wctype.h",
    # POSIX.1-2017 headers
    "aio.h", "cpio.h", "dirent.h", "dlfcn.h", "fcntl.h", "fnmatch.h",
    "ftw.h", "glob.h", "grp.h", "iconv.h", "langinfo.h", "libgen.h",
    "monetary.h", "mqueue.h", "netdb.h", "nl_types.h", "poll.h",
    "pthread.h", "pwd.h", "regex.h", "sched.h", "search.h", "semaphore.h",
    "spawn.h", "strings.h", "syslog.h", "tar.h", "termios.h",
    "unistd.h", "utime.h", "utmpx.h", "wordexp.h",
})


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
    # A real declaration always has a visible separator (whitespace and/or
    # pointer star) between the return type and the function name. A plain
    # call statement (e.g. "foo (args) ;") is a single identifier with no
    # such separator, so without this requirement \w+ can backtrack to peel
    # off the call's trailing character as a fake "name" and misparse the
    # call as a declaration (issue #273).
    r"(?:[ \t]+\*{0,2}|\*{1,2})[ \t]*"
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
    # See RE_FUNCTION_DEF above: require a real separator so a bare call
    # statement's identifier can't be split into a fake type+name pair.
    r"(?:[ \t]+\*{0,2}|\*{1,2})[ \t]*"
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
    # Each type token is followed by optional whitespace so that the star can
    # be written either adjacent to the type ("uint8_t*") or separated from
    # it ("uint8_t *").  The previous [ \t]+ required at least one space,
    # which caused "uint8_t*\t\tp_name" to go unmatched, leaving the
    # parameter absent from param_names and therefore misclassified as a
    # local variable by RE_VAR_DECL.
    r"(?:(?:const|volatile|unsigned|signed|long|short|int|char|float|double"
    r"|uint\w+|int\w+|bool|_Bool|size_t|[A-Z_]\w+_[Tt])[ \t]*)+"
    r"\*?[ \t]*([a-z_]\w*)[ \t]*(?:,|\)|\[)",
)

RE_INCLUDE_GUARD_IFNDEF = re.compile(r"^\s*#\s*ifndef\s+([A-Za-z_]\w*)", re.MULTILINE)
RE_INCLUDE_GUARD_DEFINE = re.compile(r"^\s*#\s*define\s+([A-Za-z_]\w*)\s*$", re.MULTILINE)
RE_PRAGMA_ONCE          = re.compile(r"^\s*#\s*pragma\s+once", re.MULTILINE)

RE_MAGIC_NUMBER = re.compile(r"(?<![.\w])(\d{2,})(?![.\w])")
RE_ARRAY_INDEX  = re.compile(r"\[\s*\d+\s*\]")   # matches  [2]  or  [ 10 ]

RE_ENUM_MEMBER  = re.compile(r"\b([A-Za-z_]\w*)\s*(?:=|,|\})")

RE_COMMENT_WORD = re.compile(r"[A-Za-z][A-Za-z']{2,}")


class Checker:
    def __init__(
        self,
        filepath: str,
        source: str,
        cfg: dict,
        spell_words=None,
        alias_prefixes: list | None = None,
        disabled_rules: frozenset | None = None,
        ident_disabled_rules: dict | None = None,
        inline_suppressions: dict | None = None,
        defines: list | None = None,
        extra_banned: frozenset | None = None,
        copyright_header=None,
        c_keywords: frozenset | None = None,
        c_stdlib_names: frozenset | None = None,
    ):
        self.filepath      = filepath
        # Normalise line endings once at construction time so all check
        # methods operate on LF-only source.  Without this, CRLF files from
        # Windows produce off-by-one line-length results (\r counts as a
        # character) and multi-line regex anchors behave unexpectedly.
        self.source        = source.replace('\r\n', '\n').replace('\r', '\n')
        # Step 1: strip comments and string literals
        self.clean         = preprocess(self.source)
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
        self._inline_suppressions: dict = (
            parse_inline_suppressions(source)
            if inline_suppressions is None
            else inline_suppressions
        )
        # Extra banned identifier names (from --banned-names file + builtins)
        self._extra_banned: frozenset = extra_banned or frozenset()
        # tuple (template_text, compiled_re) from --copyright, or None
        self._copyright = copyright_header
        # Keyword / stdlib sets — use explicit overrides when provided so that
        # main() does not need to mutate the module-level globals (issue #79).
        self._c_keywords: frozenset = (
            c_keywords if c_keywords is not None else C_KEYWORDS
        )
        self._c_stdlib_names: frozenset = (
            c_stdlib_names if c_stdlib_names is not None else C_STDLIB_NAMES
        )

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _violation(self, pos: int, sev: str, rule: str, msg: str) -> Violation:
        line, col = offset_to_line_col(self._line_map, pos)
        return Violation(self.filepath, line, col, sev, rule, msg)

    def _v(self, pos: int, sev: str, rule: str, msg: str) -> None:
        if self._ident_disabled:
            _m = re.search(r"'([^']+)'", msg)
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
        accepted = list(self._alias_prefixes)  # already includes canonical
        if not accepted:
            accepted = [self._prefix()]

        name_lower = name.lower()
        if any(name_lower.startswith(p.lower()) for p in accepted):
            return   # at least one prefix matched

        # Report using the canonical prefix in the message
        pfx = accepted[0]
        alias_hint = (
            " (or alias prefix(es): "
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
        self._check_macro_trailing_semicolon()    # CERT PRE11-C
        self._check_macro_multistatement_wrapper()  # CERT PRE10-C
        self._check_variables()
        self._check_functions()
        self._check_function_length()             # JPL Power of Ten Rule 4
        self._check_function_doc_header()         # ESA-R-1, JSF
        self._check_assert_density()              # JPL Power of Ten Rule 5
        self._check_declaration_spacing()         # Linux LK-8
        self._check_typedefs()
        self._check_enums()
        self._check_structs()
        if self._is_header:
            self._check_include_guard()
        self._check_misc()
        self._check_file_length()                 # ESA, industry practice
        self._check_reserved_header_name()        # CERT PRE04-C
        self._check_null_statement_comment()      # JSF Rule 192
        self._check_identifier_length()           # ESA-R-7, JSF Rule 45
        self._check_no_single_char_identifiers()  # ESA-R-4
        self._check_comment_ratio()
        self._check_whitespace_ratio()
        self._check_yoda()
        self._check_constant_comparison()
        self._check_reserved_names()
        self._check_lowercase_l_suffix()   # MISRA C:2012/2023 Rule 7.3
        self._check_octal_constants()      # MISRA C:2012/2023 Rule 7.1
        self._check_trigraphs()            # MISRA C:2012/2023 Rule 4.2
        self._check_non_ascii_source()     # MISRA C:2012/2023 Rule 4.1
        if self._spell_dict is not None:
            self._check_spelling()
        # Remove violations for rules that are disabled for this file
        if self._disabled_rules:
            self.result.violations = [
                v for v in self.result.violations
                if v.rule not in self._disabled_rules
            ]
        # Remove violations suppressed by inline comments
        if self._inline_suppressions:
            def _not_suppressed(v: Violation) -> bool:
                s = self._inline_suppressions.get(v.line, frozenset())
                return "*" not in s and v.rule not in s
            self.result.violations = [
                v for v in self.result.violations if _not_suppressed(v)
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

            # Skip constant.case for object-like #defines whose name ends
            # with the project's typedef suffix (e.g. _t / _T): these are
            # type aliases, not constant values (issue #272).
            td_suffix_cfg = self.cfg.get("typedefs", {}).get("suffix", {})
            td_suffix = (
                td_suffix_cfg.get("suffix", "_T")
                if td_suffix_cfg.get("enabled")
                else None
            )
            is_typedef_alias = (
                not is_fn
                and td_suffix is not None
                and name.lower().endswith(td_suffix.lower())
            )

            # Skip constant.case when the RHS is a single bare identifier that
            # is NOT itself an ALL_CAPS constant or boolean/null keyword: the
            # define is a function/type/symbol alias, not a constant value.
            # e.g. #define MW_KX134_HAL_PowerOnInit  HAL_Acc_PowerOnInit
            #      #define module_my_type_t          uint8_t
            # ALL_CAPS RHS (e.g. SOME_OTHER_CONST) is still a constant alias
            # so the LHS case check still applies.  issue #355
            _BOOL_NULL = {"true", "false", "TRUE", "FALSE", "NULL", "nullptr"}
            is_fn_alias = (
                not is_fn
                and bool(re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*', rest))
                and not re.fullmatch(r'[A-Z][A-Z0-9_]*', rest)
                and rest not in _BOOL_NULL
            )

            if not is_typedef_alias and not is_fn_alias \
                    and not matches_case(name, expected_case):
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
            # Same [ \t]* fix as RE_FUNCTION_PARAM: allows the star to be
            # written adjacent to the type ("uint8_t*") as well as separated
            # ("uint8_t *"), ensuring pointer parameters are checked regardless
            # of the coding style used for star placement.
            r"(?:(?:const|volatile|unsigned|signed|long|short|int|char|float|double"
            r"|uint\w+|int\w+|bool|_Bool|size_t|[A-Z_]\w+_[Tt])[ \t]*)+"
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
                            # Accept the double-pointer prefix when it appears
                            # directly in the local part OR after the parameter
                            # prefix (e.g. "p_pp_buf" satisfies pp_pfx="pp_").
                            # This is independent of whether variable.parameter
                            # .p_prefix is enabled — it reflects the naming
                            # convention that parameters are prefixed with p_
                            # and the type prefix follows.
                            pp_after_param = (
                                p_local.startswith(_pp_param_pfx) and
                                p_local[len(_pp_param_pfx):].startswith(pp_pfx)
                            )
                            if not (p_local.startswith(pp_pfx) or pp_after_param):
                                self._v(abs_pos, pp_sev,
                                        "variable.pp_prefix",
                                        f"Double-pointer parameter '{p_name}' "
                                        f"local part should start with '{pp_pfx}' "
                                        f"(BARR-C 7.1.l)")
                    elif p_stars == "*":
                        if ptr_cfg_early.get("enabled", True):
                            p_pfx = ptr_cfg_early.get("prefix", "p_")
                            p_sev = ptr_cfg_early.get("severity", "warning")
                            # Accept the pointer prefix when it appears directly
                            # in the local part OR after the parameter prefix.
                            # Example: pointer_prefix="ptr_", p_prefix="p_"
                            #   "p_ptr_packet_buffer" → p_local = "p_ptr_packet_buffer"
                            #   direct check: startswith("ptr_") → False
                            #   param-stripped: strip "p_" → "ptr_packet_buffer"
                            #                  startswith("ptr_") → True  ✓
                            ptr_after_param = (
                                p_local.startswith(_pp_param_pfx) and
                                p_local[len(_pp_param_pfx):].startswith(p_pfx)
                            )
                            if not (p_local.startswith(p_pfx) or ptr_after_param):
                                _correct = self._compute_ptr_correct_name(
                                    p_name, p_pfx, p_local, _pp_param_pfx)
                                self._v(abs_pos, p_sev,
                                        "variable.pointer_prefix",
                                        f"Pointer parameter '{p_name}' local part "
                                        f"should start with '{p_pfx}'; rename to "
                                        f"'{_correct}' (BARR-C 7.1.k)")
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
                        h_after_param = (
                            p_local.startswith(_pp_param_pfx) and
                            p_local[len(_pp_param_pfx):].startswith(_h_pfx_early)
                        )
                        if not (p_local.startswith(_h_pfx_early) or h_after_param):
                            self._v(abs_pos, _h_sev_early,
                                    "variable.handle_prefix",
                                    f"Handle parameter '{p_name}' (type '{p_type}') "
                                    f"local part should start with '{_h_pfx_early}' "
                                    f"(BARR-C 7.1.n)")
                    if _b_en_early and p_type in ("bool", "_Bool"):
                        b_after_param = (
                            p_local.startswith(_pp_param_pfx) and
                            p_local[len(_pp_param_pfx):].startswith(_b_pfx_early)
                        )
                        if not (p_local.startswith(_b_pfx_early) or b_after_param):
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

        _typedef_close: set = getattr(self, "_typedef_close_positions", set())
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
                # variable.parameter.p_prefix already emitted by _collect_sig
                # for every parameter in a signature range — no duplicate here.
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
            #
            # The naming convention allows a parameter prefix (e.g. "p_") to
            # precede the type prefix (e.g. "ptr_"), giving "p_ptr_name".
            # Accept the type prefix when it appears either directly at the
            # start of the local part OR immediately after the configured
            # parameter prefix. This applies regardless of scope — a project
            # may apply the same "p_ptr_name" convention to struct members,
            # locals, and globals, not just function parameters — and is
            # independent of whether variable.parameter.p_prefix is enabled,
            # since it reflects the physical naming convention used by the
            # project rather than the parameter-prefix rule itself.
            local_raw = self._strip_any_prefix(name)

            if stars == "**":
                if pp_cfg.get("enabled", True):
                    pp_pfx = pp_cfg.get("prefix", "pp_")
                    pp_sev = pp_cfg.get("severity", "warning")
                    pp_ok = local_raw.startswith(pp_pfx) or (
                        local_raw.startswith(_pp_param_pfx) and
                        local_raw[len(_pp_param_pfx):].startswith(pp_pfx)
                    )
                    if not pp_ok:
                        self._v(m.start(), pp_sev, "variable.pp_prefix",
                                f"Double-pointer variable '{name}' local part "
                                f"should start with '{pp_pfx}' (BARR-C 7.1.l)")
            elif stars == "*":
                if ptr_cfg.get("enabled", True):
                    p_pfx = ptr_cfg.get("prefix", "p_")
                    p_sev = ptr_cfg.get("severity", "warning")
                    ptr_ok = local_raw.startswith(p_pfx) or (
                        local_raw.startswith(_pp_param_pfx) and
                        local_raw[len(_pp_param_pfx):].startswith(p_pfx)
                    )
                    if not ptr_ok:
                        _correct = self._compute_ptr_correct_name(
                            name, p_pfx, local_raw, _pp_param_pfx)
                        self._v(m.start(), p_sev, "variable.pointer_prefix",
                                f"Pointer variable '{name}' local part should "
                                f"start with '{p_pfx}'; rename to '{_correct}' "
                                f"(BARR-C 7.1.k)")

            # Boolean prefix (BARR-C 7.1.m)
            # Variables of type bool or _Bool must have local part starting
            # with b_ and should be phrased as a question they answer.
            if bool_cfg.get("enabled", True) and type_token in ("bool", "_Bool"):
                b_pfx = bool_cfg.get("prefix", "b_")
                b_sev = bool_cfg.get("severity", "warning")
                if scope == "parameter":
                    bool_ok = local_raw.startswith(b_pfx) or (
                        local_raw.startswith(_pp_param_pfx) and
                        local_raw[len(_pp_param_pfx):].startswith(b_pfx)
                    )
                else:
                    bool_ok = local_raw.startswith(b_pfx)
                if not bool_ok:
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
                if scope == "parameter":
                    h_ok = local_raw.startswith(h_pfx) or (
                        local_raw.startswith(_pp_param_pfx) and
                        local_raw[len(_pp_param_pfx):].startswith(h_pfx)
                    )
                else:
                    h_ok = local_raw.startswith(h_pfx)
                if not h_ok:
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
    def _body_is_object_verb(body: str, object_exclusions: set, abbrevs: set) -> bool:
        """
        Return True when *body* (text after the module prefix) satisfies the
        object_verb (or verb_object) convention:

          * If any underscore-delimited segment of *body* appears in
            *object_exclusions*, the rule is waived entirely.
          * Otherwise every segment must be PascalCase or an entry in
            *abbrevs*.  A single segment (verb only, no explicit object)
            is also accepted.

        Examples that pass:
          BufferRead          — classic ObjectVerb
          Init                — single verb, no object required
          LiveDataRead_X_Start — multi-segment; last = verb, rest = object
          Wr_Mode_Transit     -- Wr is in object_exclusions -> waived
        """
        segments = [s for s in body.split("_") if s]
        if not segments:
            return False
        # Rule 1: exclusion list waives the entire check
        for seg in segments:
            if seg in object_exclusions or seg.upper() in {e.upper() for e in object_exclusions}:
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
        object_exclusions = set(fn_cfg.get("object_exclusions", []))
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
                if not self._body_is_object_verb(body, object_exclusions, abbrevs):
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
            body_offset = m.start(1)
            for mm in RE_ENUM_MEMBER.finditer(body_str):
                mname = mm.group(1)
                if not matches_case(mname, member_case):
                    self._v(body_offset + mm.start(), type_sev, "enum.member_case",
                            f"Enum member '{mname}' must be {member_case}")
                if (member_pfx_cfg.get("enabled")
                        and not mname.upper().startswith(
                            member_pfx.upper() + "_")):
                    self._v(body_offset + mm.start(),
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

        # self.source is already LF-normalised in __init__; no further
        # normalisation needed here.
        source = self.source
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
        # Skip [0] only when it is the tail fragment of the */ line.
        # When m.end() lands exactly on a '\n' there is no tail — [0] is
        # already the first post-header line and must not be discarded.
        skip = 0 if (m.end() > 0 and source[m.end() - 1] == "\n") else 1
        blank_count  = 0
        for al in after_lines[skip:]:
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

        # Exempt integer literals that are arguments at signed-parameter
        # positions of locally-declared/defined functions.
        # Parse declarations and definitions in this file to build a signature
        # map (fn_name → [True/False per param, True = signed]).  For each
        # call site whose function appears in the map, mark all character
        # positions inside signed-parameter arguments as exempt so that
        # literals like '80' passed to int8_t/int16_t/etc. parameters do not
        # trigger the unsigned_suffix or magic_number rules.
        _RE_PARAM_US = re.compile(
            r"((?:(?:const|volatile|signed|unsigned|long|short|int|char"
            r"|float|double|bool|_Bool|uint\w*|int\w*|sint\w*|size_t"
            r"|[A-Za-z_]\w*)[ \t]+)+)"
            r"\*?[ \t]*"
            r"([A-Za-z_]\w*)"
            r"[ \t]*(?:,|$|\[)",
        )

        def _param_is_signed_us(type_str: str) -> bool:
            tokens = type_str.split()
            if "unsigned" in tokens:
                return False
            if "signed" in tokens:
                return True
            for _t in tokens:
                if _t in _SIGNED_TYPES:
                    return True
            return False

        def _plist_signs(plist_text: str) -> list:
            txt = plist_text.strip()
            if txt in ("void", ""):
                return []
            result = []
            for pm in _RE_PARAM_US.finditer(txt + ","):
                result.append(_param_is_signed_us(pm.group(1)))
            return result

        def _extract_plist(fn_start: int) -> tuple:
            po = self.clean.find("(", fn_start)
            if po == -1:
                return -1, ""
            depth = 0
            for i in range(po, len(self.clean)):
                if self.clean[i] == "(":
                    depth += 1
                elif self.clean[i] == ")":
                    depth -= 1
                    if depth == 0:
                        return po, self.clean[po + 1:i]
            return -1, ""

        _fn_signs: dict = {}
        for _fn_m in RE_FUNCTION_DECL.finditer(self.clean):
            _fn_name_us = _fn_m.group(1)
            _po_us, _plist_us = _extract_plist(_fn_m.start())
            if _po_us != -1:
                _fn_signs[_fn_name_us] = _plist_signs(_plist_us)
        for _fn_m in RE_FUNCTION_DEF.finditer(self.clean):
            _fn_name_us = _fn_m.group(1)
            if _fn_name_us not in _fn_signs:
                _po_us, _plist_us = _extract_plist(_fn_m.start())
                if _po_us != -1:
                    _fn_signs[_fn_name_us] = _plist_signs(_plist_us)

        _call_re_us = re.compile(r"\b([A-Za-z_]\w*)\s*\(", re.MULTILINE)
        for _cm in _call_re_us.finditer(self.clean):
            _fn_us = _cm.group(1)
            if _fn_us not in _fn_signs:
                continue
            _signs_us = _fn_signs[_fn_us]
            if not _signs_us:
                continue
            _pos_us  = _cm.end() - 1   # position of the opening "("
            _depth_us = 0
            _aidx_us  = 0
            _astart_us = _pos_us + 1
            for _i_us in range(_pos_us, len(self.clean)):
                _ch_us = self.clean[_i_us]
                if _ch_us in "([":
                    _depth_us += 1
                elif _ch_us == ")" and _depth_us == 1:
                    if _aidx_us < len(_signs_us) and _signs_us[_aidx_us]:
                        exempt_positions.update(range(_astart_us, _i_us))
                    break
                elif _ch_us in ")]":
                    _depth_us -= 1
                elif _ch_us == "," and _depth_us == 1:
                    if _aidx_us < len(_signs_us) and _signs_us[_aidx_us]:
                        exempt_positions.update(range(_astart_us, _i_us))
                    _aidx_us += 1
                    _astart_us = _i_us + 1

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

            # Also exempt literals compared against a signed variable:
            #   if (1 < x)  or  if (x != 1)  where x is int16_t.
            # Adding 'U' here would change comparison semantics for negatives.
            _RE_SIGNED_CMP_L = re.compile(
                r"\b([0-9]+)\s*(?:[<>]=?|[=!]=)\s*([a-z_]\w*)"
            )
            _RE_SIGNED_CMP_R = re.compile(
                r"\b([a-z_]\w*)\s*(?:[<>]=?|[=!]=)\s*([0-9]+)\b"
            )
            for cm in _RE_SIGNED_CMP_L.finditer(self.clean):
                if cm.group(2) in signed_vars:
                    signed_assign_positions.update(
                        range(cm.start(1), cm.end(1)))
            for cm in _RE_SIGNED_CMP_R.finditer(self.clean):
                if cm.group(1) in signed_vars:
                    signed_assign_positions.update(
                        range(cm.start(2), cm.end(2)))

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
    # 8a. Block-comment spacing
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

        # 8b. EOF comment
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
                trailing_lines = lines[last_nb + 1:]      # lines after EOF comment
                n_after = len(trailing_lines)
                if n_after == 0:
                    # Nothing after the comment — missing trailing blank line
                    self.result.add(Violation(
                        self.filepath, lineno_nb, 1, sev, "misc.eof_comment",
                        "EOF comment must be followed by exactly one blank line"))
                elif n_after == 1:
                    # Exactly one line follows — it must be blank
                    if trailing_lines[0].strip():
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
    # 14. Comment ratio (misc.comment_ratio)
    # -----------------------------------------------------------------------

    def _check_comment_ratio(self) -> None:
        """Enforce a minimum ratio of comment lines to code lines (issue #68).

        Excluded from both counts:
          - Blank lines
          - The file header: all leading comment/blank lines before the first
            non-comment, non-blank line (copyright notices, licence blocks)
          - Doxygen blocks: /** … */ are documentation, not explanatory comments

        Counted as comment lines:
          - // line comments
          - /* … */ regular block comments (not Doxygen)

        Counted as code lines:
          - Every non-blank, non-comment line (code, preprocessor, etc.)
          - A line with a trailing // comment counts as a CODE line
        """
        misc   = self.cfg.get("misc", {})
        cr_cfg = misc.get("comment_ratio", {})
        if not cr_cfg.get("enabled", False):
            return

        sev      = cr_cfg.get("severity", "warning")
        warn_thr = float(cr_cfg.get("warning_threshold", 0.15))
        err_thr  = float(cr_cfg.get("error_threshold",  0.05))
        min_code = int(cr_cfg.get("min_code_lines", 10))

        lines = self.source.splitlines()

        # ----------------------------------------------------------------
        # Phase 1: locate the end of the file header.
        # The header region = all leading comment/blank lines before the
        # first non-comment, non-blank line.
        # ----------------------------------------------------------------
        header_end_idx = 0
        in_hdr_block   = False
        found_code     = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:                      # blank
                continue
            if in_hdr_block:
                if "*/" in line:
                    in_hdr_block = False
                continue
            if stripped.startswith("/*"):
                if "*/" not in stripped[2:]:      # multi-line block comment
                    in_hdr_block = True
                continue                           # still in header
            if stripped.startswith("//"):
                continue                           # line comment — still header
            # First actual code line: header ends here
            header_end_idx = i
            found_code     = True
            break

        if not found_code:
            return   # entire file is comments/blank — nothing to measure

        # ----------------------------------------------------------------
        # Phase 2: classify lines from header_end_idx onwards.
        # ----------------------------------------------------------------
        comment_lines = 0
        code_lines    = 0
        in_doxygen    = False
        in_block_cmt  = False

        for i, line in enumerate(lines):
            if i < header_end_idx:
                continue

            stripped = line.strip()
            if not stripped:
                continue   # blank — excluded

            if in_doxygen:
                if "*/" in line:
                    in_doxygen = False
                continue   # doxygen continuation — excluded

            if in_block_cmt:
                comment_lines += 1
                if "*/" in line:
                    in_block_cmt = False
                continue

            # Opening of a Doxygen block ( /** … )
            if stripped.startswith("/**"):
                if "*/" not in stripped[3:]:
                    in_doxygen = True
                # Doxygen opener line itself is excluded
                continue

            # Opening of a regular block comment ( /* … )
            if stripped.startswith("/*"):
                comment_lines += 1
                if "*/" not in stripped[2:]:
                    in_block_cmt = True
                continue

            # Line comment
            if stripped.startswith("//"):
                comment_lines += 1
                continue

            # Non-blank, non-comment line (code, preprocessor, …)
            code_lines += 1

        # Guard: skip files with too few code lines (trivial files, stubs, etc.)
        if code_lines < min_code:
            return

        ratio = comment_lines / code_lines

        if ratio < err_thr:
            emit_sev        = "error"
            threshold       = err_thr
            threshold_label = "error"
        elif ratio < warn_thr:
            emit_sev        = sev
            threshold       = warn_thr
            threshold_label = "warning"
        else:
            return   # ratio meets the warning threshold — all good

        pl = lambda n: "s" if n != 1 else ""  # noqa: E731
        self.result.add(Violation(
            self.filepath, 1, 1, emit_sev, "misc.comment_ratio",
            f"comment ratio {ratio:.2f} is below {threshold_label} threshold "
            f"{threshold} "
            f"({comment_lines} comment line{pl(comment_lines)} / "
            f"{code_lines} code line{pl(code_lines)})"
        ))

    # -----------------------------------------------------------------------
    # 15. Whitespace (blank-line) ratio  (misc.whitespace_ratio)
    # -----------------------------------------------------------------------

    def _check_whitespace_ratio(self) -> None:
        """Enforce a minimum ratio of blank lines to code lines (issue #143).

        Measures how 'airy' the file body is relative to its code density.
        Very few blank lines relative to code lines indicates dense,
        hard-to-read code.

        Excluded from both counts:
          - The file header: all leading comment/blank lines before the first
            non-comment, non-blank line (copyright notices, licence blocks)
          - Comment-only lines (// and /* … */) — they are not blank and are
            not code, so they are excluded from both counts

        Counted as blank lines (numerator):
          - Empty lines and whitespace-only lines in the code body

        Counted as code lines (denominator):
          - Every non-blank, non-comment line (code, preprocessor, etc.)
          - A line with a trailing // comment counts as a CODE line
        """
        misc   = self.cfg.get("misc", {})
        wr_cfg = misc.get("whitespace_ratio", {})
        if not wr_cfg.get("enabled", False):
            return

        sev       = wr_cfg.get("severity", "warning")
        warn_thr  = float(wr_cfg.get("warning_threshold", 0.10))
        err_thr   = float(wr_cfg.get("error_threshold",  0.01))
        min_lines = int(wr_cfg.get("min_lines", 20))

        lines = self.source.splitlines()

        # ----------------------------------------------------------------
        # Phase 1: locate the end of the file header.
        # Same logic as _check_comment_ratio: the header region is all
        # leading comment/blank lines before the first code line.
        # ----------------------------------------------------------------
        header_end_idx = 0
        in_hdr_block   = False
        found_code     = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:                      # blank — skip during header scan
                continue
            if in_hdr_block:
                if "*/" in line:
                    in_hdr_block = False
                continue
            if stripped.startswith("/*"):
                if "*/" not in stripped[2:]:      # multi-line block comment
                    in_hdr_block = True
                continue                           # still in header
            if stripped.startswith("//"):
                continue                           # line comment — still header
            # First actual code line: header ends here
            header_end_idx = i
            found_code     = True
            break

        if not found_code:
            return   # entire file is comments/blank — nothing to measure

        # ----------------------------------------------------------------
        # Phase 2: classify lines from header_end_idx onwards.
        # ----------------------------------------------------------------
        blank_lines  = 0
        code_lines   = 0
        in_block_cmt = False

        for i, line in enumerate(lines):
            if i < header_end_idx:
                continue

            stripped = line.strip()

            if in_block_cmt:
                if "*/" in line:
                    in_block_cmt = False
                continue   # block comment continuation — excluded from both

            if not stripped:
                blank_lines += 1   # blank line — counts toward numerator
                continue

            # Opening of a block comment (/* or /**)
            if stripped.startswith("/*"):
                if "*/" not in stripped[2:]:
                    in_block_cmt = True
                continue   # comment-only line — excluded from denominator

            # Line comment
            if stripped.startswith("//"):
                continue   # excluded from denominator

            # Non-blank, non-comment line — this is code
            code_lines += 1

        # Guard: skip files with too few code lines (trivial files, stubs)
        if code_lines < min_lines:
            return

        ratio = blank_lines / code_lines

        if ratio < err_thr:
            emit_sev        = "error"
            threshold       = err_thr
            threshold_label = "error"
        elif ratio < warn_thr:
            emit_sev        = sev
            threshold       = warn_thr
            threshold_label = "warning"
        else:
            return   # ratio meets the warning threshold — all good

        pl = lambda n: "s" if n != 1 else ""  # noqa: E731
        self.result.add(Violation(
            self.filepath, 1, 1, emit_sev, "misc.whitespace_ratio",
            f"whitespace ratio {ratio:.2f} is below {threshold_label} threshold "
            f"{threshold} "
            f"({blank_lines} blank line{pl(blank_lines)} / "
            f"{code_lines} code line{pl(code_lines)})"
        ))

    # -----------------------------------------------------------------------
    # 16. Comment spell-check
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
    # 9. Yoda conditions  (constant on the LHS of == and !=)
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

            # Extract token immediately to the RIGHT of the operator.
            # Include a leading '-' so that negative literals (-1, -100) are
            # displayed correctly in the violation message (BUG-004).
            rhs_start = m.end()
            while rhs_start < len(self.clean) and self.clean[rhs_start] in " \t":
                rhs_start += 1
            # Check for a leading minus sign (negative literal)
            rhs_display_start = rhs_start
            if (rhs_start < len(self.clean)
                    and self.clean[rhs_start] == "-"
                    and rhs_start + 1 < len(self.clean)
                    and self.clean[rhs_start + 1].isdigit()):
                rhs_start += 1   # advance past '-' so digit-only token is used
                                 # for _is_constant_token classification
            rhs_end = rhs_start
            while rhs_end < len(self.clean) and (
                    self.clean[rhs_end].isalnum()
                    or self.clean[rhs_end] in "_'xXuUlL"):
                rhs_end += 1
            rhs         = self.clean[rhs_start:rhs_end]        # digit-only for classify
            rhs_display = self.clean[rhs_display_start:rhs_end]  # includes '-' for message

            # Skip if RHS identifier is immediately followed by '[': it is an
            # array element access (runtime value), not a constant.
            # e.g.  API_TABLE[idx].field  — same guard as _check_constant_comparison.
            _after_rhs = self.clean[rhs_end:rhs_end + 10].lstrip()
            if _after_rhs.startswith('['):
                continue

            # Skip if LHS is already a constant — the expression is already in
            # constant-first (Yoda) form.  Swapping would merely exchange one
            # constant for another; misc.constant_comparison owns that report.
            # e.g.  true == API_STACK_GROWS_UP  or  NULL == API_TABLE[i].field
            if self._is_constant_token(lhs):
                continue

            if self._is_variable_token(lhs) and self._is_constant_token(rhs):
                self._v(m.start(), sev, "misc.yoda_condition",
                        f"Constant '{rhs_display}' should be on the left of '{op}': "
                        f"write '{rhs_display} {op} {lhs}'")

    @staticmethod
    def _compute_ptr_correct_name(name: str, pfx: str, local: str,
                                   pp_param_pfx: str) -> str:
        """Return the correctly ordered pointer-prefixed name for --fix messages.

        Ensures the pointer prefix is outermost (after any parameter prefix)
        and applies rename rules: strip trailing _ptr, bare 'ptr' → 'data'.
        """
        module_part = name[:len(name) - len(local)]
        if pp_param_pfx and local.startswith(pp_param_pfx) and pp_param_pfx != pfx:
            inner = local[len(pp_param_pfx):]
            if inner == "ptr":
                inner_base = "data"
            elif inner.endswith("_ptr"):
                inner_base = inner[:-4]
            else:
                inner_base = inner
            new_local = pp_param_pfx + pfx + inner_base
        else:
            if local == "ptr":
                base = "data"
            elif local.endswith("_ptr"):
                base = local[:-4]
            else:
                base = local
            new_local = pfx + base
        return module_part + new_local

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
        if re.fullmatch(r"[A-Z][A-Z0-9_]*", t):            return True  # ALL_CAPS ≥ 1 char
        return False

    @staticmethod
    def _is_variable_token(tok: str) -> bool:
        """True if *tok* is a plain variable identifier (starts with lowercase/underscore)."""
        t = tok.strip()
        if not t:
            return False
        return bool(re.fullmatch(r"[a-z_][a-zA-Z0-9_]*", t))

    # -----------------------------------------------------------------------
    # 10. Constant-to-constant comparisons
    # -----------------------------------------------------------------------

    def _check_constant_comparison(self) -> None:
        """
        Flag == and != where BOTH sides are recognisably compile-time constants.

        Comparing two constants always yields the same boolean result, making
        the comparison dead code or a copy-paste error.

        Examples (violations):
            if (NULL == NULL)       ← always true
            if (ERROR == SUCCESS)   ← always the same value
            if (true == false)      ← always false
        """
        cc_cfg = self.cfg.get("misc", {}).get("constant_comparison", {})
        if not cc_cfg.get("enabled", True):
            return
        sev = cc_cfg.get("severity", "warning")

        # Same exempt contexts as yoda_condition: #define RHS and return stmts
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
            rhs_display_start = rhs_start
            if (rhs_start < len(self.clean)
                    and self.clean[rhs_start] == "-"
                    and rhs_start + 1 < len(self.clean)
                    and self.clean[rhs_start + 1].isdigit()):
                rhs_start += 1
            rhs_end = rhs_start
            while rhs_end < len(self.clean) and (
                    self.clean[rhs_end].isalnum()
                    or self.clean[rhs_end] in "_'xXuUlL"):
                rhs_end += 1
            rhs         = self.clean[rhs_start:rhs_end]
            rhs_display = self.clean[rhs_display_start:rhs_end]

            # Skip if RHS identifier is immediately followed by '[': the token
            # is an array name and the element value is runtime-determined.
            # e.g. ALL_CAPS_TABLE[param_index].field is not a constant.
            _after_rhs = self.clean[rhs_end:rhs_end + 10].lstrip()
            if _after_rhs.startswith('['):
                continue

            if self._is_constant_token(lhs) and self._is_constant_token(rhs):
                self._v(m.start(), sev, "misc.constant_comparison",
                        f"Both sides of '{op}' are constants: "
                        f"'{lhs} {op} {rhs_display}'")

    # -----------------------------------------------------------------------
    # 11. MISRA C:2012/2023 Rule 7.3 — lowercase 'l' suffix forbidden
    #
    # The letter 'l' (lowercase L) is visually indistinguishable from the
    # digit '1' in many fonts.  MISRA C:2012 Rule 7.3 and MISRA C:2023
    # Rule 7.3 (both Required) mandate that integer literal suffixes use
    # only uppercase letters (U, L, UL, LL, ULL etc.).
    #
    # Examples:
    #   1l   → violation  (should be 1L)
    #   1ul  → violation  (should be 1UL)
    #   1UL  → OK
    #   0xFFl→ violation  (should be 0xFFL)
    # -----------------------------------------------------------------------

    # Pre-compiled once at class definition time.
    _RE_INT_WITH_SUFFIX = re.compile(
        r'\b(?:0[xX][0-9A-Fa-f]+|[0-9]+)([uUlL]+)\b'
    )

    def _check_lowercase_l_suffix(self) -> None:
        ll_cfg = self.cfg.get("misc", {}).get("lowercase_l_suffix", {})
        if not ll_cfg.get("enabled", True):
            return
        sev = ll_cfg.get("severity", "error")

        for m in self._RE_INT_WITH_SUFFIX.finditer(self.clean):
            suffix = m.group(1)
            if 'l' in suffix:   # lowercase l present anywhere in suffix
                self._v(
                    m.start(), sev, "misc.lowercase_l_suffix",
                    f"Integer literal '{m.group(0)}' uses lowercase 'l' suffix; "
                    f"use uppercase 'L' to avoid confusion with digit '1' "
                    f"(MISRA C:2012/2023 Rule 7.3)"
                )

    # -----------------------------------------------------------------------
    # 12. MISRA C:2012/2023 Rule 7.1 — octal integer constants forbidden
    #
    # An integer literal that starts with '0' followed by one or more
    # octal digits (0–7) is an octal constant.  This is a common source
    # of bugs when numeric values are zero-padded for alignment.
    #
    # Examples:
    #   010  → violation (= 8 decimal, NOT 10)
    #   07   → violation (= 7 decimal but looks like it might be "07")
    #   0    → OK  (zero)
    #   0U   → OK  (zero with suffix)
    #   0x1A → OK  (hexadecimal)
    #   0.5  → OK  (floating-point)
    # -----------------------------------------------------------------------

    # Matches a leading-zero octal literal with at least one octal digit.
    # Excludes hex (0x), float (0.), and bare zero (0 alone, 0U, 0L).
    _RE_OCTAL_LITERAL = re.compile(
        r'(?<![.\w])0[0-7][0-7]*(?:[uUlL]*)\b'
    )

    def _check_octal_constants(self) -> None:
        oc_cfg = self.cfg.get("misc", {}).get("octal_constant", {})
        if not oc_cfg.get("enabled", True):
            return
        sev = oc_cfg.get("severity", "error")

        for m in self._RE_OCTAL_LITERAL.finditer(self.clean):
            # Extra guard: reject match if preceded by 'x'/'X' (already in
            # negative lookbehind, but be explicit for readability).
            if m.start() > 0 and self.clean[m.start() - 1] in 'xX':
                continue
            self._v(
                m.start(), sev, "misc.octal_constant",
                f"Octal constant '{m.group(0).rstrip()}' is forbidden; "
                f"use decimal or hexadecimal instead "
                f"(MISRA C:2012/2023 Rule 7.1)"
            )

    # -----------------------------------------------------------------------
    # 13. MISRA C:2012/2023 Rule 4.2 — trigraphs forbidden
    #
    # Trigraphs are three-character sequences beginning with '??' that the
    # C preprocessor replaces with a single character before parsing.  They
    # exist only for keyboards lacking certain punctuation characters.
    # Their presence in modern code is almost certainly unintentional and
    # can silently change program meaning.
    #
    # MISRA C:2012 Rule 4.2 is Advisory; MISRA C:2023 Rule 4.2 is Required.
    #
    # Trigraphs:  ??=  ??(  ??)  ??/  ??'  ??<  ??>  ??!  ??-
    # Map to:      #    [    ]    \    ^    {    }    |    ~
    #
    # Note: trigraphs are checked against the raw source (self.source)
    # because they are resolved by the preprocessor before comment stripping
    # and could theoretically appear inside comments.
    # -----------------------------------------------------------------------

    _RE_TRIGRAPH = re.compile(r'\?\?[=\(\)\/\'<>!\-]')

    def _check_trigraphs(self) -> None:
        tg_cfg = self.cfg.get("misc", {}).get("trigraph", {})
        if not tg_cfg.get("enabled", True):
            return
        sev = tg_cfg.get("severity", "error")

        # Check raw source so trigraphs inside comments are also caught.
        for m in self._RE_TRIGRAPH.finditer(self.source):
            line, col = offset_to_line_col(self._line_map, m.start())
            self.result.add(Violation(
                self.filepath, line, col, sev, "misc.trigraph",
                f"Trigraph '{m.group(0)}' is forbidden "
                f"(MISRA C:2012 Rule 4.2 Advisory; MISRA C:2023 Rule 4.2 Required)"
            ))

    # -----------------------------------------------------------------------
    # 14. Non-ASCII source characters (misc.non_ascii_source, issue #279)
    #
    # Source files shall only contain printable ASCII characters and the
    # standard whitespace characters (tab, LF, CR).  Non-ASCII Unicode code
    # points and non-printable control characters are forbidden.
    #
    # We iterate over the Python str directly so that character offsets
    # align correctly with the line_map (which is also built from the str).
    # -----------------------------------------------------------------------

    def _check_non_ascii_source(self) -> None:
        na_cfg = self.cfg.get("misc", {}).get("non_ascii_source", {})
        if not na_cfg.get("enabled", True):
            return
        sev = na_cfg.get("severity", "error")
        exempt_strings = na_cfg.get("exempt_string_literals", False)

        # When exempting string literals, collect char offsets inside
        # double-quoted strings so we can skip violations at those positions.
        exempt_offsets: set = set()
        if exempt_strings:
            in_str = False
            prev_ch = ''
            for idx, ch in enumerate(self.source):
                if ch == '"' and prev_ch != '\\':
                    in_str = not in_str
                if in_str:
                    exempt_offsets.add(idx)
                prev_ch = ch

        for idx, ch in enumerate(self.source):
            cp = ord(ch)
            # Allow: tab (0x09), LF (0x0A), CR (0x0D), printable ASCII (0x20-0x7E)
            if cp == 0x09 or cp == 0x0A or cp == 0x0D:
                continue
            if 0x20 <= cp <= 0x7E:
                continue
            if idx in exempt_offsets:
                continue
            line, col = offset_to_line_col(self._line_map, idx)
            self.result.add(Violation(
                self.filepath, line, col, sev, "misc.non_ascii_source",
                f"Non-ASCII or non-printable character (0x{cp:02X}) at "
                f"line {line}, col {col}; source files must use only "
                f"printable ASCII characters (MISRA C:2012/2023 Rule 4.1)"
            ))

    # -----------------------------------------------------------------------
    # 10. Reserved / banned name check
    # -----------------------------------------------------------------------

    def _is_reserved(self, name: str) -> tuple:
        """Return (True, category_string) if *name* is a reserved identifier."""
        if name in self._c_keywords:
            return True, "C/C++ keyword"
        if name in self._c_stdlib_names:
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
        names.  Per-file exceptions are handled via --exclusions by adding
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

    # -----------------------------------------------------------------------
    # Helper: iterate function bodies
    # -----------------------------------------------------------------------

    def _iter_function_bodies(self):
        """Yield (fn_def_pos, fn_name, body_start, body_end) for each function.

        body_start points to the opening '{'; body_end points one past the
        matching closing '}'.  All positions are in self.clean / self.source
        coordinate space (preprocess() preserves source length).
        """
        for m in RE_FUNCTION_DEF.finditer(self.clean):
            name = m.group(1)
            if not name:
                continue
            open_brace = self.clean.find("{", m.start())
            if open_brace == -1:
                continue
            depth = 0
            pos = open_brace
            end = len(self.clean)
            while pos < end:
                ch = self.clean[pos]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        yield (m.start(), name, open_brace, pos + 1)
                        break
                pos += 1

    # -----------------------------------------------------------------------
    # New rule: macro.trailing_semicolon (CERT PRE11-C, issue #223)
    # -----------------------------------------------------------------------

    def _check_macro_trailing_semicolon(self) -> None:
        """Flag #define bodies that end with a bare semicolon (CERT PRE11-C)."""
        ts_cfg = self.cfg.get("macros", {}).get("trailing_semicolon", {})
        if not ts_cfg.get("enabled", False):
            return
        sev = ts_cfg.get("severity", "warning")

        lines = self.source.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            m = re.match(r'^[ \t]*#[ \t]*define[ \t]+(\w+)', line)
            if not m:
                i += 1
                continue

            macro_name = m.group(1)
            start_lineno = i + 1  # 1-based

            # Collect full body including backslash continuations
            body_parts = [line]
            while line.rstrip().endswith('\\') and i + 1 < len(lines):
                i += 1
                line = lines[i]
                body_parts.append(line)

            full_text = '\n'.join(body_parts)

            # Strip string and char literals, then comments
            stripped = re.sub(r'"(?:[^"\\]|\\.)*"', '""', full_text)
            stripped = re.sub(r"'(?:[^'\\]|\\.)'", "''", stripped)
            stripped = re.sub(r'//[^\n]*', '', stripped)
            stripped = re.sub(r'/\*.*?\*/', '', stripped, flags=re.DOTALL)

            # Isolate the macro body (everything after NAME or NAME(...))
            body_m = re.match(
                r'^[ \t]*#[ \t]*define[ \t]+\w+(?:\s*\([^)]*\))?',
                stripped,
            )
            if body_m:
                body = stripped[body_m.end():]
                body = re.sub(r'\\\n', ' ', body).strip()
                if body.endswith(';'):
                    self.result.add(Violation(
                        self.filepath, start_lineno, 1, sev,
                        "macro.trailing_semicolon",
                        f"Macro '{macro_name}' body ends with ';'; "
                        f"remove the trailing semicolon (CERT PRE11-C)",
                    ))

            i += 1

    # -----------------------------------------------------------------------
    # New rule: macro.multistatement_wrapper (CERT PRE10-C, issue #222)
    # -----------------------------------------------------------------------

    def _check_macro_multistatement_wrapper(self) -> None:
        """Flag function-like multi-statement macros not wrapped in do{}while(0)."""
        mw_cfg = self.cfg.get("macros", {}).get("multistatement_wrapper", {})
        if not mw_cfg.get("enabled", False):
            return
        sev = mw_cfg.get("severity", "warning")

        lines = self.source.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            # Only function-like macros (have a '(' immediately after name)
            m = re.match(r'^[ \t]*#[ \t]*define[ \t]+(\w+)\s*\(', line)
            if not m:
                i += 1
                continue

            macro_name = m.group(1)
            start_lineno = i + 1

            # Collect full body
            body_parts = [line]
            while line.rstrip().endswith('\\') and i + 1 < len(lines):
                i += 1
                line = lines[i]
                body_parts.append(line)

            full_text = '\n'.join(body_parts)

            # Strip literals and comments
            stripped = re.sub(r'"(?:[^"\\]|\\.)*"', '""', full_text)
            stripped = re.sub(r"'(?:[^'\\]|\\.)'", "''", stripped)
            stripped = re.sub(r'//[^\n]*', '', stripped)
            stripped = re.sub(r'/\*.*?\*/', '', stripped, flags=re.DOTALL)

            # Get body after the parameter list
            body_m = re.match(
                r'^[ \t]*#[ \t]*define[ \t]+\w+\s*\([^)]*\)',
                stripped,
            )
            if not body_m:
                i += 1
                continue

            body_flat = re.sub(r'\\\n', ' ', stripped[body_m.end():]).strip()

            # Needs wrapping only if there are 2+ semicolons (multi-statement)
            if body_flat.count(';') < 2:
                i += 1
                continue

            # Accept do { ... } while(0) or do { ... } while (0)
            if re.match(r'do\s*\{.*\}\s*while\s*\(\s*0\s*\)\s*;?\s*$',
                        body_flat, re.DOTALL):
                i += 1
                continue

            self.result.add(Violation(
                self.filepath, start_lineno, 1, sev,
                "macro.multistatement_wrapper",
                f"Multi-statement macro '{macro_name}' must be wrapped in "
                f"do {{ ... }} while(0) (CERT PRE10-C)",
            ))

            i += 1

    # -----------------------------------------------------------------------
    # New rule: misc.function_length (JPL Power of Ten Rule 4, issue #221)
    # -----------------------------------------------------------------------

    def _check_function_length(self) -> None:
        """Flag function bodies exceeding a configurable line count."""
        fl_cfg = self.cfg.get("misc", {}).get("function_length", {})
        if not fl_cfg.get("enabled", True):
            return
        sev = fl_cfg.get("severity", "warning")
        max_lines = int(fl_cfg.get("max_lines", 60))
        count_comments = fl_cfg.get("count_comments", True)

        for fn_pos, name, body_start, body_end in self._iter_function_bodies():
            body_src = self.source[body_start:body_end]
            body_lines = body_src.splitlines()

            if count_comments:
                total = len(body_lines)
            else:
                first_lineno = self.source[:body_start].count('\n') + 1
                total = sum(
                    1 for idx, ln in enumerate(body_lines)
                    if (first_lineno + idx) not in self._comment_only
                    and ln.strip()
                )

            if total > max_lines:
                self._v(
                    fn_pos, sev, "misc.function_length",
                    f"Function '{name}' body has {total} lines, exceeding "
                    f"maximum {max_lines} (JPL Power of Ten Rule 4)",
                )

    # -----------------------------------------------------------------------
    # New rule: misc.function_doc_header (ESA-R-1, JSF, issue #224)
    # -----------------------------------------------------------------------

    def _check_function_doc_header(self) -> None:
        """Require a documentation comment block before each function definition."""
        fdh_cfg = self.cfg.get("misc", {}).get("function_doc_header", {})
        if not fdh_cfg.get("enabled", False):
            return
        sev = fdh_cfg.get("severity", "warning")
        req_brief = fdh_cfg.get("require_brief", True)
        req_param = fdh_cfg.get("require_param", True)
        req_return = fdh_cfg.get("require_return", True)
        style = fdh_cfg.get("style", "doxygen")

        _fp_cfg = self.cfg.get("file_prefix", {})

        for m in RE_FUNCTION_DEF.finditer(self.clean):
            name = m.group(1)
            if not name:
                continue

            if _fp_cfg.get("exempt_main", True) and self.module == "main":
                continue
            if is_exempt(name, _fp_cfg.get("exempt_patterns", [])):
                continue

            fn_pos = m.start()
            preceding = self.source[:fn_pos]
            preceding_stripped = preceding.rstrip()

            # The immediately-preceding non-whitespace text must end with */
            if not preceding_stripped.endswith('*/'):
                self._v(fn_pos, sev, "misc.function_doc_header",
                        f"Function '{name}' must be preceded by a "
                        f"documentation comment block (ESA-R-1, JSF)")
                continue

            # Locate the matching /* or /**
            cmt_end_abs = preceding.rfind('*/')
            cmt_start_abs = preceding.rfind('/*', 0, cmt_end_abs)
            if cmt_start_abs < 0:
                self._v(fn_pos, sev, "misc.function_doc_header",
                        f"Function '{name}' must be preceded by a "
                        f"documentation comment block (ESA-R-1, JSF)")
                continue

            comment_body = preceding[cmt_start_abs: cmt_end_abs + 2]

            tags_brief  = ['@brief', '\\brief', '@details', '\\details']
            tags_param  = ['@param', '\\param']
            tags_return = ['@return', '@returns', '\\return', '\\returns']

            if req_brief and style != 'any':
                if not any(t in comment_body for t in tags_brief):
                    self._v(fn_pos, sev, "misc.function_doc_header",
                            f"Function '{name}' doc comment is missing "
                            f"@brief (ESA-R-1, JSF)")

            # Extract parameter names from signature
            paren_open = self.clean.find('(', fn_pos)
            open_brace = self.clean.find('{', fn_pos)
            if paren_open >= 0 and open_brace > paren_open:
                sig_text = self.clean[paren_open:open_brace]
                param_names = [
                    pm.group(1) for pm in RE_FUNCTION_PARAM.finditer(sig_text)
                ]
            else:
                param_names = []

            if req_param and param_names:
                if not any(t in comment_body for t in tags_param):
                    self._v(fn_pos, sev, "misc.function_doc_header",
                            f"Function '{name}' doc comment is missing "
                            f"@param entries (ESA-R-1, JSF)")

            if req_return:
                # Determine return type: text before function name in the match
                match_text = self.clean[fn_pos: fn_pos + 300]
                name_idx = match_text.find(name)
                pre_name = match_text[:name_idx] if name_idx >= 0 else ''
                pre_clean = re.sub(
                    r'\b(?:static|inline|extern|const|volatile|unsigned|signed'
                    r'|long|short|STATIC|INLINE|EXTERN|CONST|LOCAL_INLINE)\b',
                    ' ', pre_name,
                ).strip()
                parts = pre_clean.split()
                return_type = parts[-1].rstrip('*') if parts else ''
                if return_type and return_type not in ('void', ''):
                    if not any(t in comment_body for t in tags_return):
                        self._v(fn_pos, sev, "misc.function_doc_header",
                                f"Function '{name}' (returns '{return_type}') "
                                f"doc comment is missing @return (ESA-R-1, JSF)")

    # -----------------------------------------------------------------------
    # New rule: misc.assert_density (JPL Power of Ten Rule 5, issue #225)
    # -----------------------------------------------------------------------

    def _check_assert_density(self) -> None:
        """Require a minimum number of assert() calls per non-trivial function."""
        ad_cfg = self.cfg.get("misc", {}).get("assert_density", {})
        if not ad_cfg.get("enabled", False):
            return
        sev = ad_cfg.get("severity", "info")
        min_asserts = int(ad_cfg.get("min_asserts", 1))
        min_fn_lines = int(ad_cfg.get("min_function_lines", 10))
        exempt_fns = ad_cfg.get("exempt_functions", [])

        for fn_pos, name, body_start, body_end in self._iter_function_bodies():
            if is_exempt(name, exempt_fns):
                continue

            body_src = self.source[body_start:body_end]
            if len(body_src.splitlines()) < min_fn_lines:
                continue

            assert_count = len(re.findall(r'\bassert\s*\(', body_src))
            if assert_count < min_asserts:
                self._v(
                    fn_pos, sev, "misc.assert_density",
                    f"Function '{name}' has {assert_count} assert() call(s); "
                    f"minimum is {min_asserts} (Power of Ten Rule 5)",
                )

    # -----------------------------------------------------------------------
    # New rule: misc.declaration_spacing (Linux LK-8, issue #229)
    # -----------------------------------------------------------------------

    def _check_declaration_spacing(self) -> None:
        """Require a blank line between the declaration block and first statement."""
        ds_cfg = self.cfg.get("misc", {}).get("declaration_spacing", {})
        if not ds_cfg.get("enabled", False):
            return
        sev = ds_cfg.get("severity", "info")

        _RE_DECL = re.compile(
            r"^\s*(?:(?:static|extern|volatile|const|unsigned|signed|long|short)\s+)*"
            r"(?:int|char|float|double|uint\w+|int\w+|bool|_Bool|size_t|[A-Z_]\w+_[Tt])"
            r"[ \t]*\*{0,2}[ \t]*\w+[ \t]*(?:=|;|\[)"
        )

        for fn_pos, name, body_start, body_end in self._iter_function_bodies():
            # Work inside the body (exclude the outer braces)
            inner_src = self.source[body_start + 1: body_end - 1]
            first_lineno = self.source[:body_start + 1].count('\n') + 2
            lines = inner_src.splitlines()

            last_decl_idx = -1
            first_exec_idx = -1

            for idx, line in enumerate(lines):
                stripped = line.strip()
                if not stripped:
                    continue
                abs_ln = first_lineno + idx
                if abs_ln in self._comment_only:
                    continue

                if first_exec_idx < 0:  # still scanning for transition
                    if _RE_DECL.match(line):
                        last_decl_idx = idx
                    elif last_decl_idx >= 0:
                        # First non-decl, non-blank line after declarations
                        first_exec_idx = idx
                        break
                    else:
                        # Function starts with executable — no decl block
                        break

            if last_decl_idx < 0 or first_exec_idx < 0:
                continue

            has_blank = any(
                not lines[j].strip()
                for j in range(last_decl_idx + 1, first_exec_idx)
            )
            if not has_blank:
                abs_exec = first_lineno + first_exec_idx
                self.result.add(Violation(
                    self.filepath, abs_exec, 1, sev,
                    "misc.declaration_spacing",
                    f"First executable statement in '{name}' should be "
                    f"preceded by a blank line after the declaration block "
                    f"(Linux LK-8)",
                ))

    # -----------------------------------------------------------------------
    # New rule: misc.file_length (ESA/industry practice, issue #232)
    # -----------------------------------------------------------------------

    def _check_file_length(self) -> None:
        """Flag files whose total line count exceeds a configurable maximum."""
        fl_cfg = self.cfg.get("misc", {}).get("file_length", {})
        if not fl_cfg.get("enabled", True):
            return
        sev = fl_cfg.get("severity", "warning")
        max_lines = int(fl_cfg.get("max_lines", 500))
        count_blank = fl_cfg.get("count_blank_lines", True)
        count_comment = fl_cfg.get("count_comment_lines", True)

        lines = self.source.splitlines()

        if count_blank and count_comment:
            total = len(lines)
        else:
            total = 0
            for lineno, ln in enumerate(lines, 1):
                if not count_blank and not ln.strip():
                    continue
                if not count_comment and lineno in self._comment_only:
                    continue
                total += 1

        if total > max_lines:
            self.result.add(Violation(
                self.filepath, 1, 1, sev, "misc.file_length",
                f"File has {total} lines, exceeding maximum {max_lines}",
            ))

    # -----------------------------------------------------------------------
    # New rule: misc.reserved_header_name (CERT PRE04-C, issue #230)
    # -----------------------------------------------------------------------

    def _check_reserved_header_name(self) -> None:
        """Flag source files whose name collides with a standard C/POSIX header."""
        rhn_cfg = self.cfg.get("misc", {}).get("reserved_header_name", {})
        if not rhn_cfg.get("enabled", True):
            return
        sev = rhn_cfg.get("severity", "error")
        extra = {n.lower().strip() for n in rhn_cfg.get("extra_reserved", [])}

        basename = Path(self.filepath).name.lower()
        if basename in _STANDARD_C_HEADERS or basename in extra:
            self.result.add(Violation(
                self.filepath, 1, 1, sev, "misc.reserved_header_name",
                f"'{basename}' is a reserved C/POSIX header name; "
                f"rename this file to avoid include-path collisions "
                f"(CERT PRE04-C)",
            ))

    # -----------------------------------------------------------------------
    # New rule: misc.null_statement_comment (JSF Rule 192, issue #228)
    # -----------------------------------------------------------------------

    def _check_null_statement_comment(self) -> None:
        """Flag null statements without an explanatory comment (JSF Rule 192)."""
        ns_cfg = self.cfg.get("misc", {}).get("null_statement_comment", {})
        if not ns_cfg.get("enabled", True):
            return
        sev = ns_cfg.get("severity", "warning")

        # Pattern 1: control-flow keyword with ; on the SAME LINE only.
        # [^()\n] prevents matching across newlines.
        # Allows one level of nested parens (e.g. while(fn());).
        _RE_INLINE_NULL = re.compile(
            r'\b(?:while|for|if)[ \t]*\((?:[^()\n]|\([^()\n]*\))*\)[ \t]*;',
        )
        # do-while terminator: "} while (condition);" — not a null statement.
        _RE_DO_WHILE_END = re.compile(r'^\}\s*while\s*\(.*\)\s*;')
        for m in _RE_INLINE_NULL.finditer(self.clean):
            # Skip the closing line of a do-while loop.
            line_start = self.clean.rfind('\n', 0, m.start()) + 1
            line_text  = self.clean[line_start: self.clean.find('\n', m.start())]
            if _RE_DO_WHILE_END.match(line_text.strip()):
                continue
            self._v(m.start(), sev, "misc.null_statement_comment",
                    "Null statement on same line as control expression; "
                    "put ';' on its own line with an explanatory comment "
                    "(JSF Rule 192)")

        # Pattern 2: standalone ';' on its own line without a comment
        for lineno, line in enumerate(self.source.splitlines(), 1):
            if line.strip() == ';':
                self.result.add(Violation(
                    self.filepath, lineno, 1, sev,
                    "misc.null_statement_comment",
                    "Standalone null statement ';' must be accompanied by an "
                    "explanatory comment (JSF Rule 192)",
                ))

    # -----------------------------------------------------------------------
    # New rule: naming.identifier_length (ESA-R-7, JSF Rule 45, issue #227)
    # -----------------------------------------------------------------------

    def _check_identifier_length(self) -> None:
        """Enforce configurable min/max identifier length across all identifier types."""
        il_cfg = self.cfg.get("naming", {}).get("identifier_length", {})
        if not il_cfg.get("enabled", False):
            return
        sev = il_cfg.get("severity", "warning")
        min_len = il_cfg.get("min_length", 3)
        max_len = il_cfg.get("max_length", 31)
        exempt = set(il_cfg.get("exempt_names", ["i", "j", "k", "n", "x", "y", "z"]))
        check_vars = il_cfg.get("check_variables", True)
        check_fns = il_cfg.get("check_functions", True)
        check_macros_flag = il_cfg.get("check_macros", True)
        check_types = il_cfg.get("check_types", True)

        def _emit(name: str, pos: int) -> None:
            if name in exempt or name in self._c_keywords:
                return
            n = len(name)
            if min_len and n < min_len:
                self._v(pos, sev, "naming.identifier_length",
                        f"Identifier '{name}' length {n} is below "
                        f"minimum {min_len} (ESA-R-7)")
            if max_len and n > max_len:
                self._v(pos, sev, "naming.identifier_length",
                        f"Identifier '{name}' length {n} exceeds "
                        f"maximum {max_len} (JSF Rule 45)")

        if check_vars:
            for m in RE_VAR_DECL.finditer(self.clean):
                name = m.group(4)
                if name:
                    _emit(name, m.start())

        if check_fns:
            for m in RE_FUNCTION_DEF.finditer(self.clean):
                name = m.group(1)
                if name:
                    _emit(name, m.start())

        if check_macros_flag:
            for m in RE_DEFINE.finditer(self.clean):
                name = m.group(1)
                rest = self.clean[m.end():].split("\n")[0].strip()
                if rest and name:
                    _emit(name, m.start())

        if check_types:
            for m in RE_TYPEDEF_SIMPLE.finditer(self.clean):
                name = m.group(1)
                if name:
                    _emit(name, m.start())

    # -----------------------------------------------------------------------
    # New rule: naming.no_single_char_identifiers (ESA-R-4, issue #231)
    # -----------------------------------------------------------------------

    def _check_no_single_char_identifiers(self) -> None:
        """Flag single-character identifiers outside the configured exempt list."""
        ni_cfg = self.cfg.get("naming", {}).get("no_single_char_identifiers", {})
        if not ni_cfg.get("enabled", False):
            return
        sev = ni_cfg.get("severity", "warning")
        exempt = set(ni_cfg.get("exempt", ["i", "j", "k", "n", "x", "y", "z"]))

        for m in RE_VAR_DECL.finditer(self.clean):
            name = m.group(4)
            if name and len(name) == 1 and name not in exempt:
                self._v(m.start(), sev, "naming.no_single_char_identifiers",
                        f"Single-character identifier '{name}' is not allowed "
                        f"(ESA-R-4)")

        # Also check function parameters via signature scanning
        for fn_m in RE_FUNCTION_DEF.finditer(self.clean):
            paren_open = self.clean.find("(", fn_m.start())
            open_brace = self.clean.find("{", fn_m.start())
            if paren_open < 0 or open_brace <= paren_open:
                continue
            sig = self.clean[paren_open:open_brace]
            for pm in RE_FUNCTION_PARAM.finditer(sig):
                pname = pm.group(1)
                if pname and len(pname) == 1 and pname not in exempt:
                    self._v(paren_open + pm.start(), sev,
                            "naming.no_single_char_identifiers",
                            f"Single-character parameter '{pname}' is not "
                            f"allowed (ESA-R-4)")

