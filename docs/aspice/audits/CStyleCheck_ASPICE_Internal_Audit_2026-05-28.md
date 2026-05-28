# CStyleCheck — ASPICE Internal Audit Report

*Automotive SPICE® PAM v4.0 · Capability Level 2 · Internal Audit*

---

## 1. Audit Identification

| Field | Value |
|---|---|
| **Audit ID** | CSC-AUD-001 |
| **Audit Title** | CStyleCheck v1.2 ASPICE CL2 Internal Audit |
| **Audit Date** | 2026-05-28 |
| **Auditor** | Claude (AI-assisted audit tool) — see CSC-DEV-001 |
| **Audit Owner** | Dermot Murphy |
| **Scope** | PA 2.1 (Process Performance Management) and PA 2.2 (Work Product Management) for all 17 assessed processes |
| **Baseline** | CStyleCheck develop branch @ 2026-05-28, post-PR #145 |
| **Reference Standard** | Automotive SPICE® PAM v4.0 |
| **Related Document** | CSC-PA2-001 v1.4 (updated as part of this audit) |

---

## 2. Audit Scope and Methodology

### 2.1 Processes Assessed

All 17 processes declared in CSC-PA2-001 were subject to this audit:

| # | Process | Primary Evidence Document |
|---|---|---|
| 1 | SYS.2 | CSC-SYS2-001 |
| 2 | SYS.3 | CSC-SYS3-001 |
| 3 | SYS.4 | CSC-SYS4-001 |
| 4 | SYS.5 | CSC-SYS5-001 |
| 5 | SWE.1 | CSC-SWE1-001 |
| 6 | SWE.2 | CSC-SWE2-001 |
| 7 | SWE.3 | CSC-SWE3-001 |
| 8 | SWE.4 | CSC-SWE4-001 |
| 9 | SWE.5 | CSC-SWE5-001 |
| 10 | SWE.6 | CSC-SWE6-001 |
| 11 | MAN.3 | CSC-MAN3-001 |
| 12 | MAN.5 | CSC-MAN5-001 |
| 13 | SUP.1 | CSC-SUP1-001 |
| 14 | SUP.8 | CSC-SUP8-001 |
| 15 | SUP.9 | CSC-SUP9-001 |
| 16 | SUP.10 | CSC-SUP10-001 |
| 17 | ACQ.4 | CSC-ACQ4-001 |

### 2.2 Artefacts Reviewed

The following artefacts were read and cross-checked during this audit:

- All 21 ASPICE process documents in `docs/aspice/`
- `src/cstylecheck/` package — all 10 source modules
- `src/rules.yml` and `tests/rules.yml`
- All 20 test files under `tests/test_*.py`
- `tests/harness.py`
- `.github/workflows/cstylecheck_tests.yml`
- `.github/workflows/cstylecheck_rules.yml`
- `.github/workflows/docker_publish.yml`
- `.github/workflows/wiki_publish.yml`
- `pyproject.toml`
- CI run evidence from GitHub Actions

### 2.3 Methodology

For each process the following questions were applied:

**PA 2.1 — Process Performance Management:**
- Are performance objectives defined and measurable? (GP 2.1.1)
- Is there a defined process strategy? (GP 2.1.2)
- Is the process planned, monitored, and adjusted? (GP 2.1.3–5)
- Are responsibilities defined? (GP 2.1.6)
- Are interfaces managed? (GP 2.1.7)

**PA 2.2 — Work Product Management:**
- Are work product requirements defined? (GP 2.2.1)
- Are work products stored and version-controlled? (GP 2.2.2)
- Are work products reviewed before approval? (GP 2.2.3)
- Are work products adjusted based on reviews? (GP 2.2.4)

Evidence gaps were classified using the ASPICE PAM v4.0 scale:

| Rating | Meaning | Achievement Range |
|---|---|---|
| **N** | Not achieved | 0–15% |
| **P** | Partially achieved | 15–50% |
| **L** | Largely achieved | 50–85% |
| **F** | Fully achieved | 85–100% |

### 2.4 Context and Baseline State

This audit reflects the project state **after** the following significant improvements since the prior Analysis Report (CSC-Analysis_Report.md, dated 2026-04-17):

| Improvement | Resolved Issues |
|---|---|
| Package refactor — `cstylecheck.py` → `src/cstylecheck/` | #65, PR #144 |
| `misc.comment_ratio` rule implemented and documented | #68, PR #140 |
| `misc.declared_not_defined` rule implemented and documented | #114, PR #141 |
| `misc.whitespace_ratio` rule implemented and tested | #143, PR #145 |
| CI subprocess coverage instrumented; gate raised to 85% combined | #54 |
| CI path trigger corrected for package layout | F-008, PR #145 |
| AI authorship deviation formalised | #52, CSC-DEV-001 |
| Independent-reviewer deviation formalised | #61, CSC-DEV-002 |

---

## 3. Findings

### 3.1 Summary Table

| Finding ID | ASPICE Finding | Severity | Processes Affected | Issue Raised |
|---|---|---|---|---|
| F-001 | SWE2/SYS3 still describe monolith — component descriptions stale after package refactor | High | SWE.2, SYS.3 | #146 |
| F-003 | SWE5 integration test results all placeholders — no execution evidence | High | SWE.5 | #152 |
| F-004 | SYS4 system integration test results blank — no evidence | High | SYS.4 | #152 |
| F-005 | CI gate 85% vs SUP1 documented target 90% statement coverage | Medium | SWE.4, SUP.1 | #151 |
| F-006 | SYS-NF-010/011/012 deferred with no tracking or resolution plan | Medium | SYS.2, SYS.5 | #153 |
| F-007 | SYS5 verification record execution placeholders not filled | Medium | SYS.5 | #152 |
| F-008 | CI path trigger stale — changes to `src/cstylecheck/**` did not trigger tests | High | SUP.8 | **Fixed in PR #145** |
| F-009 | `wiki_publish.yml` not registered in SUP8 CI inventory | Low | SUP.8 | #150 |
| F-010 | SWE1/SWE4 document `yoda_condition` (singular) — config key is `yoda_conditions` (plural) | Medium | SWE.1, SWE.4 | #149 |
| F-011 | MAN3 WBS-10 through WBS-16 have no planned or actual completion dates | Medium | MAN.3 | #154 |
| F-012 | PA2 §5.4 document version table stale | Low | PA 2.1/2.2 | #156 |
| F-013 | SWE4 §5.1 count (32) disagrees with §6 entries (35) for test_variables.py | Low | SWE.4 | #157 |
| F-014 | RISK-003 and RISK-005 have no concrete mitigation actions or owners | Medium | MAN.5, ACQ.4 | #155 |
| F-015 | SWE3 source locations still cite `cstylecheck.py:NNN` for all 89 units | High | SWE.3 | #147 |
| F-017 | SWE1/SWE3/SWE4 have no entries for `misc.whitespace_ratio` rule | High | SWE.1, SWE.3, SWE.4 | #148 |

> **Note — F-002 and F-016 from the gap analysis are not recorded as findings:**
> - F-002: `comment_ratio` and `declared_not_defined` are fully documented in SWE1/SWE3/SWE4; only `whitespace_ratio` is missing (captured as F-017).
> - F-016: `pyproject.toml` correctly uses `packages = ["cstylecheck"]` with `package-dir = {"" = "src"}` — no issue.

### 3.2 Resolved Items (from prior Analysis Report)

The following critical findings from the prior Analysis Report are **confirmed resolved** at this audit date:

| Prior Finding | Resolution | Evidence |
|---|---|---|
| AI author listed in role-holder fields (GP 2.1.6) | Formalised as CSC-DEV-001 deviation | `docs/aspice/CStyleCheck_DEV001_AI_Authorship_Deviation.md` |
| Reviewer = Approver independence gap (GP 2.2.3) | Formalised as CSC-DEV-002 deviation | `docs/aspice/CStyleCheck_DEV002_Independent_Review_Deviation.md` |
| CI gate 72% vs 90% target (critical contradiction) | Gate raised to 85% combined; subprocess coverage wired | CI workflow; issue #54 closed |
| `\|\| true` silently swallowing exit code 2 (config error) | Exit code 2 handled explicitly in workflow | `cstylecheck_rules.yml` CSC_EXIT check |
| Concurrency control: parallel runs corrupt `trend.jsonl` | Concurrency group added to workflows | `cstylecheck_rules.yml` concurrency stanza |
| Docker path trigger references wrong filename | Fixed — trigger now watches `src/rules.yml` | `docker_publish.yml` |
| Single monolithic 3,637-line `cstylecheck.py` | Refactored into 10-module package | PR #144; `src/cstylecheck/` |
| `datetime.utcnow()` deprecated in Python 3.12 | Updated to timezone-aware call | `cstylecheck_rules.yml` |
| CI path trigger stale post-refactor (F-008) | Fixed: added `src/cstylecheck/**` to paths; mypy targets package | PR #145 |

---

## 4. Process-by-Process Assessment

### 4.1 SYS.2 — System Requirements Analysis

| | Detail |
|---|---|
| **PA 1.1 Evidence** | CSC-SYS2-001: 40+ system requirements defined, categorised (functional/non-functional/interface), traceable to SYS.3 |
| **PA 2.1 Evidence** | Performance objective defined (§4.1); strategy defined (V-model lifecycle, MAN3 §5); requirements reviewed |
| **PA 2.2 Evidence** | Document versioned and in CM; reviewed and approved |
| **Open Gaps** | F-006: SYS-NF-010/011/012 deferred with no GitHub issue, target version, or decision record (issue #153) |
| **Rating** | **L** — largely achieved; open gap on deferred requirement tracking |

### 4.2 SYS.3 — System Architecture Design

| | Detail |
|---|---|
| **PA 1.1 Evidence** | CSC-SYS3-001: 6 subsystems defined, interfaces documented, deployment view provided |
| **PA 2.1 Evidence** | Objectives defined; architecture traceability matrix references SYS.2 |
| **PA 2.2 Evidence** | Document versioned and in CM; reviewed and approved |
| **Open Gaps** | F-001: Document still describes single-file monolith — subsystem implementation column lists `cstylecheck.py` throughout (issue #146) |
| **Rating** | **L** — largely achieved; architectural description does not match deployed implementation |

### 4.3 SYS.4 — System Integration Test

| | Detail |
|---|---|
| **PA 1.1 Evidence** | CSC-SYS4-001: 14 system integration test cases (SITC-001 to SITC-014) defined |
| **PA 2.1 Evidence** | Performance objectives defined; test criteria specified |
| **PA 2.2 Evidence** | Document version-controlled; test specification reviewed |
| **Open Gaps** | F-004: §5 Results table completely blank — no execution evidence for any of the 14 test cases (issue #152) |
| **Rating** | **P** — partially achieved; test cases defined but zero execution evidence recorded |

### 4.4 SYS.5 — System Qualification Test

| | Detail |
|---|---|
| **PA 1.1 Evidence** | CSC-SYS5-001: system-level verification test cases defined |
| **PA 2.1 Evidence** | Objectives defined; criteria specified |
| **PA 2.2 Evidence** | Document version-controlled |
| **Open Gaps** | F-007: Commit SHA, Docker digest, test date, and tester all show `<fill at execution>` placeholder (issue #152); F-006: deferred requirements have no disposition (issue #153) |
| **Rating** | **P** — partially achieved; no objective execution evidence; deferred requirements undispositioned |

### 4.5 SWE.1 — Software Requirements Analysis

| | Detail |
|---|---|
| **PA 1.1 Evidence** | CSC-SWE1-001: 70+ software requirements defined across all implemented rule groups, traceable to SYS.2 |
| **PA 2.1 Evidence** | Objectives defined; requirements reviewed; traceability matrix provided |
| **PA 2.2 Evidence** | Document versioned; CM-controlled; reviewed and approved |
| **Open Gaps** | F-017: No requirements for `misc.whitespace_ratio` rule (issue #148); F-010: `yoda_condition` singular vs `yoda_conditions` plural naming inconsistency (issue #149) |
| **Rating** | **L** — largely achieved; minor requirements gap for newest rule; naming inconsistency in docs |

### 4.6 SWE.2 — Software Architecture Design

| | Detail |
|---|---|
| **PA 1.1 Evidence** | CSC-SWE2-001: 7 components (COMP-01 to COMP-07) defined with sub-components, interfaces, and function-level mapping |
| **PA 2.1 Evidence** | Objectives defined; component traceability to SWE.1 documented |
| **PA 2.2 Evidence** | Document versioned and in CM; reviewed and approved |
| **Open Gaps** | F-001: §3 states "single Python module (`cstylecheck.py`)" — no reference to package structure (issue #146). Component descriptions use function names (accurate) but file references remain `cstylecheck.py` |
| **Rating** | **L** — largely achieved; function-level content is accurate; file-level description is stale |

### 4.7 SWE.3 — Software Detailed Design

| | Detail |
|---|---|
| **PA 1.1 Evidence** | CSC-SWE3-001 v1.2: 89 units catalogued with inputs, outputs, and algorithmic specifications; package structure documented in §4.1 |
| **PA 2.1 Evidence** | Objectives defined; design-to-requirement traceability matrix provided |
| **PA 2.2 Evidence** | Document versioned (v1.2); CM-controlled; reviewed |
| **Open Gaps** | F-015: Source Location column for all 89 units cites `cstylecheck.py:NNN` — file no longer exists at that path (issue #147); F-017: No UNIT entry for `_check_whitespace_ratio` (issue #148) |
| **Rating** | **L** — largely achieved; design content complete; source location traceability broken post-refactor |

### 4.8 SWE.4 — Software Unit Verification

| | Detail |
|---|---|
| **PA 1.1 Evidence** | 839 unit tests across 20 test files; all pass on Python 3.10/3.11/3.12; 85% combined coverage enforced by CI gate; self-testing CI run |
| **PA 2.1 Evidence** | Performance objectives defined (§4.2 coverage criteria); CI provides monitoring evidence |
| **PA 2.2 Evidence** | CSC-SWE4-001 test catalogue; all tests in CM; CI run records constitute execution evidence |
| **Open Gaps** | F-005: CI gate 85% combined vs 90% statement target in SUP1 (issue #151); F-017: No test catalogue entries for `test_whitespace_ratio.py` (issue #148); F-013: §5.1 count 32 vs §6 count 35 for `test_variables.py` (issue #157); F-010: naming inconsistency (issue #149) |
| **Rating** | **L** — largely achieved; CI verification evidence strong; documentation has minor gaps |

### 4.9 SWE.5 — Software Integration Verification

| | Detail |
|---|---|
| **PA 1.1 Evidence** | CSC-SWE5-001: 13 integration test cases (SIT-001 to SIT-013) defined covering all SWA interfaces |
| **PA 2.1 Evidence** | Performance objectives defined; integration strategy documented |
| **PA 2.2 Evidence** | Document versioned and CM-controlled |
| **Open Gaps** | F-003: §5 Results table shows `<PASS/FAIL>` for all 13 tests; §6 Coverage shows `<fill from coverage.xml>` — no execution evidence recorded (issue #152) |
| **Rating** | **P** — partially achieved; test cases well-defined; zero execution evidence |

### 4.10 SWE.6 — Software Qualification Test

| | Detail |
|---|---|
| **PA 1.1 Evidence** | CSC-SWE6-001: 12 SWQ test cases; CI pipeline constitutes the qualification test execution environment; 839 tests pass consistently |
| **PA 2.1 Evidence** | Qualification criteria defined; CI run results provide monitoring evidence |
| **PA 2.2 Evidence** | Document versioned; CI artefacts stored per SUP8 retention policy |
| **Open Gaps** | F-005: CI gate 85% vs SUP1 90% statement target (issue #151); F-003: SWE6 §6 coverage section not populated from `coverage.xml` (issue #152) |
| **Rating** | **L** — largely achieved; CI execution strong; formal coverage record not completed |

### 4.11 MAN.3 — Project Management

| | Detail |
|---|---|
| **PA 1.1 Evidence** | CSC-MAN3-001: WBS, lifecycle phases, milestones, effort estimates defined; GitHub Issues used for tracking |
| **PA 2.1 Evidence** | Objectives, strategy, and monitoring mechanisms defined; CI badge provides continuous monitoring |
| **PA 2.2 Evidence** | Document versioned; reviewed and approved |
| **Open Gaps** | F-011: WBS-10 through WBS-16 all show "In Progress" with no planned or actual completion dates (issue #154) |
| **Rating** | **L** — largely achieved; project actively managed; schedule baseline incomplete |

### 4.12 MAN.5 — Risk Management

| | Detail |
|---|---|
| **PA 1.1 Evidence** | CSC-MAN5-001: 8 risks identified, scored (Likelihood × Impact), and assigned treatment strategies |
| **PA 2.1 Evidence** | Risk management objectives defined; monitoring schedule described |
| **PA 2.2 Evidence** | Document versioned and CM-controlled |
| **Open Gaps** | F-014: RISK-003 (PyYAML supply chain) and RISK-005 (bus factor) have generic mitigation text with no owner, due date, or tracking artefact (issue #155) |
| **Rating** | **L** — largely achieved; risks identified and scored; two risk mitigations not actionable |

### 4.13 SUP.1 — Quality Assurance

| | Detail |
|---|---|
| **PA 1.1 Evidence** | CSC-SUP1-001: QA objectives, CI quality gates, and pre-release checklist defined; CI enforces GATE-01 (naming violations), GATE-02 (coverage), GATE-03 (ruff lint) |
| **PA 2.1 Evidence** | QA objectives measurable; CI provides continuous monitoring |
| **PA 2.2 Evidence** | Document versioned; CI run artefacts retained per §4.3 |
| **Open Gaps** | F-005: `--cov-fail-under=85` (CI) vs ≥90% statement (SUP1 §4.2 QO-003) inconsistency (issue #151) |
| **Rating** | **L** — largely achieved; QA activities executed; documented quality gate not fully enforced |

### 4.14 SUP.8 — Configuration Management

| | Detail |
|---|---|
| **PA 1.1 Evidence** | CSC-SUP8-001: 29 CIs inventoried; Git Flow branching; annotated release tags; dual-registry Docker images |
| **PA 2.1 Evidence** | CM objectives and monitoring defined; Git provides immutable audit trail |
| **PA 2.2 Evidence** | Document versioned; all CIs in version control |
| **Open Gaps** | F-009: `wiki_publish.yml` not in CI inventory (issue #150); F-008 (stale CI path trigger) **FIXED** in PR #145 |
| **Rating** | **L** — largely achieved; one missing CI registration; CI trigger fix applied |

### 4.15 SUP.9 — Problem Resolution

| | Detail |
|---|---|
| **PA 1.1 Evidence** | CSC-SUP9-001: problem resolution procedure with SLA targets; GitHub Issues used as problem register; regression tests required for SEV-1/2 |
| **PA 2.1 Evidence** | Objectives and SLAs defined; Issue metrics available via GitHub |
| **PA 2.2 Evidence** | Document versioned; problem records (Issues) stored in CM |
| **Open Gaps** | DEV-002: Reviewer = Approver on all work products limits GP 2.2.3 independence (formally accepted deviation) |
| **Rating** | **L** — largely achieved; DEV-002 independence deviation limits rating to L |

### 4.16 SUP.10 — Change Request Management

| | Detail |
|---|---|
| **PA 1.1 Evidence** | CSC-SUP10-001: CR process with impact levels, approval thresholds, and implementation gate; GitHub Issues with CR template used consistently for all changes |
| **PA 2.1 Evidence** | CR cycle time tracked; process followed for all 17+ CRs executed in this project |
| **PA 2.2 Evidence** | Document versioned; CR records (Issues + PRs) in CM with full audit trail |
| **Open Gaps** | DEV-002: same-person reviewer/approver (formally accepted deviation) |
| **Rating** | **L** — largely achieved; process is well-defined and consistently practised; DEV-002 limits to L |

### 4.17 ACQ.4 — Supplier Monitoring

| | Detail |
|---|---|
| **PA 1.1 Evidence** | CSC-ACQ4-001: 5 suppliers monitored (Python, PyYAML, GitHub Actions, Docker, Claude AI); acceptance criteria per supplier; monitoring schedule defined |
| **PA 2.1 Evidence** | Monitoring objectives defined; Claude AI usage tracked via DEV-001 deviation |
| **PA 2.2 Evidence** | Document versioned and CM-controlled |
| **Open Gaps** | F-014 (partial): RISK-003 PyYAML supply chain risk lacks concrete mitigation — Dependabot not enabled (issue #155) |
| **Rating** | **L** — largely achieved; supplier list complete; one supplier risk mitigation actionable |

---

## 5. CL2 Achievement Summary

### 5.1 Process Rating Table

| Process | PA 1.1 | PA 2.1 | PA 2.2 | **CL2 Rating** | Open Issues |
|---|---|---|---|---|---|
| SYS.2 | F | L | L | **L** | #153 |
| SYS.3 | F | L | L | **L** | #146 |
| SYS.4 | L | P | P | **P** | #152 |
| SYS.5 | L | P | P | **P** | #152, #153 |
| SWE.1 | F | L | L | **L** | #148, #149 |
| SWE.2 | F | L | L | **L** | #146 |
| SWE.3 | F | L | L | **L** | #147, #148 |
| SWE.4 | F | L | L | **L** | #148, #149, #151, #157 |
| SWE.5 | L | P | P | **P** | #152 |
| SWE.6 | F | L | L | **L** | #151, #152 |
| MAN.3 | F | L | L | **L** | #154 |
| MAN.5 | F | L | L | **L** | #155 |
| SUP.1 | F | L | L | **L** | #151 |
| SUP.8 | F | L | L | **L** | #150 |
| SUP.9 | F | L | L | **L** | DEV-002 |
| SUP.10 | F | L | L | **L** | DEV-002 |
| ACQ.4 | F | L | L | **L** | #155 |

### 5.2 Overall CL2 Verdict

> **ASPICE CL2 is NOT YET achieved. Overall verdict: Largely Achieved.**

Fourteen of seventeen processes achieve **L** (Largely Achieved) at both PA 2.1 and PA 2.2. Three processes — SYS.4, SYS.5, and SWE.5 — achieve only **P** (Partially Achieved) due to the absence of recorded test execution evidence.

**ASPICE CL2 requires all assessed processes to achieve L or F at PA 2.1 and PA 2.2.** The three P-rated processes block CL2 award until issue #152 (test execution evidence) is closed.

### 5.3 Path to CL2

| Priority | Action Required | Issue | Blocks |
|---|---|---|---|
| 🔴 **Must close** | Record SIT-001 to SIT-013 execution results (SWE.5) | #152 | SWE.5 → P to L |
| 🔴 **Must close** | Record SITC-001 to SITC-014 execution results (SYS.4) | #152 | SYS.4 → P to L |
| 🔴 **Must close** | Record SYS-VTC execution evidence with Commit SHA, date, tester (SYS.5) | #152 | SYS.5 → P to L |
| 🟡 **Should close** | SWE2/SYS3 architecture docs updated for package structure | #146 | SWE.2/SYS.3 → L (quality) |
| 🟡 **Should close** | SWE3 source location column updated (all 89 units) | #147 | SWE.3 → L (quality) |
| 🟡 **Should close** | SWE1/SWE3/SWE4 entries for `misc.whitespace_ratio` | #148 | SWE.1/3/4 → L (quality) |
| 🟡 **Should close** | Deferred requirements NF-010/011/012 tracked or decisioned | #153 | SYS.2/5 → L (quality) |
| 🔵 **Nice to close** | Coverage gate aligned with SUP1 90% target | #151 | SUP.1/SWE.4/SWE.6 |
| 🔵 **Nice to close** | MAN3 WBS completion dates | #154 | MAN.3 |
| 🔵 **Nice to close** | Risk mitigations for RISK-003/005 | #155 | MAN.5/ACQ.4 |
| 🔵 **Nice to close** | PA2 version table, SWE4 count, wiki_publish CI item | #150, #156, #157 | Housekeeping |

---

## 6. Observations

### OBS-001 — Significant Maturity Improvement Since Prior Audit

The prior Analysis Report (2026-04-17) identified 6 critical and 10 warning-level findings. This audit confirms that all 6 critical findings and 8 of the 10 warnings are **resolved**. The project has progressed from a state where fundamental ASPICE infrastructure was missing to a state where all 17 processes are at least Partially achieved and 14 are Largely achieved. This represents a significant maturity improvement in a short timeframe.

### OBS-002 — Test Evidence is the Primary Blocker for CL2

The sole reason CL2 is not awarded is the absence of recorded test execution evidence in SWE5, SYS4, and SYS5. The tests themselves are either well-defined (SIT-001 to SIT-013) or covered by CI. The gap is administrative — results need to be recorded in the document tables. Issue #152 is the single most impactful open action for CL2 achievement.

### OBS-003 — DEV-002 Limits All Processes to L

Because Reviewer = Approver on all work products (accepted via CSC-DEV-002), GP 2.2.3 independence is not fully demonstrated for any process. This prevents any process from being rated F. Processes that would otherwise be F under independent review (SUP.10, SUP.9, ACQ.4) are capped at L. This is a structural constraint of the single-developer project model that cannot be resolved without adding a second team member.

### OBS-004 — Package Refactor Traceability Gap

The package refactor (issue #65, PR #144) was a significant architectural change that was not fully propagated into the ASPICE documentation. Issues #146 (SWE2/SYS3) and #147 (SWE3 source locations) are direct consequences. Future major refactors should include documentation updates as acceptance criteria in the CR before the PR is merged.

### OBS-005 — New Rules Need Documentation Before Implementation Merge

Three rules (comment_ratio, declared_not_defined, whitespace_ratio) were implemented before their ASPICE documentation was updated. While the implementation is correct, the ASPICE traceability chain (SWE1 → SWE3 → SWE4) should be updated as part of the same PR that implements the rule. Issue #148 captures the whitespace_ratio gap; the prior two rules' documentation was added retrospectively.

---

## 7. Audit Actions

All findings have been converted to GitHub issues for tracking:

| Issue | Finding | Title | Target |
|---|---|---|---|
| #146 | F-001 | SWE2/SYS3: architecture documents describe monolith | v1.3.0 |
| #147 | F-015 | SWE3: source location columns reference stale cstylecheck.py:NNN | v1.3.0 |
| #148 | F-017 | SWE1/SWE3/SWE4: add documentation for misc.whitespace_ratio | v1.3.0 |
| #149 | F-010 | SWE1/SWE4: yoda_conditions config key inconsistency | v1.3.0 |
| #150 | F-009 | SUP8: wiki_publish.yml not registered as CI item | v1.3.0 |
| #151 | F-005 | SUP1: CI coverage gate below documented target | v1.3.0 |
| #152 | F-003/004/007 | SWE5/SYS4/SYS5: test execution evidence placeholders | v1.3.0 |
| #153 | F-006 | SYS2: deferred requirements NF-010/011/012 need tracking | v1.3.0 |
| #154 | F-011 | MAN3: WBS milestone completion dates missing | v1.3.0 |
| #155 | F-014 | MAN5: RISK-003 and RISK-005 mitigation actions | v1.3.0 |
| #156 | F-012 | PA2: document version table stale | v1.3.0 |
| #157 | F-013 | SWE4: §5.1 vs §6 test count inconsistency | v1.3.0 |

**Closed during this audit:** F-008 (CI path trigger stale) — fixed in PR #145, committed `a36e77e`.

---

## 8. Approval

| Role | Name | Approval | Date |
|---|---|---|---|
| Auditor | Claude (AI-assisted) | Completed | 2026-05-28 |
| Audit Owner / Approver | Dermot Murphy | Pending review | 2026-05-28 |

> This audit report is placed under configuration management as `docs/aspice/audits/CStyleCheck_ASPICE_Internal_Audit_2026-05-28.md`. It constitutes the Audit Findings Log deliverable required by issue #136 (CSC-SUP10-001 §7 deliverable).
