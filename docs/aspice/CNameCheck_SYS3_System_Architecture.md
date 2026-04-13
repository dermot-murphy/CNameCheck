# System Architecture Description

*Automotive SPICE® PAM v4.0 | SYS.3 System Architectural Design*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CNC-SYS3-001 | **Version** | 1.0 |
| **Project** | CStyleCheck | **Date** | 2026-04-12 |
| **Status** | Draft | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SYS.3 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose & Scope

### 3.1 Purpose

This System Architecture Description defines the top-level structural and behavioural design of **CStyleCheck v1.0.0**, decomposing the system into its major functional subsystems, defining their interfaces, and establishing the basis for software-level design. It satisfies **Automotive SPICE® PAM v4.0, SYS.3 — System Architectural Design**.

### 3.2 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| ASPICE PAM v4.0 | Automotive SPICE Process Assessment Model | 4.0 |
| CNC-SYS2-001 | CStyleCheck System Requirements Specification | 1.0 |
| CNC-SYS4-001 | CStyleCheck System Integration Test Specification | 1.0 |
| CNC-SUP8-001 | CStyleCheck Configuration Management Plan | 1.1 |

---

## 4. System Context

CStyleCheck is a software-only system with no hardware dependencies. It is deployed on a host execution environment (Linux, macOS, or Windows) with Python 3.10+ and PyYAML. External systems interact with CStyleCheck through three integration boundaries:

```
┌─────────────────────────────────────────────────────┐
│                 EXTERNAL ENVIRONMENT                 │
│                                                     │
│  ┌──────────────┐  ┌────────────────┐  ┌─────────┐  │
│  │  Developer   │  │  GitHub Actions│  │pre-commit│  │
│  │  CLI         │  │  Runner        │  │framework │  │
│  └──────┬───────┘  └───────┬────────┘  └────┬────┘  │
│         │                  │                │        │
└─────────┼──────────────────┼────────────────┼────────┘
          │  CLI invocation  │                │
          ▼                  ▼                ▼
┌─────────────────────────────────────────────────────┐
│                   CStyleCheck System                  │
│                                                     │
│   Inputs:  .c / .h files, naming_convention.yaml,   │
│            options, dictionaries, exclusions         │
│                                                     │
│   Outputs: violations (text/JSON/SARIF), exit code, │
│            log file, GitHub annotations, baseline   │
└─────────────────────────────────────────────────────┘
```

---

## 5. System Decomposition — Static View

CStyleCheck is decomposed into six functional subsystems, all implemented within the single `cnamecheck.py` module and its supporting configuration and data files.

### 5.1 Subsystem Overview

| Subsystem ID | Name | Responsibility | Primary CIs |
|---|---|---|---|
| SS-01 | CLI & Options Loader | Parse command-line arguments and options file; resolve file lists from globs | `cnamecheck.py` (main / argparse), `cnamecheck.options` |
| SS-02 | Configuration Loader | Load and validate `naming_convention.yaml`; merge project defines and aliases | `cnamecheck.py`, `naming_convention.yaml`, `aliases.txt`, `project.defines` |
| SS-03 | Dictionary Manager | Load keyword, stdlib, and spell-check dictionaries; support runtime override | `c_keywords.txt`, `c_stdlib_names.txt`, `c_spell_dict.txt` |
| SS-04 | Source Parser & Cache | Read each source file once; tokenise identifiers, extract scoped declarations; cache content for cross-file checks | `cnamecheck.py` |
| SS-05 | Rule Engine | Evaluate all enabled rules against each identifier; classify violations by severity; apply exclusions and baselines | `cnamecheck.py`, `exclusions.yml` |
| SS-06 | Output Formatter | Render violation results as plain text, JSON, or SARIF; emit GitHub annotations; write log file; print summary | `cnamecheck.py` |

### 5.2 Subsystem Interface Summary

| Interface ID | From | To | Data Exchanged | Direction |
|---|---|---|---|---|
| IF-01 | CLI & Options Loader | Configuration Loader | Resolved config file path, defines path, aliases path | → |
| IF-02 | CLI & Options Loader | Source Parser | Resolved list of source file paths (after glob expansion and exclusion) | → |
| IF-03 | CLI & Options Loader | Output Formatter | Output format, log path, flags (`--github-actions`, `--summary`, `--verbose`) | → |
| IF-04 | Configuration Loader | Rule Engine | Parsed rule configuration object (enabled flags, severities, thresholds) | → |
| IF-05 | Dictionary Manager | Rule Engine | Keyword set, stdlib name set, spell-check word set | → |
| IF-06 | Source Parser | Rule Engine | Per-file token stream with scope annotations and line/column metadata | → |
| IF-07 | Source Parser | Rule Engine | Cross-file sign-compatibility table | → |
| IF-08 | Rule Engine | Output Formatter | Ordered list of `Violation` objects (file, line, col, severity, rule\_id, message) | → |
| IF-09 | Output Formatter | External environment | Violation text to `stdout`; annotations to `stdout`; JSON/SARIF to `stdout`; log to file | → |
| IF-10 | CLI & Options Loader | Rule Engine | Baseline file path (suppress known violations) or write-baseline path | → |

---

## 6. Deployment Architecture

### 6.1 Deployment Modes

| Mode | Deployment Unit | Entry Point | Host Requirement |
|---|---|---|---|
| Direct Python | `src/cnamecheck.py` | `python cnamecheck.py` | Python 3.10+, PyYAML |
| pip/pipx install | Python package (`.whl`) | `cnamecheck` command | Python 3.10+, PyYAML |
| Docker container | `ghcr.io/<org>/cnamecheck` image | `docker run` | Docker runtime |
| GitHub Action | `action.yml` | GitHub Actions runner step | GitHub-hosted or self-hosted runner |
| pre-commit hook | `.pre-commit-hooks.yaml` | pre-commit framework | Python 3.10+, pre-commit |

### 6.2 Docker Image Structure

```
/app/
  cnamecheck.py          ← main linter (CI-001)
  _version.py            ← version string (CI-002)
  naming_convention.yaml ← default rule config (CI-003)
  cnamecheck.options     ← default options (CI-004)
  exclusions.yml         ← default exclusions (CI-005)
  project.defines        ← default defines (CI-006)
  aliases.txt            ← default aliases (CI-007)
  c_keywords.txt         ← C keyword dictionary (CI-008)
  c_stdlib_names.txt     ← stdlib name dictionary (CI-009)
  c_spell_dict.txt       ← spell-check dictionary (CI-010)

ENTRYPOINT: python /app/cnamecheck.py
```

User source files are mounted at runtime (e.g., `-v $(pwd):/repo`). All dictionary and configuration files can be overridden via CLI flags at container invocation.

---

## 7. Dynamic Behaviour — Processing Flow

### 7.1 Normal Execution Sequence

```
1. main()
   │
   ├─ SS-01: parse_args()
   │   ├─ Load --options-file (if specified) → merge with CLI args
   │   ├─ Expand --include globs, apply --exclude filters
   │   └─ Resolve all file paths → [file_list]
   │
   ├─ SS-02: load_config()
   │   ├─ Parse naming_convention.yaml
   │   ├─ Apply --defines substitutions
   │   └─ Apply --aliases module map → config_object
   │
   ├─ SS-03: load_dictionaries()
   │   ├─ Load c_keywords.txt (or --keywords-file override)
   │   ├─ Load c_stdlib_names.txt (or --stdlib-file override)
   │   └─ Load c_spell_dict.txt (or --spell-dict override) → dict_sets
   │
   ├─ SS-04: parse_sources()  [for each file in file_list]
   │   ├─ Read file (once; cached for cross-file checks)
   │   ├─ Tokenise: extract identifiers with scope, line, col
   │   └─ Build cross-file sign-compatibility table
   │
   ├─ SS-05: run_rules()  [for each identifier token]
   │   ├─ Apply all enabled rules from config_object
   │   ├─ Apply --exclusions per-file suppressions
   │   ├─ Apply --baseline-file suppression (if specified)
   │   └─ Collect Violation objects → [violations]
   │
   └─ SS-06: format_output()
       ├─ Render violations in requested format (text/JSON/SARIF)
       ├─ Emit GitHub Actions annotations (if --github-actions)
       ├─ Write --log file (if specified)
       ├─ Print --summary table (if requested)
       └─ Return exit code (0 / 1 / 2)
```

### 7.2 Baseline Write Sequence

When `--write-baseline FILE` is specified:

1. Steps 1–5 execute as normal
2. All violations (regardless of severity) are serialised to JSON and written to `FILE`
3. System exits with code `0`

### 7.3 Error / Configuration Failure Sequence

If any configuration or invocation error is detected during steps 1 or 2:

1. A human-readable error message is emitted to `stderr`
2. System exits with code `2` immediately

---

## 8. Architecture Decisions

| Decision ID | Decision | Rationale | Alternative Considered |
|---|---|---|---|
| AD-001 | Single Python file (`cnamecheck.py`) with no third-party runtime dependencies beyond PyYAML | Maximises portability; trivially usable as a pre-commit hook and GitHub Action without packaging setup | Multi-module package — rejected: adds packaging complexity for minimal benefit at this scale |
| AD-002 | YAML for rule configuration | Human-readable, widely used in CI/CD toolchains, native Python support via PyYAML | JSON / TOML — rejected: JSON too verbose; TOML less familiar to embedded teams |
| AD-003 | Source-cache architecture (read each file once) | Eliminates duplicate I/O; required for cross-file sign-compatibility check to share the same parsed content | Re-read files per check pass — rejected: doubles I/O on large repos |
| AD-004 | Three output formats (text, JSON, SARIF) | Supports human review (text), downstream automation (JSON), and GitHub Code Scanning integration (SARIF) | Single format — rejected: insufficient for CI/CD integration requirements |
| AD-005 | Baseline suppression via JSON file in VCS | Allows incremental adoption on legacy codebases; baseline diff is human-readable and reviewable | Suppress-by-line-number — rejected: too fragile to refactoring |
| AD-006 | Module prefix derived from filename stem | Consistent, automatic, requires no additional configuration per file | Explicit prefix in config — rejected: high maintenance burden on multi-file projects |

---

## 9. Traceability: System Requirements → Architecture Elements

| SYS REQ-ID | Requirement Summary | Subsystem(s) |
|---|---|---|
| SYS-F-001 to SYS-F-010 | Input handling | SS-01 (CLI & Options Loader) |
| SYS-F-011 to SYS-F-026 | Rule checking (all 48 rule IDs) | SS-05 (Rule Engine), SS-03 (Dictionary Manager) |
| SYS-F-027 to SYS-F-033 | Output formats and reporting | SS-06 (Output Formatter) |
| SYS-F-034 to SYS-F-036 | Baseline suppression | SS-01 (flags), SS-05 (filter), SS-06 (write) |
| SYS-F-037 to SYS-F-040 | Exit codes | SS-06 (exit code return) |
| SYS-NF-001 | Single file read per invocation | SS-04 (source cache) |
| SYS-NF-002 | Analysis performance | SS-04, SS-05 (cache architecture, AD-003) |
| SYS-NF-003 to SYS-NF-004 | Python 3.10–3.12, stdlib only | All subsystems |
| SYS-NF-005 | pip/pipx installable | `pyproject.toml`, packaging (CI-013) |
| SYS-NF-006 | Multi-platform Docker | `Dockerfile` (CI-011), `docker_publish.yml` (CI-025) |
| SYS-NF-007 to SYS-NF-009 | Configurability | SS-02 (Configuration Loader) |
| SYS-NF-010 | pre-commit integration | `.pre-commit-hooks.yaml` (CI-015) |
| SYS-NF-011 to SYS-NF-012 | GitHub Action integration | `action.yml` (CI-016) |

---

## 10. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | | 2026-04-12 |
| Technical Reviewer | \<Name\> | | |
| Quality Assurance | \<Name\> | | |
| Approver | \<Name\> | | |

> **⚠️ Important:** This document must be placed under configuration management (SUP.8) upon approval. Any post-approval changes require a change request (SUP.10) and a new document version.
