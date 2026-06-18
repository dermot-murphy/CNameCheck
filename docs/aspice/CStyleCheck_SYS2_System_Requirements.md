# System Requirements Specification

*Automotive SPICE® PAM v4.0 | SYS.2 System Requirements Analysis*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CSC-SYS2-001 | **Version** | 1.6 |
| **Project** | CStyleCheck | **Date** | 2026-06-18 |
| **Status** | Released | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SYS.2 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.6 | 2026-06-18 | Claude | ASPICE audit #254 — sync referenced-document version citations to current versions |
| 1.5 | 2026-06-04 | Claude | Add SYS-F-041 to SYS-F-045 for five new features (inline suppression, --fix, --init/--preset, per-dir config, HTML output); update §6 RTM — issues #188 #189 #190 #193 #192 |
| 1.4 | 2026-06-04 | Claude | Deep accuracy audit: fix §3.2 "three modes" text (listed 4 modes), update §3.3 referenced doc versions — resolves issue #163 |
| 1.3 | 2026-06-04 | Claude | Automated accuracy audit: fix §3.1 and SYS-F-011 rule count 48→53; update referenced doc versions — resolves issue #163 |
| 1.2 | 2026-05-28 | Dermot Murphy | §5.9: formally defer NF-010 and NF-012 to v2.0; classify NF-011 as Out of Scope v1.x — closes issue #153 |
| 1.1 | 2026-05-28 | Claude | Reviewed and updated for v1.1.0 release; revision history maintained per ASPICE GP 2.2.4 |
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose & Scope

### 3.1 Purpose

This System Requirements Specification (SRS) defines the complete, structured set of system-level requirements for **CStyleCheck v1.2.x** — an embedded C naming-convention linter implementing Barr-C:2018 and MISRA-C complementary rules across 53 rule IDs.

This document satisfies the requirements of **Automotive SPICE® PAM v4.0, SYS.2 — System Requirements Analysis**.

### 3.2 Scope

CStyleCheck is a software-only system. It operates as a static analysis tool that accepts C source files and a rule-configuration file as inputs, evaluates each identifier in those files against the configured naming rules, and produces a structured violation report as output.

The system is deployed in four integration modes:

1. **Command-line tool** — invoked directly via Python or as a pip-installed entry point
2. **GitHub Action** — integrated into GitHub Actions CI workflows via `action.yml`
3. **pre-commit hook** — integrated into pre-commit framework via `.pre-commit-hooks.yml`
4. **Docker container** — packaged as a portable, self-contained image for CI/CD pipelines

### 3.3 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| ASPICE PAM v4.0 | Automotive SPICE Process Assessment Model | 4.0 |
| Barr-C:2018 | Barr Group Embedded C Coding Standard | 2018 |
| CSC-SUP8-001 | CStyleCheck Configuration Management Plan | 1.7 |
| CSC-SYS3-001 | CStyleCheck System Architecture Description | 1.5 |

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
| SYS-F-011 | The system shall enforce naming rules across 53 rule IDs covering: constants/macros, variables (by scope), functions, types (typedef/enum/struct), include guards, and miscellaneous rules | Mandatory | Test | STK-001, STK-002 |
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

### 5.8a Functional Requirements — New Features (v1.3.x)

| REQ-ID | Requirement | Priority | Verification Method | Derived From |
|---|---|---|---|---|
| SYS-F-041 | The system shall support inline suppression comments in C source using `// cstylecheck: disable=rule.id` (same-line), `// cstylecheck: disable-next-line=rule.id` (next line), and paired `disable=`/`enable=` block directives; directives shall be case-insensitive and support comma-separated rule ID lists | Mandatory | Test | STK-002 |
| SYS-F-042 | The system shall apply safe mechanical fixes in-place when `--fix` is specified; `--dry-run` shall show a unified diff without modifying files; `--safe-only` shall restrict to zero-risk fixes; fixable rules shall include at minimum `misc.unsigned_suffix` and `misc.lowercase_l_suffix` | Mandatory | Test | STK-001 |
| SYS-F-043 | The system shall provide an interactive configuration wizard (`--init`) that generates `.cstylecheck.yml` through a Q&A session; `--preset barr-c\|minimal\|misra` shall write a pre-built config without wizard interaction; `--init-output FILE` shall set the output path; `--overwrite` shall allow replacing an existing config file | Mandatory | Test | STK-002 |
| SYS-F-044 | The system shall support per-directory configuration overrides when `--per-dir-config` is specified; the system shall walk upward from each source file's directory, deep-merging any `.cstylecheck.yml` found along the path; the nearest config wins; a `root: true` entry shall stop the upward search; per-directory resolution results shall be cached | Mandatory | Test | STK-002 |
| SYS-F-045 | The system shall produce a self-contained HTML report when `--output-format html` is specified; the report shall include inline CSS, summary cards (errors/warnings/info/total/files checked), and per-file violation tables; the HTML shall be written to `--log FILE` if provided, otherwise to stdout | Mandatory | Test | STK-007 |

### 5.9 Non-Functional Requirements — Integration

| REQ-ID | Requirement | Priority | Verification Method | Derived From | Disposition |
|---|---|---|---|---|---|
| SYS-NF-010 | The system shall integrate with the pre-commit framework via `.pre-commit-hooks.yml` | Mandatory | Test | STK-001 | **Deferred — v2.0 milestone.** `.pre-commit-hooks.yml` exists; automated system-level test not yet scheduled. |
| SYS-NF-011 | The system shall integrate with GitHub Actions via `action.yml` at the repository root | Out of Scope v1.x | — | STK-005 | **Out of Scope v1.x.** Publishing to GitHub Marketplace is not a linter tool goal; `action.yml` is maintained for manual use only. |
| SYS-NF-012 | The GitHub Action shall expose violation counts (`errors`, `warnings`, `info`, `violations`) as step outputs | Mandatory | Test | STK-005 | **Deferred — v2.0 milestone.** Step output variables not yet implemented and verified at system level. |

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
| SYS-NF-010 | Integration (pre-commit) | STK-001 | `.pre-commit-hooks.yml` | Deferred v2.0 |
| SYS-NF-011 | Integration (GitHub Marketplace) | STK-005 | `action.yml` | Out of Scope v1.x |
| SYS-NF-012 | Integration (step outputs) | STK-005 | `action.yml` | Deferred v2.0 |
| SYS-F-041 | Inline suppression | STK-002 | `preprocessor.parse_inline_suppressions()` | SWE1-072, SWE1-073 |
| SYS-F-042 | Auto-fix mode | STK-001 | `fixer.py` Fixer module | SWE1-074 |
| SYS-F-043 | Config wizard and presets | STK-002 | `wizard.py` Wizard module | SWE1-075 |
| SYS-F-044 | Per-directory config | STK-002 | `config.resolve_per_dir_config()` | SWE1-076 |
| SYS-F-045 | HTML report output | STK-007 | `output._violations_to_html()` | SWE1-077 |

---

## 7. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | Approved | 2026-04-15 |
| Technical Reviewer | Dermot Murphy | Approved | 2026-04-15 |
| Quality Assurance | Dermot Murphy | Approved | 2026-04-15 |
| Approver | Dermot Murphy | Approved | 2026-04-15 |

> **Note:** This document is under configuration management (SUP.8). Post-approval changes require a change request (SUP.10) and a new document version.
