# Software Integration Test Specification

*Automotive SPICE® PAM v4.0 | SWE.5 Software Integration and Integration Verification*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CSC-SWE5-001 | **Version** | 1.0 |
| **Project** | CStyleCheck | **Date** | 2026-04-12 |
| **Status** | Released | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SWE.5 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose & Scope

This document defines the software integration test specification for **CStyleCheck v1.0.0**, verifying that the software components integrate correctly across the interfaces defined in CSC-SWE2-001. It satisfies **Automotive SPICE® PAM v4.0, SWE.5 — Software Integration and Integration Verification**.

Integration tests operate at a higher level than unit tests (SWE.4): they exercise data flows **across component boundaries** — primarily the path from COMP-01 (CLI) through COMP-04 (Parser) into COMP-05 (Rule Engine) and COMP-07 (Output Formatter) — rather than individual method logic.

The primary integration test suite is `tests/test_cli.py`, which invokes `cstylecheck.py` as a subprocess and validates its end-to-end behaviour.

### 3.1 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CSC-SWE2-001 | CStyleCheck Software Architecture Description | 1.0 |
| CSC-SWE4-001 | CStyleCheck Unit Verification Specification | 1.0 |
| CSC-SWE6-001 | CStyleCheck Software Qualification Test Specification | 1.0 |
| CSC-SYS4-001 | CStyleCheck System Integration Test Specification | 1.0 |

### 3.2 Test Environment

| Attribute | Value |
|---|---|
| **OS** | Ubuntu 24.04 (`ubuntu-latest` GitHub Actions runner) |
| **Python Versions** | 3.10, 3.11, 3.12 |
| **Test runner** | pytest 7+ via `cstylecheck_tests.yml` CI workflow |
| **Invocation method** | `subprocess.run()` — full process invocation including argument parsing |
| **CM Baseline ID** | \<Git commit SHA at test execution\> |

### 3.3 Integration Verification Criteria

| Criterion | Target | Measurement |
|---|---|---|
| All SIT test cases | PASS | pytest result |
| Interface coverage | All 10 SWA interfaces exercised | Traceability matrix |
| Exit code correctness | 100% | Subprocess return code assertion |
| Output schema conformance | JSON and SARIF valid | Schema validation in test |

---

## 4. Interface Coverage Plan

Each software architecture interface (SWA-IF-01 to SWA-IF-10) must be exercised by at least one integration test.

| Interface ID | Description | Covered By |
|---|---|---|
| SWA-IF-01 | COMP-01 → COMP-02: config/alias/exclusions paths | SIT-001, SIT-008 |
| SWA-IF-02 | COMP-01 → main(): file list and CLI flags | SIT-001, SIT-002, SIT-003 |
| SWA-IF-03 | COMP-02 → COMP-05: cfg dict, alias_prefixes, disabled_rules | SIT-004, SIT-008 |
| SWA-IF-04 | COMP-02 → COMP-04: defines substitution applied to source | SIT-009 |
| SWA-IF-05 | COMP-03 → COMP-05: keyword/stdlib/spell/banned frozensets | SIT-010 |
| SWA-IF-06 | COMP-04 → COMP-05: clean source, line_map, brace_depths | SIT-001, SIT-005 |
| SWA-IF-07 | COMP-04 → COMP-05g: cached source for cross-file sign check | SIT-011 |
| SWA-IF-08 | COMP-05 → COMP-06: violation list to baseline manager | SIT-012 |
| SWA-IF-09 | COMP-06 → COMP-05: baseline frozenset for filtering | SIT-012 |
| SWA-IF-10 | COMP-05 → COMP-07: violation list to output formatter | SIT-001, SIT-006, SIT-007 |

---

## 5. Integration Test Cases

---

### SIT-001 — CLI → Parser → Rule Engine → Output (Full Pipeline)

| Field | Value |
|---|---|
| **Test Case ID** | SIT-001 |
| **Objective** | Verify end-to-end flow through SWA-IF-01, IF-02, IF-06, IF-10 on a non-conforming source file |
| **Interfaces** | SWA-IF-01, IF-02, IF-06, IF-10 |
| **SW-REQ** | SWE1-057, SWE1-069 |
| **Test file** | `test_cli.py` |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | `subprocess.run(["python", "cstylecheck.py", "--config", "rules.yml", "violating.c"])` | Source with known `variable.global.case` violation | stdout contains `variable.global.case` violation line |
| 2 | Check output format | stdout | `{file}:{line}:{col}: ERROR [variable.global.case] ...` |
| 3 | Check exit code | returncode | `1` |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.10 | | |
| | | 3.11 | | |
| | | 3.12 | | |

---

### SIT-002 — Options File → CLI Merge → File Discovery

| Field | Value |
|---|---|
| **Test Case ID** | SIT-002 |
| **Objective** | Verify SWA-IF-02: options-file tokens injected before direct CLI args; direct args override |
| **Interfaces** | SWA-IF-02 |
| **SW-REQ** | SWE1-068 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Run with `--options-file` specifying `--config config_A.yaml` | Options file + no direct config | `config_A.yaml` used |
| 2 | Run with `--options-file` + `--config config_B.yaml` direct | Same options file | `config_B.yaml` used (direct takes precedence) |
| 3 | Verify exit code in both cases | — | Exit 0 or 1; never 2 |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SIT-003 — Glob Include + Exclude → File List (COMP-01 → main)

| Field | Value |
|---|---|
| **Test Case ID** | SIT-003 |
| **Objective** | Verify `discover_files()` correctly expands includes and applies excludes before the processing loop |
| **Interfaces** | SWA-IF-02 |
| **SW-REQ** | SWE1-070 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | `--include "src/**/*.c" --include "src/**/*.h"` | Directory with 5 `.c`, 3 `.h` | All 8 files scanned; summary shows `files_checked: 8` |
| 2 | Add `--exclude "src/cots/"` | cots/ subdirectory contains violations | Violations from cots/ not present in output |
| 3 | Verify non-excluded file violations still reported | Other src/ file with violation | Violation reported |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SIT-004 — Config Loader → Rule Engine (COMP-02 → COMP-05)

| Field | Value |
|---|---|
| **Test Case ID** | SIT-004 |
| **Objective** | Verify SWA-IF-03: disabled rule in YAML config correctly suppresses violation in rule engine |
| **Interfaces** | SWA-IF-03 |
| **SW-REQ** | SWE1-001, SWE1-005, SWE1-006 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Config with `variable.global.case.enabled: false`; source with case violation | Modified config | `variable.global.case` NOT in output |
| 2 | Same source; default config | Default config | `variable.global.case` IS in output |
| 3 | Config with per-file exclusion for the test file | exclusions YAML | Rule suppressed for that file only |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SIT-005 — Source Parser → Rule Engine Scope Detection (COMP-04 → COMP-05)

| Field | Value |
|---|---|
| **Test Case ID** | SIT-005 |
| **Objective** | Verify SWA-IF-06: brace-depth array correctly drives scope classification — global vs. file-static vs. local |
| **Interfaces** | SWA-IF-06 |
| **SW-REQ** | SWE1-014, SWE1-017 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Source with global `BadName` (no `g_` prefix) | Non-conforming global | `variable.global.g_prefix` violation at line N |
| 2 | Same name declared inside function body | Local scope | No `variable.global.g_prefix` violation; `variable.local.case` may fire |
| 3 | Static variable at file scope | File-static scope | `variable.static.s_prefix` violation if `s_` missing |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SIT-006 — Rule Engine → JSON Output (COMP-05 → COMP-07)

| Field | Value |
|---|---|
| **Test Case ID** | SIT-006 |
| **Objective** | Verify SWA-IF-10: `_violations_to_json()` correctly receives violation list and produces valid JSON schema |
| **Interfaces** | SWA-IF-10 |
| **SW-REQ** | SWE1-058, SWE1-059 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | `--output-format json` with 3-error, 2-warning source | Subprocess invocation | stdout is valid JSON |
| 2 | Parse and validate | JSON output | `summary.errors == 3`; `summary.warnings == 2`; 5 entries in `violations` array |
| 3 | Inspect each violation | violations array | All have: `file`, `line`, `col`, `severity`, `rule`, `message` |
| 4 | Check exit code | returncode | `1` (errors present) |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SIT-007 — Rule Engine → SARIF Output (COMP-05 → COMP-07)

| Field | Value |
|---|---|
| **Test Case ID** | SIT-007 |
| **Objective** | Verify SWA-IF-10: `_violations_to_sarif()` produces valid SARIF 2.1.0 |
| **Interfaces** | SWA-IF-10 |
| **SW-REQ** | SWE1-060 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | `--output-format sarif` with violation source | Subprocess | stdout is valid JSON with `$schema` field |
| 2 | Validate SARIF structure | Parsed JSON | `runs[0].tool.driver.name == "CStyleCheck"`; `runs[0].results` non-empty |
| 3 | Verify location data | Each result | `physicalLocation.artifactLocation.uri` and `region.startLine` present |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SIT-008 — exclusions File → Disabled Rules → Rule Engine (SWA-IF-01, IF-03)

| Field | Value |
|---|---|
| **Test Case ID** | SIT-008 |
| **Objective** | Verify per-file exclusion YAML flows correctly through COMP-02 into COMP-05 rule filtering |
| **Interfaces** | SWA-IF-01, SWA-IF-03 |
| **SW-REQ** | SWE1-005, SWE1-006 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | `exclusions.yml` suppresses `variable.global.case` for `uart.c` | Source with case violation | No `variable.global.case` in output for `uart.c` |
| 2 | Same exclusion; different file `spi.c` with same violation | `spi.c` | Violation IS reported for `spi.c` |
| 3 | Remove exclusion; re-run | No exclusions file | Violation reported for `uart.c` |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SIT-009 — Defines File → Source Substitution → Rule Engine (SWA-IF-04)

| Field | Value |
|---|---|
| **Test Case ID** | SIT-009 |
| **Objective** | Verify SWA-IF-04: defines substitution applied by COMP-02 before COMP-05 rule checks |
| **Interfaces** | SWA-IF-04 |
| **SW-REQ** | SWE1-003 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | `defines.txt` maps `STATIC → static`; source uses `STATIC int uart_s_count` | Source + defines file | Correctly identified as file-static; `variable.static.*` rules applied |
| 2 | Same source without defines | No defines | `STATIC` not recognised; rule may not fire correctly |
| 3 | Defines mapping `uint32_t → unsigned int`; source uses both | Mixed types | Both resolve to same signedness for sign-compat check |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SIT-010 — Dictionary Override → Rule Engine (SWA-IF-05)

| Field | Value |
|---|---|
| **Test Case ID** | SIT-010 |
| **Objective** | Verify SWA-IF-05: custom dictionary files correctly replace built-in sets in rule engine |
| **Interfaces** | SWA-IF-05 |
| **SW-REQ** | SWE1-007, SWE1-008, SWE1-009 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | `--keywords-file custom_keywords.txt` with C keyword removed | Source using removed keyword as identifier | No `reserved_name` violation |
| 2 | `--spell-dict custom_dict.txt` with extra word added | Source using extra word in identifier | No `spell_check` violation |
| 3 | Run without overrides | Same sources | Violations IS present for both cases |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SIT-011 — Source Cache → Sign Checker (COMP-04 → COMP-05g, SWA-IF-07)

| Field | Value |
|---|---|
| **Test Case ID** | SIT-011 |
| **Objective** | Verify SWA-IF-07: cross-file sign compatibility check correctly uses cached source from COMP-04 |
| **Interfaces** | SWA-IF-07 |
| **SW-REQ** | SWE1-015, SWE1-051, SWE1-052 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | `uart.c` passes `100U` to function declared with `int` param in `uart.h` | Both files | `sign_compatibility` violation raised |
| 2 | Both files use `uint32_t` consistently | Consistent pair | No violation |
| 3 | Verify single file read per file | — | No observable duplicate I/O (source cache enforced by architecture) |
| 4 | `plain_char_is_signed: false`; pass `char` arg to `unsigned char` param | Config + source | Violation raised; re-run with `true` → no violation |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SIT-012 — Baseline Write → Load → Rule Engine Filter (SWA-IF-08, IF-09)

| Field | Value |
|---|---|
| **Test Case ID** | SIT-012 |
| **Objective** | Verify SWA-IF-08 and IF-09: violation list written to baseline correctly filters rule engine output on reload |
| **Interfaces** | SWA-IF-08, SWA-IF-09 |
| **SW-REQ** | SWE1-065, SWE1-066, SWE1-067 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | `--write-baseline baseline.json` with 2-violation source | Source v1 | `baseline.json` created; 2 entries; exit 0 |
| 2 | `--baseline-file baseline.json` same source | Source v1 + baseline | 0 violations output; exit 0 |
| 3 | Add third violation to source | Source v2 | 1 violation reported (new); 2 suppressed; exit 1 |
| 4 | Inspect `baseline.json` | File | Valid JSON array with `rule`, `filepath`, `line`, `message` per entry |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

### SIT-013 — Log File Tee (COMP-07 filesystem interface)

| Field | Value |
|---|---|
| **Test Case ID** | SIT-013 |
| **Objective** | Verify `Tee` class mirrors stdout content to log file without modification |
| **Interfaces** | SWA-IF-10 (filesystem output) |
| **SW-REQ** | SWE1-062 |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | `--log results.txt` with violation source | Subprocess | `results.txt` created; content matches stdout |
| 2 | Run without `--log` | Same source | No `results.txt` created |
| 3 | Inspect `results.txt` | File content | Identical to stdout (same violation lines) |

| Date | Tester | Python | Result | Deviation |
|---|---|---|---|---|
| | | 3.11 | | |

---

## 6. Integration Test Results Summary

| SIT-ID | Test Case | Interfaces | Status | Deviation Ref |
|---|---|---|---|---|
| SIT-001 | Full pipeline: CLI → Output | IF-01, IF-02, IF-06, IF-10 | \<PASS/FAIL\> | |
| SIT-002 | Options file → CLI merge | IF-02 | \<PASS/FAIL\> | |
| SIT-003 | Glob include + exclude | IF-02 | \<PASS/FAIL\> | |
| SIT-004 | Config loader → Rule engine | IF-03 | \<PASS/FAIL\> | |
| SIT-005 | Parser scope → Rule engine | IF-06 | \<PASS/FAIL\> | |
| SIT-006 | Rule engine → JSON output | IF-10 | \<PASS/FAIL\> | |
| SIT-007 | Rule engine → SARIF output | IF-10 | \<PASS/FAIL\> | |
| SIT-008 | exclusions -> rule engine | IF-01, IF-03 | \<PASS/FAIL\> | |
| SIT-009 | Defines → Source → Rule engine | IF-04 | \<PASS/FAIL\> | |
| SIT-010 | Dictionary override → Rule engine | IF-05 | \<PASS/FAIL\> | |
| SIT-011 | Source cache → Sign checker | IF-07 | \<PASS/FAIL\> | |
| SIT-012 | Baseline write → load → filter | IF-08, IF-09 | \<PASS/FAIL\> | |
| SIT-013 | Log file Tee | IF-10 (filesystem) | \<PASS/FAIL\> | |

**Overall Integration Verification Result:** \<PASS / FAIL\>

> **📋 Note:** All 10 defined software architecture interfaces must be covered before integration testing is considered complete. Any uncovered interface must be resolved via a new or updated test case.

---

## 7. Traceability Matrix

| SIT-ID | SW-REQ-IDs | SWA Interface(s) | SWE.4 Unit Tests | SWE.6 Qual Test |
|---|---|---|---|---|
| SIT-001 | SWE1-057, SWE1-069 | IF-01, IF-02, IF-06, IF-10 | UV-CLI-001, UV-CLI-003 | SWQ-001 |
| SIT-002 | SWE1-068 | IF-02 | UV-CLI-001, UV-CLI-002 | SWQ-002 |
| SIT-003 | SWE1-070 | IF-02 | UV-CLI-009 | SWQ-002 |
| SIT-004 | SWE1-001, SWE1-005, SWE1-006 | IF-03 | UV-VAR-001, UV-VAR-014 | SWQ-003 |
| SIT-005 | SWE1-014, SWE1-017 | IF-06 | UV-VAR-004 | SWQ-003 |
| SIT-006 | SWE1-058, SWE1-059 | IF-10 | UV-CLI-006 | SWQ-004 |
| SIT-007 | SWE1-060 | IF-10 | UV-CLI-007 | SWQ-004 |
| SIT-008 | SWE1-005, SWE1-006 | IF-01, IF-03 | UV-CLI-002 | SWQ-003 |
| SIT-009 | SWE1-003 | IF-04 | — | SWQ-003 |
| SIT-010 | SWE1-007, SWE1-008, SWE1-009 | IF-05 | UV-DCT-001, UV-DCT-002 | SWQ-005 |
| SIT-011 | SWE1-015, SWE1-051, SWE1-052 | IF-07 | UV-SGN-001, UV-SGN-004 | SWQ-006 |
| SIT-012 | SWE1-065, SWE1-066, SWE1-067 | IF-08, IF-09 | UV-CLI-008 | SWQ-007 |
| SIT-013 | SWE1-062 | IF-10 | — | SWQ-004 |

---

## 8. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | Approved | 2026-04-15 |
| Technical Reviewer | Dermot Murphy | Approved | 2026-04-15 |
| Quality Assurance | Dermot Murphy | Approved | 2026-04-15 |
| Approver | Dermot Murphy | Approved | 2026-04-15 |

> **Note:** This document is under configuration management (SUP.8). Post-approval changes require a change request (SUP.10) and a new document version.
