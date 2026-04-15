# Software Architecture Description

*Automotive SPICE® PAM v4.0 | SWE.2 Software Architectural Design*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CNC-SWE2-001 | **Version** | 1.0 |
| **Project** | CStyleCheck | **Date** | 2026-04-12 |
| **Status** | Draft | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SWE.2 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose & Scope

This Software Architecture Description defines the internal structure, component decomposition, interfaces, and dynamic behaviour of **CStyleCheck v1.0.0**. It refines the system architecture (CNC-SYS3-001) to the software component level, providing the design basis for detailed design (SWE.3) and integration testing (SWE.5).

This document satisfies **Automotive SPICE® PAM v4.0, SWE.2 — Software Architectural Design**.

### 3.1 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CNC-SWE1-001 | CStyleCheck Software Requirements Specification | 1.0 |
| CNC-SYS3-001 | CStyleCheck System Architecture Description | 1.0 |
| CNC-SWE3-001 | CStyleCheck Software Detailed Design | 1.0 |
| CNC-SUP8-001 | CStyleCheck Configuration Management Plan | 1.1 |

---

## 4. Architectural Overview

CStyleCheck is implemented as a **single Python module** (`cstylecheck.py`) with supporting data files. The module is structured into distinct functional components that map directly to the system-level subsystems defined in CNC-SYS3-001. The architecture follows a **pipeline pattern**: each source file passes sequentially through preprocessing, caching, rule evaluation, and output formatting.

```
cstylecheck.py
│
├── [COMP-01] CLI & Options Loader     (parse_args, _expand_options_file, discover_files)
├── [COMP-02] Configuration Loader     (load_config, load_alias_file, load_cstylecheck_exclusions_file,
│                                       load_defines_file, apply_defines)
├── [COMP-03] Dictionary Manager       (_load_dict_file, _data_file, _build_spell_dict,
│                                       load_spell_words, load_banned_names_file)
├── [COMP-04] Source Parser & Cache    (strip_comments, strip_strings, preprocess,
│                                       build_line_map, offset_to_line_col,
│                                       _build_brace_depths, _comment_only_lines,
│                                       extract_comments)
├── [COMP-05] Rule Engine              (class Checker — all _check_* methods)
│   ├── [COMP-05a] Variable Checker    (_check_variables)
│   ├── [COMP-05b] Function Checker    (_check_functions)
│   ├── [COMP-05c] Define Checker      (_check_defines)
│   ├── [COMP-05d] Type Checker        (_check_typedefs, _check_enums, _check_structs)
│   ├── [COMP-05e] Guard Checker       (_check_include_guard)
│   ├── [COMP-05f] Misc Checker        (_check_misc, _check_yoda, _check_spelling,
│   │                                   _check_reserved_names, _check_copyright_header,
│   │                                   _check_block_comment_spacing, _check_eof_comment)
│   └── [COMP-05g] Sign Checker        (class SignChecker — _check_calls)
├── [COMP-06] Baseline Manager         (load_baseline, write_baseline, _baseline_key)
└── [COMP-07] Output Formatter         (_violations_to_json, _violations_to_sarif,
                                        print_summary, class Tee, Violation.github_annotation)
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
| **Source functions** | `load_config()`, `load_alias_file()`, `load_cstylecheck_exclusions_file()`, `_disabled_rules_for_file()`, `load_defines_file()`, `apply_defines()` |
| **Responsibility** | Load and validate YAML config; build alias-prefix lists; resolve per-file disabled rules; apply defines substitutions to preprocessed source |
| **Inputs** | YAML config file path; alias file path; cstylecheck_exclusions file path; defines file path |
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
| **Source functions** | `strip_comments()`, `strip_strings()`, `preprocess()`, `build_line_map()`, `offset_to_line_col()`, `_build_brace_depths()`, `_comment_only_lines()`, `extract_comments()` |
| **Responsibility** | Produce a clean (comment/string-free) version of source; build offset→(line,col) map; build brace-depth array for scope inference; cache raw source for cross-file checks |
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
| `_check_block_comment_spacing()` | `misc.block_comment_spacing` |
| `_check_eof_comment()` | `misc.eof_comment` |

#### COMP-05g — Sign Checker (`class SignChecker`)

| Attribute | Value |
|---|---|
| **Class** | `SignChecker` |
| **Responsibility** | Cross-file sign-compatibility analysis; resolves typedef chains; enforces `plain_char_is_signed` without global state mutation |
| **Key method** | `_check_calls()` — finds function calls and validates argument signedness against parameter declarations |
| **Rule enforced** | `sign_compatibility` |

### COMP-06 — Baseline Manager

| Attribute | Value |
|---|---|
| **Source functions** | `_baseline_key()`, `load_baseline()`, `write_baseline()` |
| **Responsibility** | Serialise/deserialise violation baselines; generate stable violation keys for suppression matching |
| **Baseline key** | `"{rule}::{filepath}::{line}::{message}"` |

### COMP-07 — Output Formatter

| Attribute | Value |
|---|---|
| **Source functions** | `_violations_to_json()`, `_violations_to_sarif()`, `print_summary()`, `class Tee` |
| **Source method** | `Violation.__str__()`, `Violation.github_annotation()` |
| **Responsibility** | Render violations in text/JSON/SARIF; emit GitHub annotations; duplicate stdout to log file via `Tee`; print summary table |

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
| SWA-IF-01 | COMP-01 | COMP-02 | Config file path, defines path, aliases path, cstylecheck_exclusions path | Paths from `argparse.Namespace` |
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
│   ├─ COMP-02: load_cstylecheck_exclusions, _disabled_rules_for_file → disabled_rules
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

---

## 11. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | | 2026-04-12 |
| Technical Reviewer | \<Name\> | | |
| Quality Assurance | \<Name\> | | |
| Approver | \<Name\> | | |

> **⚠️ Important:** This document must be placed under configuration management (SUP.8) upon approval. Any post-approval changes require a change request (SUP.10) and a new document version.
