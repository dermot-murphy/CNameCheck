# System Architecture Description

*Automotive SPICE® PAM v4.0 | SYS.3 System Architectural Design*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CSC-SYS3-001 | **Version** | 1.5 |
| **Project** | CStyleCheck | **Date** | 2026-06-18 |
| **Status** | Released | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SYS.3 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.5 | 2026-06-18 | Claude | ASPICE audit #254 — sync referenced-document version citations to current versions |
| 1.4 | 2026-06-05 | Claude | CSC-AUD-005 corrective action — fix factual errors identified in audit |
| 1.3 | 2026-06-04 | Claude | Deep accuracy audit: fix §3.1 version text, update §3.2 referenced doc versions — resolves issue #163 |
| 1.2 | 2026-05-28 | Claude | Update §5/§6/§8 to reflect package refactor (issue #144): replace single `cstylecheck.py` references with package sub-modules — closes issue #146 |
| 1.1 | 2026-05-28 | Claude | Reviewed and updated for v1.1.0 release; revision history maintained per ASPICE GP 2.2.4 |
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose & Scope

### 3.1 Purpose

This System Architecture Description defines the top-level structural and behavioural design of **CStyleCheck v1.2.x**, decomposing the system into its major functional subsystems, defining their interfaces, and establishing the basis for software-level design. It satisfies **Automotive SPICE® PAM v4.0, SYS.3 — System Architectural Design**.

### 3.2 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| ASPICE PAM v4.0 | Automotive SPICE Process Assessment Model | 4.0 |
| CSC-SYS2-001 | CStyleCheck System Requirements Specification | 1.6 |
| CSC-SYS4-001 | CStyleCheck System Integration Test Specification | 1.4 |
| CSC-SUP8-001 | CStyleCheck Configuration Management Plan | 1.7 |

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
│   Inputs:  .c / .h files, rules.yml,   │
│            options, dictionaries, exclusions                     │
│                                                     │
│   Outputs: violations (text/JSON/SARIF), exit code, │
│            log file, GitHub annotations, baseline   │
└─────────────────────────────────────────────────────┘
```

---

## 5. System Decomposition — Static View

CStyleCheck is decomposed into six functional subsystems, all implemented within the `src/cstylecheck/` Python package (12 sub-modules) and its supporting configuration and data files.

### 5.1 Subsystem Overview

| Subsystem ID | Name | Responsibility | Primary CIs |
|---|---|---|---|
| SS-01 | CLI & Options Loader | Parse command-line arguments and options file; resolve file lists from globs | `cli.py`, `config.py` (_read_options_file, _expand_options_file), `options.txt` |
| SS-02 | Configuration Loader | Load and validate `rules.yml`; merge project defines and aliases | `config.py`, `rules.yml`, `aliases.txt`, `defines.txt` |
| SS-03 | Dictionary Manager | Load keyword, stdlib, and spell-check dictionaries; support runtime override | `c_keywords.txt`, `c_stdlib_names.txt`, `c_spell_dict.txt` |
| SS-04 | Source Parser & Cache | Read each source file once; tokenise identifiers, extract scoped declarations; cache content for cross-file checks | `preprocessor.py` |
| SS-05 | Rule Engine | Evaluate all enabled rules against each identifier; classify violations by severity; apply exclusions and baselines | `checker.py`, `sign_checker.py`, `exclusions.yml` |
| SS-06 | Output Formatter | Render violation results as plain text, JSON, or SARIF; emit GitHub annotations; write log file; print summary | `output.py`, `baseline.py` |
| SS-07 | Auto-fix Engine | Apply safe mechanical in-place fixes (`--fix`); show unified diff without writing (`--dry-run`); restrict to zero-risk fixes (`--safe-only`) | `fixer.py` — `apply_fixes`, `unified_diff` |
| SS-08 | Config Wizard | Interactive Q&A config generation (`--init`); pre-built preset config generation (`--preset`) without running wizard | `wizard.py` — `run_wizard`, `run_preset` |
| SS-09 | Per-directory Config | Walk upward from each source file's directory; deep-merge found `.cstylecheck.yml` on top of root config; nearest config wins; `root: true` stops search; cache per directory | `config.py` — `resolve_per_dir_config` |

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
| Direct Python | `src/cstylecheck.py` | `python cstylecheck.py` | Python 3.10+, PyYAML |
| pip/pipx install | Python package (`.whl`) | `cstylecheck` command | Python 3.10+, PyYAML |
| Docker container | `ghcr.io/<org>/cstylecheck` image | `docker run` | Docker runtime |
| GitHub Action | `action.yml` | GitHub Actions runner step | GitHub-hosted or self-hosted runner |
| pre-commit hook | `.pre-commit-hooks.yml` | pre-commit framework | Python 3.10+, pre-commit |

### 6.2 Docker Image Structure

```
/app/
  cstylecheck/            ← main linter package (CI-001)
  _version.py            ← version string (CI-002)
  rules.yml ← default rule config (CI-003)
  options.txt     ← default options (CI-004)
  exclusions.yml         <- default exclusions (CI-005)
  defines.txt        ← default defines (CI-006)
  aliases.txt            ← default aliases (CI-007)
  c_keywords.txt         ← C keyword dictionary (CI-008)
  c_stdlib_names.txt     ← stdlib name dictionary (CI-009)
  c_spell_dict.txt       ← spell-check dictionary (CI-010)

ENTRYPOINT: python /app/cstylecheck.py
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
   │   ├─ Parse rules.yml
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
| AD-001 | Python package (`src/cstylecheck/`, 12 sub-modules) with no third-party runtime dependencies beyond PyYAML | Maximises maintainability; package refactor (issue #144) splits the original monolithic file into logical modules while preserving full backward compatibility via `__init__.py` re-exports | Single monolithic file — was v1.0/v1.1 approach; refactored in v1.2 to aid readability and navigation |
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
| SYS-F-011 to SYS-F-026 | Rule checking (all 53 rule IDs) | SS-05 (Rule Engine), SS-03 (Dictionary Manager) |
| SYS-F-027 to SYS-F-033 | Output formats and reporting | SS-06 (Output Formatter) |
| SYS-F-034 to SYS-F-036 | Baseline suppression | SS-01 (flags), SS-05 (filter), SS-06 (write) |
| SYS-F-037 to SYS-F-040 | Exit codes | SS-06 (exit code return) |
| SYS-NF-001 | Single file read per invocation | SS-04 (source cache) |
| SYS-NF-002 | Analysis performance | SS-04, SS-05 (cache architecture, AD-003) |
| SYS-NF-003 to SYS-NF-004 | Python 3.10–3.12, stdlib only | All subsystems |
| SYS-NF-005 | pip/pipx installable | `pyproject.toml`, packaging (CI-013) |
| SYS-NF-006 | Multi-platform Docker | `Dockerfile` (CI-011), `docker_publish.yml` (CI-025) |
| SYS-NF-007 to SYS-NF-009 | Configurability | SS-02 (Configuration Loader) |
| SYS-NF-010 | pre-commit integration | `.pre-commit-hooks.yml` (CI-015) |
| SYS-NF-011 to SYS-NF-012 | GitHub Action integration | `action.yml` (CI-016) |
| SYS-F-041 | Inline suppression comment directives | SS-01 (Preprocessor/Source Parser — `parse_inline_suppressions`) |
| SYS-F-042 | Auto-fix mode (`--fix`, `--dry-run`, `--safe-only`) | SS-07 (Auto-fix Engine) |
| SYS-F-043 | Config wizard (`--init`) and preset generation (`--preset`) | SS-08 (Config Wizard) |
| SYS-F-044 | Per-directory config override resolution (`--per-dir-config`) | SS-09 (Per-directory Config) |
| SYS-F-045 | HTML report output (`--output-format html`) | SS-06 (Output Formatter) |

---

## 10. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | Approved | 2026-04-15 |
| Technical Reviewer | Dermot Murphy | Approved | 2026-04-15 |
| Quality Assurance | Dermot Murphy | Approved | 2026-04-15 |
| Approver | Dermot Murphy | Approved | 2026-04-15 |

> **Note:** This document is under configuration management (SUP.8). Post-approval changes require a change request (SUP.10) and a new document version.
