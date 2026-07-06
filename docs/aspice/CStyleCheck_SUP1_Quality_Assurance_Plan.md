# Quality Assurance Plan

*Automotive SPICE® PAM v4.0 | SUP.1 Quality Assurance*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CSC-SUP1-001 | **Version** | 1.9 |
| **Project** | CStyleCheck | **Date** | 2026-07-06 |
| **Status** | Released | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SUP.1 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.9 | 2026-07-06 | Claude | ASPICE audit — update quality objectives to v1.6.0 actuals — closes #379 |
| 1.8 | 2026-06-27 | Fix §3.1 cross-refs: SUP8 1.7→1.9, SWE4 1.14→1.17 | Dermot Murphy |
| 1.7 | 2026-06-26 | Claude | ASPICE audit — update §3.1 SWE4 ref (1.12→1.14) — closes #306 #329 |
| 1.6 | 2026-06-26 | Claude | Update §3 scope to v1.5.0 (minor release: F-017 misc.non_ascii_source, F-018 per-file summary, F-019 constant.case typedef exemption, B-004 RE_FUNCTION_DECL fix) |
| 1.5 | 2026-06-26 | Claude | §5.4: add per-release peer-review record production as a release gate checklist item; update §3 scope to v1.4.1 — closes issue #268 |
| 1.4 | 2026-06-18 | Claude | ASPICE audit #254 — sync referenced-document version citations to current versions |
| 1.3 | 2026-06-04 | Claude | Deep accuracy audit: fix §3 Purpose version text, update §3.1 referenced doc versions (all 5 stale), update QO-006 and §5.4 to v1.2.0, clarify §7 version language — resolves issue #163 |
| 1.2 | 2026-05-28 | Dermot Murphy | §4 QO-003/QO-004: document 85% combined CI gate as enforced threshold; 90% statement as aspirational target; align §5.4 checklist — closes issue #151 |
| 1.1 | 2026-05-28 | Claude | Reviewed and updated for v1.1.0 release; revision history maintained per ASPICE GP 2.2.4 |
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose & Scope

This Quality Assurance Plan defines the QA strategy, activities, criteria, and records for **CStyleCheck v1.5.0**. It satisfies **Automotive SPICE® PAM v4.0, SUP.1 — Quality Assurance**.

QA activities for CStyleCheck verify that project processes are followed as planned and that work products meet their defined quality criteria. Because CStyleCheck is itself a quality tool (a naming-convention linter), the project benefits from self-hosting its own quality checks.

### 3.1 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CSC-MAN3-001 | Project Management Plan | 1.6 |
| CSC-SUP8-001 | Configuration Management Plan | 1.9 |
| CSC-SUP9-001 | Problem Resolution Management Plan | 1.2 |
| CSC-SUP10-001 | Change Request Management Plan | 1.2 |
| CSC-SWE4-001 | Unit Verification Specification | 1.17 |

---

## 4. Quality Objectives

| QO-ID | Objective | Target | Measurement |
|---|---|---|---|
| QO-001 | All unit tests pass on all supported Python versions | 100% PASS on 3.10, 3.11, 3.12 | `cstylecheck_tests.yml` CI result |
| QO-002 | Source code naming conventions self-compliant | Zero error-level violations on `cstylecheck.py` | `rules.yml` CI result |
| QO-003 | Statement code coverage | ≥ 85% combined statement + branch (CI gate; `--cov-fail-under=85`); aspirational long-term target ≥ 90% statement (issue #54 — closed; v1.2.0 historical baseline: 89.8% statement, 87.31% combined; v1.6.0 CI measurement pending) | `pytest-cov` coverage report |
| QO-004 | Branch code coverage | ≥ 85% (combined with statement via `--cov-branch`; v1.2.0 historical baseline: 87.31% combined; v1.6.0 CI measurement pending) | `pytest-cov` coverage report |
| QO-005 | All ASPICE CL2 work products documented and reviewed | 100% of required WPs approved | Document review records |
| QO-006 | All GitHub Issues resolved before release | Zero open bug-labelled Issues at v1.6.0 tag | GitHub Issues board |
| QO-007 | All releases reproducible from baseline | Docker image digest recorded per release | GitHub Actions run log |

---

## 5. QA Activities

### 5.1 Process Audits

| Audit ID | Scope | Method | Frequency | Evidence |
|---|---|---|---|---|
| PA-01 | Git Flow branching compliance | Review branch names and merge targets in GitHub | Per milestone | GitHub network graph; PR merge records |
| PA-02 | Change control adherence | Verify all changes linked to a GitHub Issue | Per release | GitHub Issue/PR linkage |
| PA-03 | CM baseline consistency | Verify version in `_version.py` and `pyproject.toml` match release tag | Pre-release | Version file inspection + tag comparison |
| PA-04 | ASPICE document review records | Verify all WPs have reviewer/approver entries | Pre-assessment | Document approval tables |
| PA-05 | Test execution evidence | Verify CI run evidence exists for release commit | Pre-release | GitHub Actions run URL recorded in SWE.4, SWE.6 |

### 5.2 Work Product Quality Checks

| WP-ID | Work Product | Quality Criteria | Verification Method |
|---|---|---|---|
| WP-01 | `cstylecheck.py` | Zero naming violations; all tests pass; coverage ≥ targets | CI (automated) |
| WP-02 | Test suite | All tests pass; each test has clear assertion; test IDs traceable to requirements | Peer review; CI |
| WP-03 | `rules.yml` | Valid YAML; loads without error; each rule documented in README | CI parse check; inspection |
| WP-04 | `Dockerfile` | Builds successfully; image runs `--help`; both platforms available | CI `docker_publish.yml` |
| WP-05 | ASPICE documentation | All required sections present; traceability tables complete; no placeholder IDs in approved docs | Document review |
| WP-06 | `pyproject.toml` | Version matches `_version.py`; all required fields present | Inspection pre-release |
| WP-07 | GitHub Release notes | Covers all changes since previous release; baseline tag correct | Review pre-publication |

### 5.3 Automated QA Gates (CI Enforcement)

The following CI checks act as automated quality gates. Merging to `develop` or `main` is blocked if any gate fails:

| Gate ID | CI Workflow | Check | Branch |
|---|---|---|---|
| GATE-01 | `cstylecheck_tests.yml` | All pytest tests pass (Python 3.10, 3.11, 3.12) | `develop`, `main` |
| GATE-02 | `rules.yml` | `cstylecheck.py` passes its own naming rules (zero errors) | All branches touching `src/` |
| GATE-03 | `docker_publish.yml` | Docker image builds successfully | `main`, `v*.*.*` tags |

### 5.4 Pre-Release Quality Review Checklist

Performed by the QA role before creating the release baseline:

- [ ] All CI gates (GATE-01, GATE-02, GATE-03) pass on release commit
- [ ] Coverage gate met: combined ≥ 85% (`--cov-fail-under=85 --cov-branch`) per CI result
- [ ] All SWQ qualification test cases recorded as PASS in CSC-SWE6-001
- [ ] All SYS-VTC verification test cases recorded as PASS in CSC-SYS5-001
- [ ] Version in `_version.py` == version in `pyproject.toml` == intended release tag
- [ ] GitHub Release draft prepared with correct change log
- [ ] All ASPICE documents reviewed and approval tables signed
- [ ] Zero open GitHub Issues with `bug` label targeting the release version
- [ ] Docker image digest recorded in GitHub Actions log
- [ ] CM baseline checklist in CSC-SUP8-001 §11 completed
- [ ] **Peer-review record produced**: copy `CStyleCheck_Review_Template.md`, populate as `CStyleCheck_Review_Record_v<X.Y>.md`, commit to `docs/aspice/`, and reference from CSC-PA2-001 §5.4 (per CSC-REVIEW-TEMPLATE-001; ASPICE GP 2.2.3)

---

## 6. QA Records

All QA evidence is retained as follows:

| Record Type | Storage Location | Retention |
|---|---|---|
| CI test results (pytest) | GitHub Actions run logs | GitHub platform; 90-day default (configurable) |
| Coverage reports (`coverage.xml`) | GitHub Actions artefacts | 30 days per run |
| Docker image digests | GitHub Actions run logs + GHCR manifest | Indefinite (GHCR) |
| Process audit records | GitHub PR review comments; this document | Indefinite (GitHub) |
| Work product review records | Reviewer/approver tables in each ASPICE document | CM baseline (Git) |
| Problem reports | GitHub Issues | Indefinite |
| Change requests | GitHub Issues (labelled `change-request`) | Indefinite |

---

## 7. Non-Conformance Handling

When a QA gate failure or non-conformance is identified:

1. Raise a GitHub Issue with label `bug` (process violation) or `non-conformance` (QA process)
2. Assign to responsible party (Dermot Murphy / Claude)
3. Implement fix on `bugfix/<issue-id>-<description>` branch
4. Verify fix resolves the non-conformance (re-run affected CI gates)
5. Merge via pull request; close Issue with resolution comment
6. If non-conformance affects a released version: raise SUP.10 change request and plan patch release

---

## 8. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | Approved | 2026-06-27 |
| Technical Reviewer | Dermot Murphy | Approved | 2026-06-27 |
| Quality Assurance | Dermot Murphy | Approved | 2026-06-27 |
| Approver | Dermot Murphy | Approved | 2026-06-27 |

> **Note:** This document is under configuration management (SUP.8). Post-approval changes require a change request (SUP.10) and a new document version.
