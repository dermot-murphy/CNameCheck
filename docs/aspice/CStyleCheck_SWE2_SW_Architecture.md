# Software Architecture Description

*Automotive SPICE® PAM v4.0 | SWE.2 Software Architectural Design*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CSC-SWE2-001 | **Version** | 1.7 |
| **Project** | CStyleCheck | **Date** | 2026-06-05 |
| **Status** | Released | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SWE.2 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.7 | 2026-06-08 | Claude | ASPICE audit #238 — add COMP-05h (naming rules); extend §10 RTM with SWE1-078–088 |
| 1.6 | 2026-06-05 | Claude | CSC-AUD-005 corrective action — fix factual errors identified in audit |
| 1.5 | 2026-06-04 | Claude | Add COMP-08 (Fixer), COMP-09 (Config Wizard), COMP-10 (Per-dir Config); add `parse_inline_suppressions` to COMP-04; add `_violations_to_html` to COMP-07; update §8.1 sequence; update §10 RTM — issues #188 #189 #190 #193 #192 |
| 1.4 | 2026-06-04 | Claude | Deep accuracy audit: fix §3 version text, update §3.1 referenced doc versions, fix COMP-05f functions (remove non-existent, add missing), add comment/whitespace ratio to §8.1 sequence, add SWE1-071/MISRA rows to §10 RTM, add config utility functions to COMP-02 — resolves issue #163 |
| 1.3 | 2026-06-04 | Claude | Automated accuracy audit: update referenced doc versions in §3.1 — resolves issue #163 |
| 1.2 | 2026-05-28 | Claude | Update §3/§4 to reflect package refactor (issue #144): replace "single Python module (cstylecheck.py)" with "Python package (src/cstylecheck/)" — closes issue #146 |
| 1.1 | 2026-05-28 | Claude | Reviewed and updated for v1.1.0 release; revision history maintained per ASPICE GP 2.2.4 |
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose & Scope

This Software Architecture Description defines the internal structure, component decomposition, interfaces, and dynamic behaviour of **CStyleCheck v1.2.x**. It refines the system architecture (CSC-SYS3-001) to the software component level, providing the design basis for detailed design (SWE.3) and integration testing (SWE.5).

This document satisfies **Automotive SPICE® PAM v4.0, SWE.2 — Software Architectural Design**.

### 3.1 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CSC-SWE1-001 | CStyleCheck Software Requirements Specification | 1.7 |
| CSC-SYS3-001 | CStyleCheck System Architecture Description | 1.4 |
| CSC-SWE3-001 | CStyleCheck Software Detailed Design | 1.8 |
| CSC-SUP8-001 | CStyleCheck Configuration Management Plan | 1.5 |

---

## 4. Architectural Overview

CStyleCheck is implemented as a **Python package** (`src/cstylecheck/`) comprising 12 sub-modules with supporting data files. The package is structured into distinct functional components that map directly to the system-level subsystems defined in CSC-SYS3-001. The architecture follows a **pipeline pattern**: each source file passes sequentially through preprocessing, caching, rule evaluation, and output formatting.

```
src/cstylecheck/   (package — 12 sub-modules)
│
├── [COMP-01] CLI & Options Loader     (parse_args, _expand_options_file, discover_files)
├── [COMP-02] Configuration Loader     (load_config, load_alias_file, load_exclusions_file,
│                                       load_defines_file, apply_defines, update_config,
│                                       _find_default_rules, _deep_merge, _collect_paths)
├── [COMP-03] Dictionary Manager       (_load_dict_file, _data_file, _build_spell_dict,
│                                       load_spell_words, load_banned_names_file)
├── [COMP-04] Source Parser & Cache    (strip_comments, strip_strings, preprocess,
│                                       build_line_map, offset_to_line_col,
│                                       _build_brace_depths, _comment_only_lines,
│                                       extract_comments, parse_inline_suppressions)
├── [COMP-05] Rule Engine              (class Checker — all _check_* methods)
│   ├── [COMP-05a] Variable Checker    (_check_variables)
│   ├── [COMP-05b] Function Checker    (_check_functions)
│   ├── [COMP-05c] Define Checker      (_check_defines)
│   ├── [COMP-05d] Type Checker        (_check_typedefs, _check_enums, _check_structs)
│   ├── [COMP-05e] Guard Checker       (_check_include_guard)
│   ├── [COMP-05f] Misc Checker        (_check_misc, _check_yoda, _check_spelling,
│   │                                   _check_reserved_names, _check_copyright_header,
│   │                                   _check_comment_ratio, _check_whitespace_ratio,
│   │                                   _check_function_length, _check_function_doc_header,
│   │                                   _check_assert_density, _check_null_statement_comment,
│   │                                   _check_declaration_spacing, _check_file_length,
│   │                                   _check_reserved_header_name)
│   ├── [COMP-05g] Sign Checker        (class SignChecker — _check_calls)
│   └── [COMP-05h] Naming Checker      (_check_identifier_length,
│                                       _check_no_single_char_identifiers)
├── [COMP-06] Baseline Manager         (load_baseline, write_baseline, _baseline_key)
├── [COMP-07] Output Formatter         (_violations_to_json, _violations_to_sarif,
│                                       _violations_to_html, print_summary,
│                                       class Tee, Violation.github_annotation)
├── [COMP-08] Fixer                    (fixer.py — apply_fixes, --fix, --dry-run, --safe-only)
├── [COMP-09] Config Wizard            (wizard.py — run_wizard, run_preset,
│                                       --init, --preset, --init-output, --overwrite)
└── [COMP-10] Per-directory Config     (config.resolve_per_dir_config — upward dir-walk,
                                        deep-merge, root-stop, per-dir cache)
```

---

## 5. Component Descriptions

### COMP-01 — CLI & Options Loader

| Attribute | Value |
|---|---|
| **Source functions** | `parse_args()`, `_build_parser()`, `_expand_options_file()`, `_read_options_file()`, `discover_files()`, `_path_matches_exclude()` |
| **Responsibility** | Parse command-line arguments; expand `--options-file` tokens before direct CLI args; resolve source file lists from globs; validate invocation |
| **Inputs** | `sys.argv`; options file on disk |
| **Outputs** | `argparse.Namespace` object; resolved `[filepath]` list |
| **Key behaviour** | Options-file tokens are injected before direct argv tokens so direct args always take precedence |

### COMP-02 — Configuration Loader

| Attribute | Value |
|---|---|
| **Source functions** | `load_config()`, `load_alias_file()`, `load_exclusions_file()`, `_disabled_rules_for_file()`, `load_defines_file()`, `apply_defines()`, `update_config()`, `_find_default_rules()`, `_deep_merge()`, `_collect_paths()` |
| **Responsibility** | Load and validate YAML config; build alias-prefix lists; resolve per-file disabled rules; apply defines substitutions to preprocessed source |
| **Inputs** | YAML config file path; alias file path; exclusions file path; defines file path |
| **Outputs** | `cfg` dict; `alias_prefixes` list; `disabled_rules` frozenset; preprocessed source text |

### COMP-03 — Dictionary Manager

| Attribute | Value |
|---|---|
| **Source functions** | `_load_dict_file()`, `_data_file()`, `_build_spell_dict()`, `load_spell_words()`, `load_banned_names_file()` |
| **Responsibility** | Load C keyword, stdlib, spell-check, and banned-name dictionaries; locate built-in data files via `_data_file()` with install-path fallback |
| **Inputs** | File paths (from CLI or defaults) |
| **Outputs** | `frozenset` objects for keywords, stdlib names, spell words, banned names |

### COMP-04 — Source Parser & Cache

| Attribute | Value |
|---|---|
| **Source functions** | `strip_comments()`, `strip_strings()`, `preprocess()`, `build_line_map()`, `offset_to_line_col()`, `_build_brace_depths()`, `_comment_only_lines()`, `extract_comments()`, `parse_inline_suppressions()` |
| **Responsibility** | Produce a clean (comment/string-free) version of source; build offset→(line,col) map; build brace-depth array for scope inference; cache raw source for cross-file checks; parse inline suppression directives from source comments |
| **Inputs** | Raw source text string |
| **Outputs** | `clean` source string; `_line_map` list; `_brace_depths` list; `_comment_only` set |

### COMP-05 — Rule Engine (`class Checker`)

The `Checker` class is the central analysis component. It is instantiated once per source file, receives all parsed inputs, and exposes a `run_all()` method that orchestrates all sub-checkers.

| Attribute | Value |
|---|---|
| **Class** | `Checker` |
| **Constructor inputs** | `filepath`, `source`, `cfg`, `spell_words`, `alias_prefixes`, `disabled_rules`, `ident_disabled_rules`, `defines`, `extra_banned`, `copyright_header` |
| **Public interface** | `run_all() → CheckResult` |
| **Internal state** | `self.clean`, `self.module`, `self.result`, `self._line_map`, `self._brace_depths`, `self._comment_only`, `self._disabled_rules`, `self._alias_prefixes` |

#### COMP-05a — Variable Checker

| Method | Key Regex | Rules Enforced |
|---|---|---|
| `_check_variables()` | `RE_VAR_DECL` | `variable.global.*`, `variable.static.*`, `variable.local.*`, `variable.parameter.*`, `variable.pointer_prefix`, `variable.pp_prefix`, `variable.bool_prefix`, `variable.handle_prefix`, `variable.prefix_order`, `variable.min_length`, `variable.max_length`, `variable.no_numeric_in_name` |

#### COMP-05b — Function Checker

| Method | Key Regex | Rules Enforced |
|---|---|---|
| `_check_functions()` | `RE_FUNC_DEF` | `function.prefix`, `function.style`, `function.min_length`, `function.max_length`, `function.static_prefix` |

#### COMP-05c — Define Checker

| Method | Key Regex | Rules Enforced |
|---|---|---|
| `_check_defines()` | `RE_DEFINE` | `constant.case`, `constant.min_length`, `constant.max_length`, `constant.prefix`, `macro.case`, `macro.min_length`, `macro.max_length`, `macro.prefix` |

#### COMP-05d — Type Checker

| Method | Key Regex | Rules Enforced |
|---|---|---|
| `_check_typedefs()` | `RE_TYPEDEF_SIMPLE`, `RE_TYPEDEF_STRUCT` | `typedef.case`, `typedef.suffix` |
| `_check_enums()` | `RE_ENUM` | `enum.type_case`, `enum.type_suffix`, `enum.member_case`, `enum.member_prefix` |
| `_check_structs()` | `RE_STRUCT` | `struct.tag_case`, `struct.tag_suffix`, `struct.member_case` |

#### COMP-05e — Include Guard Checker

| Method | Rules Enforced |
|---|---|
| `_check_include_guard()` | `include_guard.missing`, `include_guard.format` |

#### COMP-05f — Miscellaneous Checker

| Method | Rules Enforced |
|---|---|
| `_check_misc()` | `misc.line_length`, `misc.indentation`, `misc.magic_number`, `misc.unsigned_suffix` |
| `_check_yoda()` | `misc.yoda_condition` |
| `_check_spelling()` | `spell_check` |
| `_check_reserved_names()` | `reserved_name` |
| `_check_copyright_header()` | `misc.copyright_header` |
| `_check_comment_ratio()` | `misc.comment_ratio` |
| `_check_whitespace_ratio()` | `misc.whitespace_ratio` |

#### COMP-05g — Sign Checker (`class SignChecker`)

| Attribute | Value |
|---|---|
| **Class** | `SignChecker` |
| **Responsibility** | Cross-file sign-compatibility analysis; resolves typedef chains; enforces `plain_char_is_signed` without global state mutation |
| **Key method** | `_check_calls()` — finds function calls and validates argument signedness against parameter declarations |
| **Rule enforced** | `sign_compatibility` |

#### COMP-05h — Naming Constraints Checker

| Attribute | Value |
|---|---|
| **Source module** | `checker.py` |
| **Methods** | `_check_identifier_length()`, `_check_no_single_char_identifiers()` |
| **Responsibility** | Enforce cross-category identifier naming constraints: uniform min/max length (`naming.identifier_length`) and single-character identifier prohibition (`naming.no_single_char_identifiers`); both rules are opt-in (disabled by default) |
| **Config section** | `naming:` |
| **Rules enforced** | `naming.identifier_length`, `naming.no_single_char_identifiers` |

### COMP-06 — Baseline Manager

| Attribute | Value |
|---|---|
| **Source functions** | `_baseline_key()`, `load_baseline()`, `write_baseline()` |
| **Responsibility** | Serialise/deserialise violation baselines; generate stable violation keys for suppression matching |
| **Baseline key** | `"{rule}::{filepath}::{line}::{message}"` |

### COMP-07 — Output Formatter

| Attribute | Value |
|---|---|
| **Source functions** | `_violations_to_json()`, `_violations_to_sarif()`, `_violations_to_html()`, `print_summary()`, `class Tee` |
| **Source method** | `Violation.__str__()`, `Violation.github_annotation()` |
| **Responsibility** | Render violations in text/JSON/SARIF/HTML; emit GitHub annotations; duplicate stdout to log file via `Tee`; print summary table |

### COMP-08 — Fixer

| Attribute | Value |
|---|---|
| **Source module** | `fixer.py` |
| **Responsibility** | Apply safe mechanical fixes in-place (`--fix`); show unified diff without writing (`--dry-run`); restrict to zero-risk fixes (`--safe-only`); currently fixable: `misc.unsigned_suffix` and `misc.lowercase_l_suffix` |
| **Inputs** | Source file list, violation list, CLI flags (`--fix`, `--dry-run`, `--safe-only`) |
| **Outputs** | Modified source files on disk, or unified diff to stdout |

### COMP-09 — Config Wizard

| Attribute | Value |
|---|---|
| **Source module** | `wizard.py` |
| **Responsibility** | Interactive Q&A wizard (`--init`) writing `.cstylecheck.yml`; pre-built config generation without wizard (`--preset barr-c\|minimal\|misra`); custom output path (`--init-output`); overwrite guard (`--overwrite`) |
| **Inputs** | CLI flags; interactive terminal input (for `--init`) |
| **Outputs** | `.cstylecheck.yml` (or `--init-output` path) |

### COMP-10 — Per-directory Config

| Attribute | Value |
|---|---|
| **Source function** | `config.resolve_per_dir_config()` |
| **Responsibility** | Walk upward from each source file's directory looking for `.cstylecheck.yml`; deep-merge found configs on top of the root config; the nearest (deepest) config wins; stop upward search at `root: true` or filesystem root; cache results per directory |
| **Inputs** | Source file path, root config dict |
| **Outputs** | Merged config dict for that file |

---

## 6. Data Structures

| Structure | Type | Fields | Used By |
|---|---|---|---|
| `Violation` | `@dataclass` | `filepath: str`, `line: int`, `col: int`, `severity: str`, `rule: str`, `message: str` | All COMP-05 sub-checkers → COMP-06, COMP-07 |
| `CheckResult` | `@dataclass` | `violations: List[Violation]` | COMP-05 → `main()` |
| `_ParamSig` | `@dataclass` | `name: str`, `type_str: str`, `signedness: str` | COMP-05g |
| `_FuncSig` | `@dataclass` | `name: str`, `params: List[_ParamSig]` | COMP-05g |
| `cfg` | `dict` | Nested YAML-derived configuration | COMP-02 → COMP-05 |

---

## 7. Inter-Component Interfaces

| Interface ID | From | To | Data | Notes |
|---|---|---|---|---|
| SWA-IF-01 | COMP-01 | COMP-02 | Config file path, defines path, aliases path, exclusions path | Paths from `argparse.Namespace` |
| SWA-IF-02 | COMP-01 | `main()` | Resolved file list, all CLI flags | `argparse.Namespace` |
| SWA-IF-03 | COMP-02 | COMP-05 | `cfg` dict, `alias_prefixes`, `disabled_rules` | Per-file constructor args |
| SWA-IF-04 | COMP-02 | COMP-04 | Source text (for `apply_defines`) | After initial read |
| SWA-IF-05 | COMP-03 | COMP-05 | Keyword `frozenset`, stdlib `frozenset`, spell `set`, banned `frozenset` | Constructor args |
| SWA-IF-06 | COMP-04 | COMP-05 | `clean` source, `_line_map`, `_brace_depths`, `_comment_only` | Constructor args via `Checker.__init__` |
| SWA-IF-07 | COMP-04 | COMP-05g | Raw source (cached) | Cross-file sign check reuses cached content |
| SWA-IF-08 | COMP-05 | COMP-06 | `List[Violation]` | Passed to `write_baseline()` or filtered by `load_baseline()` |
| SWA-IF-09 | COMP-06 | COMP-05 | `frozenset` of baseline keys | Used in `main()` to filter violations |
| SWA-IF-10 | COMP-05 | COMP-07 | `List[Violation]`, `files_checked: int` | Rendered to stdout / file / JSON / SARIF |

---

## 8. Dynamic Behaviour — Execution Sequence

### 8.1 Per-File Processing Loop

```
main()
│
├─ COMP-01: resolve file list [f1.c, f2.h, ...]
├─ COMP-02: load_config() → cfg
├─ COMP-03: load dictionaries → keyword_set, stdlib_set, spell_set
├─ COMP-06: load_baseline() → baseline_keys (if --baseline-file)
│
├─ for each file in file_list:
│   ├─ read file once → raw_source (cached in source_cache dict)
│   ├─ COMP-02: load_exclusions_file, _disabled_rules_for_file → disabled_rules
│   ├─ COMP-04: preprocess(raw_source) → clean; build_line_map; _build_brace_depths
│   ├─ COMP-05: Checker(filepath, raw_source, cfg, ...).run_all() → CheckResult
│   │   ├─ _check_defines()
│   │   ├─ _check_variables()
│   │   ├─ _check_functions()
│   │   ├─ _check_typedefs()
│   │   ├─ _check_enums()
│   │   ├─ _check_structs()
│   │   ├─ _check_include_guard()  [header files only]
│   │   ├─ _check_misc()
│   │   ├─ _check_comment_ratio()
│   │   ├─ _check_whitespace_ratio()
│   │   ├─ _check_yoda()
│   │   ├─ _check_spelling()
│   │   └─ _check_reserved_names()
│   └─ accumulate violations
│
├─ COMP-05g: SignChecker(source_cache, cfg).check() → sign violations
├─ filter violations against baseline_keys
├─ COMP-07: render output (text / JSON / SARIF)
└─ return exit code (0 / 1 / 2)
```

### 8.2 Error Handling

| Error Condition | Detection Point | Response |
|---|---|---|
| YAML config missing or malformed | `load_config()` (COMP-02) | `sys.exit(2)` with message to stderr |
| Source file unreadable | `main()` file read loop | Warning to stderr; file skipped |
| Baseline file malformed | `load_baseline()` (COMP-06) | `sys.exit(2)` with message to stderr |
| PyYAML not installed | Module import | `sys.exit("PyYAML is required")` |

---

## 9. Architecture Evaluation

| Quality Attribute | Design Decision | Evidence |
|---|---|---|
| Maintainability | All rule checks are independent methods; adding a rule requires adding one `_check_*` method and one YAML key | Low coupling between sub-checkers |
| Testability | `Checker` accepts `source` as a string; no file I/O inside the class; tests inject source directly | `harness.py` uses `run(source, cfg)` pattern |
| Portability | No third-party runtime imports beyond PyYAML; `_data_file()` handles pip-install vs source-checkout path differences | `pyproject.toml` dependencies |
| Performance | Single-read source cache; brace-depth array precomputed once per file | `SWE1-015`, `SWE1-014` |

---

## 10. Traceability: SW Requirements → Architecture Components

| SW-REQ-ID Range | Requirement Area | Component(s) |
|---|---|---|
| SWE1-001 to SWE1-006 | Configuration loading | COMP-02 |
| SWE1-007 to SWE1-010 | Dictionary management | COMP-03 |
| SWE1-011 to SWE1-016 | Source parsing and cache | COMP-04 |
| SWE1-017 to SWE1-029 | Variable rules | COMP-05a |
| SWE1-030 to SWE1-034 | Function rules | COMP-05b |
| SWE1-035 to SWE1-039 | Constant/macro rules | COMP-05c |
| SWE1-040 to SWE1-042 | Type rules | COMP-05d |
| SWE1-043 to SWE1-044 | Include guard rules | COMP-05e |
| SWE1-045 to SWE1-050 | Miscellaneous rules | COMP-05f |
| SWE1-051 to SWE1-053 | Cross-file sign compatibility | COMP-05g |
| SWE1-054 to SWE1-056 | Reserved names and spell check | COMP-05f |
| SWE1-057 to SWE1-064 | Output formatting | COMP-07 |
| SWE1-065 to SWE1-067 | Baseline suppression | COMP-06 |
| SWE1-068 to SWE1-070 | CLI and entry point | COMP-01 |
| SWE1-071 | Whitespace ratio check | COMP-05f |
| SWE1-MISRA-001 to SWE1-MISRA-003 | MISRA C lexical rules (lowercase l, octal, trigraphs) | COMP-05f |
| SWE1-072 to SWE1-073 | Inline suppression comments | COMP-04 |
| SWE1-074 | Auto-fix mode | COMP-08 |
| SWE1-075 | Config wizard and presets | COMP-09 |
| SWE1-076 | Per-directory config | COMP-10 |
| SWE1-077 | HTML report output | COMP-07 |
| SWE1-078 | `misc.function_length` | COMP-05f |
| SWE1-079 | `misc.function_doc_header` | COMP-05f |
| SWE1-080 | `misc.assert_density` | COMP-05f |
| SWE1-081 | `misc.null_statement_comment` | COMP-05f |
| SWE1-082 | `misc.declaration_spacing` | COMP-05f |
| SWE1-083 | `misc.file_length` | COMP-05f |
| SWE1-084 | `misc.reserved_header_name` | COMP-05f |
| SWE1-085 | `macro.trailing_semicolon` | COMP-05c |
| SWE1-086 | `macro.multistatement_wrapper` | COMP-05c |
| SWE1-087 | `naming.identifier_length` | COMP-05h |
| SWE1-088 | `naming.no_single_char_identifiers` | COMP-05h |

---

## 11. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | Approved | 2026-04-15 |
| Technical Reviewer | Dermot Murphy | Approved | 2026-04-15 |
| Quality Assurance | Dermot Murphy | Approved | 2026-04-15 |
| Approver | Dermot Murphy | Approved | 2026-04-15 |

> **Note:** This document is under configuration management (SUP.8). Post-approval changes require a change request (SUP.10) and a new document version.
