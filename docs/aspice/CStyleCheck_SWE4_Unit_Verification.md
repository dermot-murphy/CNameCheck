# Software Unit Verification Specification

*Automotive SPICE® PAM v4.0 | SWE.4 Software Unit Verification*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CSC-SWE4-001 | **Version** | 1.9 |
| **Project** | CStyleCheck | **Date** | 2026-06-08 |
| **Status** | Released | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SWE.4 |

> **Note — Reviewer independence (CSC-DEV-002):** The Reviewer and Approver are the same person (Dermot Murphy). This is accepted under deviation record **CSC-DEV-002** (`docs/aspice/CStyleCheck_DEV002_Independent_Review_Deviation.md`) on the basis that CStyleCheck has a single human team member.

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.9 | 2026-06-08 | Claude | Add 11 new test modules (102 tests) for issues #221–#232; update §6 totals; update §7 traceability |
| 1.8 | 2026-06-05 | Claude | CSC-AUD-005 corrective action — fix factual errors identified in audit |
| 1.6 | 2026-06-04 | Claude | Automated accuracy audit: add §6 rows for test_preprocessor.py/test_comment_ratio/test_declared_not_defined/test_update_config/test_config_loading; update total 786→965; fix section header counts (§5.4/§5.6/§5.12/§5.13); update referenced doc versions; fix §3 version text; update coverage note — resolves issue #163 |
| 1.5 | 2026-05-28 | Claude | Add §5.7b whitespace_ratio test catalogue (27 tests); fix §5.1 count 32→35; add §6 row for test_whitespace_ratio.py; update total 759→786; update §7 traceability — closes issues #148 #157 |
| 1.4 | 2026-05-28 | Dermot Murphy | §4.2: implement subprocess coverage via COVERAGE_PROCESS_START + sitecustomize.py; raise CI gate to 85% combined; actual v1.2.0 CI: 89.8% stmt, 87.31% combined — closes issue #54 |
| 1.3 | 2026-05-28 | Dermot Murphy | Populate §6 results table: actual test counts, all PASS; coverage 86% stmt / N/A branch (v1.1.0 CI); add 5 missing test modules — closes issue #53 |
| 1.2 | 2026-05-28 | Dermot Murphy | Add CSC-DEV-002 deviation footnote to §1 — closes issue #61 |
| 1.1 | 2026-05-28 | Claude | Added static type check (mypy --ignore-missing-imports) and lint check (ruff) as verification methods in §4.1; updated CI workflow reference |
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose & Scope

This specification defines the unit verification strategy, coverage criteria, and test case catalogue for **CStyleCheck v1.2.x**. It satisfies **Automotive SPICE® PAM v4.0, SWE.4 — Software Unit Verification**.

Unit verification covers both dynamic testing (pytest test suite) and static verification (naming convention self-check via `rules.yml` CI workflow).

### 3.1 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CSC-SWE1-001 | CStyleCheck Software Requirements Specification | 1.7 |
| CSC-SWE3-001 | CStyleCheck Software Detailed Design | 1.8 |
| CSC-SWE5-001 | CStyleCheck Software Integration Test Specification | 1.4 |
| CSC-SUP8-001 | CStyleCheck Configuration Management Plan | 1.4 |

---

## 4. Unit Verification Strategy

### 4.1 Verification Methods

| Method | Scope | Tool |
|---|---|---|
| Dynamic unit testing | All COMP-05 rule-check methods; COMP-02, COMP-03, COMP-04, COMP-06, COMP-07 utility functions | pytest 7+ |
| Static verification (naming convention) | `src/cstylecheck/` package source files | `cstylecheck` self-hosted via `rules.yml` CI |
| Static type check | `src/cstylecheck/` — import and inferred-type check (`--ignore-missing-imports`; `--strict` deferred until codebase is annotated) | mypy 1.0+ |
| Lint check | `src/` and `tests/` — style and common error detection | ruff 0.1+ |
| Code coverage measurement | `src/cstylecheck/` | pytest-cov |
| Code review / inspection | `SignChecker` try/finally pattern (SWE1-053); `_data_file()` fallback logic | Manual review during PR |

### 4.2 Coverage Criteria

| Coverage Type | Long-term Target | v1.1.0 Baseline (stmt-only, excl. subprocess) | CI Gate | Rationale |
|---|---|---|---|---|
| Statement coverage | ≥ 90% | 89.8% (1,694 stmts, 172 missed — v1.2.0 CI with subprocess) | ≥ 85% combined (see note) | All reachable statements exercised; subprocess coverage via `COVERAGE_PROCESS_START` |
| Branch coverage | ≥ 85% | 87.31% combined stmt+branch (874 branch pts, 96 partial — v1.2.0 CI) | ≥ 85% combined (see note) | All major decision branches covered |
| Function coverage | 100% of public functions | ~95% | reported only | Every unit invoked at least once |

Coverage is measured per CI run on all three Python matrix versions (3.10, 3.11, 3.12) and reported via `coverage.xml` artefact (uploaded as a GitHub Actions artefact, Python 3.11 build).

**CI gate (from v1.2.0+):** `--cov-fail-under=85 --cov-branch` applied across all 1041 tests including `test_cli.py` subprocess calls. Combined coverage 87.31% ≥ 85% gate ✅

> **Subprocess coverage implementation (issue #54 — resolved):** From v1.2.0 CI onwards, `COVERAGE_PROCESS_START` and `sitecustomize.py` subprocess instrumentation are enabled in `cstylecheck_tests.yml`. This allows `test_cli.py` to contribute coverage of `main()` and the CLI output helpers (`_violations_to_json`, `_violations_to_sarif`, `write_baseline`, `load_baseline`, `print_summary`), which previously accounted for ~14% of unmeasured statements (the v1.1.0 measured baseline was 86% statement-only, excluding subprocess invocations). The CI gate has been raised from 72% statement-only to 85% combined statement + branch. The long-term targets of ≥ 90% statement and ≥ 85% branch remain; the 85% combined gate will be reviewed once the first post-instrumentation CI run reports actual figures (baseline reference: 1041 tests as of v1.2.x).

### 4.3 Test Infrastructure

All dynamic unit tests use the shared test harness in `tests/harness.py`:

```python
from harness import run, rules, has, clean, count, cfg_only

# Inject source string directly — no file I/O in unit tests
violations = run(source="uint32_t BadName = 0U;\n", cfg=cfg, filepath="mymod.c")
assert "variable.global.case" in rules(source, cfg, filepath="mymod.c")
```

Key harness functions:

| Function | Purpose |
|---|---|
| `run(source, cfg, **kw)` | Return `List[Violation]` for given source and config |
| `rules(source, cfg, **kw)` | Return list of rule ID strings |
| `has(source, cfg, rule_id, **kw)` | Return `True` if rule\_id present in violations |
| `clean(source, cfg, **kw)` | Return `True` if zero violations |
| `count(source, cfg, rule_id, **kw)` | Return count of a specific rule ID |
| `cfg_only(**overrides)` | Build config with all rules off except those in overrides |

### 4.4 Naming Convention Self-Check (Static Verification)

CStyleCheck enforces its own naming rules on `src/cstylecheck/` via the `rules.yml` CI workflow. This constitutes a static verification pass satisfying SWE.4 BP3.

| Verification Item | Evidence |
|---|---|
| Zero `error`-level violations on `src/cstylecheck/` | `rules.yml` CI job PASS |
| Workflow trigger | Every push that modifies `src/cstylecheck/` |

---

## 5. Unit Test Catalogue

Tests are organised by test module. Each module maps to one or more COMP-05 sub-checkers.

---

### 5.1 Variable Rules — `test_variables.py` (35 tests)

| TC-ID | Test Name | Rule Verified | Pass Condition |
|---|---|---|---|
| UV-VAR-001 | `test_correct_global_passes` | `variable.global.case` | Clean source; no violation |
| UV-VAR-002 | `test_wrong_module_prefix_fails` | `variable.global.prefix` | `variable.global.prefix` violation raised |
| UV-VAR-003 | `test_g_prefix_warning` | `variable.global.g_prefix` | `variable.global.g_prefix` warning raised |
| UV-VAR-004 | `test_static_s_prefix_required` | `variable.static.s_prefix` | Violation raised for missing `s_` |
| UV-VAR-005 | `test_static_correct_prefix_passes` | `variable.static.s_prefix` | No violation for `s_` prefix |
| UV-VAR-006 | `test_pointer_p_prefix_required` | `variable.pointer_prefix` | Violation for `*data` parameter |
| UV-VAR-007 | `test_double_pointer_pp_prefix` | `variable.pp_prefix` | Violation for `**buf` without `pp_` |
| UV-VAR-008 | `test_bool_prefix_required` | `variable.bool_prefix` | Violation for `bool enabled` without `b_` |
| UV-VAR-009 | `test_prefix_order_enforced` | `variable.prefix_order` | Violation if `p_g_` instead of `g_p_` |
| UV-VAR-010 | `test_min_length_enforced` | `variable.min_length` | Violation for 2-char name when min=3 |
| UV-VAR-011 | `test_loop_var_exemption` | `variable.min_length` | Single-char loop var exempt when configured |
| UV-VAR-012 | `test_max_length_enforced` | `variable.max_length` | Violation for name > max_length |
| UV-VAR-013 | `test_allowed_abbreviations_exempt` | `variable.global.case` | `FIFO` in name does not trigger case violation |
| UV-VAR-014 | `test_local_var_no_prefix_required` | `variable.local.*` | Local var without module prefix passes |
| UV-VAR-015 | `test_parameter_case` | `variable.parameter.case` | `lower_snake` enforced on parameters |

---

### 5.2 Function Rules — `test_functions.py` (14 tests)

| TC-ID | Test Name | Rule Verified | Pass Condition |
|---|---|---|---|
| UV-FUN-001 | `test_correct_function_passes` | `function.prefix` | No violation for `uart_BufferRead()` in `uart.c` |
| UV-FUN-002 | `test_missing_prefix_fails` | `function.prefix` | Violation for `Init()` in `uart.c` |
| UV-FUN-003 | `test_object_verb_style` | `function.style` | `uart_BufferRead` passes; `uart_readBuffer` fails |
| UV-FUN-004 | `test_static_function_prv_prefix` | `function.static_prefix` | Violation for `static int helper()` without `prv_` |
| UV-FUN-005 | `test_function_min_length` | `function.min_length` | Violation for function name below min |
| UV-FUN-006 | `test_function_max_length` | `function.max_length` | Violation for function name above max |
| UV-FUN-007 | `test_main_exempt` | `function.prefix` | `main()` in `main.c` does not require module prefix |

---

### 5.3 Constant and Macro Rules — `test_defines.py` (16 tests)

| TC-ID | Test Name | Rule Verified | Pass Condition |
|---|---|---|---|
| UV-DEF-001 | `test_upper_snake_constant_passes` | `constant.case` | `#define UART_MAX_BAUD 115200U` passes |
| UV-DEF-002 | `test_mixed_case_constant_fails` | `constant.case` | `#define Uart_MaxBaud` raises violation |
| UV-DEF-003 | `test_constant_module_prefix` | `constant.prefix` | Missing module prefix raises violation |
| UV-DEF-004 | `test_macro_with_params` | `macro.case` | Function-like macro checked separately |
| UV-DEF-005 | `test_exempt_pattern_skipped` | `constant.case` | `__FILE__` exempt via `exempt_patterns` |
| UV-DEF-006 | `test_constant_min_length` | `constant.min_length` | Violation for constant name below min |
| UV-DEF-007 | `test_constant_max_length` | `constant.max_length` | Violation for constant name above max |

---

### 5.4 Type Rules — `test_typedefs.py` (8), `test_enums.py` (11), `test_structs.py` (12)

| TC-ID | Test Name | Rule Verified | Pass Condition |
|---|---|---|---|
| UV-TYP-001 | `test_typedef_t_suffix_required` | `typedef.suffix` | `typedef uint8_t BYTE_T` passes; `BYTE` fails |
| UV-TYP-002 | `test_typedef_upper_snake_case` | `typedef.case` | `typedef uint8_t byte_t` fails |
| UV-TYP-003 | `test_multi_token_typedef` | `typedef.case` | `typedef unsigned int UINT_T` correctly detected |
| UV-TYP-004 | `test_enum_type_suffix` | `enum.type_suffix` | `enum uart_state_t` passes; `uart_state` fails |
| UV-TYP-005 | `test_enum_member_prefix` | `enum.member_prefix` | `UART_STATE_IDLE` passes; `STATE_IDLE` fails |
| UV-TYP-006 | `test_struct_tag_suffix` | `struct.tag_suffix` | `struct uart_cfg_s` passes |
| UV-TYP-007 | `test_struct_member_case` | `struct.member_case` | `lower_snake` enforced on members |

---

### 5.5 Include Guard Rules — `test_include_guards.py` (8 tests)

| TC-ID | Test Name | Rule Verified | Pass Condition |
|---|---|---|---|
| UV-INC-001 | `test_correct_guard_passes` | `include_guard.format` | `#ifndef UART_H_` passes for `uart.h` |
| UV-INC-002 | `test_missing_guard_fails` | `include_guard.missing` | Header with no guard raises violation |
| UV-INC-003 | `test_pragma_once_accepted` | `include_guard.missing` | `#pragma once` accepted as valid guard |
| UV-INC-004 | `test_wrong_guard_name` | `include_guard.format` | Guard name not matching filename raises violation |
| UV-INC-005 | `test_c_file_no_guard_required` | `include_guard.missing` | `.c` files not checked for guards |

---

### 5.6 Miscellaneous Rules — `test_misc.py` (28), `test_misc_improvements.py` (77), `test_block_comment_spacing.py`

| TC-ID | Test Name | Rule Verified | Pass Condition |
|---|---|---|---|
| UV-MSC-001 | `test_line_too_long` | `misc.line_length` | Line > max raises violation |
| UV-MSC-002 | `test_line_at_limit_passes` | `misc.line_length` | Line exactly at limit passes |
| UV-MSC-003 | `test_comment_line_exempt` | `misc.line_length` | Comment-only line exempt |
| UV-MSC-004 | `test_magic_number_detected` | `misc.magic_number` | Literal `42` in expression raises violation |
| UV-MSC-005 | `test_define_rhs_exempt` | `misc.magic_number` | `#define X 42` RHS is exempt |
| UV-MSC-006 | `test_unsigned_suffix_required` | `misc.unsigned_suffix` | `uint32_t x = 100;` raises violation (needs `100U`) |
| UV-MSC-007 | `test_unsigned_suffix_passes` | `misc.unsigned_suffix` | `100U` passes |

---

### 5.7 Yoda Conditions — `test_yoda_condition.py` (37 tests)

| TC-ID | Test Name | Rule Verified | Pass Condition |
|---|---|---|---|
| UV-YOD-001 | `test_null_on_left_passes` | `misc.yoda_condition` | `if (NULL == p_ptr)` passes |
| UV-YOD-002 | `test_null_on_right_fails` | `misc.yoda_condition` | `if (p_ptr == NULL)` fails |
| UV-YOD-003 | `test_literal_on_left_passes` | `misc.yoda_condition` | `if (0 == count)` passes |
| UV-YOD-004 | `test_two_variables_exempt` | `misc.yoda_condition` | `if (a == b)` no violation |
| UV-YOD-005 | `test_not_equal_enforced` | `misc.yoda_condition` | `!= NULL` also enforced |

---

### 5.7b Whitespace Ratio Rules — `test_whitespace_ratio.py` (27 tests)

| TC-ID | Test Name | Rule Verified | Pass Condition |
|---|---|---|---|
| UV-WSR-001 | `test_disabled_produces_no_violation` | `misc.whitespace_ratio` | No violation when rule disabled |
| UV-WSR-002 | `test_zero_blank_lines_raises_violation` | `misc.whitespace_ratio` | Violation when ratio = 0 |
| UV-WSR-003 | `test_sufficient_blank_lines_passes` | `misc.whitespace_ratio` | No violation when ratio above warning threshold |
| UV-WSR-004 | `test_exactly_at_warning_threshold_passes` | `misc.whitespace_ratio` | No violation at exactly the warning threshold |
| UV-WSR-005 | `test_one_below_warning_threshold_fails` | `misc.whitespace_ratio` | Warning violation when one blank line below threshold |
| UV-WSR-006 | `test_single_violation_emitted_per_file` | `misc.whitespace_ratio` | Exactly one violation emitted per non-compliant file |
| UV-WSR-007 | `test_below_error_threshold_emits_error` | `misc.whitespace_ratio` | Error severity when ratio below error threshold |
| UV-WSR-008 | `test_between_thresholds_emits_configured_severity` | `misc.whitespace_ratio` | Configured severity used when between thresholds |
| UV-WSR-009 | `test_custom_severity_used_between_thresholds` | `misc.whitespace_ratio` | Custom severity key respected |
| UV-WSR-010 | `test_exactly_at_error_threshold_is_warning_not_error` | `misc.whitespace_ratio` | Warning (not error) when exactly at error threshold |
| UV-WSR-011 | `test_fewer_than_min_lines_skipped` | `misc.whitespace_ratio` | No violation when code lines below minimum |
| UV-WSR-012 | `test_exactly_min_lines_is_checked` | `misc.whitespace_ratio` | Checked when code lines equals minimum |
| UV-WSR-013 | `test_custom_min_lines` | `misc.whitespace_ratio` | Custom min_lines config respected |
| UV-WSR-014 | `test_comments_do_not_contribute_to_min_lines` | `misc.whitespace_ratio` | Comment lines excluded from minimum code-line count |
| UV-WSR-015 | `test_blank_lines_in_block_header_not_counted` | `misc.whitespace_ratio` | Header blank lines excluded from ratio |
| UV-WSR-016 | `test_blank_lines_between_header_comments_not_counted` | `misc.whitespace_ratio` | Header region blank lines excluded |
| UV-WSR-017 | `test_blank_lines_in_body_counted_after_header` | `misc.whitespace_ratio` | Body blank lines counted correctly |
| UV-WSR-018 | `test_line_comments_excluded_from_denominator` | `misc.whitespace_ratio` | Line comment lines excluded from code count |
| UV-WSR-019 | `test_block_comments_excluded_from_denominator` | `misc.whitespace_ratio` | Block comment lines excluded from code count |
| UV-WSR-020 | `test_code_line_with_trailing_comment_counts_as_code` | `misc.whitespace_ratio` | Trailing-comment lines count as code |
| UV-WSR-021 | `test_mixed_blanks_and_comments_ratio_correct` | `misc.whitespace_ratio` | Correct ratio when mix of blank, comment, code lines |
| UV-WSR-022 | `test_message_contains_ratio_and_counts` | `misc.whitespace_ratio` | Violation message includes ratio and counts |
| UV-WSR-023 | `test_message_mentions_threshold` | `misc.whitespace_ratio` | Violation message includes threshold value |
| UV-WSR-024 | `test_message_says_error_threshold_when_below_error` | `misc.whitespace_ratio` | Message identifies error threshold when below it |
| UV-WSR-025 | `test_violation_reported_at_line_1` | `misc.whitespace_ratio` | Violation always at line 1 |
| UV-WSR-026 | `test_singular_blank_line_grammar` | `misc.whitespace_ratio` | "1 blank line" (not "1 blank lines") in message |
| UV-WSR-027 | `test_plural_blank_lines_grammar` | `misc.whitespace_ratio` | "N blank lines" (plural) in message |

---

### 5.8 Reserved Names — `test_reserved_name.py` (40 tests)

| TC-ID | Test Name | Rule Verified | Pass Condition |
|---|---|---|---|
| UV-RES-001 | `test_c_keyword_reserved` | `reserved_name` | `int for = 0;` raises violation |
| UV-RES-002 | `test_stdlib_name_reserved` | `reserved_name` | Variable named `printf` raises violation |
| UV-RES-003 | `test_normal_name_passes` | `reserved_name` | `uart_g_count` passes |
| UV-RES-004 | `test_banned_names_extra` | `reserved_name` | Extra banned names via `--banned-names` caught |

---

### 5.9 Spell Check — `test_spell_check.py` (9 tests)

| TC-ID | Test Name | Rule Verified | Pass Condition |
|---|---|---|---|
| UV-SPL-001 | `test_correct_word_passes` | `spell_check` | Known word in dict passes |
| UV-SPL-002 | `test_misspelled_word_fails` | `spell_check` | Unknown word raises violation |
| UV-SPL-003 | `test_possessive_s_stripping` | `spell_check` | `status` not stripped to `statu` (bug fix) |
| UV-SPL-004 | `test_domain_word_exempt` | `spell_check` | `FIFO` in spell dict exempt |

---

### 5.10 Sign Compatibility — `test_sign_compatibility.py` (7 tests)

| TC-ID | Test Name | Rule Verified | Pass Condition |
|---|---|---|---|
| UV-SGN-001 | `test_unsigned_arg_to_signed_param` | `sign_compatibility` | `100U` passed to `int` param raises violation |
| UV-SGN-002 | `test_matching_signs_pass` | `sign_compatibility` | `100U` to `uint32_t` param passes |
| UV-SGN-003 | `test_plain_char_signed_option` | `sign_compatibility` | `plain_char_is_signed: false` changes char treatment |
| UV-SGN-004 | `test_no_global_mutation` | `sign_compatibility` | Second call with different config not affected by first |

---

### 5.11 Dictionary Loading — `test_dictionaries.py` (32 tests)

| TC-ID | Test Name | Unit Verified | Pass Condition |
|---|---|---|---|
| UV-DCT-001 | `test_load_keywords_default` | UNIT-11, UNIT-12 | Built-in keyword file loaded correctly |
| UV-DCT-002 | `test_load_keywords_override` | UNIT-11 | `--keywords-file` replaces built-in |
| UV-DCT-003 | `test_data_file_fallback` | UNIT-12 | Fallback to `sys.prefix/share/cstylecheck/` works |
| UV-DCT-004 | `test_spell_dict_merge` | UNIT-13 | YAML exemptions merged with file dictionary |

---

### 5.12 CLI and Integration — `test_cli.py` (43 tests)

| TC-ID | Test Name | Unit Verified | Pass Condition |
|---|---|---|---|
| UV-CLI-001 | `test_options_file_loaded` | UNIT-02 | Options from file merged before CLI args |
| UV-CLI-002 | `test_cli_overrides_options_file` | UNIT-02 | Direct CLI arg overrides options-file value |
| UV-CLI-003 | `test_exit_code_zero_clean` | UNIT-46 | Exit 0 on clean source |
| UV-CLI-004 | `test_exit_code_one_errors` | UNIT-46 | Exit 1 on errors |
| UV-CLI-005 | `test_exit_code_two_bad_config` | UNIT-46 | Exit 2 on missing config |
| UV-CLI-006 | `test_json_output_valid` | UNIT-38 | JSON output parseable; schema correct |
| UV-CLI-007 | `test_sarif_output_valid` | UNIT-39 | SARIF output parseable |
| UV-CLI-008 | `test_baseline_write_and_load` | UNIT-35, UNIT-36, UNIT-37 | Round-trip: write then suppress |
| UV-CLI-009 | `test_exclude_glob_applied` | UNIT-04 | Excluded files not scanned |
| UV-CLI-010 | `test_version_flag` | UNIT-46 | `--version` outputs version; exit 0 |

---

### 5.13 Bug-Fix and Improvement Tests — `test_improvements.py` (67), `test_barr_c.py` (42), `test_eof_comment.py`, `test_copyright_header.py`, `test_parameter_prefix.py`, `test_exclusions.py`

These test modules provide regression coverage for previously fixed bugs and new rules. Key cases:

| TC-ID | Area | Verified Behaviour |
|---|---|---|
| UV-IMP-001 | Possessive stripping bug | `status` not mangled to `statu` |
| UV-IMP-002 | `plain_char_is_signed: false` | `char` treated as unsigned without mutation |
| UV-IMP-003 | `_SIGNED_TYPES` mutation | Second call to sign checker unaffected by first |
| UV-IMP-004 | Multi-token typedef regex | `typedef unsigned int UINT_T` correctly detected |
| UV-IMP-005 | `function.min_length` | Previously undocumented; now implemented and tested |

---

### 5.14 MISRA C Rule Tests — `test_misra_rules.py` (52 tests)

Added in v1.1. Covers three new MISRA C:2012/2023 Required rules and one BUG-004 regression.
ASPICE traceability: SWE1-MISRA-001 (Rule 7.3), SWE1-MISRA-002 (Rule 7.1), SWE1-MISRA-003 (Rule 4.2).

| TC-ID | MISRA Rule | SWE4 Test ID range | Verified Behaviour |
|---|---|---|---|
| SWE4-TC-7.3-001 to 7.3-015 | Rule 7.3 (lowercase `l`) | 15 tests | Flags `1l`, `0xFFl`, `1ul`; passes `1L`, `1UL`, `0xFFL` |
| SWE4-TC-7.1-001 to 7.1-016 | Rule 7.1 (octal constants) | 16 tests | Flags `010`, `07`, `0777U`; passes `0`, `0U`, `0x08`, `0.5` |
| SWE4-TC-4.2-001 to 4.2-017 | Rule 4.2 (trigraphs) | 17 tests | Flags all 9 trigraph sequences; passes `??` alone, `?` alone |
| BUG-004-001 to 004-004 | Yoda negative literal | 4 tests | `x == -1` message shows `-1`, not `1` |

Each test class verifies: positive detection, negative non-detection, disabled-rule suppression, configurable severity, violation message content, and (for trigraphs) accurate line number.
| UV-IMP-006 | `function.static_prefix` | `prv_` prefix enforced on static functions |
| UV-IMP-007 | `constant.min_length` / `macro.min_length` | Previously undocumented; now implemented |
| UV-IMP-008 | Baseline suppression | Known violations suppressed; new ones reported |

---

## 6. Verification Results Summary

| Test Module | Tests | Pass | Fail | Coverage Contribution |
|---|---|---|---|---|
| `test_variables.py` | 35 | 35 | 0 | `_check_variables` |
| `test_functions.py` | 14 | 14 | 0 | `_check_functions` |
| `test_defines.py` | 16 | 16 | 0 | `_check_defines` |
| `test_typedefs.py` | 8 | 8 | 0 | `_check_typedefs` |
| `test_enums.py` | 11 | 11 | 0 | `_check_enums` |
| `test_structs.py` | 12 | 12 | 0 | `_check_structs` |
| `test_include_guards.py` | 8 | 8 | 0 | `_check_include_guard` |
| `test_misc.py` | 28 | 28 | 0 | `_check_misc` |
| `test_misc_improvements.py` | 77 | 77 | 0 | `_check_misc`, improvements |
| `test_yoda_condition.py` | 37 | 37 | 0 | `_check_yoda` |
| `test_whitespace_ratio.py` | 27 | 27 | 0 | `_check_whitespace_ratio` |
| `test_reserved_name.py` | 40 | 40 | 0 | `_check_reserved_names` |
| `test_spell_check.py` | 9 | 9 | 0 | `_check_spelling` |
| `test_sign_compatibility.py` | 7 | 7 | 0 | `SignChecker` |
| `test_dictionaries.py` | 32 | 32 | 0 | COMP-03 |
| `test_improvements.py` | 67 | 67 | 0 | Multiple |
| `test_barr_c.py` | 42 | 42 | 0 | Multiple |
| `test_cli.py` | 43 | 43 | 0 | COMP-01, COMP-07 |
| `test_exclusions.py` | 28 | 28 | 0 | COMP-02 |
| `test_eof_comment.py` | 33 | 33 | 0 | `_check_eof_comment` |
| `test_copyright_header.py` | 55 | 55 | 0 | `_check_copyright_header` |
| `test_parameter_prefix.py` | 42 | 42 | 0 | `_check_variables` |
| `test_misra_rules.py` | 52 | 52 | 0 | `_check_lowercase_l_suffix`, `_check_octal_constants`, `_check_trigraphs`, `_check_yoda` |
| `test_block_comment_spacing.py` | 29 | 29 | 0 | `_check_block_comment_spacing` |
| `test_workflow_config.py` | 16 | 16 | 0 | CI workflow configuration regression |
| `test_github_annotations.py` | 8 | 8 | 0 | GitHub Actions annotation output |
| `test_case_patterns.py` | 6 | 6 | 0 | Case pattern matching (`_check_case_patterns`) |
| `test_thread_safe_globals.py` | 4 | 4 | 0 | Thread-safe global state (`C_KEYWORDS`, `C_STDLIB_NAMES`) |
| `test_preprocessor.py` | 76 | 76 | 0 | COMP-04 (`preprocessor.py`) — strip_comments, strip_strings, preprocess, build_line_map, brace depths, extract_comments |
| `test_comment_ratio.py` | 24 | 24 | 0 | `_check_comment_ratio` |
| `test_declared_not_defined.py` | 39 | 39 | 0 | `DeclaredNotDefinedChecker` |
| `test_config_loading.py` | 13 | 13 | 0 | COMP-02 (`load_config` — UTF-8, missing file, YAML errors) |
| `test_update_config.py` | 27 | 27 | 0 | COMP-02 (`_deep_merge`) |
| `test_inline_suppression.py` | 15 | 15 | 0 | COMP-04 (`parse_inline_suppressions`) |
| `test_fix_mode.py` | 11 | 11 | 0 | COMP-08 (`apply_fixes`, `unified_diff`) |
| `test_init_wizard.py` | 15 | 15 | 0 | COMP-09 (`run_wizard`, `run_preset`) |
| `test_per_dir_config.py` | 15 | 15 | 0 | COMP-10 (`resolve_per_dir_config`) |
| `test_html_report.py` | 20 | 20 | 0 | COMP-07 (`_violations_to_html`) |
| `test_function_length.py` | 11 | 11 | 0 | COMP-01 (`_check_function_length`) |
| `test_function_doc_header.py` | 12 | 12 | 0 | COMP-01 (`_check_function_doc_header`) |
| `test_assert_density.py` | 8 | 8 | 0 | COMP-01 (`_check_assert_density`) |
| `test_null_statement_comment.py` | 9 | 9 | 0 | COMP-01 (`_check_null_statement_comment`) |
| `test_declaration_spacing.py` | 8 | 8 | 0 | COMP-01 (`_check_declaration_spacing`) |
| `test_file_length.py` | 8 | 8 | 0 | COMP-01 (`_check_file_length`) |
| `test_reserved_header_name.py` | 10 | 10 | 0 | COMP-01 (`_check_reserved_header_name`) |
| `test_macro_trailing_semicolon.py` | 9 | 9 | 0 | COMP-01 (`_check_macro_trailing_semicolon`) |
| `test_macro_multistatement_wrapper.py` | 9 | 9 | 0 | COMP-01 (`_check_macro_multistatement_wrapper`) |
| `test_identifier_length.py` | 10 | 10 | 0 | COMP-01 (`_check_identifier_length`) |
| `test_no_single_char_identifiers.py` | 8 | 8 | 0 | COMP-01 (`_check_no_single_char_identifiers`) |
| **Total** | **1143** | **1143** | **0** | All rules covered — 49 modules |

**Statement Coverage (v1.1.0 CI — unit tests excl. subprocess):** 86% (1,694 statements, 243 missed)
**Statement Coverage (v1.2.0 CI — 1041 tests incl. subprocess):** 89.8% (1,694 statements, 172 missed)
**Branch Coverage (v1.2.0 CI — 1041 tests incl. subprocess):** 874 branch points, 96 partial → **87.31% combined statement + branch** ≥ 85% gate ✅ (issue #54 resolved)

**Static Verification (rules.yml):** PASS

---

## 7. Traceability: SW Requirements → Test Cases

| SW-REQ-ID | Requirement | Unit Test(s) |
|---|---|---|
| SWE1-017 to SWE1-029 | Variable rules | UV-VAR-001 to UV-VAR-015 |
| SWE1-030 to SWE1-034 | Function rules | UV-FUN-001 to UV-FUN-007 |
| SWE1-035 to SWE1-039 | Constant/macro rules | UV-DEF-001 to UV-DEF-007 |
| SWE1-040 to SWE1-042 | Type rules | UV-TYP-001 to UV-TYP-007 |
| SWE1-043 to SWE1-044 | Include guard rules | UV-INC-001 to UV-INC-005 |
| SWE1-045 to SWE1-050 | Miscellaneous rules | UV-MSC-001 to UV-MSC-007 |
| SWE1-071 | Whitespace ratio | UV-WSR-001 to UV-WSR-027 |
| SWE1-049 | Yoda conditions | UV-YOD-001 to UV-YOD-005 |
| SWE1-051 to SWE1-053 | Sign compatibility | UV-SGN-001 to UV-SGN-004 |
| SWE1-054 to SWE1-055 | Reserved names | UV-RES-001 to UV-RES-004 |
| SWE1-056 | Spell check | UV-SPL-001 to UV-SPL-004 |
| SWE1-007 to SWE1-010 | Dictionary management | UV-DCT-001 to UV-DCT-004 |
| SWE1-065 to SWE1-067 | Baseline suppression | UV-CLI-008 |
| SWE1-068 to SWE1-070 | CLI / entry point | UV-CLI-001 to UV-CLI-010 |
| SWE1-072 to SWE1-073 | Inline suppression comments (`parse_inline_suppressions`, suppression logic) | `test_inline_suppression.py` |
| SWE1-074 | Auto-fix mode (`apply_fixes`, `unified_diff`) | `test_fix_mode.py` |
| SWE1-075 | Config wizard and presets (`run_wizard`, `run_preset`) | `test_init_wizard.py` |
| SWE1-076 | Per-directory config (`resolve_per_dir_config`) | `test_per_dir_config.py` |
| SWE1-077 | HTML report output (`_violations_to_html`) | `test_html_report.py` |
| SWE1-078 | Function length (`_check_function_length`) | `test_function_length.py` |
| SWE1-079 | Function doc header (`_check_function_doc_header`) | `test_function_doc_header.py` |
| SWE1-080 | Assert density (`_check_assert_density`) | `test_assert_density.py` |
| SWE1-081 | Null statement comment (`_check_null_statement_comment`) | `test_null_statement_comment.py` |
| SWE1-082 | Declaration spacing (`_check_declaration_spacing`) | `test_declaration_spacing.py` |
| SWE1-083 | File length (`_check_file_length`) | `test_file_length.py` |
| SWE1-084 | Reserved header name (`_check_reserved_header_name`) | `test_reserved_header_name.py` |
| SWE1-085 | Macro trailing semicolon (`_check_macro_trailing_semicolon`) | `test_macro_trailing_semicolon.py` |
| SWE1-086 | Macro multistatement wrapper (`_check_macro_multistatement_wrapper`) | `test_macro_multistatement_wrapper.py` |
| SWE1-087 | Identifier length (`_check_identifier_length`) | `test_identifier_length.py` |
| SWE1-088 | No single-char identifiers (`_check_no_single_char_identifiers`) | `test_no_single_char_identifiers.py` |

---

## 8. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | Approved | 2026-04-15 |
| Technical Reviewer | Dermot Murphy | Approved | 2026-04-15 |
| Quality Assurance | Dermot Murphy | Approved | 2026-04-15 |
| Approver | Dermot Murphy | Approved | 2026-04-15 |

> **Note:** This document is under configuration management (SUP.8). Post-approval changes require a change request (SUP.10) and a new document version.
