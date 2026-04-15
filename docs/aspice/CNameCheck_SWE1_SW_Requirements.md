# Software Requirements Specification

*Automotive SPICE® PAM v4.0 | SWE.1 Software Requirements Analysis*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CNC-SWE1-001 | **Version** | 1.0 |
| **Project** | CStyleCheck | **Date** | 2026-04-12 |
| **Status** | Draft | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SWE.1 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose & Scope

### 3.1 Purpose

This Software Requirements Specification (SRS) refines the system-level requirements from CNC-SYS2-001 into software-specific, implementable requirements for **CStyleCheck v1.0.0**. It provides the direct input to software architectural design (SWE.2) and defines the verification criteria used in SWE.4–SWE.6.

This document satisfies **Automotive SPICE® PAM v4.0, SWE.1 — Software Requirements Analysis**.

### 3.2 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CNC-SYS2-001 | CStyleCheck System Requirements Specification | 1.0 |
| CNC-SYS3-001 | CStyleCheck System Architecture Description | 1.0 |
| CNC-SWE2-001 | CStyleCheck Software Architecture Description | 1.0 |
| CNC-SUP8-001 | CStyleCheck Configuration Management Plan | 1.1 |
| Barr-C:2018 | Barr Group Embedded C Coding Standard | 2018 |
| ASPICE PAM v4.0 | Automotive SPICE Process Assessment Model | 4.0 |

### 3.3 Glossary

| Term | Definition |
|---|---|
| `Checker` | The primary analysis class in `cstylecheck.py` responsible for per-file rule evaluation |
| `CheckResult` | Data class aggregating `Violation` objects produced by one `Checker` run |
| `Violation` | Data class holding: `filepath`, `line`, `col`, `severity`, `rule`, `message` |
| `SignChecker` | Cross-file sign-compatibility analysis class |
| `module_name` | The filename stem (e.g. `uart` from `uart.c`) used as the mandatory identifier prefix |
| `clean` | Source text after stripping comments and string literals |
| `defines` | Keyword/type alias substitutions applied to source before analysis |
| `cstylecheck_exclusions` | Per-file YAML map of rule IDs to suppressed identifier patterns |
| `baseline` | JSON file of known violations used to suppress pre-existing findings |

---

## 4. Software Requirements

### 4.1 Configuration Loading (SS-02)

| SW-REQ-ID | Requirement | Priority | Verification | Parent |
|---|---|---|---|---|
| SWE1-001 | The software shall parse the YAML configuration file into a nested dictionary accessible via the `load_config()` function | Mandatory | Test | SYS-F-002 |
| SWE1-002 | The software shall raise a configuration error (exit code 2) if the YAML file is absent, malformed, or unparseable | Mandatory | Test | SYS-F-039 |
| SWE1-003 | The software shall apply project `--defines` substitutions to the preprocessed source text before any rule check, using the `apply_defines()` function | Mandatory | Test | SYS-F-006 |
| SWE1-004 | The software shall load the module alias map via `load_alias_file()` and use it to derive accepted prefix strings per source file | Mandatory | Test | SYS-F-007 |
| SWE1-005 | The software shall load per-file rule cstylecheck_exclusions via `load_cstylecheck_exclusions_file()` and pass the resulting map to each `Checker` instance | Mandatory | Test | SYS-F-008 |
| SWE1-006 | The software shall resolve the set of disabled rules for each source file via `_disabled_rules_for_file()` before instantiating the `Checker` | Mandatory | Test | SYS-F-008 |

### 4.2 Dictionary Management (SS-03)

| SW-REQ-ID | Requirement | Priority | Verification | Parent |
|---|---|---|---|---|
| SWE1-007 | The software shall load the C keyword dictionary from `c_keywords.txt` (or `--keywords-file` override) as a `frozenset` via `_load_dict_file()` | Mandatory | Test | SYS-F-009 |
| SWE1-008 | The software shall load the C stdlib name dictionary from `c_stdlib_names.txt` (or `--stdlib-file` override) as a `frozenset` | Mandatory | Test | SYS-F-009 |
| SWE1-009 | The software shall load the spell-check dictionary from `c_spell_dict.txt` (or `--spell-dict` override) and merge it with YAML-configured exemptions via `_build_spell_dict()` | Mandatory | Test | SYS-F-009 |
| SWE1-010 | The software shall locate built-in dictionary files relative to `__file__` with a fallback to `{sys.prefix}/share/cstylecheck/` via `_data_file()` | Mandatory | Test | SYS-F-009 |

### 4.3 Source Parsing and Cache (SS-04)

| SW-REQ-ID | Requirement | Priority | Verification | Parent |
|---|---|---|---|---|
| SWE1-011 | The software shall strip C block and line comments from source text using `strip_comments()` before identifier extraction | Mandatory | Test | SYS-F-010 |
| SWE1-012 | The software shall strip string literal contents from source text using `strip_strings()` before identifier extraction | Mandatory | Test | SYS-F-010 |
| SWE1-013 | The software shall build a line-offset map via `build_line_map()` enabling `offset_to_line_col()` to convert byte positions to (line, col) pairs | Mandatory | Test | SYS-F-027 |
| SWE1-014 | The software shall build a per-line brace-depth array via `_build_brace_depths()` to determine identifier scope (global / file-static / local) | Mandatory | Test | SYS-NF-001 |
| SWE1-015 | Each source file shall be read from disk exactly once per invocation; the content shall be cached in memory for use by both the `Checker` and `SignChecker` instances | Mandatory | Test | SYS-NF-001 |
| SWE1-016 | The software shall identify comment-only lines via `_comment_only_lines()` and exempt them from indentation and line-length checks | Mandatory | Test | SYS-F-020 |

### 4.4 Rule Engine — Variables (SS-05)

| SW-REQ-ID | Requirement | Priority | Verification | Parent |
|---|---|---|---|---|
| SWE1-017 | The `_check_variables()` method shall detect variable declarations at global, file-static, local, and parameter scope using regex against the preprocessed source | Mandatory | Test | SYS-F-013 |
| SWE1-018 | The software shall enforce `lower_snake` case on variable names at all scopes, with independently configurable severity per scope | Mandatory | Test | SYS-F-013, SYS-F-018 |
| SWE1-019 | The software shall require the module prefix on global and file-static variable names when `require_module_prefix: true` | Mandatory | Test | SYS-F-012 |
| SWE1-020 | The software shall enforce the `g_` prefix on global variable local parts when `g_prefix.enabled: true` | Mandatory | Test | SYS-F-013 |
| SWE1-021 | The software shall enforce the `s_` prefix on file-static variable local parts when `s_prefix.enabled: true` | Mandatory | Test | SYS-F-013 |
| SWE1-022 | The software shall enforce the `p_` prefix on single-pointer variables when `pointer_prefix.enabled: true` | Mandatory | Test | SYS-F-014 |
| SWE1-023 | The software shall enforce the `pp_` prefix on double-pointer variables when `pp_prefix.enabled: true` | Mandatory | Test | SYS-F-014 |
| SWE1-024 | The software shall enforce the `b_` prefix on `bool`/`_Bool` variables when `bool_prefix.enabled: true` | Mandatory | Test | SYS-F-014 |
| SWE1-025 | The software shall enforce the handle prefix on configured handle types when `handle_prefix.enabled: true` | Mandatory | Test | SYS-F-014 |
| SWE1-026 | The software shall enforce the prefix ordering rule `[g_][p_\|pp_][b_\|h_]` on variable local parts | Mandatory | Test | SYS-F-014 |
| SWE1-027 | The software shall enforce `min_length` and `max_length` constraints on variable names, with `allow_single_char_loop_vars` and `allow_loop_vars_short` exemptions | Mandatory | Test | SYS-F-017 |
| SWE1-028 | The software shall enforce the `variable.no_numeric_in_name` rule when configured | Mandatory | Test | SYS-F-011 |
| SWE1-029 | The software shall permit uppercase abbreviations listed in `allowed_abbreviations` within otherwise `lower_snake` variable names | Mandatory | Test | SYS-F-024 |

### 4.5 Rule Engine — Functions (SS-05)

| SW-REQ-ID | Requirement | Priority | Verification | Parent |
|---|---|---|---|---|
| SWE1-030 | The `_check_functions()` method shall detect C function definitions by regex and extract function names | Mandatory | Test | SYS-F-015 |
| SWE1-031 | The software shall enforce module prefix on all public (non-static) function names | Mandatory | Test | SYS-F-012 |
| SWE1-032 | The software shall enforce the configured function naming style: `object_verb`, `verb_object`, or `lower_snake` | Mandatory | Test | SYS-F-015 |
| SWE1-033 | The software shall enforce the static function prefix (e.g. `prv_`) on file-scope static function names when `functions.static_prefix.enabled: true` | Mandatory | Test | SYS-F-016 |
| SWE1-034 | The software shall enforce `min_length` and `max_length` constraints on function names | Mandatory | Test | SYS-F-017 |

### 4.6 Rule Engine — Constants and Macros (SS-05)

| SW-REQ-ID | Requirement | Priority | Verification | Parent |
|---|---|---|---|---|
| SWE1-035 | The `_check_defines()` method shall detect `#define` directives and extract macro and constant names | Mandatory | Test | SYS-F-011 |
| SWE1-036 | The software shall enforce `UPPER_SNAKE_CASE` on macro and constant names | Mandatory | Test | SYS-F-018 |
| SWE1-037 | The software shall enforce the module prefix on macro and constant names | Mandatory | Test | SYS-F-012 |
| SWE1-038 | The software shall enforce `min_length` and `max_length` constraints on macro and constant names | Mandatory | Test | SYS-F-017 |
| SWE1-039 | The software shall exempt patterns matching `exempt_patterns` (e.g. compiler-built-in `__` prefixes) from all macro rules | Mandatory | Test | SYS-F-024 |

### 4.7 Rule Engine — Types (SS-05)

| SW-REQ-ID | Requirement | Priority | Verification | Parent |
|---|---|---|---|---|
| SWE1-040 | The `_check_typedefs()` method shall enforce `UPPER_SNAKE_CASE` with a `_T` suffix on `typedef` names; multi-token base types (e.g. `typedef unsigned int UINT_T`) shall be correctly detected | Mandatory | Test | SYS-F-011 |
| SWE1-041 | The `_check_enums()` method shall enforce `lower_snake_t` on enum type names and `UPPER_SNAKE` with enum-name-derived prefix on enum member names | Mandatory | Test | SYS-F-011 |
| SWE1-042 | The `_check_structs()` method shall enforce `lower_snake_s` on struct tag names and `lower_snake` on struct member names | Mandatory | Test | SYS-F-011 |

### 4.8 Rule Engine — Include Guards (SS-05)

| SW-REQ-ID | Requirement | Priority | Verification | Parent |
|---|---|---|---|---|
| SWE1-043 | The `_check_include_guard()` method shall verify that header files contain a correctly formatted include guard (`{FILENAME_UPPER}_{EXT_UPPER}_`) or `#pragma once` | Mandatory | Test | SYS-F-019 |
| SWE1-044 | Missing include guards in `.h` files shall produce an `include_guard.missing` violation | Mandatory | Test | SYS-F-019 |

### 4.9 Rule Engine — Miscellaneous Rules (SS-05)

| SW-REQ-ID | Requirement | Priority | Verification | Parent |
|---|---|---|---|---|
| SWE1-045 | The `_check_misc()` method shall enforce maximum line length on non-comment lines when `misc.line_length.enabled: true` | Mandatory | Test | SYS-F-020 |
| SWE1-046 | The software shall enforce indentation style (tab vs. spaces, configurable width) on non-comment lines | Mandatory | Test | SYS-F-020 |
| SWE1-047 | The software shall detect magic number literals when `misc.magic_numbers.enabled: true`; `#define` RHS, array indices, and `return` values shall be exempt | Mandatory | Test | SYS-F-020 |
| SWE1-048 | The software shall require the `U`/`UL` unsigned suffix on numeric integer constants when `misc.unsigned_suffix.enabled: true` | Mandatory | Test | SYS-F-020 |
| SWE1-049 | The `_check_yoda()` method shall enforce Yoda-condition ordering in `==` and `!=` comparisons | Mandatory | Test | SYS-F-020 |
| SWE1-050 | The software shall enforce block comment spacing rules when `misc.block_comment_spacing.enabled: true` | Mandatory | Test | SYS-F-020 |

### 4.10 Rule Engine — Cross-File Sign Compatibility (SS-04/SS-05)

| SW-REQ-ID | Requirement | Priority | Verification | Parent |
|---|---|---|---|---|
| SWE1-051 | The `SignChecker` class shall detect unsigned literals passed to signed-typed parameters and signed literals passed to unsigned parameters across related `.c`/`.h` file pairs | Mandatory | Test | SYS-F-021 |
| SWE1-052 | The `SignChecker` shall resolve `typedef` chains to determine the underlying signedness of type names | Mandatory | Test | SYS-F-021 |
| SWE1-053 | The `SignChecker` shall honour the `plain_char_is_signed` configuration option without permanent mutation of module-level type sets (use `try/finally` to restore) | Mandatory | Test | SYS-F-021 |

### 4.11 Rule Engine — Reserved Names and Spell Check (SS-05)

| SW-REQ-ID | Requirement | Priority | Verification | Parent |
|---|---|---|---|---|
| SWE1-054 | The `_check_reserved_names()` method shall flag any identifier that matches a C/C++ keyword or C stdlib name | Mandatory | Test | SYS-F-023 |
| SWE1-055 | The software shall load additional banned names via `--banned-names` and include them in the reserved-name check | Mandatory | Test | SYS-F-023 |
| SWE1-056 | The `_check_spelling()` method shall split identifier tokens on underscore and case-boundary, then check each word against the spell-check dictionary | Mandatory | Test | SYS-F-022 |

### 4.12 Output Formatter (SS-06)

| SW-REQ-ID | Requirement | Priority | Verification | Parent |
|---|---|---|---|---|
| SWE1-057 | Plain-text output shall format each violation as: `{filepath}:{line}:{col}: {SEVERITY} [{rule}] {message}` | Mandatory | Test | SYS-F-027 |
| SWE1-058 | JSON output via `_violations_to_json()` shall produce a top-level object with `summary` (files_checked, errors, warnings, info, total) and `violations` array | Mandatory | Test | SYS-F-028 |
| SWE1-059 | Each JSON violation object shall contain: `file`, `line`, `col`, `severity`, `rule`, `message` | Mandatory | Test | SYS-F-028 |
| SWE1-060 | SARIF output via `_violations_to_sarif()` shall conform to SARIF 2.1.0 schema with `$schema`, `version`, `runs[].tool`, and `runs[].results` fields populated | Mandatory | Test | SYS-F-029 |
| SWE1-061 | GitHub Actions annotations shall be emitted via `Violation.github_annotation()` producing `::error file=…,line=…,col=…,title=…::` format | Mandatory | Test | SYS-F-030 |
| SWE1-062 | The `Tee` class shall mirror all output to the log file path specified by `--log` without modifying stdout content | Mandatory | Test | SYS-F-031 |
| SWE1-063 | The `print_summary()` function shall print a tabulated summary of violation counts per severity and per file when `--summary` is specified | Mandatory | Test | SYS-F-032 |
| SWE1-064 | Verbose progress to `stderr` shall overwrite the current terminal line with the directory being scanned when `--verbose` is specified | Mandatory | Test | SYS-F-033 |

### 4.13 Baseline Suppression (SS-01/SS-05/SS-06)

| SW-REQ-ID | Requirement | Priority | Verification | Parent |
|---|---|---|---|---|
| SWE1-065 | The `write_baseline()` function shall serialise all violations to a JSON array and write to the specified file; each entry shall be keyed by `_baseline_key()` | Mandatory | Test | SYS-F-034 |
| SWE1-066 | The `load_baseline()` function shall return a `frozenset` of baseline keys from the JSON file | Mandatory | Test | SYS-F-035 |
| SWE1-067 | The rule engine shall filter out any `Violation` whose `_baseline_key()` matches an entry in the loaded baseline frozenset | Mandatory | Test | SYS-F-035 |

### 4.14 CLI and Entry Point (SS-01)

| SW-REQ-ID | Requirement | Priority | Verification | Parent |
|---|---|---|---|---|
| SWE1-068 | The `_expand_options_file()` function shall insert options-file tokens before direct CLI tokens so that direct CLI arguments take precedence | Mandatory | Test | SYS-NF-008 |
| SWE1-069 | The `main()` function shall return exit code `0`, `1`, or `2` as defined in SYS-F-037 to SYS-F-039, and the `cstylecheck` entry point defined in `pyproject.toml` shall invoke `main()` | Mandatory | Test | SYS-F-037 to SYS-F-039 |
| SWE1-070 | The `discover_files()` function shall expand `--include` globs, de-duplicate paths, and apply `--exclude` filters using `_path_matches_exclude()` | Mandatory | Test | SYS-F-004, SYS-F-005 |

### 4.15 Verification Criteria

The following criteria shall be met by all software requirements above. They are used as the basis for SWE.4 unit verification.

| Criterion | Target | Measurement |
|---|---|---|
| Statement coverage | ≥ 90% of `cstylecheck.py` | pytest-cov report |
| Branch coverage | ≥ 85% of `cstylecheck.py` | pytest-cov report |
| MISRA-equivalent naming compliance | Zero `cstylecheck` self-violations | `cstylecheck_rules.yml` CI result |
| All unit test cases | PASS | pytest result across Python 3.10 / 3.11 / 3.12 |

---

## 5. Requirements Traceability Matrix

| SW-REQ-ID | Software Requirement Summary | Parent SYS REQ | SWE.2 Design Element | SWE.4 Test Reference |
|---|---|---|---|---|
| SWE1-001 to SWE1-006 | Configuration loading | SYS-F-002, F-006, F-007, F-008 | Configuration Loader module | `test_cli.py`, `test_dictionaries.py` |
| SWE1-007 to SWE1-010 | Dictionary management | SYS-F-009 | Dictionary Manager module | `test_dictionaries.py` |
| SWE1-011 to SWE1-016 | Source parsing and cache | SYS-F-010, SYS-NF-001 | Source Parser / Cache | `test_misc.py` |
| SWE1-017 to SWE1-029 | Variable rules | SYS-F-013, F-014, F-017, F-018 | `Checker._check_variables()` | `test_variables.py` |
| SWE1-030 to SWE1-034 | Function rules | SYS-F-015, F-016, F-017 | `Checker._check_functions()` | `test_functions.py` |
| SWE1-035 to SWE1-039 | Constant and macro rules | SYS-F-011, F-012, F-017, F-018 | `Checker._check_defines()` | `test_defines.py` |
| SWE1-040 to SWE1-042 | Type rules | SYS-F-011 | `Checker._check_typedefs/enums/structs()` | `test_typedefs.py`, `test_enums.py`, `test_structs.py` |
| SWE1-043 to SWE1-044 | Include guard rules | SYS-F-019 | `Checker._check_include_guard()` | `test_include_guards.py` |
| SWE1-045 to SWE1-050 | Miscellaneous rules | SYS-F-020 | `Checker._check_misc()`, `_check_yoda()` | `test_misc.py`, `test_yoda_condition.py`, `test_block_comment_spacing.py` |
| SWE1-051 to SWE1-053 | Cross-file sign compatibility | SYS-F-021 | `SignChecker` class | `test_sign_compatibility.py` |
| SWE1-054 to SWE1-056 | Reserved names and spell check | SYS-F-022, F-023 | `Checker._check_reserved_names()`, `_check_spelling()` | `test_reserved_name.py`, `test_spell_check.py` |
| SWE1-057 to SWE1-064 | Output formatting | SYS-F-027 to F-033 | Output Formatter / `Tee` | `test_cli.py` |
| SWE1-065 to SWE1-067 | Baseline suppression | SYS-F-034 to F-036 | Baseline Manager | `test_cli.py` |
| SWE1-068 to SWE1-070 | CLI and entry point | SYS-F-004, F-005, SYS-NF-008 | CLI module / `main()` | `test_cli.py` |

---

## 6. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | | 2026-04-12 |
| Technical Reviewer | \<Name\> | | |
| Quality Assurance | \<Name\> | | |
| Approver | \<Name\> | | |

> **⚠️ Important:** This document must be placed under configuration management (SUP.8) upon approval. Any post-approval changes require a change request (SUP.10) and a new document version.
