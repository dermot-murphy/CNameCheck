# System Verification Report

*Automotive SPICE® PAM v4.0 | SYS.5 System Verification*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CNC-SYS5-001 | **Version** | 1.0 |
| **Project** | CNameCheck | **Date** | 2026-04-12 |
| **Status** | Draft | **Classification** | Internal |
| **Author** | Dermot Murphy | **Reviewer** | \<Reviewer Name\> |
| **Approver** | \<Approver Name\> | **Related Process** | SYS.5 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | 2026-04-12 | Dermot Murphy | Initial release |

---

## 3. Purpose & Scope

### 3.1 Purpose

This System Verification Report documents the qualification test specification, execution results, and verdict for **CNameCheck v1.0.0** — verifying that the complete, integrated system satisfies all system requirements defined in CNC-SYS2-001. It satisfies **Automotive SPICE® PAM v4.0, SYS.5 — System Verification**.

System verification (SYS.5) differs from system integration testing (SYS.4) in that it tests the **complete, fully integrated system against its requirements**, rather than testing interface behaviour between subsystems.

### 3.2 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CNC-SYS2-001 | CNameCheck System Requirements Specification | 1.0 |
| CNC-SYS3-001 | CNameCheck System Architecture Description | 1.0 |
| CNC-SYS4-001 | CNameCheck System Integration Test Specification | 1.0 |
| ASPICE PAM v4.0 | Automotive SPICE Process Assessment Model | 4.0 |
| CNC-SUP8-001 | CNameCheck Configuration Management Plan | 1.1 |

### 3.3 System Configuration Under Test

| Attribute | Value |
|---|---|
| **Software Version** | 1.0.0 |
| **Git Tag** | v1.0.0 |
| **Commit SHA** | \<SHA to be filled at execution\> |
| **Python Versions Tested** | 3.10, 3.11, 3.12 |
| **OS** | Ubuntu 24.04 (`ubuntu-latest` GitHub Actions runner) |
| **Docker Image** | `ghcr.io/<org>/cnamecheck:1.0.0` |
| **Docker Image Digest** | \<SHA-256 digest to be filled at execution\> |
| **Test Execution Date** | \<YYYY-MM-DD\> |
| **Tester** | \<Name\> |
| **CM Baseline** | v1.0.0 release tag |

### 3.4 Verification Strategy

| Verification Method | Applied To |
|---|---|
| Dynamic test execution (pytest) | All functional requirements; performance; portability |
| Inspection (code review) | SYS-NF-004 (stdlib only), SYS-F-036 (JSON baseline format), AD-003 (source cache) |
| CI evidence review | SYS-NF-003 (Python matrix), SYS-NF-006 (multi-platform Docker) |

---

## 4. Verification Criteria

| Criterion | Target | Pass Condition |
|---|---|---|
| All SYS-VTC test cases | PASS | Zero FAIL results |
| Requirement coverage | 100% | All SYS-F and SYS-NF requirements traced to at least one SYS-VTC |
| Python version matrix | 3.10, 3.11, 3.12 | All pass on all three versions |
| Exit code correctness | 100% | All exit code test cases PASS |
| Output format conformance | JSON valid, SARIF 2.1.0 valid | Schema validation PASS |
| Open GitHub Issues against v1.0.0 | 0 | No unresolved bug-labelled Issues targeting v1.0.0 |

---

## 5. Qualification Test Cases

---

### SYS-VTC-001 — Input: Multiple Source Files and Glob Expansion

| Field | Value |
|---|---|
| **Test Case ID** | SYS-VTC-001 |
| **Requirement** | SYS-F-001, SYS-F-004, SYS-F-005 |
| **Objective** | Verify system accepts multiple `.c`/`.h` files as arguments, expands `--include` globs, and respects `--exclude` filters |
| **Pass Criteria** | All matching files scanned; excluded files not scanned; exit code correct |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | `python cnamecheck.py file1.c file2.h file3.c` | 3 source files (all clean) | All 3 files scanned; exit 0 |
| 2 | `python cnamecheck.py --include "src/**/*.c" --include "src/**/*.h"` | Directory with 5 `.c`, 3 `.h` | All 8 files scanned |
| 3 | `python cnamecheck.py --include "src/**" --exclude "src/cots/"` | src/ with cots/ subdirectory (containing violations) | cots/ violations NOT reported |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.10 | | |
| | | 3.11 | | |
| | | 3.12 | | |

---

### SYS-VTC-002 — Configuration Loading and Rule Enablement

| Field | Value |
|---|---|
| **Test Case ID** | SYS-VTC-002 |
| **Requirement** | SYS-F-002, SYS-F-025, SYS-F-026, SYS-NF-007 |
| **Objective** | Verify all rules can be independently enabled/disabled and that severity is configurable per rule |
| **Pass Criteria** | Disabled rule produces no violations; severity label in output matches configuration |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Disable `variable.global.case` in YAML; run on file with case violation | Modified config | No `variable.global.case` violation reported |
| 2 | Re-enable with `severity: warning`; run on same file | Modified config | Violation reported as `warning` not `error` |
| 3 | Disable `spell_check`; run on file with misspelled identifier | Modified config | No `spell_check` violation reported |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SYS-VTC-003 — Full Rule Coverage (48 Rule IDs)

| Field | Value |
|---|---|
| **Test Case ID** | SYS-VTC-003 |
| **Requirement** | SYS-F-011 through SYS-F-024 |
| **Objective** | Verify that all 48 rule IDs detect violations when triggered by conforming test inputs |
| **Pass Criteria** | Each rule ID appears in at least one violation report when a known-bad input is provided |

| Rule Category | Rule IDs | Evidence Source | Result |
|---|---|---|---|
| Constants / macros | `constant.case`, `constant.min_length`, `constant.max_length`, `constant.prefix`, `macro.case`, `macro.min_length`, `macro.max_length`, `macro.prefix` | `test_defines.py` (16 tests) | |
| Variables — global | `variable.global.case`, `variable.global.prefix`, `variable.global.g_prefix` | `test_variables.py` | |
| Variables — static | `variable.static.case`, `variable.static.prefix`, `variable.static.s_prefix` | `test_variables.py` | |
| Variables — local/param | `variable.local.case`, `variable.parameter.case`, `variable.parameter.p_prefix` | `test_variables.py` | |
| Variable prefixes | `variable.min_length`, `variable.max_length`, `variable.pointer_prefix`, `variable.pp_prefix`, `variable.bool_prefix`, `variable.handle_prefix`, `variable.no_numeric_in_name`, `variable.prefix_order` | `test_variables.py`, `test_misc_improvements.py` | |
| Functions | `function.prefix`, `function.style`, `function.min_length`, `function.max_length`, `function.static_prefix` | `test_functions.py` | |
| Types | `typedef.case`, `typedef.suffix`, `enum.type_case`, `enum.type_suffix`, `enum.member_case`, `enum.member_prefix`, `struct.tag_case`, `struct.tag_suffix`, `struct.member_case` | `test_typedefs.py`, `test_enums.py`, `test_structs.py` | |
| Include guards | `include_guard.missing`, `include_guard.format` | `test_include_guards.py` | |
| Misc | `misc.line_length`, `misc.indentation`, `misc.magic_number`, `misc.unsigned_suffix`, `misc.yoda_condition`, `misc.block_comment_spacing` | `test_misc.py`, `test_misc_improvements.py` | |
| Other | `reserved_name`, `spell_check`, `sign_compatibility` | `test_reserved_name.py`, `test_spell_check.py`, `test_sign_compatibility.py` | |

**Overall VTC-003 Result:** \<PASS / FAIL\>

---

### SYS-VTC-004 — Module Prefix Enforcement

| Field | Value |
|---|---|
| **Test Case ID** | SYS-VTC-004 |
| **Requirement** | SYS-F-012 |
| **Objective** | Verify module prefix is correctly derived from filename stem and enforced on globals, statics, functions, macros, and constants |
| **Pass Criteria** | Missing or incorrect prefix → violation; correct prefix → no violation |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | File named `uart.c` with global `int uart_g_count = 0;` | Conforming prefix | No violation |
| 2 | File named `uart.c` with global `int spi_g_count = 0;` | Wrong module prefix | `variable.global.prefix` violation |
| 3 | File named `main.c` with `exempt_main: true` | `main.c` | No module-prefix violation regardless of identifier names |
| 4 | Function `uart_BufferRead()` in `uart.c` | Conforming | No violation |
| 5 | Function `Init()` in `uart.c` | Missing prefix | `function.prefix` violation |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SYS-VTC-005 — Pointer and Scope Prefix Rules

| Field | Value |
|---|---|
| **Test Case ID** | SYS-VTC-005 |
| **Requirement** | SYS-F-013, SYS-F-014 |
| **Objective** | Verify scope-aware variable rules and pointer/boolean/handle prefix enforcement |
| **Pass Criteria** | Correct prefixes pass; missing/wrong prefixes produce appropriate violations |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | `static int uart_s_count = 0;` in file scope | File-scope static | No violation |
| 2 | `static int uart_count = 0;` in file scope | Missing `s_` | `variable.static.s_prefix` violation |
| 3 | `uint8_t *p_data` parameter | Single pointer | No violation |
| 4 | `uint8_t *data` parameter | Missing `p_` | `variable.parameter.p_prefix` violation |
| 5 | `uint8_t **pp_buffer` | Double pointer | No violation |
| 6 | `bool b_enabled` local | Bool variable | No violation |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SYS-VTC-006 — Output Formats: Text, JSON, SARIF

| Field | Value |
|---|---|
| **Test Case ID** | SYS-VTC-006 |
| **Requirement** | SYS-F-027, SYS-F-028, SYS-F-029 |
| **Objective** | Verify all three output formats render correct violation data for the same source input |
| **Pass Criteria** | All three formats report identical violation count for the same source; JSON and SARIF are schema-valid |

| Step | Action | Format | Expected Result |
|---|---|---|---|
| 1 | Invoke on source with 3 errors, 2 warnings | `text` | 5 violation lines; summary shows 3 errors, 2 warnings |
| 2 | Same source | `json` | Valid JSON; `summary.errors == 3`; `summary.warnings == 2`; 5 entries in `violations` |
| 3 | Same source | `sarif` | Valid SARIF 2.1.0; 5 results in `runs[0].results` |
| 4 | Verify cross-format consistency | All three | Violation counts match across all three formats |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SYS-VTC-007 — Baseline Suppression Behaviour

| Field | Value |
|---|---|
| **Test Case ID** | SYS-VTC-007 |
| **Requirement** | SYS-F-034, SYS-F-035, SYS-F-036 |
| **Objective** | Verify baseline write and suppress behaviour across the complete system |
| **Pass Criteria** | Baseline file is valid JSON; suppressed violations are not reported; new violations are reported |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | `--write-baseline baseline.json` with 3-violation source | Source v1 | `baseline.json` is valid JSON with 3 entries; exit 0 |
| 2 | `--baseline-file baseline.json` with same 3-violation source | Source v1 + baseline | Zero violations reported; exit 0 |
| 3 | `--baseline-file baseline.json` with 4-violation source (1 new) | Source v2 + baseline | 1 new violation reported; exit 1 |
| 4 | Inspect `baseline.json` in text editor | File | Readable; diffable; no binary content |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SYS-VTC-008 — Exit Code Verification (All Conditions)

| Field | Value |
|---|---|
| **Test Case ID** | SYS-VTC-008 |
| **Requirement** | SYS-F-037, SYS-F-038, SYS-F-039, SYS-F-040 |
| **Objective** | Verify the system returns correct exit codes under all defined conditions |
| **Pass Criteria** | Each scenario returns the specified exit code |

| Scenario | Invocation | Expected Exit Code | Result |
|---|---|---|---|
| Clean source | `cnamecheck clean.c` | 0 | |
| Errors present | `cnamecheck violating.c` | 1 | |
| Warnings only, default | `cnamecheck warning_only.c` | 0 | |
| Warnings only, `--warnings-as-errors` | `cnamecheck --warnings-as-errors warning_only.c` | 1 | |
| Invalid config | `cnamecheck --config missing.yaml` | 2 | |
| `--version` | `cnamecheck --version` | 0 | |
| `--help` | `cnamecheck --help` | 0 | |
| `--exit-zero` + errors | `cnamecheck --exit-zero violating.c` | 0 | |
| `--write-baseline` + errors | `cnamecheck --write-baseline b.json violating.c` | 0 | |

**Overall VTC-008 Result:** \<PASS / FAIL\>

---

### SYS-VTC-009 — Python Version Portability

| Field | Value |
|---|---|
| **Test Case ID** | SYS-VTC-009 |
| **Requirement** | SYS-NF-003 |
| **Objective** | Verify the system operates correctly on Python 3.10, 3.11, and 3.12 |
| **Pass Criteria** | All CI matrix jobs PASS on all three versions |

| Python Version | CI Job | Result | GitHub Actions Run URL |
|---|---|---|---|
| 3.10 | `cnamecheck_tests.yml` | \<PASS / FAIL\> | \<URL\> |
| 3.11 | `cnamecheck_tests.yml` | \<PASS / FAIL\> | \<URL\> |
| 3.12 | `cnamecheck_tests.yml` | \<PASS / FAIL\> | \<URL\> |

---

### SYS-VTC-010 — Third-Party Dependency Constraint

| Field | Value |
|---|---|
| **Test Case ID** | SYS-VTC-010 |
| **Requirement** | SYS-NF-004 |
| **Objective** | Verify that `cnamecheck.py` has no runtime imports outside Python stdlib and PyYAML |
| **Verification Method** | Inspection |
| **Pass Criteria** | Code review confirms no runtime third-party imports |

| Check | Finding | Result |
|---|---|---|
| Inspect all `import` statements in `cnamecheck.py` | All imports are from Python stdlib or `yaml` (PyYAML) | \<PASS / FAIL\> |
| Inspect `requirements.txt` | Contains only `pyyaml>=6.0,<7.0` | \<PASS / FAIL\> |
| Inspect `pyproject.toml` dependencies | `dependencies = ["pyyaml>=6.0,<7.0"]` only | \<PASS / FAIL\> |

---

### SYS-VTC-011 — pip and pipx Installation

| Field | Value |
|---|---|
| **Test Case ID** | SYS-VTC-011 |
| **Requirement** | SYS-NF-005 |
| **Objective** | Verify successful pip and pipx installation and correct entry point |
| **Pass Criteria** | `cnamecheck` command available after install; version correct |

| Step | Action | Expected Result | Result |
|---|---|---|---|
| 1 | `python -m venv venv && pip install .` in clean venv | Install completes; no errors | |
| 2 | `venv/bin/cnamecheck --version` | Prints `CNameCheck v1.0.0`; exit 0 | |
| 3 | `pipx install .` (separate test) | Install completes; `cnamecheck` on PATH | |
| 4 | `cnamecheck --version` via pipx | Correct version; exit 0 | |

---

### SYS-VTC-012 — Docker Multi-Platform Build

| Field | Value |
|---|---|
| **Test Case ID** | SYS-VTC-012 |
| **Requirement** | SYS-NF-006 |
| **Objective** | Verify Docker image is built and available for both `linux/amd64` and `linux/arm64` |
| **Verification Method** | CI evidence review (`docker_publish.yml` job result) |
| **Pass Criteria** | Both platform manifests present in GHCR for tag `v1.0.0` |

| Check | Finding | Result |
|---|---|---|
| `docker manifest inspect ghcr.io/<org>/cnamecheck:1.0.0` | Contains `linux/amd64` digest | \<PASS / FAIL\> |
| `docker manifest inspect ghcr.io/<org>/cnamecheck:1.0.0` | Contains `linux/arm64` digest | \<PASS / FAIL\> |
| `docker_publish.yml` CI run result | Job `build-and-push` status = success | \<PASS / FAIL\> |
| Image digest recorded | Digest in Actions log | \<Digest value\> |

---

### SYS-VTC-013 — Self-Hosting: Linter Passes Its Own Rules

| Field | Value |
|---|---|
| **Test Case ID** | SYS-VTC-013 |
| **Requirement** | SYS-F-011 (implicit quality gate) |
| **Objective** | Verify that `cnamecheck.py` passes its own naming-convention rules, as enforced by the `naming_convention.yml` CI workflow |
| **Verification Method** | CI evidence review |
| **Pass Criteria** | `naming_convention.yml` workflow reports zero errors on the v1.0.0 release commit |

| Check | Finding | Result |
|---|---|---|
| `naming_convention.yml` CI job on v1.0.0 tag | Status = success; zero error violations | \<PASS / FAIL\> |
| Workflow run URL | \<GitHub Actions URL\> | |

---

## 6. Verification Results Summary

| SYS-VTC-ID | Test Case | SYS REQ Coverage | Result | Deviation Ref |
|---|---|---|---|---|
| SYS-VTC-001 | Input: multiple files and globs | SYS-F-001, F-004, F-005 | \<PASS/FAIL\> | |
| SYS-VTC-002 | Configuration and rule enablement | SYS-F-002, F-025, F-026, NF-007 | \<PASS/FAIL\> | |
| SYS-VTC-003 | Full rule coverage (48 rule IDs) | SYS-F-011 to F-024 | \<PASS/FAIL\> | |
| SYS-VTC-004 | Module prefix enforcement | SYS-F-012 | \<PASS/FAIL\> | |
| SYS-VTC-005 | Pointer and scope prefix rules | SYS-F-013, F-014 | \<PASS/FAIL\> | |
| SYS-VTC-006 | Output formats: text, JSON, SARIF | SYS-F-027, F-028, F-029 | \<PASS/FAIL\> | |
| SYS-VTC-007 | Baseline suppression | SYS-F-034, F-035, F-036 | \<PASS/FAIL\> | |
| SYS-VTC-008 | Exit code verification | SYS-F-037, F-038, F-039, F-040 | \<PASS/FAIL\> | |
| SYS-VTC-009 | Python version portability | SYS-NF-003 | \<PASS/FAIL\> | |
| SYS-VTC-010 | Third-party dependency constraint | SYS-NF-004 | \<PASS/FAIL\> | |
| SYS-VTC-011 | pip and pipx installation | SYS-NF-005 | \<PASS/FAIL\> | |
| SYS-VTC-012 | Docker multi-platform build | SYS-NF-006 | \<PASS/FAIL\> | |
| SYS-VTC-013 | Self-hosting: linter passes own rules | SYS-F-011 | \<PASS/FAIL\> | |

**Overall System Verification Verdict:** \<PASS / FAIL\>

---

## 7. Requirements Coverage Matrix

| SYS REQ-ID | Requirement Summary | Covered By | Status |
|---|---|---|---|
| SYS-F-001 | Accept `.c`/`.h` files as arguments | SYS-VTC-001 | \<Covered\> |
| SYS-F-002 | Accept `--config` YAML file | SYS-VTC-002 | \<Covered\> |
| SYS-F-003 | Accept `--options-file` | SITC-003 | \<Covered\> |
| SYS-F-004 | `--include` glob patterns | SYS-VTC-001 | \<Covered\> |
| SYS-F-005 | `--exclude` glob patterns | SYS-VTC-001 | \<Covered\> |
| SYS-F-006 | `--defines` file | \<SYS-VTC-xxx\> | \<TBD\> |
| SYS-F-007 | `--aliases` file | \<SYS-VTC-xxx\> | \<TBD\> |
| SYS-F-008 | `--exclusions` file | SITC-009 | \<Covered\> |
| SYS-F-009 | Dictionary override flags | \<SYS-VTC-xxx\> | \<TBD\> |
| SYS-F-010 | Single file read per invocation | SYS-VTC-003 (via cache), SITC-008 | \<Covered\> |
| SYS-F-011 to F-024 | All 48 rule IDs | SYS-VTC-003, VTC-004, VTC-005 | \<Covered\> |
| SYS-F-025 | Rule `enabled` toggle | SYS-VTC-002 | \<Covered\> |
| SYS-F-026 | Per-rule severity | SYS-VTC-002 | \<Covered\> |
| SYS-F-027 | Text output format | SYS-VTC-006 | \<Covered\> |
| SYS-F-028 | JSON output format | SYS-VTC-006 | \<Covered\> |
| SYS-F-029 | SARIF output format | SYS-VTC-006 | \<Covered\> |
| SYS-F-030 | GitHub Actions annotations | SITC-013 | \<Covered\> |
| SYS-F-031 | `--log` file output | SITC-006 | \<Covered\> |
| SYS-F-032 | `--summary` table | \<SYS-VTC-xxx\> | \<TBD\> |
| SYS-F-033 | `--verbose` progress | \<SYS-VTC-xxx\> | \<TBD\> |
| SYS-F-034 | `--write-baseline` | SYS-VTC-007 | \<Covered\> |
| SYS-F-035 | `--baseline-file` suppression | SYS-VTC-007 | \<Covered\> |
| SYS-F-036 | Baseline file is plain JSON | SYS-VTC-007 | \<Covered\> |
| SYS-F-037 | Exit code 0 (clean) | SYS-VTC-008 | \<Covered\> |
| SYS-F-038 | Exit code 1 (errors) | SYS-VTC-008 | \<Covered\> |
| SYS-F-039 | Exit code 2 (config error) | SYS-VTC-008 | \<Covered\> |
| SYS-F-040 | `--warnings-as-errors` | SYS-VTC-008, SITC-014 | \<Covered\> |
| SYS-NF-001 | Single file read | SITC-008 | \<Covered\> |
| SYS-NF-002 | Performance (100 files / 30s) | \<SYS-VTC-xxx\> | \<TBD\> |
| SYS-NF-003 | Python 3.10, 3.11, 3.12 | SYS-VTC-009 | \<Covered\> |
| SYS-NF-004 | stdlib only + PyYAML | SYS-VTC-010 | \<Covered\> |
| SYS-NF-005 | pip/pipx install | SYS-VTC-011 | \<Covered\> |
| SYS-NF-006 | Multi-platform Docker | SYS-VTC-012 | \<Covered\> |
| SYS-NF-007 | YAML configuration | SYS-VTC-002 | \<Covered\> |
| SYS-NF-008 | Options file precedence | SITC-003 | \<Covered\> |
| SYS-NF-009 | Per-file exclusions | SITC-009 | \<Covered\> |
| SYS-NF-010 | pre-commit integration | \<SYS-VTC-xxx\> | \<TBD\> |
| SYS-NF-011 | GitHub Action `action.yml` | \<SYS-VTC-xxx\> | \<TBD\> |
| SYS-NF-012 | GitHub Action step outputs | \<SYS-VTC-xxx\> | \<TBD\> |

> **📋 Note:** Requirements marked \<TBD\> require additional test cases to be added in a subsequent version of this document before the system verification can be closed. These shall be tracked as GitHub Issues.

---

## 8. Open Issues & Deviations

| Issue # | Description | Severity | Status |
|---|---|---|---|
| \<#\> | \<Description of any open issue or test deviation\> | \<Critical / Major / Minor\> | \<Open / Closed\> |

---

## 9. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Dermot Murphy | | 2026-04-12 |
| Technical Reviewer | \<Name\> | | |
| Quality Assurance | \<Name\> | | |
| Approver | \<Name\> | | |

> **⚠️ Important:** System verification is considered complete only when all SYS-VTC test cases achieve PASS status and all \<TBD\> requirements are covered. This document must be approved before the system is released to production and before the release baseline is created (SUP.8). Any open issues must be resolved or formally accepted via the change control process (SUP.10).
