# Software Unit Verification Specification

*Automotive SPICE® PAM v4.0 | SWE.4 Software Unit Verification*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CNC-SWE4-001 | **Version** | 1.0 |
| **Project** | CStyleCheck | **Date** | 2026-04-12 |
| **Status** | Draft | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SWE.4 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose & Scope

This specification defines the unit verification strategy, coverage criteria, and test case catalogue for **CStyleCheck v1.0.0**. It satisfies **Automotive SPICE® PAM v4.0, SWE.4 — Software Unit Verification**.

Unit verification covers both dynamic testing (pytest test suite) and static verification (naming convention self-check via `naming_convention.yml` CI workflow).

### 3.1 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CNC-SWE1-001 | CStyleCheck Software Requirements Specification | 1.0 |
| CNC-SWE3-001 | CStyleCheck Software Detailed Design | 1.0 |
| CNC-SWE5-001 | CStyleCheck Software Integration Test Specification | 1.0 |
| CNC-SUP8-001 | CStyleCheck Configuration Management Plan | 1.1 |

---

## 4. Unit Verification Strategy

### 4.1 Verification Methods

| Method | Scope | Tool |
|---|---|---|
| Dynamic unit testing | All COMP-05 rule-check methods; COMP-02, COMP-03, COMP-04, COMP-06, COMP-07 utility functions | pytest 7+ |
| Static verification (naming convention) | `cnamecheck.py` source file itself | `cnamecheck` self-hosted via `naming_convention.yml` CI |
| Code coverage measurement | `src/cnamecheck.py` | pytest-cov |
| Code review / inspection | `SignChecker` try/finally pattern (SWE1-053); `_data_file()` fallback logic | Manual review during PR |

### 4.2 Coverage Criteria

| Coverage Type | Target | Rationale |
|---|---|---|
| Statement coverage | ≥ 90% | All reachable statements exercised |
| Branch coverage | ≥ 85% | All major decision branches covered |
| Function coverage | 100% of public functions | Every unit invoked at least once |

Coverage is measured per CI run on Python 3.11 and reported via `coverage.xml` artefact.

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

CStyleCheck enforces its own naming rules on `cnamecheck.py` via the `naming_convention.yml` CI workflow. This constitutes a static verification pass satisfying SWE.4 BP3.

| Verification Item | Evidence |
|---|---|
| Zero `error`-level violations on `cnamecheck.py` | `naming_convention.yml` CI job PASS |
| Workflow trigger | Every push that modifies `src/cnamecheck.py` |

---

## 5. Unit Test Catalogue

Tests are organised by test module. Each module maps to one or more COMP-05 sub-checkers.

---

### 5.1 Variable Rules — `test_variables.py` (32 tests)

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

### 5.4 Type Rules — `test_typedefs.py` (8), `test_enums.py` (11), `test_structs.py` (7)

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

### 5.6 Miscellaneous Rules — `test_misc.py` (23), `test_misc_improvements.py` (65), `test_block_comment_spacing.py`

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
| UV-DCT-003 | `test_data_file_fallback` | UNIT-12 | Fallback to `sys.prefix/share/cnamecheck/` works |
| UV-DCT-004 | `test_spell_dict_merge` | UNIT-13 | YAML exemptions merged with file dictionary |

---

### 5.12 CLI and Integration — `test_cli.py` (29 tests)

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

### 5.13 Bug-Fix and Improvement Tests — `test_improvements.py` (63), `test_barr_c.py` (42), `test_eof_comment.py`, `test_copyright_header.py`, `test_parameter_prefix.py`, `test_exclusions.py`

These test modules provide regression coverage for previously fixed bugs and new rules. Key cases:

| TC-ID | Area | Verified Behaviour |
|---|---|---|
| UV-IMP-001 | Possessive stripping bug | `status` not mangled to `statu` |
| UV-IMP-002 | `plain_char_is_signed: false` | `char` treated as unsigned without mutation |
| UV-IMP-003 | `_SIGNED_TYPES` mutation | Second call to sign checker unaffected by first |
| UV-IMP-004 | Multi-token typedef regex | `typedef unsigned int UINT_T` correctly detected |
| UV-IMP-005 | `function.min_length` | Previously undocumented; now implemented and tested |
| UV-IMP-006 | `function.static_prefix` | `prv_` prefix enforced on static functions |
| UV-IMP-007 | `constant.min_length` / `macro.min_length` | Previously undocumented; now implemented |
| UV-IMP-008 | Baseline suppression | Known violations suppressed; new ones reported |

---

## 6. Verification Results Summary

| Test Module | Tests | Pass | Fail | Coverage Contribution |
|---|---|---|---|---|
| `test_variables.py` | 32 | \<N\> | \<N\> | `_check_variables` |
| `test_functions.py` | 14 | \<N\> | \<N\> | `_check_functions` |
| `test_defines.py` | 16 | \<N\> | \<N\> | `_check_defines` |
| `test_typedefs.py` | 8 | \<N\> | \<N\> | `_check_typedefs` |
| `test_enums.py` | 11 | \<N\> | \<N\> | `_check_enums` |
| `test_structs.py` | 7 | \<N\> | \<N\> | `_check_structs` |
| `test_include_guards.py` | 8 | \<N\> | \<N\> | `_check_include_guard` |
| `test_misc.py` | 23 | \<N\> | \<N\> | `_check_misc` |
| `test_misc_improvements.py` | 65 | \<N\> | \<N\> | `_check_misc`, improvements |
| `test_yoda_condition.py` | 37 | \<N\> | \<N\> | `_check_yoda` |
| `test_reserved_name.py` | 40 | \<N\> | \<N\> | `_check_reserved_names` |
| `test_spell_check.py` | 9 | \<N\> | \<N\> | `_check_spelling` |
| `test_sign_compatibility.py` | 7 | \<N\> | \<N\> | `SignChecker` |
| `test_dictionaries.py` | 32 | \<N\> | \<N\> | COMP-03 |
| `test_improvements.py` | 63 | \<N\> | \<N\> | Multiple |
| `test_barr_c.py` | 42 | \<N\> | \<N\> | Multiple |
| `test_cli.py` | 29 | \<N\> | \<N\> | COMP-01, COMP-07 |
| `test_exclusions.py` | \<N\> | \<N\> | \<N\> | COMP-02 |
| `test_eof_comment.py` | \<N\> | \<N\> | \<N\> | `_check_eof_comment` |
| `test_copyright_header.py` | \<N\> | \<N\> | \<N\> | `_check_copyright_header` |
| `test_parameter_prefix.py` | \<N\> | \<N\> | \<N\> | `_check_variables` |
| **Total** | **≥ 500** | | | |

**Statement Coverage:** \<fill from coverage.xml\> %
**Branch Coverage:** \<fill from coverage.xml\> %

**Static Verification (naming_convention.yml):** \<PASS / FAIL\>

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
| SWE1-049 | Yoda conditions | UV-YOD-001 to UV-YOD-005 |
| SWE1-051 to SWE1-053 | Sign compatibility | UV-SGN-001 to UV-SGN-004 |
| SWE1-054 to SWE1-055 | Reserved names | UV-RES-001 to UV-RES-004 |
| SWE1-056 | Spell check | UV-SPL-001 to UV-SPL-004 |
| SWE1-007 to SWE1-010 | Dictionary management | UV-DCT-001 to UV-DCT-004 |
| SWE1-065 to SWE1-067 | Baseline suppression | UV-CLI-008 |
| SWE1-068 to SWE1-070 | CLI / entry point | UV-CLI-001 to UV-CLI-010 |

---

## 8. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | | 2026-04-12 |
| Technical Reviewer | \<Name\> | | |
| Quality Assurance | \<Name\> | | |
| Approver | \<Name\> | | |

> **⚠️ Important:** Unit verification must be complete and all test cases must achieve PASS status before software integration testing (SWE.5) commences. Results must be placed under configuration management (SUP.8).
