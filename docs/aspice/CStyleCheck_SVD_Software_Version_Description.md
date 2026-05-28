# Software Version Description

*Automotive SPICE® PAM v4.0 | SUP.8 Configuration Management — Release Artefact*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CSC-SVD-001 | **Version** | 1.1 |
| **Project** | CStyleCheck | **Date** | 2026-05-28 |
| **Status** | Released | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SUP.8 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.1 | 2026-05-28 | Claude | Initial SVD document created for v1.1.0 release |

---

## 3. Purpose & Scope

This **Software Version Description (SVD)** formally describes the **CStyleCheck v1.1.0** software release. It identifies the software items delivered, the baseline against which changes are recorded, and the configuration status of all controlled work products.

This document satisfies the release-identification and configuration-status-accounting requirements of **Automotive SPICE® PAM v4.0, SUP.8 — Configuration Management**.

### 3.1 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CSC-SWE1-001 | CStyleCheck Software Requirements Specification | 1.1 |
| CSC-SWE2-001 | CStyleCheck Software Architecture Design | 1.1 |
| CSC-SWE3-001 | CStyleCheck Software Detailed Design | 1.1 |
| CSC-SWE4-001 | CStyleCheck Software Unit Verification Specification | 1.1 |
| CSC-SWE5-001 | CStyleCheck Software Integration Test Specification | 1.1 |
| CSC-SWE6-001 | CStyleCheck Software Qualification Test Specification | 1.1 |
| CSC-SUP8-001 | CStyleCheck Configuration Management Plan | 1.1 |
| CSC-SUP1-001 | CStyleCheck Quality Assurance Plan | 1.1 |
| CSC-MAN3-001 | CStyleCheck Project Management Plan | 1.1 |

---

## 4. Software Version Identification

### 4.1 Release Summary

| Field | Value |
|---|---|
| **Product Name** | CStyleCheck |
| **Version** | 1.1.0 |
| **Release Date** | 2026-05-28 |
| **Release Type** | Minor Release |
| **Git Tag** | `v1.1.0` |
| **Branch** | `main` |
| **Previous Release** | V1.0.0 (2026-04-15) |
| **Repository** | https://github.com/dermot-murphy/CStyleCheck |

### 4.2 Release Classification

This is a **minor release** under Semantic Versioning. It is **backward-compatible** with v1.0.0: all existing `rules.yml` configurations, CLI flags, and pre-commit hook integrations continue to work without modification.

New capabilities (MISRA coverage matrix, CI quality gates) are additive and do not alter the checker's violation output for any rule that was functional in v1.0.0.

---

## 5. Delivered Software Items

### 5.1 Primary Deliverable

| Item | Description | Location |
|---|---|---|
| `src/cstylecheck.py` | Main checker script (~3 200 lines, stdlib only) | `src/cstylecheck.py` |
| `src/rules.yml` | Rule configuration for the CStyleCheck project | `src/rules.yml` |
| `src/_version.py` | Version string: `1.1.0` | `src/_version.py` |
| `src/aliases.txt` | Module alias map | `src/aliases.txt` |
| `src/exclusions.yml` | Per-file rule suppressions | `src/exclusions.yml` |
| `src/options.txt` | Project defaults for `--options-file` | `src/options.txt` |
| `src/defines.txt` | Keyword/type aliases for `--defines` | `src/defines.txt` |
| `src/copyright_header.txt` | Copyright block template for `--copyright` | `src/copyright_header.txt` |
| `src/c_keywords.txt` | C/C++ keyword list for `--keywords-file` | `src/c_keywords.txt` |
| `src/c_stdlib_names.txt` | C stdlib name list for `--stdlib-file` | `src/c_stdlib_names.txt` |
| `src/c_spell_dict.txt` | Spell-check dictionary for `--spell-dict` | `src/c_spell_dict.txt` |

### 5.2 Docker Image

| Registry | Image | Tags |
|---|---|---|
| Docker Hub | `cstylecheck/cstylecheck` | `1.1.0`, `1.1`, `1`, `latest` |
| GitHub Container Registry | `ghcr.io/dermot-murphy/cstylecheck` | `1.1.0`, `1.1`, `1`, `latest` |

Platforms: `linux/amd64`, `linux/arm64`.

### 5.3 CI / Automation Scripts

| Item | Description |
|---|---|
| `scripts/ci/append_trend_record.py` | Appends JSON record to `gh-pages/cstylecheck/trend.jsonl` |
| `scripts/ci/generate_trend.py` | Regenerates `gh-pages/cstylecheck/index.html` and `badge.json` |
| `scripts/ci/update_readme_badge.py` | Updates the naming-convention badge link in `README.md` |

### 5.4 Test Suite

| Item | Test Count | Description |
|---|---|---|
| `tests/test_barr_c.py` | 42 | Barr-C rules |
| `tests/test_yoda_condition.py` | 37 | misc.yoda_condition |
| `tests/test_reserved_name.py` | 40 | reserved_name |
| `tests/test_dictionaries.py` | 32 | dict file loading and CLI flags |
| `tests/test_misc_improvements.py` | 65 | unsigned_suffix, loop vars, numerics |
| `tests/test_defines.py` | 16 | constant.* / macro.* |
| `tests/test_variables.py` | 32 | all variable.* rules |
| `tests/test_functions.py` | 14 | function.* |
| `tests/test_typedefs.py` | 8 | typedef.* |
| `tests/test_enums.py` | 11 | enum.* |
| `tests/test_structs.py` | 7 | struct.* |
| `tests/test_include_guards.py` | 8 | include_guard.* |
| `tests/test_misc.py` | 23 | line_length / indentation / magic / suffix |
| `tests/test_spell_check.py` | 9 | spell_check |
| `tests/test_sign_compatibility.py` | 7 | cross-file sign compatibility |
| `tests/test_block_comment_spacing.py` | 18 | misc.block_comment_spacing |
| `tests/test_copyright_header.py` | 55 | misc.copyright_header |
| `tests/test_eof_comment.py` | 33 | misc.eof_comment |
| `tests/test_cli.py` | 29 | CLI flags end-to-end |
| `tests/test_improvements.py` | 63 | all 10 improvements (bugs + new features) |
| `tests/test_workflow_config.py` | — | CI workflow configuration regression tests |

### 5.5 Documentation

| Document ID | Title | Version |
|---|---|---|
| CSC-SVD-001 | Software Version Description (this document) | 1.1 |
| CSC-SWE1-001 | Software Requirements Specification | 1.1 |
| CSC-SWE2-001 | Software Architecture Design | 1.1 |
| CSC-SWE3-001 | Software Detailed Design | 1.1 |
| CSC-SWE4-001 | Software Unit Verification Specification | 1.1 |
| CSC-SWE5-001 | Software Integration Test Specification | 1.1 |
| CSC-SWE6-001 | Software Qualification Test Specification | 1.1 |
| CSC-SYS2-001 | System Requirements Specification | 1.1 |
| CSC-SYS3-001 | System Architecture Design | 1.1 |
| CSC-SYS4-001 | System Integration Test Specification | 1.1 |
| CSC-SYS5-001 | System Verification Specification | 1.1 |
| CSC-MAN3-001 | Project Management Plan | 1.1 |
| CSC-MAN5-001 | Risk Management Plan | 1.1 |
| CSC-SUP1-001 | Quality Assurance Plan | 1.1 |
| CSC-SUP8-001 | Configuration Management Plan | 1.1 |
| CSC-SUP9-001 | Problem Resolution Plan | 1.1 |
| CSC-SUP10-001 | Change Request Plan | 1.1 |
| CSC-ACQ4-001 | Supplier Monitoring Plan | 1.1 |
| CSC-PA2-001 | Capability Level 2 Records | 1.1 |
| CSC-DEV001 | AI Authorship Deviation Record | 1.0 |

---

## 6. Change Summary (v1.0.0 → v1.1.0)

### 6.1 New Features

| ID | Description | Issue |
|---|---|---|
| F-001 | MISRA C:2012/2023 coverage matrix added to Rules-and-Configuration.md | [#64](https://github.com/dermot-murphy/CStyleCheck/issues/64) |
| F-002 | mypy static type-checking CI gate: `mypy --ignore-missing-imports --implicit-optional` | [#66](https://github.com/dermot-murphy/CStyleCheck/issues/66) |
| F-003 | ruff lint CI gate with project-specific configuration in `pyproject.toml` | [#66](https://github.com/dermot-murphy/CStyleCheck/issues/66) |
| F-004 | CI scripts extracted from inline YAML into `scripts/ci/` Python modules | [#63](https://github.com/dermot-murphy/CStyleCheck/issues/63) |
| F-005 | CSC-DEV-001 AI Authorship Deviation Record added to ASPICE documentation | [#52](https://github.com/dermot-murphy/CStyleCheck/issues/52) |
| F-006 | Badge-path regression tests added to `test_workflow_config.py` | [#42](https://github.com/dermot-murphy/CStyleCheck/issues/42) |

### 6.2 Bug Fixes

| ID | Description | Issue |
|---|---|---|
| B-001 | `--spell-words` flag with disabled spell check now emits a clear warning | [#90](https://github.com/dermot-murphy/CStyleCheck/issues/90) |
| B-002 | `tj-actions/changed-files` pinned to full SHA to prevent mutable tag risk | [#59](https://github.com/dermot-murphy/CStyleCheck/issues/59) |
| B-003 | `moby/buildkit` Docker driver pinned to `v0.19.0` for reproducibility | [#60](https://github.com/dermot-murphy/CStyleCheck/issues/60) |
| B-004 | Global mutation of `C_KEYWORDS`/`C_STDLIB_NAMES` eliminated in `main()` | [#79](https://github.com/dermot-murphy/CStyleCheck/issues/79) |
| B-005 | GitHub Actions annotation titles now reflect rule severity (Error/Warning/Info) | [#77](https://github.com/dermot-murphy/CStyleCheck/issues/77) |
| B-006 | `lower`/`upper` case patterns corrected — reject underscores where disallowed | [#74](https://github.com/dermot-murphy/CStyleCheck/issues/74) |
| B-007 | CRLF line endings normalised once in `Checker.__init__()` — fixes false positives on Windows files | [#73](https://github.com/dermot-murphy/CStyleCheck/issues/73) |
| B-008 | Single-quoted char literals stripped in `strip_strings()` | [#72](https://github.com/dermot-murphy/CStyleCheck/issues/72) |
| B-009 | Digit segments accepted in `lower_snake` names (e.g. `buf16`, `i2c_bus`) | [#70](https://github.com/dermot-murphy/CStyleCheck/issues/70) |
| B-010 | Bidirectional alias map: either column order accepted in `aliases.txt` | [#57](https://github.com/dermot-murphy/CStyleCheck/issues/57) |
| B-011 | `datetime.utcnow()` replaced with `datetime.now(timezone.utc)` | [#56](https://github.com/dermot-murphy/CStyleCheck/issues/56) |
| B-012 | Concurrency group added to `cstylecheck_rules.yml` — prevents trend-record races | [#55](https://github.com/dermot-murphy/CStyleCheck/issues/55) |
| B-013 | Exit code 2 (config error) now correctly terminates CI with annotation | [#50](https://github.com/dermot-murphy/CStyleCheck/issues/50) |
| B-014 | Explicit `token:` added to all bare `actions/checkout` steps | [#51](https://github.com/dermot-murphy/CStyleCheck/issues/51) |
| B-015 | Dead `_vb_prev_dir` assignments removed from `main()` | [#76](https://github.com/dermot-murphy/CStyleCheck/issues/76) |
| B-016 | Redundant local `re` import removed from `_v()` | [#75](https://github.com/dermot-murphy/CStyleCheck/issues/75) |
| B-017 | Unused `OrderedDict` import, spurious `f`-prefix strings, unused locals cleaned up | [#66](https://github.com/dermot-murphy/CStyleCheck/issues/66) |
| B-018 | Shields.io badge endpoint uses `raw.githubusercontent.com` — fixes intermittent badge staleness | — |

### 6.3 Documentation Updates

| ID | Description | Issue |
|---|---|---|
| D-001 | All 17 ASPICE work products updated with v1.1 revision history entries | [#62](https://github.com/dermot-murphy/CStyleCheck/issues/62) |
| D-002 | `aliases.txt` clarified to explain bidirectionality and commented examples | [#71](https://github.com/dermot-murphy/CStyleCheck/issues/71) |
| D-003 | SWE.3 Detailed Design section headers renumbered to match `run_all()` order | [#78](https://github.com/dermot-murphy/CStyleCheck/issues/78) |

---

## 7. Known Issues and Limitations

The following issues are open at the time of this release and deferred to a future version:

| Issue | Title | Priority |
|---|---|---|
| [#53](https://github.com/dermot-murphy/CStyleCheck/issues/53) | Investigate `macro.style` false positives on function-like macros | Medium |
| [#54](https://github.com/dermot-murphy/CStyleCheck/issues/54) | `misc.copyright_header` regex anchoring edge cases | Low |
| [#61](https://github.com/dermot-murphy/CStyleCheck/issues/61) | Add `--output-format=junit-xml` option | Low |
| [#65](https://github.com/dermot-murphy/CStyleCheck/issues/65) | Improve error message when `rules.yml` has unknown keys | Low |
| [#68](https://github.com/dermot-murphy/CStyleCheck/issues/68) | Pre-commit hook fails when no C files staged | Low |
| [#114](https://github.com/dermot-murphy/CStyleCheck/issues/114) | `function.return_type` false positive on K&R-style definitions | Low |

---

## 8. Release Verification

### 8.1 CI Status at Release

All of the following CI checks passed on the `main` branch at commit `9edac99` before tag creation:

| Check | Result |
|---|---|
| Unit Tests (Python 3.10) | ✅ Pass |
| Unit Tests (Python 3.11) | ✅ Pass |
| Unit Tests (Python 3.12) | ✅ Pass |
| mypy type check (Python 3.11) | ✅ Pass |
| ruff lint (Python 3.11) | ✅ Pass |
| Example C file action (CStyleCheck self-check) | ✅ Pass |

### 8.2 Qualification Test Status

The full qualification test suite passes with no failures. Test counts per module are documented in §5.4.

### 8.3 Docker Build

The Docker image is built for `linux/amd64` and `linux/arm64` and published to Docker Hub and GHCR on tag creation via `docker_publish.yml`.

---

## 9. Installation and Upgrade Notes

### 9.1 Upgrade from v1.0.0

No breaking changes. Upgrade steps:

```bash
# pip / pipx
pip install --upgrade cstylecheck

# Docker
docker pull cstylecheck/cstylecheck:1.1.0

# pre-commit (update rev in .pre-commit-config.yaml)
rev: v1.1.0
```

### 9.2 New CI Configuration

If upgrading the GitHub Actions workflow:

1. Replace the inline Python blocks in `cstylecheck_rules.yml` with calls to `scripts/ci/`.
2. The `--spell-words` flag will now emit a warning if `spell_check: disabled` — this is informational only and does not break existing pipelines.

---

## 10. Traceability

| Work Product | Document | Version | Status |
|---|---|---|---|
| Software Requirements | CSC-SWE1-001 | 1.1 | Released |
| Software Architecture | CSC-SWE2-001 | 1.1 | Released |
| Detailed Design | CSC-SWE3-001 | 1.1 | Released |
| Unit Verification | CSC-SWE4-001 | 1.1 | Released |
| Integration Tests | CSC-SWE5-001 | 1.1 | Released |
| Qualification Tests | CSC-SWE6-001 | 1.1 | Released |
| Source Code | `src/cstylecheck.py` | 1.1.0 | Released |
| Test Suite | `tests/` | 1.1.0 | Released |
| CI Automation | `.github/workflows/` + `scripts/ci/` | 1.1.0 | Released |
| Docker Image | `Dockerfile/Dockerfile` | 1.1.0 | Released |
| Change Log | `CHANGELOG.md` | 1.1.0 | Released |

---

*End of Software Version Description — CStyleCheck v1.1.0*
