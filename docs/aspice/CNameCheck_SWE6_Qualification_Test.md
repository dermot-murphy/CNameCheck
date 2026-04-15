# Software Qualification Test Specification

*Automotive SPICE® PAM v4.0 | SWE.6 Software Verification*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CNC-SWE6-001 | **Version** | 1.0 |
| **Project** | CStyleCheck | **Date** | 2026-04-12 |
| **Status** | Draft | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SWE.6 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose & Scope

This Software Qualification Test Specification defines the qualification test cases that verify **CStyleCheck v1.0.0** against its software requirements (CNC-SWE1-001) as a complete software build. It satisfies **Automotive SPICE® PAM v4.0, SWE.6 — Software Verification**.

Qualification tests (SWE.6) differ from integration tests (SWE.5) in that they verify the software against its **specification**, not its internal architecture. They confirm that all SWE.1 requirements are met by the delivered software artefact and provide the final evidence gate before the software is released via SPL.2.

### 3.1 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CNC-SWE1-001 | CStyleCheck Software Requirements Specification | 1.0 |
| CNC-SWE5-001 | CStyleCheck Software Integration Test Specification | 1.0 |
| CNC-SYS5-001 | CStyleCheck System Verification Report | 1.0 |
| CNC-SUP8-001 | CStyleCheck Configuration Management Plan | 1.1 |

### 3.2 Software Configuration Under Test

| Attribute | Value |
|---|---|
| **Software Version** | 1.0.0 |
| **Git Tag** | v1.0.0 |
| **Commit SHA** | \<SHA to be recorded at execution\> |
| **Python Version** | 3.11 (primary); 3.10 and 3.12 (regression) |
| **OS** | Ubuntu 24.04 |
| **Test Execution Date** | \<YYYY-MM-DD\> |
| **Tester** | \<Name\> |

### 3.3 Qualification Criteria

| Criterion | Target | Pass Condition |
|---|---|---|
| All SWQ test cases | PASS | Zero FAIL results |
| SW Requirements coverage | 100% | All SWE1-001 to SWE1-070 traced to ≥ 1 SWQ test |
| Statement coverage | ≥ 90% | Coverage report at execution |
| Branch coverage | ≥ 85% | Coverage report at execution |
| Static verification | PASS | `cstylecheck_rules.yml` CI job on v1.0.0 commit |
| Open bug Issues targeting v1.0.0 | 0 | No unresolved bug-labelled Issues |

---

## 4. Qualification Test Cases

---

### SWQ-001 — Configuration Loading and Validation

| Field | Value |
|---|---|
| **Test Case ID** | SWQ-001 |
| **Objective** | Verify all configuration loading requirements (SWE1-001 to SWE1-006) |
| **SW-REQ** | SWE1-001, SWE1-002, SWE1-003, SWE1-004, SWE1-005, SWE1-006 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Run with valid `cstylecheck_rules.yaml` | Valid YAML | Tool runs; exit 0 or 1 (not 2) |
| 2 | Run with malformed YAML | `bad: [unclosed` | Exit 2; error message to stderr |
| 3 | Run with missing YAML | `--config nonexistent.yaml` | Exit 2; error message to stderr |
| 4 | Run with `--defines project.defines` | Valid defines file | Tool runs; defines applied (verify via known substitution) |
| 5 | Run with `--aliases cstylecheck_aliases.txt` | Valid aliases file | Tool runs; alias prefixes accepted |
| 6 | Run with `--cstylecheck_exclusions cstylecheck_exclusions.yml` | Valid cstylecheck_exclusions | Tool runs; excluded rules suppressed for specified files |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SWQ-002 — File Discovery and CLI Argument Processing

| Field | Value |
|---|---|
| **Test Case ID** | SWQ-002 |
| **Objective** | Verify CLI input handling requirements (SWE1-068 to SWE1-070) |
| **SW-REQ** | SWE1-068, SWE1-069, SWE1-070 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Positional source files | `cstylecheck.py file1.c file2.h` | Both files scanned |
| 2 | `--include` glob | `--include "src/**/*.c"` | All matching `.c` files scanned |
| 3 | `--exclude` pattern | `--exclude "src/cots/"` | Files in cots/ not scanned |
| 4 | `--options-file` with `--config` | Options file sets config; direct arg overrides | Direct arg config used |
| 5 | `--version` | — | Version string printed; exit 0 |
| 6 | `--help` | — | Help text printed; exit 0 |
| 7 | `--exit-zero` with errors | Violating source | Exit 0 despite errors |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.10 | | |
| | | 3.11 | | |
| | | 3.12 | | |

---

### SWQ-003 — All 48 Rule IDs Detected

| Field | Value |
|---|---|
| **Test Case ID** | SWQ-003 |
| **Objective** | Verify all 48 rule IDs are implemented and detect violations when triggered (SWE1-017 to SWE1-056) |
| **SW-REQ** | SWE1-017 to SWE1-056 |

| Rule Category | Rule IDs | Test Module | Result |
|---|---|---|---|
| Variables — global | `variable.global.case`, `variable.global.prefix`, `variable.global.g_prefix` | `test_variables.py` | |
| Variables — static | `variable.static.case`, `variable.static.prefix`, `variable.static.s_prefix` | `test_variables.py` | |
| Variables — local/param | `variable.local.case`, `variable.parameter.case`, `variable.parameter.p_prefix` | `test_variables.py`, `test_parameter_prefix.py` | |
| Variable prefixes | `variable.pointer_prefix`, `variable.pp_prefix`, `variable.bool_prefix`, `variable.handle_prefix`, `variable.prefix_order`, `variable.min_length`, `variable.max_length`, `variable.no_numeric_in_name` | `test_variables.py`, `test_misc_improvements.py` | |
| Functions | `function.prefix`, `function.style`, `function.min_length`, `function.max_length`, `function.static_prefix` | `test_functions.py` | |
| Constants | `constant.case`, `constant.min_length`, `constant.max_length`, `constant.prefix` | `test_defines.py` | |
| Macros | `macro.case`, `macro.min_length`, `macro.max_length`, `macro.prefix` | `test_defines.py` | |
| Types | `typedef.case`, `typedef.suffix`, `enum.type_case`, `enum.type_suffix`, `enum.member_case`, `enum.member_prefix`, `struct.tag_case`, `struct.tag_suffix`, `struct.member_case` | `test_typedefs.py`, `test_enums.py`, `test_structs.py` | |
| Include guards | `include_guard.missing`, `include_guard.format` | `test_include_guards.py` | |
| Miscellaneous | `misc.line_length`, `misc.indentation`, `misc.magic_number`, `misc.unsigned_suffix`, `misc.yoda_condition`, `misc.block_comment_spacing` | `test_misc.py`, `test_yoda_condition.py`, `test_block_comment_spacing.py` | |
| Other | `reserved_name`, `spell_check`, `sign_compatibility` | `test_reserved_name.py`, `test_spell_check.py`, `test_sign_compatibility.py` | |

**SWQ-003 Overall Result:** \<PASS / FAIL\>

---

### SWQ-004 — Output Format Qualification

| Field | Value |
|---|---|
| **Test Case ID** | SWQ-004 |
| **Objective** | Verify all output format requirements (SWE1-057 to SWE1-064) |
| **SW-REQ** | SWE1-057, SWE1-058, SWE1-059, SWE1-060, SWE1-061, SWE1-062, SWE1-063, SWE1-064 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Text output (default) | Violating source | Each line: `{file}:{line}:{col}: {SEVERITY} [{rule}] {message}` |
| 2 | JSON output | `--output-format json` | Valid JSON; schema-conformant; counts correct |
| 3 | SARIF output | `--output-format sarif` | Valid SARIF 2.1.0; `runs[0].results` populated |
| 4 | GitHub annotations | `--github-actions` | `::error file=…,line=…,col=…,title=…::` format |
| 5 | Log file | `--log results.txt` | File created; content matches stdout |
| 6 | Summary table | `--summary` | Summary table with counts printed after violations |
| 7 | Verbose progress | `--verbose` with large file set | Directory names printed to stderr; updates in place |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SWQ-005 — Dictionary and Spell-Check Qualification

| Field | Value |
|---|---|
| **Test Case ID** | SWQ-005 |
| **Objective** | Verify dictionary loading and spell-check requirements (SWE1-007 to SWE1-010, SWE1-056) |
| **SW-REQ** | SWE1-007, SWE1-008, SWE1-009, SWE1-010, SWE1-056 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Default keyword dict | No `--keywords-file` | Built-in `c_keywords.txt` loaded from `_data_file()` |
| 2 | Override keyword dict | `--keywords-file custom.txt` | Custom file replaces built-in |
| 3 | Override stdlib dict | `--stdlib-file custom.txt` | Custom stdlib replaces built-in |
| 4 | Spell check with misspelled word | Identifier `uart_recive_data` | `spell_check` violation for `recive` |
| 5 | Spell check with domain word in dict | `FIFO`, `CRC` in dict | No `spell_check` violation |
| 6 | Possessive stripping bug | `status` in identifier | `status` not mangled to `statu` |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SWQ-006 — Cross-File Sign Compatibility Qualification

| Field | Value |
|---|---|
| **Test Case ID** | SWQ-006 |
| **Objective** | Verify sign compatibility requirements (SWE1-051 to SWE1-053) including bug fixes |
| **SW-REQ** | SWE1-051, SWE1-052, SWE1-053 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Unsigned arg to signed param | `100U` → `int` param | `sign_compatibility` violation |
| 2 | Matching signs | `100U` → `uint32_t` param | No violation |
| 3 | Typedef chain resolution | `typedef signed char int8_t`; pass `100U` to `int8_t` param | Violation (resolved to signed) |
| 4 | `plain_char_is_signed: false` | `char` → `unsigned char` param | Violation raised |
| 5 | `plain_char_is_signed: true` | `char` → `unsigned char` param | No violation |
| 6 | No global state mutation | Run twice with different config | Second run unaffected by first (`try/finally` verified) |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SWQ-007 — Baseline Suppression Qualification

| Field | Value |
|---|---|
| **Test Case ID** | SWQ-007 |
| **Objective** | Verify baseline write, load, and filtering requirements (SWE1-065 to SWE1-067) |
| **SW-REQ** | SWE1-065, SWE1-066, SWE1-067 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Write baseline | `--write-baseline b.json` with 2 violations | `b.json` is valid JSON; 2 entries; exit 0 |
| 2 | Suppress all | Same source + `--baseline-file b.json` | 0 violations; exit 0 |
| 3 | New violation added | Source v2 (3 violations) + `--baseline-file b.json` | 1 new violation reported; exit 1 |
| 4 | Baseline key stability | Move violation to different line | Different line → not suppressed (line number in key) |
| 5 | Plain JSON format | Inspect `b.json` | Human-readable; parseable with `jq` |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SWQ-008 — Exit Code Qualification

| Field | Value |
|---|---|
| **Test Case ID** | SWQ-008 |
| **Objective** | Verify all exit code requirements (SWE1-069) |
| **SW-REQ** | SWE1-069 |

| Scenario | Invocation | Expected Exit Code | Result |
|---|---|---|---|
| Clean source | `cstylecheck clean.c` | 0 | |
| Error violations | `cstylecheck violating.c` | 1 | |
| Warnings only, default | `cstylecheck warning_only.c` | 0 | |
| Warnings + `--warnings-as-errors` | `cstylecheck --warnings-as-errors warning_only.c` | 1 | |
| Invalid config path | `cstylecheck --config missing.yaml` | 2 | |
| Invalid YAML syntax | `cstylecheck --config bad.yaml` | 2 | |
| `--version` | `cstylecheck --version` | 0 | |
| `--help` | `cstylecheck --help` | 0 | |
| `--exit-zero` + errors | `cstylecheck --exit-zero violating.c` | 0 | |
| `--write-baseline` + errors | `cstylecheck --write-baseline b.json violating.c` | 0 | |

**SWQ-008 Overall Result:** \<PASS / FAIL\>

---

### SWQ-009 — Source Cache: Single Read per File

| Field | Value |
|---|---|
| **Test Case ID** | SWQ-009 |
| **Objective** | Verify SWE1-015: each source file read exactly once per invocation |
| **SW-REQ** | SWE1-015 |
| **Verification Method** | Inspection of source architecture + integration test observability |

| Step | Action | Expected Result | Result |
|---|---|---|---|
| 1 | Inspect `main()` source loop | Single `open()` call per file; result stored in `source_cache` dict | Confirmed by code review |
| 2 | `SignChecker` uses `source_cache` | No separate file read in `SignChecker.__init__` | Confirmed by code review |
| 3 | Run with `--verbose` on large set | Single directory-entry per file in verbose output | No duplicate entries |

---

### SWQ-010 — Multi-Token Typedef Detection

| Field | Value |
|---|---|
| **Test Case ID** | SWQ-010 |
| **Objective** | Verify SWE1-040: `RE_TYPEDEF_SIMPLE` correctly handles multi-token base types |
| **SW-REQ** | SWE1-040 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | `typedef unsigned int UINT_T;` | Single-word base type | Correctly detected; no false positive |
| 2 | `typedef unsigned long int ULONG_T;` | Multi-word base type | Correctly detected; `ULONG_T` extracted |
| 3 | `typedef unsigned int BadName;` (no `_T`) | Missing `_T` suffix | `typedef.suffix` violation raised |
| 4 | `typedef struct uart_cfg_s uart_cfg_t;` | Struct typedef | Correctly handled; no false positive |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SWQ-011 — Naming Convention Self-Verification (Static Verification)

| Field | Value |
|---|---|
| **Test Case ID** | SWQ-011 |
| **Objective** | Verify the delivered `cstylecheck.py` passes its own naming rules |
| **SW-REQ** | SWE1-017 to SWE1-056 (self-hosting quality gate) |
| **Verification Method** | CI evidence — `cstylecheck_rules.yml` job on v1.0.0 tag |

| Check | Evidence | Result |
|---|---|---|
| `cstylecheck_rules.yml` CI job result | GitHub Actions job PASS on v1.0.0 commit | \<PASS / FAIL\> |
| Zero error-level violations on `cstylecheck.py` | Workflow output — errors count = 0 | \<PASS / FAIL\> |
| CI Run URL | \<GitHub Actions run URL\> | |

---

### SWQ-012 — Python Portability Qualification

| Field | Value |
|---|---|
| **Test Case ID** | SWQ-012 |
| **Objective** | Verify SWE1-007 (implicitly) — full test suite passes on Python 3.10, 3.11, 3.12 |
| **SW-REQ** | SWE1-069 (portability via `pyproject.toml`) |
| **Verification Method** | CI matrix evidence — `cstylecheck_tests.yml` |

| Python Version | CI Job | Result | GitHub Actions Run URL |
|---|---|---|---|
| 3.10 | `cstylecheck_tests.yml` | \<PASS / FAIL\> | \<URL\> |
| 3.11 | `cstylecheck_tests.yml` | \<PASS / FAIL\> | \<URL\> |
| 3.12 | `cstylecheck_tests.yml` | \<PASS / FAIL\> | \<URL\> |

---

## 5. Qualification Test Results Summary

| SWQ-ID | Test Case | SW-REQ Coverage | Result | Deviation |
|---|---|---|---|---|
| SWQ-001 | Configuration loading | SWE1-001 to SWE1-006 | \<PASS/FAIL\> | |
| SWQ-002 | File discovery and CLI | SWE1-068 to SWE1-070 | \<PASS/FAIL\> | |
| SWQ-003 | All 48 rule IDs | SWE1-017 to SWE1-056 | \<PASS/FAIL\> | |
| SWQ-004 | Output format qualification | SWE1-057 to SWE1-064 | \<PASS/FAIL\> | |
| SWQ-005 | Dictionary and spell check | SWE1-007 to SWE1-010, SWE1-056 | \<PASS/FAIL\> | |
| SWQ-006 | Cross-file sign compatibility | SWE1-051 to SWE1-053 | \<PASS/FAIL\> | |
| SWQ-007 | Baseline suppression | SWE1-065 to SWE1-067 | \<PASS/FAIL\> | |
| SWQ-008 | Exit code qualification | SWE1-069 | \<PASS/FAIL\> | |
| SWQ-009 | Source cache single read | SWE1-015 | \<PASS/FAIL\> | |
| SWQ-010 | Multi-token typedef detection | SWE1-040 | \<PASS/FAIL\> | |
| SWQ-011 | Naming convention self-verification | SWE1-017 to SWE1-056 | \<PASS/FAIL\> | |
| SWQ-012 | Python portability | SWE1-069 | \<PASS/FAIL\> | |

**Overall Software Qualification Verdict:** \<PASS / FAIL\>

---

## 6. Software Requirements Coverage Matrix

| SW-REQ-ID | Requirement Summary | Qualification Test | Status |
|---|---|---|---|
| SWE1-001 to SWE1-006 | Configuration loading | SWQ-001 | \<Covered\> |
| SWE1-007 to SWE1-010 | Dictionary management | SWQ-005 | \<Covered\> |
| SWE1-011 to SWE1-016 | Source parsing and cache | SWQ-009, SIT-005 | \<Covered\> |
| SWE1-017 to SWE1-029 | Variable rules | SWQ-003 | \<Covered\> |
| SWE1-030 to SWE1-034 | Function rules | SWQ-003 | \<Covered\> |
| SWE1-035 to SWE1-039 | Constant/macro rules | SWQ-003 | \<Covered\> |
| SWE1-040 to SWE1-042 | Type rules | SWQ-003, SWQ-010 | \<Covered\> |
| SWE1-043 to SWE1-044 | Include guard rules | SWQ-003 | \<Covered\> |
| SWE1-045 to SWE1-050 | Miscellaneous rules | SWQ-003 | \<Covered\> |
| SWE1-051 to SWE1-053 | Sign compatibility | SWQ-006 | \<Covered\> |
| SWE1-054 to SWE1-056 | Reserved names / spell check | SWQ-003, SWQ-005 | \<Covered\> |
| SWE1-057 to SWE1-064 | Output formats | SWQ-004 | \<Covered\> |
| SWE1-065 to SWE1-067 | Baseline suppression | SWQ-007 | \<Covered\> |
| SWE1-068 to SWE1-070 | CLI and entry point | SWQ-002 | \<Covered\> |

**Requirements Coverage:** 70 / 70 requirements covered (100%)

---

## 7. Code Coverage Report

| Metric | Measured Value | Target | Status |
|---|---|---|---|
| Statement coverage | \<fill from coverage.xml\> % | ≥ 90% | \<PASS/FAIL\> |
| Branch coverage | \<fill from coverage.xml\> % | ≥ 85% | \<PASS/FAIL\> |
| Function coverage | \<fill from coverage.xml\> % | 100% | \<PASS/FAIL\> |
| Coverage report artefact | `coverage.xml` | GitHub Actions artefact | \<URL\> |

---

## 8. Open Issues and Deviations

| Issue # | Description | Severity | Status | Resolution |
|---|---|---|---|---|
| \<#\> | \<Description\> | \<Critical / Major / Minor\> | \<Open / Closed\> | \<Resolution or reference\> |

---

## 9. Release Readiness Gate

All of the following conditions must be met before the v1.0.0 release baseline is created (SPL.2):

- [ ] All SWQ test cases: PASS
- [ ] Statement coverage ≥ 90%
- [ ] Branch coverage ≥ 85%
- [ ] `cstylecheck_rules.yml` CI job: PASS on v1.0.0 commit
- [ ] `cstylecheck_tests.yml` CI: PASS on Python 3.10, 3.11, 3.12
- [ ] `docker_publish.yml` CI: PASS; image available on GHCR + Docker Hub
- [ ] Zero open bug-labelled GitHub Issues targeting v1.0.0
- [ ] This document approved and placed under CM baseline (SUP.8)
- [ ] All TBD items in SYS.5 requirements coverage resolved or formally accepted

---

## 10. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | | 2026-04-12 |
| Technical Reviewer | \<Name\> | | |
| Quality Assurance | \<Name\> | | |
| Approver | \<Name\> | | |

> **⚠️ Important:** Software qualification is the final gate before release. This document must be approved and all release readiness conditions in §9 satisfied before the v1.0.0 release baseline is created and the product is released via SPL.2.
