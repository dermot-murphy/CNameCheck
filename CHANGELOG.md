# Changelog

All notable changes to CStyleCheck are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

---

## [1.5.0] — 2026-06-26

### Added

- **`misc.non_ascii_source` rule** — flags characters outside the printable ASCII set
  (code points outside 0x20–0x7E, plus TAB/LF/CR), implementing MISRA C:2012/2023 Rule 4.1.
  Optional `exempt_string_literals: true` suppresses violations inside double-quoted string
  literals (issue [#279](https://github.com/dermot-murphy/CStyleCheck/issues/279)).
- **Per-file breakdown in `--summary` output** — the summary block now includes
  "Files with errors / warnings / info / clean" counts. Invariant: all four buckets
  sum to the total files-checked count
  (issue [#278](https://github.com/dermot-murphy/CStyleCheck/issues/278)).

### Changed

- **`constant.case` typedef-alias exemption** — object-like `#define` names ending with
  the configured `typedefs.suffix.suffix` (e.g. `_t`) are now exempt from `constant.case`
  when `typedefs.suffix.enabled: true`. This eliminates the false positive on
  `#define api_nvm_error_t uint8_t`-style type aliases
  (issues [#272](https://github.com/dermot-murphy/CStyleCheck/issues/272),
  [#244](https://github.com/dermot-murphy/CStyleCheck/issues/244)).

### Fixed

- **`variable.parameter.p_prefix` false positive on call statements** —
  `RE_FUNCTION_DECL`/`RE_FUNCTION_DEF` now require a real (non-zero-width) separator
  between the return-type token and the function-name token, preventing regex
  backtracking from misparsing a plain call statement as a declaration/definition
  (issue [#273](https://github.com/dermot-murphy/CStyleCheck/issues/273)).

---

## [1.4.1] — 2026-06-18

### Fixed

- **`variable.parameter.p_prefix` false positive on call statements** —
  `RE_FUNCTION_DECL`/`RE_FUNCTION_DEF` allowed a zero-width separator between
  the captured return-type token and the function-name token. Regex
  backtracking on a plain call statement (e.g. `foo (args) ;`, a single
  identifier with no real type/name split) could split that identifier into a
  fake type + fake name, making the call match as if it were a declaration or
  definition. The call's arguments were then parsed as parameters, producing
  nonsensical `variable.parameter.p_prefix` violations (e.g. flagging `t` from
  a `(uint16_t)` cast, or substrings of `interval`/`timeout`). Fixed by
  requiring a real (non-zero-width) separator — whitespace and/or a pointer
  star — between the return type and the name
  (issue [#273](https://github.com/dermot-murphy/CStyleCheck/issues/273)).
- **`docker_publish.yml` `github-release` job** — checkout step was missing
  the explicit `token: secrets.GITHUB_TOKEN`, inconsistent with the
  `build-and-push` job's checkout step.

---

## [1.4.0] — 2026-06-18

### Added

- **`macro.trailing_semicolon` rule** — detects `#define` macros whose expansion ends
  with a semicolon, preventing double-semicolon and dangling-else bugs at the call site
  (issue [#228](https://github.com/dermot-murphy/CStyleCheck/issues/228)).
- **`macro.multistatement_wrapper` rule** — enforces that function-like macros containing
  multiple statements are wrapped in `do { ... } while (0)` for safe use in `if`/`else`
  branches
  (issue [#229](https://github.com/dermot-murphy/CStyleCheck/issues/229)).
- **`misc.function_length` rule** — configurable maximum function body line count;
  supports `count_comments: false` to exclude blank and comment-only lines from the count
  (issue [#221](https://github.com/dermot-murphy/CStyleCheck/issues/221)).
- **`misc.function_doc_header` rule** — requires a Doxygen-style `@brief`/`@param`/`@return`
  block comment before each non-static function definition (disabled by default)
  (issue [#222](https://github.com/dermot-murphy/CStyleCheck/issues/222)).
- **`misc.assert_density` rule** — enforces a minimum number of `assert()` calls per
  qualifying function; supports per-function exemption via regex patterns (disabled by default)
  (issue [#225](https://github.com/dermot-murphy/CStyleCheck/issues/225)).
- **`misc.null_statement_comment` rule** — requires a comment whenever a null statement
  (`while (x) ;`, standalone `;`) is used, preventing accidental empty loop bodies
  (issue [#227](https://github.com/dermot-murphy/CStyleCheck/issues/227)).
- **`misc.declaration_spacing` rule** — enforces a blank line between variable declarations
  and the first executable statement in a function body (disabled by default)
  (issue [#224](https://github.com/dermot-murphy/CStyleCheck/issues/224)).
- **`misc.file_length` rule** — configurable maximum total lines per source file; supports
  excluding blank and/or comment-only lines from the count
  (issue [#232](https://github.com/dermot-murphy/CStyleCheck/issues/232)).
- **`misc.reserved_header_name` rule** — flags source files and `#include "..."` directives
  that use a name identical to a standard C or POSIX library header, preventing shadowing
  (issue [#230](https://github.com/dermot-murphy/CStyleCheck/issues/230)).
- **`naming.identifier_length` rule** — uniform minimum/maximum identifier-length check
  across all identifier categories with per-name exemptions (disabled by default)
  (issue [#223](https://github.com/dermot-murphy/CStyleCheck/issues/223)).
- **`naming.no_single_char_identifiers` rule** — flags single-character variable names
  outside a configurable exempt list (e.g. `i`, `j`, `k`) (disabled by default)
  (issue [#231](https://github.com/dermot-murphy/CStyleCheck/issues/231)).
- **102 new tests** (1152 total) covering all 11 new rules, including edge cases for
  multi-line macros, nested braces, comment exclusion, and regex-based exemptions.
- Draft companion documents `embedded_c_style_guide.md`, `embedded_c_coding_standard.md`,
  and `external_standards_analysis.md` — pending rule population, linked from the README.

### Fixed

- Parameter and pointer naming-prefix checks no longer require both prefixes
  simultaneously when only one is configured, fixing false positives on otherwise
  compliant declarations
  (issues [#245](https://github.com/dermot-murphy/CStyleCheck/issues/245),
  [#246](https://github.com/dermot-murphy/CStyleCheck/issues/246)).
- Fixed a catastrophic-backtracking (ReDoS) regular expression in
  `misc.null_statement_comment` that could hang indefinitely on an unclosed
  `if`/`while`/`for` condition spanning a long line
  (issues [#248](https://github.com/dermot-murphy/CStyleCheck/issues/248),
  [#249](https://github.com/dermot-murphy/CStyleCheck/issues/249)).
- Fixed broken GitHub Wiki links: malformed triple-hyphen slugs for headings containing
  backticks/parentheses, and a non-functional "Rules and Configuration Reference" link
  that previously prompted "Create a new page" instead of opening the Rules page
  (issue [#251](https://github.com/dermot-murphy/CStyleCheck/issues/251)).

---

## [1.3.0] — 2026-06-05

### Added

- **Inline suppression comments** (`preprocessor.parse_inline_suppressions`) — suppress
  violations on a per-line, next-line, or block basis using structured `// cstylecheck:
  disable=rule.id` comments in C source.  Multiple rules can be comma-separated;
  directives are case-insensitive
  (issue [#188](https://github.com/dermot-murphy/CStyleCheck/issues/188)).
- **`--fix` auto-fix mode** (`fixer.py`) — apply safe mechanical fixes in-place.
  Currently fixes `misc.unsigned_suffix` (`42u` → `42U`) and `misc.lowercase_l_suffix`
  (`100l` → `100L`).  Use `--dry-run` to preview a unified diff without writing, and
  `--safe-only` to restrict to zero-risk fixes (all current fixes qualify)
  (issue [#189](https://github.com/dermot-murphy/CStyleCheck/issues/189)).
- **`--init` config wizard and `--preset`** (`wizard.py`) — `--init` launches an
  interactive Q&A wizard that writes `.cstylecheck.yml`; `--preset barr-c|minimal|misra`
  writes a pre-built config without the wizard.  `--init-output FILE` sets a custom
  output path; `--overwrite` allows overwriting an existing file
  (issue [#190](https://github.com/dermot-murphy/CStyleCheck/issues/190)).
- **Per-directory config** (`config.py resolve_per_dir_config`) — `--per-dir-config`
  flag enables upward directory-walk from each source file, deep-merging any
  `.cstylecheck.yml` found along the path on top of the root config.  The nearest config
  wins; `root: true` in any `.cstylecheck.yml` stops the upward search.  Results are
  cached per directory
  (issue [#193](https://github.com/dermot-murphy/CStyleCheck/issues/193)).
- **HTML report** (`output.py _violations_to_html`) — `--output-format html` produces a
  self-contained HTML report with inline CSS, summary cards (errors / warnings / info /
  total / files), and per-file violation tables.  Written to `--log FILE` if provided,
  else stdout
  (issue [#192](https://github.com/dermot-murphy/CStyleCheck/issues/192)).

---


## [1.2.1] — 2026-05-29

### Fixed

- **Docker image broken in v1.2.0** — `Dockerfile` was missing `COPY src/cstylecheck/ ./cstylecheck/`.
  The shim `cstylecheck.py` does `from cstylecheck.cli import main` which requires the package
  directory to be present alongside the shim inside `/app/`. Without it, Python resolved
  `cstylecheck` to the shim file itself, producing
  `ModuleNotFoundError: No module named 'cstylecheck.cli'; 'cstylecheck' is not a package`.

---

## [1.2.0] — 2026-05-29

### Added

- **`misc.comment_ratio` rule** — configurable minimum comment-density gate; fails when the
  ratio of comment lines to total lines in a file falls below the configured threshold
  (issue [#68](https://github.com/dermot-murphy/CStyleCheck/issues/68)).
- **`misc.whitespace_ratio` rule** — configurable blank-line density gate; fails when the
  ratio of blank lines to total lines exceeds the configured ceiling, catching overly sparse or
  padded source files
  (issue [#145](https://github.com/dermot-murphy/CStyleCheck/issues/145)).
- **`misc.declared_not_defined` cross-file rule** — detects functions declared in a `.h` file
  but never defined in any paired `.c` file in the same invocation, surfacing missing
  implementation stubs early
  (issue [#114](https://github.com/dermot-murphy/CStyleCheck/issues/114)).
- **Package refactor** — `cstylecheck.py` monolith split into a proper Python package
  (`src/cstylecheck/`) comprising 10 sub-modules (`checker.py`, `cli.py`, `config.py`,
  `models.py`, `preprocessor.py`, `utils.py`, `sign_checker.py`, `baseline.py`, `output.py`,
  `__init__.py`). The thin shim `src/cstylecheck.py` retains CLI backward compatibility
  (issue [#65](https://github.com/dermot-murphy/CStyleCheck/issues/65)).
- **CSC-DEV-002 Independent Review Deviation Record** added to ASPICE documentation, formally
  acknowledging the solo-developer peer-review constraint
  (issue [#61](https://github.com/dermot-murphy/CStyleCheck/issues/61)).
- **ASPICE internal audit (CSC-AUD-001)** completed; 58 defects in 14 work products resolved
  (issues [#143](https://github.com/dermot-murphy/CStyleCheck/issues/143),
  [#146](https://github.com/dermot-murphy/CStyleCheck/issues/146)–[#157](https://github.com/dermot-murphy/CStyleCheck/issues/157)).

### Changed

- **Test suite expanded to 839 tests** across 30 test modules — 290 tests added since v1.1.0
  covering the 3 new rules, package refactor, and additional edge cases.
- **Coverage gate raised to 85% combined** (statement + branch) via subprocess coverage for the
  CLI entry point; `--cov-fail-under=85` enforced in CI
  (issue [#54](https://github.com/dermot-murphy/CStyleCheck/issues/54)).
- **ASPICE documentation** — all 17 work products updated with v1.2.x revision history entries.
  ASPICE SWE3 Detailed Design updated to reflect the new 10-module package architecture.

### Fixed

- **CI path trigger** for `cstylecheck_tests.yml` corrected to include `src/cstylecheck/**`
  after the package refactor (was triggering only on `src/cstylecheck.py`).

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

[Unreleased]: https://github.com/dermot-murphy/CStyleCheck/compare/v1.5.0...HEAD
[1.5.0]: https://github.com/dermot-murphy/CStyleCheck/compare/v1.4.1...v1.5.0
[1.4.1]: https://github.com/dermot-murphy/CStyleCheck/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/dermot-murphy/CStyleCheck/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/dermot-murphy/CStyleCheck/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/dermot-murphy/CStyleCheck/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/dermot-murphy/CStyleCheck/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/dermot-murphy/CStyleCheck/compare/V1.0.0...v1.1.0
[1.0.2]: https://github.com/dermot-murphy/CStyleCheck/compare/V1.0.0...V1.0.2
[1.0.0]: https://github.com/dermot-murphy/CStyleCheck/releases/tag/V1.0.0
