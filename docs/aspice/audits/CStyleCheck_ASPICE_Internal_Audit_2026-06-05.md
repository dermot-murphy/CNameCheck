# CStyleCheck ASPICE Internal Audit — CSC-AUD-005

| Field | Value |
|---|---|
| **Audit ID** | CSC-AUD-005 |
| **Date** | 2026-06-05 |
| **Branch** | `main` |
| **Auditor** | AI-assisted internal audit |
| **Scope** | All ASPICE work products — post-release accuracy check for features #188–#193 |
| **Overall Status** | **Pass with Findings** |
| **Findings** | 32 (17 High, 15 Medium) |
| **Test count (actual)** | 1041 |

---

## 1. Scope

Post-release audit following merge of features:
- **#188** — Inline suppression comments (`parse_inline_suppressions`)
- **#189** — `--fix` auto-fix mode (`fixer.py`: `apply_fixes`, `unified_diff`)
- **#190** — `--init` wizard and `--preset` (`wizard.py`: `run_wizard`, `run_preset`)
- **#192** — HTML report (`output.py`: `_violations_to_html`)
- **#193** — Per-directory config (`config.py`: `resolve_per_dir_config`)

All 28 ASPICE work products were reviewed against the actual codebase.

---

## 2. Findings

### SWE3 — Detailed Design (v1.6)

#### SWE3-F-001 — UNIT-96: wrong class, wrong signature, wrong return type [High]

Documented: `Fixer.apply_fixes(files: list[str], violations: list[Violation]) → None`

Three errors:
1. No class `Fixer` exists. `apply_fixes` is a module-level function.
2. First parameter is `source: str`, not `files: list[str]`.
3. Return type is `tuple[str, int]`, not `None`.

**Correct:** `apply_fixes(source: str, violations: list, safe_only: bool = False) → tuple[str, int]`

#### SWE3-F-002 — UNIT-97: wrong function name, wrong class, wrong signature [High]

Documented: `Fixer.dry_run_diff(files: list[str], violations: list[Violation]) → str`

Three errors:
1. Function is named `unified_diff`, not `dry_run_diff`.
2. No class `Fixer` exists.
3. Actual signature: `unified_diff(original: str, fixed: str, filepath: str) → str`

#### SWE3-F-003 — UNIT-99: wrong function name `write_preset` [High]

Documented: `write_preset(preset: str, output_path: str, overwrite: bool) → None`

Function `write_preset` does not exist. Actual function: `run_preset(preset_name: str, output_path: str | None = None, print_fn=print, overwrite: bool = False) → int`

#### SWE3-F-004 — UNIT-98: `run_wizard` wrong return type [High]

Documented: `run_wizard() → dict` — "returns a config dict suitable for writing to .cstylecheck.yml."

Actual: `run_wizard(...) → int` — writes `.cstylecheck.yml` directly and returns 0 (success) or 1 (abort). Does not return a dict.

#### SWE3-F-005 — §4.1 package structure lists non-existent `Fixer class` [High]

Documented:
```
fixer.py  — Fixer class: apply_fixes, dry_run_diff
wizard.py — run_wizard, write_preset
```

Correct:
```
fixer.py  — apply_fixes, unified_diff
wizard.py — run_wizard, run_preset
```

#### SWE3-F-006 — §8 RTM: SWE1-071 double-mapped, UNIT-84 orphaned [High]

SWE1-071 (whitespace_ratio → UNIT-90) appears in two RTM rows — once correctly and once incorrectly mapped to UNIT-84 (`DeclaredNotDefinedChecker`). UNIT-84 has no SWE1 requirement assigned.

#### SWE3-F-007 — Stale referenced document versions [Medium]

- CSC-SWE1-001 cited as v1.5; actual v1.6
- CSC-SWE2-001 cited as v1.4; actual v1.5

---

### SWE4 — Unit Verification (v1.6)

#### SWE4-F-001 — Test count wrong: 965 documented, 1041 actual [High]

Five new test modules (76 tests) absent from §6:

| File | Tests |
|---|---|
| `test_inline_suppression.py` | 15 |
| `test_fix_mode.py` | 11 |
| `test_init_wizard.py` | 15 |
| `test_per_dir_config.py` | 15 |
| `test_html_report.py` | 20 |
| **Total missing** | **76** |

§6 total: 33 modules / 965 tests → correct: **38 modules / 1041 tests**.

#### SWE4-F-002 — §7 traceability missing SWE1-072 to SWE1-077 [High]

SWE1-072 through SWE1-077 (inline suppression, fix mode, wizard, per-dir config, HTML output) have no SWE4 test traceability entries. Breaks SWE1→SWE4 forward traceability.

#### SWE4-F-003 — §4.1/§4.4 reference `src/cstylecheck.py` as static-check target [Medium]

Since the package refactor (v1.2, issue #144), the primary source is `src/cstylecheck/` package. The shim `src/cstylecheck.py` is a thin wrapper only.

#### SWE4-F-004 — Coverage footnote cites 839-test baseline while table shows 965 [Medium]

Footnote in §6: "Statement Coverage (v1.2.0 CI — **839 tests** incl. subprocess): 89.8%". Should reference current baseline.

#### SWE4-F-005 — Stale referenced document versions [Medium]

- CSC-SWE1-001: cited v1.3; actual v1.6
- CSC-SWE3-001: cited v1.3; actual v1.6
- CSC-SWE5-001: cited v1.2; actual v1.3

---

### SWE2 — SW Architecture (v1.5)

#### SWE2-F-001 — Package described as "10 sub-modules"; actual is 12 [High]

§4 opening and ASCII diagram both state "10 sub-modules". After adding `fixer.py` (COMP-08) and `wizard.py` (COMP-09) the package contains 12 files.

#### SWE2-F-002 — COMP-09 diagram lists `write_preset`; actual is `run_preset` [High]

ASCII component diagram (§4): `[COMP-09] Config Wizard (wizard.py — run_wizard, write_preset, …)`. Function `write_preset` does not exist.

#### SWE2-F-003 — Stale referenced document version [Medium]

CSC-SWE1-001 cited as v1.5; actual v1.6.

---

### SWE1 — SW Requirements (v1.6)

#### SWE1-F-001 — Stale referenced document versions [Medium]

- CSC-SYS2-001: cited v1.4; actual v1.5
- CSC-SWE2-001: cited v1.3; actual v1.5

#### SWE1-F-002 — RTM points new-feature reqs to wrong test files [High]

| Requirement | Documented test file | Correct test file |
|---|---|---|
| SWE1-072/073 (inline suppression) | `test_improvements.py` | `test_inline_suppression.py` |
| SWE1-074 (auto-fix) | `test_cli.py` | `test_fix_mode.py` |
| SWE1-075 (wizard/presets) | `test_cli.py` | `test_init_wizard.py` |
| SWE1-076 (per-dir config) | `test_cli.py` | `test_per_dir_config.py` |
| SWE1-077 (HTML report) | `test_cli.py` | `test_html_report.py` |

---

### SYS3 — System Architecture (v1.3)

#### SYS3-F-001 — §9 RTM missing SYS-F-041 to SYS-F-045 [High]

Breaks SYS2→SYS3 forward traceability for all five new features.

#### SYS3-F-002 — §5 and AD-001 state "10 sub-modules" [High]

Actual count: 12. SYS3 was not updated when COMP-08/09 were added.

#### SYS3-F-003 — §5.1 subsystem table omits Fixer, Wizard, Per-dir Config [High]

SS-01 to SS-06 only. Three new functional components (COMP-08/09/10 in SWE2) have no SYS3 subsystem entry.

#### SYS3-F-004 — Stale referenced document version [Medium]

CSC-SYS2-001 cited as v1.4; actual v1.5.

---

### SVD — Software Version Description (v1.5)

#### SVD-F-001 — §5.4 lists 33 modules / 965 tests; actual 38 / 1041 [High]

Five new test files absent from §5.4 table; §8.2 paragraph also states "All 965 tests pass".

#### SVD-F-002 — §6.1 F-001 describes package as "10 sub-modules" [Medium]

Internal inconsistency: same SVD already documents fixer.py (F-009) and wizard.py (F-010), making the count 12.

#### SVD-F-003 — Stale referenced document version [Medium]

CSC-SYS2-001 cited as v1.4; actual v1.5.

---

### SWE5 — Integration Test (v1.3)

#### SWE5-F-001 — §3 body text says "CStyleCheck v1.0.0" [High]

Document header and revision history correctly reference v1.2.x, but §3 Purpose still reads "CStyleCheck **v1.0.0**".

#### SWE5-F-002 — Stale referenced document versions [High]

- CSC-SWE2-001: cited v1.2; actual v1.5
- CSC-SYS4-001: cited v1.2; actual v1.3

#### SWE5-F-003 — No SIT test cases for SYS-F-041 to SYS-F-045 [Medium]

SIT-001 to SIT-013 cover features through SWE1-070. No integration test cases exist for the five new features.

---

### SWE6 — Qualification Test (v1.4)

#### SWE6-F-001 — Qualification scope "SWE1-001 to SWE1-070" incomplete [High]

§3.3 criteria and §6 coverage matrix end at SWE1-070. SWE1-071 to SWE1-077 are unverified. "100% coverage" claim fails.

#### SWE6-F-002 — §9 release gate references v1.1.0 with 759 tests [Medium]

"v1.1.0 release baseline — 759 tests". Should reference v1.2.x. Appendix A also cites "692 total passing tests as of v1.1".

#### SWE6-F-003 — §3.3 and SWQ-011 reference "v1.0.0 commit" [Medium]

Static verification evidence should reference v1.2.0.

#### SWE6-F-004 — Stale referenced document versions [Medium]

- CSC-SWE1-001: cited v1.3; actual v1.6
- CSC-SWE5-001: cited v1.2; actual v1.3

---

### SYS4 / SYS5 — System Integration & Verification

#### SYS45-F-001 — No system-level test cases for SYS-F-041 to SYS-F-045 [Medium]

Neither SYS4 nor SYS5 contain test cases or verification entries for the five new features. SYS5 §6 result table cites "965 tests" (stale).

#### SYS45-F-002 — Stale referenced document version [Low]

Both SYS5 and SYS3 cite CSC-SYS2-001 as v1.4; actual v1.5.

---

## 3. Summary Table

| Finding ID | Document | Priority | Description |
|---|---|---|---|
| SWE3-F-001 | SWE3 | **High** | UNIT-96: wrong class, param, return type for `apply_fixes` |
| SWE3-F-002 | SWE3 | **High** | UNIT-97: wrong name (`dry_run_diff` → `unified_diff`), class, params |
| SWE3-F-003 | SWE3 | **High** | UNIT-99: `write_preset` → `run_preset` |
| SWE3-F-004 | SWE3 | **High** | UNIT-98: `run_wizard` returns `int`, not `dict` |
| SWE3-F-005 | SWE3 | **High** | §4.1: "Fixer class" does not exist; `dry_run_diff` → `unified_diff` |
| SWE3-F-006 | SWE3 | **High** | §8 RTM: SWE1-071 double-mapped; UNIT-84 orphaned |
| SWE4-F-001 | SWE4 | **High** | Test count 965 → 1041; 5 new test modules missing from §6 |
| SWE4-F-002 | SWE4 | **High** | §7 traceability missing SWE1-072 to SWE1-077 |
| SWE1-F-002 | SWE1 | **High** | RTM wrong test file names for SWE1-072–077 |
| SWE2-F-001 | SWE2 | **High** | "10 sub-modules" → 12 |
| SWE2-F-002 | SWE2 | **High** | COMP-09: `write_preset` → `run_preset` |
| SYS3-F-001 | SYS3 | **High** | §9 RTM missing SYS-F-041–045 |
| SYS3-F-002 | SYS3 | **High** | "10 sub-modules" → 12 in §5 and AD-001 |
| SYS3-F-003 | SYS3 | **High** | §5.1 subsystem table missing Fixer, Wizard, Per-dir Config |
| SVD-F-001 | SVD | **High** | §5.4: 33/965 → 38/1041; 5 new test files missing |
| SWE6-F-001 | SWE6 | **High** | Qualification scope ends at SWE1-070; SWE1-071–077 uncovered |
| SWE5-F-001 | SWE5 | **High** | §3 body says "v1.0.0" → should be "v1.2.x" |
| SWE5-F-002 | SWE5 | **High** | SWE2 cited as v1.2; actual v1.5 |
| SWE6-F-002 | SWE6 | **Medium** | §9 gate cites v1.1.0 / 759 tests; Appendix A cites 692 tests |
| SWE6-F-003 | SWE6 | **Medium** | Static verification evidence cites "v1.0.0 commit" → v1.2.0 |
| SWE4-F-003 | SWE4 | **Medium** | §4.1/§4.4 reference shim `src/cstylecheck.py` instead of package |
| SWE4-F-004 | SWE4 | **Medium** | Coverage footnote cites 839-test baseline |
| SVD-F-002 | SVD | **Medium** | F-001 says "10 sub-modules" — internal inconsistency |
| SWE5-F-003 | SWE5 | **Medium** | No SIT cases for SYS-F-041–045 |
| SYS45-F-001 | SYS4/5 | **Medium** | No system test cases/verification for SYS-F-041–045 |
| SWE1-F-001 | SWE1 | **Medium** | SYS2 cited v1.4, SWE2 cited v1.3 |
| SWE3-F-007 | SWE3 | **Medium** | SWE1 cited v1.5, SWE2 cited v1.4 |
| SWE4-F-005 | SWE4 | **Medium** | SWE1/SWE3/SWE5 all several versions behind |
| SWE6-F-004 | SWE6 | **Medium** | SWE1 cited v1.3, SWE5 cited v1.2 |
| SYS3-F-004 | SYS3 | **Medium** | SYS2 cited v1.4; actual v1.5 |
| SVD-F-003 | SVD | **Medium** | SYS2 cited v1.4; actual v1.5 |
| SWE2-F-003 | SWE2 | **Medium** | SWE1 cited v1.5; actual v1.6 |

---

## 4. Action Required

All 17 High findings and 15 Medium findings to be resolved in a single corrective action — see linked GitHub issue.

**Key facts for assessor:**
1. `fixer.py` has **no `Fixer` class** — SWE2, SWE3 both assert one
2. `write_preset` **does not exist** — actual function is `run_preset`
3. **1041 tests, not 965** — 5 new test modules entirely unregistered in ASPICE docs
4. **SYS3 was not updated** for features #188–193 — SYS2→SYS3 forward traceability broken
5. SWE3 §8 **double-assigns SWE1-071** to two different units
