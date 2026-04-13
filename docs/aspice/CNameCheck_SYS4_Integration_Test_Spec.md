# System Integration Test Specification

*Automotive SPICE® PAM v4.0 | SYS.4 System Integration and Integration Verification*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CNC-SYS4-001 | **Version** | 1.0 |
| **Project** | CStyleCheck | **Date** | 2026-04-12 |
| **Status** | Draft | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SYS.4 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose & Scope

### 3.1 Purpose

This System Integration Test Specification defines the integration test cases that verify the correct assembly, interface behaviour, and end-to-end operation of the **CStyleCheck v1.0.0** system across its six subsystems and four deployment modes. It satisfies **Automotive SPICE® PAM v4.0, SYS.4 — System Integration and Integration Verification**.

### 3.2 Scope

Integration testing at the system level verifies the interfaces and data flows **between** subsystems rather than internal unit behaviour. Tests in this specification exercise:

- The complete CLI invocation path (SS-01 → SS-02 → SS-03 → SS-04 → SS-05 → SS-06)
- Cross-subsystem data flows (configuration loader feeding rule engine; source cache feeding cross-file check)
- All three output format pipelines (text, JSON, SARIF)
- All four deployment modes (CLI Python, pip install, Docker, GitHub Action)
- Integration with pre-commit framework

SWE.4/SWE.5 unit and component-level tests are documented in the software test specifications.

### 3.3 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CNC-SYS2-001 | CStyleCheck System Requirements Specification | 1.0 |
| CNC-SYS3-001 | CStyleCheck System Architecture Description | 1.0 |
| CNC-SYS5-001 | CStyleCheck System Verification Report | 1.0 |
| ASPICE PAM v4.0 | Automotive SPICE Process Assessment Model | 4.0 |

### 3.4 Test Environment

| Attribute | Value |
|---|---|
| **Operating System** | Ubuntu 24.04 (GitHub Actions `ubuntu-latest`) |
| **Python Versions** | 3.10, 3.11, 3.12 (matrix) |
| **Test Framework** | pytest + subprocess (for integration tests) |
| **Docker Runtime** | Docker CLI on GitHub Actions runner |
| **CM Baseline ID** | \<Git tag / commit SHA at test execution\> |

### 3.5 Verification Criteria

| Criterion | Target | Measurement Method |
|---|---|---|
| All SITC test cases | PASS | pytest result / CI job result |
| Exit codes correct | 100% | Subprocess return code assertion |
| JSON schema conformance | Zero violations | JSON schema validator |
| SARIF schema conformance | Zero violations | SARIF validator |
| Docker image available | Build succeeds | `docker_publish.yml` CI job |

---

## 4. Integration Test Cases

---

### SITC-001 — End-to-End CLI: Clean File, Zero Violations

| Field | Value |
|---|---|
| **Test Case ID** | SITC-001 |
| **Test Objective** | Verify that a conforming C source file produces zero violations and exit code 0 across the complete SS-01 → SS-06 pipeline |
| **Architecture Interface** | IF-01, IF-02, IF-04, IF-06, IF-08, IF-09 |
| **Requirement Reference** | SYS-F-001, SYS-F-027, SYS-F-037 |
| **Pre-conditions** | `naming_convention.yaml` present; conforming `.c` and `.h` files available |
| **Test Method** | Dynamic execution via subprocess |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Invoke: `python cnamecheck.py --config naming_convention.yaml clean.c` | Conforming `clean.c` | stdout: no violation lines |
| 2 | Check exit code | — | Exit code = 0 |
| 3 | Repeat on Python 3.10, 3.11, 3.12 | — | All pass |

| Execution Date | Tester | SW Version | Result | Deviation Ref |
|---|---|---|---|---|
| | | | | |

---

### SITC-002 — End-to-End CLI: Violation File, Correct Output Format

| Field | Value |
|---|---|
| **Test Case ID** | SITC-002 |
| **Test Objective** | Verify that a non-conforming file produces violations in the correct text format with correct metadata (file, line, col, severity, rule ID, message) |
| **Architecture Interface** | IF-06, IF-08, IF-09 |
| **Requirement Reference** | SYS-F-027, SYS-F-038 |
| **Pre-conditions** | Source file with a known `variable.global.case` violation |
| **Test Method** | Dynamic execution via subprocess |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Invoke with file containing `int BadName = 0;` in global scope | `--config naming_convention.yaml` | stdout contains line with format: `<file>:<line>:<col>: error [variable.global.case] ...` |
| 2 | Verify all four fields present | — | File path, line number, column, rule ID all present in output |
| 3 | Check exit code | — | Exit code = 1 |

| Execution Date | Tester | SW Version | Result | Deviation Ref |
|---|---|---|---|---|
| | | | | |

---

### SITC-003 — Options File Integration (SS-01 → SS-02 Interface)

| Field | Value |
|---|---|
| **Test Case ID** | SITC-003 |
| **Test Objective** | Verify that options loaded from `--options-file` are correctly merged with direct CLI arguments, and that direct CLI args take precedence (IF-01) |
| **Architecture Interface** | IF-01 |
| **Requirement Reference** | SYS-F-003, SYS-NF-008 |
| **Pre-conditions** | `cnamecheck.options` specifying a config file; direct `--config` override available |
| **Test Method** | Dynamic execution via subprocess |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Invoke with `--options-file cnamecheck.options` | Options file specifies `--config src/naming_convention.yaml` | Tool uses the config from options file; no error |
| 2 | Invoke with `--options-file cnamecheck.options --config override.yaml` | Override config has different rules | Tool uses `override.yaml` not the options file config (CLI takes precedence) |
| 3 | Check exit codes | — | Both invocations: exit 0 or 1 (not 2) |

| Execution Date | Tester | SW Version | Result | Deviation Ref |
|---|---|---|---|---|
| | | | | |

---

### SITC-004 — JSON Output Format (SS-05 → SS-06 Interface)

| Field | Value |
|---|---|
| **Test Case ID** | SITC-004 |
| **Test Objective** | Verify that `--output-format json` produces valid JSON conforming to the documented schema, with correct `summary` and `violations` fields |
| **Architecture Interface** | IF-08, IF-09 |
| **Requirement Reference** | SYS-F-028 |
| **Pre-conditions** | Source file with known violations |
| **Test Method** | Dynamic execution; JSON schema validation |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Invoke: `python cnamecheck.py --output-format json --config naming_convention.yaml violating.c` | File with 3 errors, 2 warnings | stdout is valid JSON |
| 2 | Parse JSON and validate schema | JSON output | `summary.errors == 3`, `summary.warnings == 2`, `violations` array has 5 entries |
| 3 | Verify each violation object | — | Each entry has: `file`, `line`, `col`, `severity`, `rule`, `message` keys |
| 4 | Check exit code | — | Exit code = 1 (errors present) |

| Execution Date | Tester | SW Version | Result | Deviation Ref |
|---|---|---|---|---|
| | | | | |

---

### SITC-005 — SARIF Output Format

| Field | Value |
|---|---|
| **Test Case ID** | SITC-005 |
| **Test Objective** | Verify that `--output-format sarif` produces valid SARIF 2.1.0 output |
| **Architecture Interface** | IF-08, IF-09 |
| **Requirement Reference** | SYS-F-029 |
| **Pre-conditions** | Source file with known violations |
| **Test Method** | Dynamic execution; SARIF schema validation |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Invoke: `python cnamecheck.py --output-format sarif --config naming_convention.yaml violating.c` | Violating source file | stdout is valid SARIF 2.1.0 JSON |
| 2 | Validate SARIF schema | SARIF output | `$schema` field present; `runs[0].results` array populated |
| 3 | Verify location data | — | Each result includes `physicalLocation.artifactLocation.uri` and `region.startLine` |

| Execution Date | Tester | SW Version | Result | Deviation Ref |
|---|---|---|---|---|
| | | | | |

---

### SITC-006 — Log File Output (SS-06 Interface to Filesystem)

| Field | Value |
|---|---|
| **Test Case ID** | SITC-006 |
| **Test Objective** | Verify that `--log FILE` writes identical content to both stdout and the log file |
| **Architecture Interface** | IF-09 |
| **Requirement Reference** | SYS-F-031 |
| **Pre-conditions** | Writable output directory |
| **Test Method** | Dynamic execution; file comparison |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Invoke with `--log output/results.txt` | Violating source | stdout shows violations |
| 2 | Read `output/results.txt` | Log file | Content matches stdout |
| 3 | Verify file created | — | File exists and is non-empty |

| Execution Date | Tester | SW Version | Result | Deviation Ref |
|---|---|---|---|---|
| | | | | |

---

### SITC-007 — Baseline Suppression Round-Trip

| Field | Value |
|---|---|
| **Test Case ID** | SITC-007 |
| **Test Objective** | Verify the complete baseline write → suppress cycle: write baseline, add new violation, verify only new violation reported |
| **Architecture Interface** | IF-10, IF-08, IF-09 |
| **Requirement Reference** | SYS-F-034, SYS-F-035, SYS-F-036 |
| **Pre-conditions** | Source file with one known violation |
| **Test Method** | Dynamic execution; file inspection |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Invoke: `python cnamecheck.py --write-baseline baseline.json violating_v1.c` | File with 1 violation | baseline.json created; exit code = 0 |
| 2 | Inspect baseline.json | JSON file | Valid JSON; contains the 1 violation entry |
| 3 | Add second violation to source → `violating_v2.c` | Source with 2 violations | — |
| 4 | Invoke: `python cnamecheck.py --baseline-file baseline.json violating_v2.c` | Source v2 + baseline | Only the new (2nd) violation reported; original suppressed |
| 5 | Check exit code | — | Exit code = 1 (new error present) |

| Execution Date | Tester | SW Version | Result | Deviation Ref |
|---|---|---|---|---|
| | | | | |

---

### SITC-008 — Cross-File Sign Compatibility (SS-04 → SS-05 Interface IF-07)

| Field | Value |
|---|---|
| **Test Case ID** | SITC-008 |
| **Test Objective** | Verify that the source cache correctly passes sign-compatibility data between the parser and rule engine for cross-file checks |
| **Architecture Interface** | IF-07 |
| **Requirement Reference** | SYS-F-021 |
| **Pre-conditions** | Paired `.c` and `.h` files with mismatched signedness declarations |
| **Test Method** | Dynamic execution |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Invoke with `.c` and `.h` where `unsigned int` in `.c` conflicts with `int` in `.h` | Both files passed to tool | `sign_compatibility` violation raised |
| 2 | Verify single read per file | — | No duplicate I/O (verify via source cache; each file read once) |
| 3 | Invoke with matching declarations | Conforming pair | No `sign_compatibility` violation |

| Execution Date | Tester | SW Version | Result | Deviation Ref |
|---|---|---|---|---|
| | | | | |

---

### SITC-009 — Exclusions File Integration (SS-02 → SS-05)

| Field | Value |
|---|---|
| **Test Case ID** | SITC-009 |
| **Test Objective** | Verify that per-file rule suppressions defined in `exclusions.yml` are applied correctly by the rule engine |
| **Architecture Interface** | IF-04, IF-08 |
| **Requirement Reference** | SYS-F-008, SYS-NF-009 |
| **Pre-conditions** | `exclusions.yml` suppressing a specific rule for a specific file; source file violating that rule |
| **Test Method** | Dynamic execution |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Invoke with `--exclusions exclusions.yml` on file that violates an excluded rule | Both file and exclusions | Excluded violation NOT reported |
| 2 | Invoke without `--exclusions` on same file | Same source only | Violation IS reported |
| 3 | Verify other rules still enforced | Same file with additional unexcluded violation | Unexcluded violation reported |

| Execution Date | Tester | SW Version | Result | Deviation Ref |
|---|---|---|---|---|
| | | | | |

---

### SITC-010 — Exit Code Matrix

| Field | Value |
|---|---|
| **Test Case ID** | SITC-010 |
| **Test Objective** | Verify all three exit codes are returned correctly under the appropriate conditions |
| **Architecture Interface** | IF-09 (exit code output) |
| **Requirement Reference** | SYS-F-037, SYS-F-038, SYS-F-039 |
| **Pre-conditions** | Clean file, violating file, and invalid config available |
| **Test Method** | Dynamic execution |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Invoke on clean file | Conforming source | Exit code = 0 |
| 2 | Invoke on violating file | Non-conforming source | Exit code = 1 |
| 3 | Invoke with nonexistent config file | `--config missing.yaml` | Exit code = 2; error to stderr |
| 4 | Invoke with `--version` | — | Exit code = 0; version string on stdout |
| 5 | Invoke with `--exit-zero` on violating file | Non-conforming source | Exit code = 0 despite violations |

| Execution Date | Tester | SW Version | Result | Deviation Ref |
|---|---|---|---|---|
| | | | | |

---

### SITC-011 — Docker Container Integration

| Field | Value |
|---|---|
| **Test Case ID** | SITC-011 |
| **Test Objective** | Verify that the Docker image correctly mounts user source files and produces correct output |
| **Architecture Interface** | All (via container boundary) |
| **Requirement Reference** | SYS-NF-006 |
| **Pre-conditions** | Docker runtime available; `cnamecheck` image built and available |
| **Test Method** | Dynamic execution via `docker run` |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | `docker run --rm -v "$(pwd):/repo" cnamecheck:latest --config /app/naming_convention.yaml /repo/violating.c` | Violating source mounted at `/repo` | Violations reported to stdout |
| 2 | Check exit code | — | Exit code = 1 |
| 3 | Invoke with `--help` via Docker | — | Help text printed; exit code = 0 |
| 4 | Verify image available for `linux/amd64` and `linux/arm64` | `docker manifest inspect` | Both platform digests present |

| Execution Date | Tester | SW Version | Result | Deviation Ref |
|---|---|---|---|---|
| | | | | |

---

### SITC-012 — pip Install Integration

| Field | Value |
|---|---|
| **Test Case ID** | SITC-012 |
| **Test Objective** | Verify that `pip install .` produces a working `cnamecheck` command with correct version |
| **Architecture Interface** | Entry point → SS-01 |
| **Requirement Reference** | SYS-NF-005 |
| **Pre-conditions** | Clean Python virtualenv |
| **Test Method** | Dynamic execution in virtualenv |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | `pip install .` in clean venv | Repository root | Installation succeeds; no errors |
| 2 | `cnamecheck --version` | — | Version string matches `_version.py`; exit code = 0 |
| 3 | `cnamecheck --config src/naming_convention.yaml clean.c` | Conforming source | Exit code = 0; no violations |

| Execution Date | Tester | SW Version | Result | Deviation Ref |
|---|---|---|---|---|
| | | | | |

---

### SITC-013 — GitHub Actions `--github-actions` Annotation Mode

| Field | Value |
|---|---|
| **Test Case ID** | SITC-013 |
| **Test Objective** | Verify that `--github-actions` flag produces `::error` and `::warning` annotation syntax on stdout |
| **Architecture Interface** | IF-09 |
| **Requirement Reference** | SYS-F-030 |
| **Pre-conditions** | Source with at least one error and one warning violation |
| **Test Method** | Dynamic execution; stdout pattern match |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Invoke: `python cnamecheck.py --github-actions --config naming_convention.yaml violating.c` | Mixed error/warning source | stdout contains `::error file=...,line=...,col=...::` for errors |
| 2 | Verify warning format | — | stdout contains `::warning file=...,line=...,col=...::` for warnings |
| 3 | Invoke without `--github-actions` | Same source | No `::error` / `::warning` prefixes in output |

| Execution Date | Tester | SW Version | Result | Deviation Ref |
|---|---|---|---|---|
| | | | | |

---

### SITC-014 — `--warnings-as-errors` Promotion

| Field | Value |
|---|---|
| **Test Case ID** | SITC-014 |
| **Test Objective** | Verify that `--warnings-as-errors` causes warnings to be treated as errors for exit-code purposes |
| **Architecture Interface** | IF-09 |
| **Requirement Reference** | SYS-F-040 |
| **Pre-conditions** | Source file with warning-level violations only (no errors) |
| **Test Method** | Dynamic execution |

| Step | Action | Input | Expected Result |
|---|---|---|---|
| 1 | Invoke without `--warnings-as-errors` on warning-only source | Warning-level violations | Exit code = 0 (warnings do not trigger exit 1) |
| 2 | Invoke with `--warnings-as-errors` on same source | Same source | Exit code = 1; warnings shown as errors in output |

| Execution Date | Tester | SW Version | Result | Deviation Ref |
|---|---|---|---|---|
| | | | | |

---

## 5. Integration Test Results Summary

| SITC-ID | Test Case | Status | Deviation Ref |
|---|---|---|---|
| SITC-001 | End-to-End CLI: clean file | \<PASS / FAIL / N/A\> | |
| SITC-002 | End-to-End CLI: violation output format | \<PASS / FAIL / N/A\> | |
| SITC-003 | Options file integration | \<PASS / FAIL / N/A\> | |
| SITC-004 | JSON output format | \<PASS / FAIL / N/A\> | |
| SITC-005 | SARIF output format | \<PASS / FAIL / N/A\> | |
| SITC-006 | Log file output | \<PASS / FAIL / N/A\> | |
| SITC-007 | Baseline suppression round-trip | \<PASS / FAIL / N/A\> | |
| SITC-008 | Cross-file sign compatibility | \<PASS / FAIL / N/A\> | |
| SITC-009 | Exclusions file integration | \<PASS / FAIL / N/A\> | |
| SITC-010 | Exit code matrix | \<PASS / FAIL / N/A\> | |
| SITC-011 | Docker container integration | \<PASS / FAIL / N/A\> | |
| SITC-012 | pip install integration | \<PASS / FAIL / N/A\> | |
| SITC-013 | GitHub Actions annotation mode | \<PASS / FAIL / N/A\> | |
| SITC-014 | `--warnings-as-errors` promotion | \<PASS / FAIL / N/A\> | |

**Overall Result:** \<PASS / FAIL\>

> **📋 Note:** All SITC test cases must achieve PASS status before the system verification (SYS.5) activities commence. Any FAIL result must be tracked as a GitHub Issue and resolved via the change control process (SUP.10).

---

## 6. Traceability Matrix

| SITC-ID | SYS REQ-ID | Architecture Interface | SWE.5 Component Test |
|---|---|---|---|
| SITC-001 | SYS-F-001, SYS-F-027, SYS-F-037 | IF-01, IF-02, IF-04, IF-06, IF-08, IF-09 | \<SWE5-TC-001\> |
| SITC-002 | SYS-F-027, SYS-F-038 | IF-06, IF-08, IF-09 | \<SWE5-TC-002\> |
| SITC-003 | SYS-F-003, SYS-NF-008 | IF-01 | \<SWE5-TC-003\> |
| SITC-004 | SYS-F-028 | IF-08, IF-09 | \<SWE5-TC-004\> |
| SITC-005 | SYS-F-029 | IF-08, IF-09 | \<SWE5-TC-005\> |
| SITC-006 | SYS-F-031 | IF-09 | \<SWE5-TC-006\> |
| SITC-007 | SYS-F-034, SYS-F-035, SYS-F-036 | IF-10, IF-08, IF-09 | \<SWE5-TC-007\> |
| SITC-008 | SYS-F-021 | IF-07 | \<SWE5-TC-008\> |
| SITC-009 | SYS-F-008, SYS-NF-009 | IF-04, IF-08 | \<SWE5-TC-009\> |
| SITC-010 | SYS-F-037, SYS-F-038, SYS-F-039 | IF-09 | \<SWE5-TC-010\> |
| SITC-011 | SYS-NF-006 | All | \<SWE5-TC-011\> |
| SITC-012 | SYS-NF-005 | Entry point | \<SWE5-TC-012\> |
| SITC-013 | SYS-F-030 | IF-09 | \<SWE5-TC-013\> |
| SITC-014 | SYS-F-040 | IF-09 | \<SWE5-TC-014\> |

---

## 7. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | | 2026-04-12 |
| Technical Reviewer | \<Name\> | | |
| Quality Assurance | \<Name\> | | |
| Approver | \<Name\> | | |

> **⚠️ Important:** This document must be approved before integration testing commences. All test results must be recorded in this document or a linked test execution report and placed under configuration management (SUP.8).
