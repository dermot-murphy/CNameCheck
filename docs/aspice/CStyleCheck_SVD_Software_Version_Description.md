# Software Version Description

*Automotive SPICE® PAM v4.0 | SUP.8 Configuration Management — Release Artefact*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CSC-SVD-001 | **Version** | 1.10 |
| **Project** | CStyleCheck | **Date** | 2026-06-18 |
| **Status** | Released | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SUP.8 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.10 | 2026-06-18 | Claude | v1.4.0 release — update all version identifiers, release summary, change log, upgrade notes |
| 1.9 | 2026-06-18 | Claude | ASPICE audit #254 — fix internally inconsistent test counts: §3/§5.4/§8.2/§9 now all read 1152 tests / 49 modules (previously a mix of 1143 and stale 1041) |
| 1.8 | 2026-06-08 | Claude | ASPICE audit #238 — update SWE1/SWE3/SWE4 version refs; correct rule count 53→64; update test count 1041→1143, 38→49 modules |
| 1.7 | 2026-06-05 | Claude | v1.3.0 release — update all version identifiers, release summary, change log, upgrade notes |
| 1.6 | 2026-06-05 | Claude | CSC-AUD-005 corrective action — fix factual errors identified in audit |
| 1.5 | 2026-06-04 | Claude | Add §6.1 F-008 to F-012 for five new features (inline suppression, --fix, --init/--preset, per-dir config, HTML output); update §5.1 deliverables, §5.5 doc versions, §10 traceability — issues #188 #189 #190 #193 #192 |
| 1.4 | 2026-06-04 | Claude | Deep accuracy audit: update §3.1, §5.5, §10 document version tables to reflect post-audit versions — resolves issue #163 |
| 1.3 | 2026-06-04 | Claude | Automated accuracy audit: test count 839→965 (33 modules), add missing test modules to §5.4, fix SWE6 version in §5.5, update §8.2 and §10 — resolves issue #163 |
| 1.2 | 2026-05-29 | Claude | Updated for v1.2.0 release — package refactor, 3 new rules, 839 tests |
| 1.1 | 2026-05-28 | Claude | Initial SVD document created for v1.1.0 release |

---

## 3. Purpose & Scope

This **Software Version Description (SVD)** formally describes the **CStyleCheck v1.4.0** software release. It identifies the software items delivered, the baseline against which changes are recorded, and the configuration status of all controlled work products.

This document satisfies the release-identification and configuration-status-accounting requirements of **Automotive SPICE® PAM v4.0, SUP.8 — Configuration Management**.

### 3.1 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CSC-SWE1-001 | CStyleCheck Software Requirements Specification | 1.9 |
| CSC-SWE2-001 | CStyleCheck Software Architecture Design | 1.8 |
| CSC-SWE3-001 | CStyleCheck Software Detailed Design | 1.10 |
| CSC-SWE4-001 | CStyleCheck Software Unit Verification Specification | 1.11 |
| CSC-SWE5-001 | CStyleCheck Software Integration Test Specification | 1.5 |
| CSC-SWE6-001 | CStyleCheck Software Qualification Test Specification | 1.6 |
| CSC-SUP8-001 | CStyleCheck Configuration Management Plan | 1.7 |
| CSC-SUP1-001 | CStyleCheck Quality Assurance Plan | 1.4 |
| CSC-MAN3-001 | CStyleCheck Project Management Plan | 1.6 |

---

## 4. Software Version Identification

### 4.1 Release Summary

| Field | Value |
|---|---|
| **Product Name** | CStyleCheck |
| **Version** | 1.4.0 |
| **Release Date** | 2026-06-18 |
| **Release Type** | Minor Release |
| **Git Tag** | `v1.4.0` |
| **Branch** | `main` |
| **Previous Release** | v1.3.0 (2026-06-05) |
| **Repository** | https://github.com/dermot-murphy/CStyleCheck |

### 4.2 Release Classification

This is a **minor release** under Semantic Versioning. It is **backward-compatible** with v1.3.0: all existing `rules.yml` configurations, CLI flags, and pre-commit hook integrations continue to work without modification.

New capabilities are 11 new rules from issues #221–#232 (`macro.trailing_semicolon`,
`macro.multistatement_wrapper`, `misc.function_length`, `misc.function_doc_header`,
`misc.assert_density`, `misc.null_statement_comment`, `misc.declaration_spacing`,
`misc.file_length`, `misc.reserved_header_name`, `naming.identifier_length`,
`naming.no_single_char_identifiers`), bringing the total from 64 to **75 rule IDs**. All
new rules are entirely additive; several are disabled by default. This release also
includes three bug fixes (issues #245/#246, #248/#249, #251) — see §6.2. The CLI entry
point, all pre-existing rule IDs, and all existing output formats remain
backward-compatible with v1.3.0.

---

## 5. Delivered Software Items

### 5.1 Primary Deliverable

| Item | Description | Location |
|---|---|---|
| `src/cstylecheck.py` | Thin CLI shim — backward-compatible entry point | `src/cstylecheck.py` |
| `src/cstylecheck/__init__.py` | Package root — re-exports full public API | `src/cstylecheck/__init__.py` |
| `src/cstylecheck/cli.py` | Argument parsing and file discovery | `src/cstylecheck/cli.py` |
| `src/cstylecheck/config.py` | Rule configuration loading (YAML, defines, aliases, exclusions) | `src/cstylecheck/config.py` |
| `src/cstylecheck/models.py` | Violation, CheckResult, shared constants | `src/cstylecheck/models.py` |
| `src/cstylecheck/preprocessor.py` | Comment/string stripping, token extraction | `src/cstylecheck/preprocessor.py` |
| `src/cstylecheck/utils.py` | Case matching helpers, module-name derivation | `src/cstylecheck/utils.py` |
| `src/cstylecheck/checker.py` | Main Checker class — all 75 rule implementations | `src/cstylecheck/checker.py` |
| `src/cstylecheck/sign_checker.py` | Cross-file sign-compatibility and declared_not_defined | `src/cstylecheck/sign_checker.py` |
| `src/cstylecheck/baseline.py` | Baseline load / write | `src/cstylecheck/baseline.py` |
| `src/cstylecheck/output.py` | Text / JSON / SARIF / HTML formatters, Tee, summary table | `src/cstylecheck/output.py` |
| `src/cstylecheck/fixer.py` | Auto-fix engine: apply_fixes, unified_diff (`--fix`, `--dry-run`, `--safe-only`) | `src/cstylecheck/fixer.py` |
| `src/cstylecheck/wizard.py` | Config wizard and preset writer (`--init`, `--preset`) | `src/cstylecheck/wizard.py` |
| `src/rules.yml` | Rule configuration for the CStyleCheck project | `src/rules.yml` |
| `src/_version.py` | Version string: `1.4.0` (generated by CI: `git describe --tags`) | `src/_version.py` |
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
| Docker Hub | `dermotmurphy/cstylecheck` | `1.4.0`, `1.4`, `1`, `latest` |
| GitHub Container Registry | `ghcr.io/dermot-murphy/cstylecheck` | `1.4.0`, `1.4`, `1`, `latest` |

Platforms: `linux/amd64`, `linux/arm64`.

### 5.3 CI / Automation Scripts

| Item | Description |
|---|---|
| `scripts/ci/append_trend_record.py` | Appends JSON record to `gh-pages/cstylecheck/trend.jsonl` |
| `scripts/ci/generate_trend.py` | Regenerates `gh-pages/cstylecheck/index.html` and `badge.json` |
| `scripts/ci/update_readme_badge.py` | Updates the naming-convention badge link in `README.md` |

### 5.4 Test Suite

**Total: 1152 tests across 49 modules** — all passing.

| Item | Test Count | Description |
|---|---|---|
| `tests/test_barr_c.py` | 42 | Barr-C naming rules |
| `tests/test_yoda_condition.py` | 37 | misc.yoda_condition |
| `tests/test_reserved_name.py` | 40 | reserved_name |
| `tests/test_dictionaries.py` | 32 | dict file loading and CLI flags |
| `tests/test_misc_improvements.py` | 77 | unsigned_suffix, loop vars, numerics |
| `tests/test_defines.py` | 16 | constant.* / macro.* |
| `tests/test_variables.py` | 43 | all variable.* rules |
| `tests/test_functions.py` | 14 | function.* |
| `tests/test_typedefs.py` | 8 | typedef.* |
| `tests/test_enums.py` | 11 | enum.* |
| `tests/test_structs.py` | 12 | struct.* |
| `tests/test_include_guards.py` | 8 | include_guard.* |
| `tests/test_misc.py` | 28 | line_length / indentation / magic / suffix |
| `tests/test_spell_check.py` | 9 | spell_check |
| `tests/test_sign_compatibility.py` | 7 | cross-file sign compatibility |
| `tests/test_block_comment_spacing.py` | 29 | misc.block_comment_spacing |
| `tests/test_copyright_header.py` | 55 | misc.copyright_header |
| `tests/test_eof_comment.py` | 33 | misc.eof_comment |
| `tests/test_cli.py` | 43 | CLI flags end-to-end |
| `tests/test_improvements.py` | 67 | bugs + new feature regression tests |
| `tests/test_comment_ratio.py` | 24 | misc.comment_ratio (new in v1.2.0) |
| `tests/test_whitespace_ratio.py` | 27 | misc.whitespace_ratio (new in v1.2.0) |
| `tests/test_declared_not_defined.py` | 39 | misc.declared_not_defined (new in v1.2.0) |
| `tests/test_misra_rules.py` | 52 | MISRA C rule coverage |
| `tests/test_parameter_prefix.py` | 42 | variable.parameter.* rules |
| `tests/test_exclusions.py` | 28 | per-file rule suppression |
| `tests/test_github_annotations.py` | 8 | GitHub Actions annotation output |
| `tests/test_case_patterns.py` | 6 | case-pattern helper functions |
| `tests/test_thread_safe_globals.py` | 4 | thread-safety of shared globals |
| `tests/test_preprocessor.py` | 76 | preprocessor.py — strip_comments, strip_strings, preprocess, build_line_map, etc. |
| `tests/test_config_loading.py` | 13 | config.py — load_config UTF-8 handling, missing file, YAML errors |
| `tests/test_update_config.py` | 27 | config.py — _deep_merge function |
| `tests/test_workflow_config.py` | 16 | CI workflow configuration regression tests |
| `tests/test_inline_suppression.py` | 15 | Inline suppression comments (`parse_inline_suppressions`) |
| `tests/test_fix_mode.py` | 11 | Auto-fix engine (`apply_fixes`, `unified_diff`) |
| `tests/test_init_wizard.py` | 15 | Config wizard and presets (`run_wizard`, `run_preset`) |
| `tests/test_per_dir_config.py` | 15 | Per-directory config resolution (`resolve_per_dir_config`) |
| `tests/test_html_report.py` | 20 | HTML report output (`_violations_to_html`) |
| `tests/test_function_length.py` | 11 | `misc.function_length` rule |
| `tests/test_function_doc_header.py` | 12 | `misc.function_doc_header` rule |
| `tests/test_assert_density.py` | 8 | `misc.assert_density` rule |
| `tests/test_null_statement_comment.py` | 10 | `misc.null_statement_comment` rule |
| `tests/test_declaration_spacing.py` | 8 | `misc.declaration_spacing` rule |
| `tests/test_file_length.py` | 8 | `misc.file_length` rule |
| `tests/test_reserved_header_name.py` | 10 | `misc.reserved_header_name` rule |
| `tests/test_macro_trailing_semicolon.py` | 9 | `macro.trailing_semicolon` rule |
| `tests/test_macro_multistatement_wrapper.py` | 9 | `macro.multistatement_wrapper` rule |
| `tests/test_identifier_length.py` | 10 | `naming.identifier_length` rule |
| `tests/test_no_single_char_identifiers.py` | 8 | `naming.no_single_char_identifiers` rule |
| **Total** | **1152** | |

### 5.5 Documentation

| Document ID | Title | Version |
|---|---|---|
| CSC-SVD-001 | Software Version Description (this document) | 1.9 |
| CSC-SWE1-001 | Software Requirements Specification | 1.9 |
| CSC-SWE2-001 | Software Architecture Design | 1.8 |
| CSC-SWE3-001 | Software Detailed Design | 1.10 |
| CSC-SWE4-001 | Software Unit Verification Specification | 1.11 |
| CSC-SWE5-001 | Software Integration Test Specification | 1.5 |
| CSC-SWE6-001 | Software Qualification Test Specification | 1.6 |
| CSC-SYS2-001 | System Requirements Specification | 1.6 |
| CSC-SYS3-001 | System Architecture Design | 1.5 |
| CSC-SYS4-001 | System Integration Test Specification | 1.4 |
| CSC-SYS5-001 | System Verification Specification | 1.6 |
| CSC-MAN3-001 | Project Management Plan | 1.6 |
| CSC-MAN5-001 | Risk Management Plan | 1.3 |
| CSC-SUP1-001 | Quality Assurance Plan | 1.4 |
| CSC-SUP8-001 | Configuration Management Plan | 1.7 |
| CSC-SUP9-001 | Problem Resolution Plan | 1.2 |
| CSC-SUP10-001 | Change Request Plan | 1.2 |
| CSC-ACQ4-001 | Supplier Monitoring Plan | 1.2 |
| CSC-PA2-001 | Capability Level 2 Records | 1.9 |
| CSC-DEV001 | AI Authorship Deviation Record | 1.0 |
| CSC-DEV002 | Independent Review Deviation Record | 1.0 |

---

## 6. Change Summary (v1.3.0 → v1.4.0)

### 6.1 New Features

| ID | Description | Issue |
|---|---|---|
| F-006 | `macro.trailing_semicolon` — flags `#define` macros whose expansion ends with a semicolon, preventing double-semicolon and dangling-else bugs at the call site | [#228](https://github.com/dermot-murphy/CStyleCheck/issues/228) |
| F-007 | `macro.multistatement_wrapper` — enforces that function-like macros containing multiple statements are wrapped in `do { ... } while (0)` for safe use in `if`/`else` branches | [#229](https://github.com/dermot-murphy/CStyleCheck/issues/229) |
| F-008 | `misc.function_length` — configurable maximum function body line count; supports `count_comments: false` to exclude blank and comment-only lines | [#221](https://github.com/dermot-murphy/CStyleCheck/issues/221) |
| F-009 | `misc.function_doc_header` — requires a Doxygen-style `@brief`/`@param`/`@return` block comment before each non-static function definition (disabled by default) | [#222](https://github.com/dermot-murphy/CStyleCheck/issues/222) |
| F-010 | `misc.assert_density` — enforces a minimum number of `assert()` calls per qualifying function; supports per-function exemption via regex patterns (disabled by default) | [#225](https://github.com/dermot-murphy/CStyleCheck/issues/225) |
| F-011 | `misc.null_statement_comment` — requires a comment whenever a null statement (`while (x) ;`, standalone `;`) is used | [#227](https://github.com/dermot-murphy/CStyleCheck/issues/227) |
| F-012 | `misc.declaration_spacing` — enforces a blank line between variable declarations and the first executable statement in a function body (disabled by default) | [#224](https://github.com/dermot-murphy/CStyleCheck/issues/224) |
| F-013 | `misc.file_length` — configurable maximum total lines per source file; supports excluding blank and/or comment-only lines from the count | [#232](https://github.com/dermot-murphy/CStyleCheck/issues/232) |
| F-014 | `misc.reserved_header_name` — flags source files and `#include "..."` directives that use a name identical to a standard C or POSIX library header | [#230](https://github.com/dermot-murphy/CStyleCheck/issues/230) |
| F-015 | `naming.identifier_length` — uniform minimum/maximum identifier-length check across all identifier categories with per-name exemptions (disabled by default) | [#223](https://github.com/dermot-murphy/CStyleCheck/issues/223) |
| F-016 | `naming.no_single_char_identifiers` — flags single-character variable names outside a configurable exempt list (disabled by default) | [#231](https://github.com/dermot-murphy/CStyleCheck/issues/231) |

### 6.2 Bug Fixes

| ID | Description | Issue |
|---|---|---|
| B-001 | Parameter and pointer naming-prefix checks no longer require both prefixes simultaneously when only one is configured, fixing false positives on otherwise compliant declarations | [#245](https://github.com/dermot-murphy/CStyleCheck/issues/245), [#246](https://github.com/dermot-murphy/CStyleCheck/issues/246) |
| B-002 | Fixed a catastrophic-backtracking (ReDoS) regular expression in `misc.null_statement_comment` that could hang indefinitely on an unclosed `if`/`while`/`for` condition spanning a long line | [#248](https://github.com/dermot-murphy/CStyleCheck/issues/248), [#249](https://github.com/dermot-murphy/CStyleCheck/issues/249) |
| B-003 | Fixed broken GitHub Wiki links: malformed triple-hyphen slugs for headings containing backticks/parentheses, and a non-functional "Rules and Configuration Reference" link | [#251](https://github.com/dermot-murphy/CStyleCheck/issues/251) |

### 6.3 Documentation Updates

| ID | Description | Issue |
|---|---|---|
| D-006 | ASPICE audit CSC-AUD-006 corrective action: fixed pervasive stale test counts (1152/49 modules), a Document-ID collision (`CSC-STD-001`), systemic cross-reference version-citation drift across all 22 `docs/aspice/*.md` work products, three orphaned top-level docs, and `CHANGELOG.md` gaps | [#254](https://github.com/dermot-murphy/CStyleCheck/issues/254) |
| D-007 | Fixed Wiki sidebar/README links: malformed triple-hyphen slugs and the non-functional "Rules and Configuration Reference" link | [#251](https://github.com/dermot-murphy/CStyleCheck/issues/251) |
| D-008 | 102 new tests (1152 total) covering all 11 new rules, including edge cases for multi-line macros, nested braces, comment exclusion, and regex-based exemptions | — |

---

## 7. Known Issues and Limitations

The following issues are open at the time of this release and deferred to a future version:

| Issue | Title | Priority |
|---|---|---|
| [#159](https://github.com/dermot-murphy/CStyleCheck/issues/159) | Add `--output-format=junit-xml` output option | Low |
| [#160](https://github.com/dermot-murphy/CStyleCheck/issues/160) | Pre-commit hook: warn gracefully when no C files are staged | Low |
| [#161](https://github.com/dermot-murphy/CStyleCheck/issues/161) | `misc.copyright_header` regex anchoring edge cases on Windows line endings | Low |

> No open issues map to known functional defects in the 75 active rules. All issue numbers above are illustrative; see GitHub for the live issue tracker.

---

## 8. Release Verification

### 8.1 CI Status at Release

All of the following CI checks passed on the `develop` branch before tag creation and merge to `main`:

| Check | Result |
|---|---|
| Unit Tests (Python 3.10) | ✅ Pass |
| Unit Tests (Python 3.11) | ✅ Pass |
| Unit Tests (Python 3.12) | ✅ Pass |
| mypy type check (Python 3.11) | ✅ Pass |
| ruff lint (Python 3.11) | ✅ Pass |
| Coverage gate ≥ 85% combined (Python 3.11) | ✅ Pass |
| Example C file action (CStyleCheck self-check) | ✅ Pass |

### 8.2 Qualification Test Status

All 1152 tests pass with no failures. Test counts per module are documented in §5.4.

### 8.3 Docker Build

The Docker image is built for `linux/amd64` and `linux/arm64` and published to Docker Hub and GHCR automatically on creation of the `v1.4.0` tag via `docker_publish.yml`.

### 8.4 GitHub Pages / Wiki

The GitHub Wiki is rebuilt automatically on any push to `main` that touches `README.md` or `docs/aspice/**` via `wiki_publish.yml`. GitHub Pages (gh-pages branch) hosts the naming-convention trend dashboard, updated on each main-branch push via `cstylecheck_rules.yml`.

---

## 9. Installation and Upgrade Notes

### 9.1 Upgrade from v1.3.0

No breaking changes. Upgrade steps:

```bash
# pip / pipx
pip install --upgrade cstylecheck

# Docker
docker pull dermotmurphy/cstylecheck:1.4.0

# pre-commit (update rev in .pre-commit-config.yaml)
rev: v1.4.0
```

### 9.2 New Features — Optional Activation

New rules in v1.4.0 that require explicit opt-in (`enabled: true` under their key in
`rules.yml`) because they are disabled by default:

- **`misc.function_doc_header`**, **`misc.assert_density`**, **`misc.declaration_spacing`**,
  **`naming.identifier_length`**, **`naming.no_single_char_identifiers`**.

The remaining six new rules (`macro.trailing_semicolon`, `macro.multistatement_wrapper`,
`misc.function_length`, `misc.null_statement_comment`, `misc.file_length`,
`misc.reserved_header_name`) are enabled by default; no config change is required to
benefit from them.

### 9.3 Backward Compatibility

The `src/cstylecheck.py` entry point shim is unchanged. All pre-existing rule IDs,
existing `rules.yml` configurations, and pre-commit hook definitions are unchanged. The
11 new rules added in this release bring the total to 75 rule IDs. Users who import the
checker programmatically via `import cstylecheck` continue to work without modification.

---

## 10. Traceability

| Work Product | Document | Version | Status |
|---|---|---|---|
| System Requirements | CSC-SYS2-001 | 1.6 | Released |
| System Architecture | CSC-SYS3-001 | 1.5 | Released |
| System Integration Tests | CSC-SYS4-001 | 1.4 | Released |
| System Verification | CSC-SYS5-001 | 1.6 | Released |
| Software Requirements | CSC-SWE1-001 | 1.9 | Released |
| Software Architecture | CSC-SWE2-001 | 1.8 | Released |
| Detailed Design | CSC-SWE3-001 | 1.10 | Released |
| Unit Verification | CSC-SWE4-001 | 1.11 | Released |
| Integration Tests | CSC-SWE5-001 | 1.5 | Released |
| Qualification Tests | CSC-SWE6-001 | 1.6 | Released |
| Source Code | `src/cstylecheck/` (package) | 1.4.0 | Released |
| Test Suite | `tests/` (1152 tests) | 1.4.0 | Released |
| CI Automation | `.github/workflows/` + `scripts/ci/` | 1.4.0 | Released |
| Docker Image | `Dockerfile/Dockerfile` | 1.4.0 | Released |
| Change Log | `CHANGELOG.md` | 1.4.0 | Released |

---

## 11. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | Approved | 2026-05-29 |
| Technical Reviewer | Dermot Murphy | Approved | 2026-05-29 |
| Quality Assurance | Dermot Murphy | Approved | 2026-05-29 |
| Approver | Dermot Murphy | Approved | 2026-05-29 |

> **Note:** This document is under configuration management (SUP.8). Post-approval changes require a change request (SUP.10) and a new document version.

---

*End of Software Version Description — CStyleCheck v1.4.0*
