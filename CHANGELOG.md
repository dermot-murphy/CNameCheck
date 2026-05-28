# Changelog

All notable changes to CStyleCheck are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.1.0] — 2026-05-28

### Added

- **MISRA C:2012/2023 coverage matrix** added to `Rules-and-Configuration.md`, mapping each
  CStyleCheck rule ID to the MISRA C:2012 and MISRA C:2023 rules it implements or supports
  (issues [#64](https://github.com/dermot-murphy/CStyleCheck/issues/64)).
- **mypy static type-checking gate** added to the CI test workflow
  (`cstylecheck_tests.yml`): runs `mypy src/cstylecheck.py --ignore-missing-imports
  --implicit-optional` on Python 3.11 and fails the build on type errors
  (issue [#66](https://github.com/dermot-murphy/CStyleCheck/issues/66)).
- **ruff lint gate** added to the CI test workflow: runs `ruff check src/ tests/` on
  Python 3.11 and fails the build on lint violations; ruff config added to `pyproject.toml`
  (issue [#66](https://github.com/dermot-murphy/CStyleCheck/issues/66)).
- **CSC-DEV-001 AI Authorship Deviation Record** (`docs/aspice/CStyleCheck_DEV001_AI_Authorship_Deviation.md`)
  documents the approved deviation for AI-assisted content generation across all ASPICE work
  products (issue [#52](https://github.com/dermot-murphy/CStyleCheck/issues/52)).
- **Badge-path regression tests** (`tests/test_workflow_config.py`) prevent future drift in
  the shields.io badge endpoint path (issue [#42](https://github.com/dermot-murphy/CStyleCheck/issues/42)).

### Changed

- **CI scripts extracted from workflow YAML**: inline Python blocks in
  `cstylecheck_rules.yml` moved to dedicated scripts in `scripts/ci/`:
  `append_trend_record.py`, `generate_trend.py`, `update_readme_badge.py`.
  Improves readability and testability (issue [#63](https://github.com/dermot-murphy/CStyleCheck/issues/63)).
- **Shields.io badge endpoint** now uses `raw.githubusercontent.com` (gh-pages branch) as
  the endpoint URL instead of the GitHub Pages CDN — fixes intermittent badge staleness.
- **ASPICE work products** updated with v1.1 revision history entries in all 17 documents
  (issue [#62](https://github.com/dermot-murphy/CStyleCheck/issues/62)).

### Fixed

- **`--spell-words` with disabled spell check** now emits a clear warning instead of
  silently ignoring the flag (issue [#90](https://github.com/dermot-murphy/CStyleCheck/issues/90)).
- **`tj-actions/changed-files`** pinned to full commit SHA (SHA-pinned to v44) to prevent
  supply-chain risk from mutable tag references
  (issue [#59](https://github.com/dermot-murphy/CStyleCheck/issues/59)).
- **`moby/buildkit`** Docker build driver pinned to `v0.19.0` for reproducible multi-platform
  builds (issue [#60](https://github.com/dermot-murphy/CStyleCheck/issues/60)).
- **Global mutation of `C_KEYWORDS`/`C_STDLIB_NAMES`** in `main()` eliminated; lists are now
  copied before modification, preventing cross-invocation contamination when the checker is
  imported (issue [#79](https://github.com/dermot-murphy/CStyleCheck/issues/79)).
- **GitHub Actions annotation titles** now reflect the rule type (Error/Warning/Info) rather
  than always showing "error" (issue [#77](https://github.com/dermot-murphy/CStyleCheck/issues/77)).
- **`lower` and `upper` case pattern matchers** corrected to reject identifiers containing
  underscores where the rule requires purely lower-case or upper-case letters
  (issue [#74](https://github.com/dermot-murphy/CStyleCheck/issues/74)).
- **CRLF line endings** normalised once in `Checker.__init__()` rather than on every
  individual check, fixing false positives on Windows-formatted files
  (issue [#73](https://github.com/dermot-murphy/CStyleCheck/issues/73)).
- **Single-quoted char literals** (e.g. `'\n'`, `'a'`) now stripped in `strip_strings()`,
  preventing false positives from character constants
  (issue [#72](https://github.com/dermot-murphy/CStyleCheck/issues/72)).
- **Digit segments in `lower_snake` variable names** now accepted (e.g. `buf16`, `i2c_bus`)
  (issue [#70](https://github.com/dermot-murphy/CStyleCheck/issues/70)).
- **Bidirectional alias map** built correctly so that either column order in `aliases.txt`
  is accepted (issue [#57](https://github.com/dermot-murphy/CStyleCheck/issues/57)).
- **`datetime.utcnow()`** replaced with timezone-aware `datetime.now(timezone.utc)` in
  trend-record script, eliminating Python 3.12 deprecation warning
  (issue [#56](https://github.com/dermot-murphy/CStyleCheck/issues/56)).
- **CI concurrency group** added to `cstylecheck_rules.yml` to serialise runs on the same
  branch and prevent parallel pushes racing to append trend records
  (issue [#55](https://github.com/dermot-murphy/CStyleCheck/issues/55)).
- **Exit code 2** (configuration error) now correctly terminates CI with an informative
  error annotation rather than silently passing
  (issue [#50](https://github.com/dermot-murphy/CStyleCheck/issues/50)).
- **Explicit `token:` parameter** added to all bare `actions/checkout` steps to prevent
  intermittent authentication failures on self-hosted runners
  (issue [#51](https://github.com/dermot-murphy/CStyleCheck/issues/51)).
- **Dead `_vb_prev_dir` assignments** removed from `main()` (dead code cleanup)
  (issue [#76](https://github.com/dermot-murphy/CStyleCheck/issues/76)).
- **Redundant local `re` import** removed from `_v()` (code hygiene)
  (issue [#75](https://github.com/dermot-murphy/CStyleCheck/issues/75)).
- **Unused `OrderedDict` import** removed from `_violations_to_sarif()`; spurious `f`-prefix
  strings and unused local variables cleaned up to pass ruff `F401`/`F541`/`F841` checks
  (issue [#66](https://github.com/dermot-murphy/CStyleCheck/issues/66)).

### Documentation

- `docs/aliases.txt` clarified to explain bidirectionality and document commented-out examples
  (issue [#71](https://github.com/dermot-murphy/CStyleCheck/issues/71)).
- `docs/aspice/CStyleCheck_SWE3_Detailed_Design.md` section headers renumbered to match
  `run_all()` execution order (issue [#78](https://github.com/dermot-murphy/CStyleCheck/issues/78)).

---

## [1.0.2] — 2026-05-12

Internal maintenance release (tag only, no GitHub Release page).

### Fixed

- Version badge references updated in README.
- `docker_publish.yml` path trigger corrected to `src/rules.yml`.

---

## [1.0.0] — 2026-04-15

Initial public release.

### Added

- **50 rule IDs** implementing Barr-C:2018 and MISRA-C complementary naming conventions.
- GitHub Actions CI workflow (`cstylecheck_rules.yml`) with trend graph and shields.io badge.
- Docker image published to GHCR and Docker Hub (`cstylecheck`).
- ASPICE CL2 work-product documentation suite (SYS, SWE, MAN, SUP, ACQ processes).
- pre-commit hook support.
- Baseline suppression file (`--exclusions`).
- Structured SARIF / JSON output.
- `--spell-check` integration with custom dictionary.
- `--copyright` file enforcement (`misc.copyright_header`).
- `--eof-comment` mandatory EOF marker (`misc.eof_comment`).

---

[1.1.0]: https://github.com/dermot-murphy/CStyleCheck/compare/V1.0.0...v1.1.0
[1.0.2]: https://github.com/dermot-murphy/CStyleCheck/compare/V1.0.0...V1.0.2
[1.0.0]: https://github.com/dermot-murphy/CStyleCheck/releases/tag/V1.0.0
