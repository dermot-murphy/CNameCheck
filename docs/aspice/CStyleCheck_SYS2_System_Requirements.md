# System Requirements Specification

*Automotive SPICE® PAM v4.0 | SYS.2 System Requirements Analysis*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CSC-SYS2-001 | **Version** | 1.0 |
| **Project** | CStyleCheck | **Date** | 2026-04-12 |
| **Status** | Released | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SYS.2 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose & Scope

### 3.1 Purpose

This System Requirements Specification (SRS) defines the complete, structured set of system-level requirements for **CStyleCheck v1.0.0** — an embedded C naming-convention linter implementing Barr-C:2018 and MISRA-C complementary rules across 48 rule IDs.

This document satisfies the requirements of **Automotive SPICE® PAM v4.0, SYS.2 — System Requirements Analysis**.

### 3.2 Scope

CStyleCheck is a software-only system. It operates as a static analysis tool that accepts C source files and a rule-configuration file as inputs, evaluates each identifier in those files against the configured naming rules, and produces a structured violation report as output.

The system is deployed in three integration modes:

1. **Command-line tool** — invoked directly via Python or as a pip-installed entry point
2. **GitHub Action** — integrated into GitHub Actions CI workflows via `action.yml`
3. **pre-commit hook** — integrated into pre-commit framework via `.pre-commit-hooks.yml`
4. **Docker container** — packaged as a portable, self-contained image for CI/CD pipelines

### 3.3 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| ASPICE PAM v4.0 | Automotive SPICE Process Assessment Model | 4.0 |
| Barr-C:2018 | Barr Group Embedded C Coding Standard | 2018 |
| CSC-SUP8-001 | CStyleCheck Configuration Management Plan | 1.1 |
| CSC-SYS3-001 | CStyleCheck System Architecture Description | 1.0 |

### 3.4 Glossary

| Term | Definition |
|---|---|
| CI | Configuration Item or Continuous Integration (context-dependent) |
| Identifier | Any named entity in C source: variable, function, type, macro, enum, struct tag |
| Rule ID | A dot-separated string identifying a specific naming rule (e.g., `variable.global.case`) |
| Severity | Classification of a violation: `error`, `warning`, or `info` |
| Module prefix | The filename stem of the source file used as a mandatory identifier prefix |
| Baseline | A saved JSON file of known violations used to suppress pre-existing findings |
| SARIF | Static Analysis Results Interchange Format (v2.1.0) |

---

## 4. Stakeholder Requirements Summary

The following table summarises the stakeholder needs from which the system requirements are derived.

| STK-ID | Stakeholder | Need |
|---|---|---|
| STK-001 | Embedded C developer | Enforce consistent naming conventions without manual review effort |
| STK-002 | Project lead / tech lead | Configure and enforce project-specific naming rules across the team |
| STK-003 | CI/CD pipeline operator | Run the linter automatically on every commit/PR with machine-readable output |
| STK-004 | Legacy codebase maintainer | Adopt the linter incrementally without being blocked by pre-existing violations |
| STK-005 | GitHub Actions user | Receive inline PR annotations for naming violations without additional tooling |
| STK-006 | Docker/container user | Run the linter in a containerised environment without local Python setup |
| STK-007 | Quality assurance engineer | Obtain a structured, auditable violation report for process evidence |

---

## 5. System Requirements

### 5.1 Functional Requirements — Input Handling

| REQ-ID | Requirement | Priority | Verification Method | Derived From |
|---|---|---|---|---|
| SYS-F-001 | The system shall accept one or more C source files (`.c` and `.h`) as positional arguments | Mandatory | Test | STK-001 |
| SYS-F-002 | The system shall accept a YAML rule-configuration file via `--config` | Mandatory | Test | STK-002 |
| SYS-F-003 | The system shall accept an options file via `--options-file` that specifies CLI arguments one per line, with `#` as a comment character | Mandatory | Test | STK-002 |
| SYS-F-004 | The system shall accept glob patterns for source inclusion via `--include` (repeatable) | Mandatory | Test | STK-002 |
| SYS-F-005 | The system shall accept glob patterns for source exclusion via `--exclude` (repeatable) | Mandatory | Test | STK-002 |
| SYS-F-006 | The system shall accept a project defines file via `--defines` for keyword/type alias substitution | Mandatory | Test | STK-002 |
| SYS-F-007 | The system shall accept a module alias map via `--aliases` | Mandatory | Test | STK-002 |
| SYS-F-008 | The system shall accept a per-file rule suppression file via `--exclusions` | Mandatory | Test | STK-002 |
| SYS-F-009 | The system shall accept replacement dictionary files for C keywords (`--keywords-file`), stdlib names (`--stdlib-file`), and spell-check words (`--spell-dict`) | Mandatory | Test | STK-002 |
| SYS-F-010 | The system shall read each source file exactly once per invocation | Mandatory | Test | STK-001 |

### 5.2 Functional Requirements — Rule Checking

| REQ-ID | Requirement | Priority | Verification Method | Derived From |
|---|---|---|---|---|
| SYS-F-011 | The system shall enforce naming rules across 48 rule IDs covering: constants/macros, variables (by scope), functions, types (typedef/enum/struct), include guards, and miscellaneous rules | Mandatory | Test | STK-001, STK-002 |
| SYS-F-012 | The system shall enforce module-prefix requirements on global variables, file-scope static variables, public functions, macros, and constants | Mandatory | Test | STK-001 |
| SYS-F-013 | The system shall enforce scope-aware variable rules: global (`g_` prefix), file-static (`s_` prefix), local, and parameter — each independently configurable | Mandatory | Test | STK-001 |
| SYS-F-014 | The system shall enforce pointer-prefix rules: single pointer (`p_`), double pointer (`pp_`), boolean (`b_`), and handle variables (`h_`) | Mandatory | Test | STK-001 |
| SYS-F-015 | The system shall enforce function naming style: object\_verb, verb\_object, or lower\_snake, as configured | Mandatory | Test | STK-001 |
| SYS-F-016 | The system shall enforce static function prefix (e.g., `prv_`) when enabled | Mandatory | Test | STK-001 |
| SYS-F-017 | The system shall enforce min-length and max-length constraints on variable, function, constant, and macro identifiers | Mandatory | Test | STK-001 |
| SYS-F-018 | The system shall enforce case rules (`lower_snake`, `UPPER_SNAKE`, `UpperCamelCase`) per identifier category | Mandatory | Test | STK-001 |
| SYS-F-019 | The system shall enforce include guard presence and format rules | Mandatory | Test | STK-001 |
| SYS-F-020 | The system shall enforce miscellaneous rules: line length, indentation, magic number detection, unsigned integer suffix (`U`/`UL`), yoda conditions, and block comment spacing | Mandatory | Test | STK-001 |
| SYS-F-021 | The system shall perform cross-file sign-compatibility checking between related `.c` and `.h` files | Mandatory | Test | STK-001 |
| SYS-F-022 | The system shall perform spell-checking on identifier tokens against a configurable dictionary | Mandatory | Test | STK-001 |
| SYS-F-023 | The system shall detect reserved C/C++ keyword and stdlib name usage as identifiers | Mandatory | Test | STK-001 |
| SYS-F-024 | The system shall support configurable allowed abbreviations (e.g., `FIFO`, `CRC`, `ADC`) that are exempt from case-rule enforcement within otherwise conforming names | Mandatory | Test | STK-002 |
| SYS-F-025 | Each rule shall be independently toggleable via the `enabled` field in the YAML configuration | Mandatory | Test | STK-002 |
| SYS-F-026 | Each rule shall support an independently configurable severity level (`error`, `warning`, `info`) | Mandatory | Test | STK-002 |

### 5.3 Functional Requirements — Output

| REQ-ID | Requirement | Priority | Verification Method | Derived From |
|---|---|---|---|---|
| SYS-F-027 | The system shall produce a plain-text violation report to `stdout` by default, including file path, line number, column number, severity, rule ID, and human-readable message for each violation | Mandatory | Test | STK-001 |
| SYS-F-028 | The system shall produce a structured JSON report when `--output-format json` is specified, conforming to the defined JSON schema | Mandatory | Test | STK-003 |
| SYS-F-029 | The system shall produce a SARIF 2.1.0 report when `--output-format sarif` is specified | Mandatory | Test | STK-005 |
| SYS-F-030 | The system shall emit GitHub Actions `::error` and `::warning` annotations when `--github-actions` is specified | Mandatory | Test | STK-005 |
| SYS-F-031 | The system shall write output to a log file when `--log FILE` is specified, in addition to `stdout` | Mandatory | Test | STK-003, STK-007 |
| SYS-F-032 | The system shall print a violation summary table (files checked, errors, warnings, info, total) when `--summary` is specified | Mandatory | Test | STK-007 |
| SYS-F-033 | The system shall print verbose directory-progress information to `stderr` when `--verbose` is specified, updating in place | Mandatory | Test | STK-001 |

### 5.4 Functional Requirements — Baseline Suppression

| REQ-ID | Requirement | Priority | Verification Method | Derived From |
|---|---|---|---|---|
| SYS-F-034 | The system shall write all current violations to a JSON baseline file and exit 0 when `--write-baseline FILE` is specified | Mandatory | Test | STK-004 |
| SYS-F-035 | The system shall suppress violations present in the baseline file when `--baseline-file FILE` is specified, reporting only newly introduced violations | Mandatory | Test | STK-004 |
| SYS-F-036 | The baseline file shall be plain JSON, human-readable, and diffable in version control | Mandatory | Inspection | STK-004 |

### 5.5 Functional Requirements — Exit Codes

| REQ-ID | Requirement | Priority | Verification Method | Derived From |
|---|---|---|---|---|
| SYS-F-037 | The system shall exit with code `0` when no errors are found, or when invoked with `--version`, `--help`, `--exit-zero`, or `--write-baseline` | Mandatory | Test | STK-003 |
| SYS-F-038 | The system shall exit with code `1` when one or more error-level violations are found | Mandatory | Test | STK-003 |
| SYS-F-039 | The system shall exit with code `2` when a configuration or invocation error occurs | Mandatory | Test | STK-003 |
| SYS-F-040 | The system shall promote all warnings and info-level violations to errors when `--warnings-as-errors` is specified | Mandatory | Test | STK-002 |

### 5.6 Non-Functional Requirements — Performance

| REQ-ID | Requirement | Priority | Verification Method | Derived From |
|---|---|---|---|---|
| SYS-NF-001 | The system shall read each source file at most once per invocation (source cache requirement) | Mandatory | Inspection / Test | STK-003 |
| SYS-NF-002 | The system shall complete analysis of a 100-file, 10,000-line C project within 30 seconds on a standard CI runner | Desired | Test | STK-003 |

### 5.7 Non-Functional Requirements — Portability

| REQ-ID | Requirement | Priority | Verification Method | Derived From |
|---|---|---|---|---|
| SYS-NF-003 | The system shall run on Python 3.10, 3.11, and 3.12 | Mandatory | Test (CI matrix) | STK-001, STK-003 |
| SYS-NF-004 | The system shall use Python standard library only — no third-party runtime dependencies beyond PyYAML | Mandatory | Inspection | STK-001 |
| SYS-NF-005 | The system shall be installable via `pip install .` and `pipx install .` | Mandatory | Test | STK-001 |
| SYS-NF-006 | The Docker image shall support `linux/amd64` and `linux/arm64` platforms | Mandatory | Test (CI build) | STK-006 |

### 5.8 Non-Functional Requirements — Configurability

| REQ-ID | Requirement | Priority | Verification Method | Derived From |
|---|---|---|---|---|
| SYS-NF-007 | All rules shall be configurable via a single YAML file without modifying source code | Mandatory | Inspection | STK-002 |
| SYS-NF-008 | The system shall apply CLI arguments specified in `--options-file` before direct CLI arguments, allowing direct arguments to override | Mandatory | Test | STK-002 |
| SYS-NF-009 | The system shall support per-file rule suppression via a YAML exclusions file | Mandatory | Test | STK-002 |

### 5.9 Non-Functional Requirements — Integration

| REQ-ID | Requirement | Priority | Verification Method | Derived From |
|---|---|---|---|---|
| SYS-NF-010 | The system shall integrate with the pre-commit framework via `.pre-commit-hooks.yml` | Mandatory | Test | STK-001 |
| SYS-NF-011 | The system shall integrate with GitHub Actions via `action.yml` at the repository root | Mandatory | Test | STK-005 |
| SYS-NF-012 | The GitHub Action shall expose violation counts (`errors`, `warnings`, `info`, `violations`) as step outputs | Mandatory | Test | STK-005 |

---

## 6. Requirements Traceability Matrix

| REQ-ID | Category | Stakeholder Need | SYS.3 Architecture Element | SWE.1 SW Requirement |
|---|---|---|---|---|
| SYS-F-001 to SYS-F-010 | Input handling | STK-001, STK-002 | Input parser subsystem | \<SWE.1-REQ-001 to 010\> |
| SYS-F-011 to SYS-F-026 | Rule engine | STK-001, STK-002 | Rule engine subsystem | \<SWE.1-REQ-011 to 026\> |
| SYS-F-027 to SYS-F-033 | Output / reporting | STK-003, STK-005, STK-007 | Output formatter subsystem | \<SWE.1-REQ-027 to 033\> |
| SYS-F-034 to SYS-F-036 | Baseline suppression | STK-004 | Baseline manager subsystem | \<SWE.1-REQ-034 to 036\> |
| SYS-F-037 to SYS-F-040 | Exit codes | STK-003 | Main orchestrator | \<SWE.1-REQ-037 to 040\> |
| SYS-NF-001 to SYS-NF-002 | Performance | STK-003 | Source cache | \<SWE.1-REQ-041 to 042\> |
| SYS-NF-003 to SYS-NF-006 | Portability | STK-001, STK-006 | Build / packaging | \<SWE.1-REQ-043 to 046\> |
| SYS-NF-007 to SYS-NF-009 | Configurability | STK-002 | Configuration loader | \<SWE.1-REQ-047 to 049\> |
| SYS-NF-010 to SYS-NF-012 | Integration | STK-005 | Integration layer | \<SWE.1-REQ-050 to 052\> |

---

## 7. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | Approved | 2026-04-15 |
| Technical Reviewer | Dermot Murphy | Approved | 2026-04-15 |
| Quality Assurance | Dermot Murphy | Approved | 2026-04-15 |
| Approver | Dermot Murphy | Approved | 2026-04-15 |

> **Note:** This document is under configuration management (SUP.8). Post-approval changes require a change request (SUP.10) and a new document version.
