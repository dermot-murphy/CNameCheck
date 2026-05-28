"""
models.py — Core data structures for CStyleCheck.

Contains Violation, CheckResult, _ParamSig, and _FuncSig.
No internal dependencies (stdlib only).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

_MISRA_ANNOTATION_RULES: frozenset = frozenset({
    "misc.trigraph",
    "misc.octal_constant",
    "misc.lowercase_l_suffix",
})

_NAMING_ANNOTATION_PREFIXES: frozenset = frozenset({
    "constant",
    "enum",
    "function",
    "include_guard",
    "macro",
    "reserved_name",
    "struct",
    "typedef",
    "variable",
})


@dataclass
class Violation:
    filepath: str
    line: int
    col: int
    severity: str          # error | warning | info
    rule: str
    message: str

    def github_annotation(self) -> str:
        from .utils import _github_annotation_category
        level = (
            self.severity
            if self.severity in ("error", "warning", "notice")
            else "notice"
        )
        title = _github_annotation_category(self.rule)
        return (
            f"::{level} file={self.filepath},line={self.line},"
            f"col={self.col},title={title}[{self.rule}]::"
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
# Sign-checker constants (shared between checker.py and sign_checker.py)
# ---------------------------------------------------------------------------

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
    signedness: str   # signed | unsigned | unknown


@dataclass
class _FuncSig:
    """Resolved signature of a declared function."""
    name:   str
    params: list      # list[_ParamSig]
