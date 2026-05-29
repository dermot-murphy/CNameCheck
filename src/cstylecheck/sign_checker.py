"""
sign_checker.py — Cross-file sign compatibility and declared-not-defined checkers.

Contains SignChecker, DeclaredNotDefinedChecker, and sign-analysis helpers
(_classify_tokens, _signedness_of_type, _classify_arg, _extract_call_args).

Imports from: models, preprocessor, checker (regex patterns).
"""
from __future__ import annotations

import re

from .models import (
    Violation,
    _ParamSig, _FuncSig,
    _SIGN_SIGNED, _SIGN_UNSIGNED, _SIGN_UNKNOWN, _SIGN_NEUTRAL,
    _SIGNED_TYPES, _UNSIGNED_TYPES,
)
from .preprocessor import (
    preprocess, build_line_map, offset_to_line_col,
    _build_brace_depths,
)
from .checker import (
    RE_FUNCTION_DEF, RE_FUNCTION_DECL,
    RE_TYPEDEF_STRUCT, RE_TYPEDEF_ENUM,
    RE_VAR_DECL,
)
from .config import apply_defines

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


def _classify_tokens(tokens: list,
                     signed_types: set = None,
                     unsigned_types: set = None) -> str:
    """Return sign classification from a list of type/qualifier tokens.

    *signed_types* and *unsigned_types* default to the module-level sets when
    not supplied.  Passing explicit copies is the thread-safe path used by
    ``SignChecker`` so that the ``plain_char_is_signed`` option never mutates
    the module globals.
    """
    _st = signed_types   if signed_types   is not None else _SIGNED_TYPES
    _ut = unsigned_types if unsigned_types is not None else _UNSIGNED_TYPES
    tset = set(tokens)
    if "unsigned" in tset:
        return _SIGN_UNSIGNED
    if "signed" in tset:
        return _SIGN_SIGNED
    for t in tokens:
        if t in _ut:
            return _SIGN_UNSIGNED
        if t in _st:
            return _SIGN_SIGNED
    return _SIGN_UNKNOWN


def _signedness_of_type(type_str: str, tmap: dict,
                        signed_types: set = None,
                        unsigned_types: set = None) -> str:
    """Resolve a full type string (e.g. 'int8_t' or 'unsigned short') to a sign."""
    tokens = type_str.split()
    result = _classify_tokens(tokens, signed_types, unsigned_types)
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

        # Build thread-safe local copies of the sign-type sets.
        # Do NOT mutate the module-level globals — concurrent SignChecker
        # instances (e.g. pytest-xdist) would race on them.
        signed_types   = set(_SIGNED_TYPES)
        unsigned_types = set(_UNSIGNED_TYPES)
        if not sc_cfg.get("plain_char_is_signed", True):
            signed_types.discard("char")
            unsigned_types.add("char")

        self._build_typedef_map(signed_types, unsigned_types)
        self._build_signatures(signed_types, unsigned_types)
        return self._check_calls(sev, signed_types, unsigned_types)

    # --- Stage 1: typedef resolution ---

    def _build_typedef_map(self, signed_types: set, unsigned_types: set) -> None:
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
                result = _classify_tokens(tokens, signed_types, unsigned_types)
            resolved[name] = result
            return result

        for n in raw:
            resolve(n)
        self._tmap = resolved

    # --- Stage 2: function signature extraction ---

    def _build_signatures(self, signed_types: set, unsigned_types: set) -> None:
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
                    sign     = _signedness_of_type(type_str, self._tmap,
                                                   signed_types, unsigned_types)
                    params.append(_ParamSig(pname, type_str, sign))
                # Prefer the first (header) declaration if already seen
                if fname not in self._sigs:
                    self._sigs[fname] = _FuncSig(fname, params)

    # --- Stage 3: call-site sign checking ---

    def _check_calls(self, sev: str,
                     signed_types: set, unsigned_types: set) -> list:
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
# DeclaredNotDefinedChecker (cross-file declared-but-not-defined check)
# ---------------------------------------------------------------------------

class DeclaredNotDefinedChecker:
    """
    Cross-file declared-but-not-defined checker (misc.declared_not_defined).

    Identifies C objects that are declared (via 'extern' or a forward typedef)
    but for which no matching definition can be found across all files in a
    single checker invocation.

    Single-file runs always emit no violations — the definition may exist in
    an unscanned translation unit (e.g. a BSP provided at link time).

    Usage:
        dndc = DeclaredNotDefinedChecker(cfg)
        for filepath, source in all_files:
            dndc.ingest(filepath, source)
        violations = dndc.check()
    """

    # extern <type> <name> ;  — variable/constant declaration (no parens → not a function)
    _RE_EXTERN_VAR = re.compile(
        r"(?:^|\n)[ \t]*extern[ \t]+"
        r"(?:(?:const|volatile|unsigned|signed|long|short"
        r"|struct|enum|union)[ \t]+)*"
        r"[A-Za-z_]\w*(?:[ \t]*\*+)?[ \t]*"
        r"([A-Za-z_]\w*)"               # variable name — group 1
        r"(?![ \t]*\()"                  # NOT followed by ( → not a function
        r"[ \t]*(?:\[[^\]]*\][ \t]*)*"  # optional array brackets
        r"[ \t]*;",
        re.MULTILINE,
    )

    # typedef struct Tag Tag;  — forward struct typedef (no body brace between names)
    _RE_FWD_STRUCT = re.compile(
        r"(?:^|\n)[ \t]*typedef[ \t]+struct[ \t]+"
        r"([A-Za-z_]\w*)[ \t]+"         # struct tag name — group 1
        r"([A-Za-z_]\w*)[ \t]*;",       # alias name — group 2
        re.MULTILINE,
    )

    # typedef enum Tag Tag;  — forward enum typedef (no body brace between names)
    _RE_FWD_ENUM = re.compile(
        r"(?:^|\n)[ \t]*typedef[ \t]+enum[ \t]+"
        r"([A-Za-z_]\w*)[ \t]+"         # enum tag name — group 1
        r"([A-Za-z_]\w*)[ \t]*;",       # alias name — group 2
        re.MULTILINE,
    )

    # Non-extern, non-static file-scope variable definition (any identifier casing).
    # Ends with = ; or [ so function definitions (ending with {) are excluded.
    _RE_VAR_DEF = re.compile(
        r"(?:^|\n)[ \t]*"
        r"(?!(?:extern|static|typedef|if|else|while|for|do|switch|return"
        r"|break|continue|goto|sizeof|case|assert)\b)"
        r"(?:(?:volatile|const|unsigned|signed|long|short"
        r"|struct|enum|union)[ \t]+)*"
        r"(?:(?:long[ \t]+long|long|short)[ \t]+)?"
        r"[A-Za-z_]\w*(?:[ \t]*\*+)?[ \t]*"
        r"([A-Za-z_]\w*)"               # defined name — group 1
        r"(?![ \t]*\()"                  # NOT a function definition
        r"[ \t]*(?:=|;|\[)",
        re.MULTILINE,
    )

    def __init__(self, cfg: dict, defines: list = None):
        self._cfg:         dict = cfg
        self._defines:     list = defines or []
        self._decls:       list = []   # (filepath, line, col, name, kind)
        self._func_defs:   set  = set()
        self._var_defs:    set  = set()
        self._struct_defs: set  = set()
        self._enum_defs:   set  = set()
        self._file_count:  int  = 0
        # Pre-compile extern_macros patterns for fast substitution in ingest().
        dnd_cfg = cfg.get("misc", {}).get("declared_not_defined", {})
        self._extern_macro_res: list = [
            re.compile(r'\b' + re.escape(m) + r'\b')
            for m in dnd_cfg.get("extern_macros", [])
        ]

    def _apply_extern_substitutions(self, clean: str) -> str:
        """
        Substitute extern-alias macros so pattern matching can find them.

        Two mechanisms are supported (applied in order):

        1. **``--defines`` file** — if the user already lists the macro in
           their project defines file (e.g. ``API_WDT_EXTERN  extern``),
           ``apply_defines()`` performs whole-word substitution.  The
           DeclaredNotDefinedChecker receives the same defines list as the
           main Checker, so no extra configuration is required.

        2. **``misc.declared_not_defined.extern_macros``** — a YAML list of
           macro names that represent ``extern`` linkage for the purposes of
           this rule only.  Useful when the macro is not in the project defines
           file or expands to something more complex (e.g.
           ``__declspec(dllimport)``).

        Both mechanisms replace the macro with the literal token ``extern``
        so that ``RE_FUNCTION_DECL`` and the ``extern``-keyword filter in
        ``ingest()`` work unchanged.
        """
        if self._defines:
            clean = apply_defines(clean, self._defines)
        for pat in self._extern_macro_res:
            clean = pat.sub("extern", clean)
        return clean

    def ingest(self, filepath: str, source: str) -> None:
        """Scan one file for declarations and definitions."""
        self._file_count += 1
        clean        = preprocess(source)
        # Apply --defines and extern_macros substitutions so that macros such
        # as API_WDT_EXTERN (which expand to 'extern') are recognised as
        # extern declarations by the pattern matchers below (issue #168).
        clean        = self._apply_extern_substitutions(clean)
        line_map     = build_line_map(clean)
        brace_depths = _build_brace_depths(clean)
        src_lines    = source.splitlines()

        def _suppressed(lineno: int) -> bool:
            raw = src_lines[lineno - 1] if 0 < lineno <= len(src_lines) else ""
            return "cstylecheck: disable misc.declared_not_defined" in raw

        # --- Collect definitions (satisfy declarations) ---

        for m in RE_FUNCTION_DEF.finditer(clean):
            self._func_defs.add(m.group(1))

        for m in RE_TYPEDEF_STRUCT.finditer(clean):
            name = m.group(3)
            if name:
                self._struct_defs.add(name)

        for m in RE_TYPEDEF_ENUM.finditer(clean):
            name = m.group(2)
            if name:
                self._enum_defs.add(name)

        # File-scope non-extern/non-static variable definitions (brace depth 0)
        for m in self._RE_VAR_DEF.finditer(clean):
            pos = m.start()
            if pos < len(brace_depths) and brace_depths[pos] == 0:
                self._var_defs.add(m.group(1))

        # RE_VAR_DECL captures lowercase names; also add them for completeness.
        for m in RE_VAR_DECL.finditer(clean):
            if "extern" not in m.group(1) and "static" not in m.group(1):
                pos = m.start()
                if pos < len(brace_depths) and brace_depths[pos] == 0:
                    self._var_defs.add(m.group(4))

        # --- Collect declarations (to be satisfied by definitions) ---

        # Extern function declarations
        for m in RE_FUNCTION_DECL.finditer(clean):
            if not re.search(r"\bextern\b", m.group(0)):
                continue
            pos = m.start()
            if pos < len(brace_depths) and brace_depths[pos] != 0:
                continue   # inside a nested scope — skip
            fname  = m.group(1)
            line, col = offset_to_line_col(line_map, m.start(1))
            if _suppressed(line):
                continue
            self._decls.append((filepath, line, col, fname, "function"))

        # Extern variable declarations
        for m in self._RE_EXTERN_VAR.finditer(clean):
            pos = m.start()
            if pos < len(brace_depths) and brace_depths[pos] != 0:
                continue
            vname  = m.group(1)
            line, col = offset_to_line_col(line_map, m.start(1))
            if _suppressed(line):
                continue
            self._decls.append((filepath, line, col, vname, "variable"))

        # Forward typedef struct declarations
        for m in self._RE_FWD_STRUCT.finditer(clean):
            pos = m.start()
            if pos < len(brace_depths) and brace_depths[pos] != 0:
                continue
            tname  = m.group(2)   # the typedef alias name
            line, col = offset_to_line_col(line_map, m.start(2))
            if _suppressed(line):
                continue
            self._decls.append((filepath, line, col, tname, "typedef_struct"))

        # Forward typedef enum declarations
        for m in self._RE_FWD_ENUM.finditer(clean):
            pos = m.start()
            if pos < len(brace_depths) and brace_depths[pos] != 0:
                continue
            tname  = m.group(2)   # the typedef alias name
            line, col = offset_to_line_col(line_map, m.start(2))
            if _suppressed(line):
                continue
            self._decls.append((filepath, line, col, tname, "typedef_enum"))

    def check(self) -> list:
        """Return violations for all declared-but-not-defined objects."""
        cfg = self._cfg.get("misc", {}).get("declared_not_defined", {})
        if not cfg.get("enabled", False):
            return []
        if self._file_count < 2:
            # Single-file run: definition may exist in an unscanned TU
            return []
        sev        = cfg.get("severity", "warning")
        seen:       set  = set()
        violations: list = []
        for filepath, line, col, name, kind in self._decls:
            if name in seen:
                continue
            seen.add(name)
            if kind == "function":
                defined = name in self._func_defs
            elif kind == "variable":
                defined = name in self._var_defs
            elif kind == "typedef_struct":
                defined = name in self._struct_defs
            else:   # typedef_enum
                defined = name in self._enum_defs
            if not defined:
                violations.append(Violation(
                    filepath, line, col, sev,
                    "misc.declared_not_defined",
                    f"'{name}' is declared but no definition found in scanned files",
                ))
        return violations

