# Project Management Plan

*Automotive SPICE® PAM v4.0 | MAN.3 Project Management*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CNC-MAN3-001 | **Version** | 1.0 |
| **Project** | CStyleCheck | **Date** | 2026-04-12 |
| **Status** | Draft | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | MAN.3 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose & Scope

This Project Management Plan (PMP) defines the project scope, lifecycle, work breakdown, resources, schedule, interfaces, and monitoring approach for **CStyleCheck v1.0.0**. It satisfies **Automotive SPICE® PAM v4.0, MAN.3 — Project Management**.

### 3.1 Project Overview

| Attribute | Value |
|---|---|
| **Product** | CStyleCheck — Embedded C naming-convention linter |
| **Version** | 1.0.0 |
| **Repository** | `https://github.com/dermot-murphy/CStyleCheck` |
| **Language** | Python 3.10–3.12 |
| **Deployment** | CLI, pip/pipx, Docker (GHCR + Docker Hub), GitHub Action, pre-commit |
| **Standards** | Barr-C:2018, MISRA-C complementary, Automotive SPICE® PAM v4.0 |
| **Licence** | MIT |

### 3.2 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CNC-SYS2-001 | System Requirements Specification | 1.0 |
| CNC-SWE1-001 | Software Requirements Specification | 1.0 |
| CNC-SUP8-001 | Configuration Management Plan | 1.1 |
| CNC-MAN5-001 | Risk Management Plan | 1.0 |
| CNC-SUP1-001 | Quality Assurance Plan | 1.0 |

---

## 4. Project Scope and Objectives

### 4.1 In Scope

- Design, implementation, and testing of `cstylecheck.py` (≈2,800 lines) implementing 48 rule IDs
- Test suite (≥500 pytest tests across 20+ test modules)
- Docker image build and multi-platform publication to GHCR and Docker Hub
- GitHub Action integration (`action.yml`)
- pre-commit hook integration (`.pre-commit-hooks.yaml`)
- pip/pipx packaging (`pyproject.toml`)
- Full ASPICE CL2 documentation set (SYS.2–SYS.5, SWE.1–SWE.6, MAN.3, MAN.5, SUP.1, SUP.8–SUP.10, ACQ.4, PA 2.1, PA 2.2)
- CI/CD automation via GitHub Actions (3 workflows)

### 4.2 Out of Scope

- GUI or IDE plugin
- C++ language support beyond C/C++ keyword detection
- Hardware engineering or mechanical engineering processes
- Machine learning engineering processes

### 4.3 Feasibility Assessment

| Constraint | Assessment |
|---|---|
| **Technical** | Python-only implementation; single-file architecture; no exotic dependencies. Technically feasible with one engineer |
| **Schedule** | v1.0.0 development complete; documentation phase in progress |
| **Resources** | Solo developer; GitHub Actions for CI/CD (zero compute cost for public repo) |
| **Standards compliance** | ASPICE CL2 documentation producible; naming convention self-check demonstrable |

---

## 5. Project Lifecycle

CStyleCheck follows a **Git Flow** based lifecycle aligned with the V-model:

```
Requirements  →  Architecture  →  Detailed Design  →  Implementation
    (SYS.2/SWE.1)   (SYS.3/SWE.2)     (SWE.3)            (SWE.3 BP8)
         ↑                                                       ↓
  System Verification  ←  SW Qualification  ←  SW Integration  ←  Unit Verification
      (SYS.5)               (SWE.6)              (SWE.5)           (SWE.4)
```

### 5.1 Project Phases

| Phase ID | Phase Name | Deliverables | Entry Criteria | Exit Criteria |
|---|---|---|---|---|
| PH-01 | Requirements | SYS.2, SWE.1 | Project initiated | Requirements reviewed and approved |
| PH-02 | Architecture | SYS.3, SWE.2 | Requirements approved | Architecture reviewed and approved |
| PH-03 | Detailed Design | SWE.3 | Architecture approved | Design reviewed and approved |
| PH-04 | Implementation | `cstylecheck.py` v1.0.0, test suite | Design approved | All unit tests pass (SWE.4) |
| PH-05 | Integration & Verification | SWE.5, SWE.6, SYS.4, SYS.5 | Unit tests pass | All qualification tests pass |
| PH-06 | Release | v1.0.0 tag, GHCR image, GitHub Release | All tests pass; docs approved | Release baseline created (SPL.2) |
| PH-07 | Documentation | Full ASPICE CL2 doc set | Release complete | All documents approved |

---

## 6. Work Breakdown Structure

| WBS-ID | Work Package | Estimated Effort | Responsible | Status |
|---|---|---|---|---|
| WBS-01 | System requirements (SYS.2) | 4h | Claude | Complete |
| WBS-02 | System architecture (SYS.3) | 4h | Claude | Complete |
| WBS-03 | Software requirements (SWE.1) | 8h | Claude | Complete |
| WBS-04 | Software architecture (SWE.2) | 6h | Claude | Complete |
| WBS-05 | Detailed design (SWE.3) | 8h | Claude | Complete |
| WBS-06 | Core linter implementation | 80h | Claude | Complete |
| WBS-07 | Test suite (500+ tests) | 40h | Claude | Complete |
| WBS-08 | Docker packaging and CI | 8h | Claude | Complete |
| WBS-09 | GitHub Action and pre-commit | 6h | Claude | Complete |
| WBS-10 | Unit verification (SWE.4) | 4h | Claude | In Progress |
| WBS-11 | Integration testing (SWE.5) | 4h | Claude | In Progress |
| WBS-12 | Qualification testing (SWE.6) | 4h | Claude | In Progress |
| WBS-13 | System integration testing (SYS.4) | 4h | Claude | In Progress |
| WBS-14 | System verification (SYS.5) | 4h | Claude | In Progress |
| WBS-15 | Management documents (MAN.3, MAN.5) | 4h | Claude | In Progress |
| WBS-16 | Support documents (SUP.1, SUP.9, SUP.10, ACQ.4) | 6h | Claude | In Progress |
| WBS-17 | Release (v1.0.0 tag, GitHub Release) | 2h | Claude | Planned |

---

## 7. Resource Plan

| Resource | Type | Allocation |
|---|---|---|
| Claude | Engineer (sole developer) | 100% |
| GitHub Actions | CI/CD infrastructure | On-demand; zero cost (public repo) |
| GHCR | Container registry | Free tier |
| Docker Hub | Container registry | Free tier |
| GitHub Issues | Change/problem tracking | Included in GitHub |
| `pytest` / `pytest-cov` | Test tooling | Open source |

---

## 8. Project Schedule

| Milestone | Target Date | Status | Actual Date |
|---|---|---|---|
| Core linter v1.0.0 implementation complete | 2026-04-11 | ✅ Complete | 2026-04-11 |
| Test suite ≥500 tests all passing | 2026-04-11 | ✅ Complete | 2026-04-11 |
| Docker image published to GHCR | 2026-04-11 | ✅ Complete | 2026-04-11 |
| SYS.2–SYS.5 documentation complete | 2026-04-12 | ✅ Complete | 2026-04-12 |
| SWE.1–SWE.6 documentation complete | 2026-04-12 | ✅ Complete | 2026-04-12 |
| Remaining ASPICE CL2 documents complete | 2026-04-12 | 🔄 In Progress | |
| All documents reviewed and approved | \<TBD\> | Planned | |
| v1.0.0 release baseline created | \<TBD\> | Planned | |

---

## 9. Project Interfaces

| Interface | Counterpart | Type | Communication Method | Frequency |
|---|---|---|---|---|
| INT-01 | End users (embedded C developers) | External | GitHub README, GitHub Releases, Docker Hub | On release |
| INT-02 | CI/CD system (GitHub Actions) | Internal tool | `push` / `pull_request` event triggers | Per commit/PR |
| INT-03 | Container registries (GHCR, Docker Hub) | External service | Automated push via `docker_publish.yml` | On release tag |
| INT-04 | pre-commit framework | External tool | `.pre-commit-hooks.yaml` | On user install |
| INT-05 | GitHub Marketplace | External platform | `action.yml` + release tag | On publish |
| INT-06 | Assessor / auditor | External | ASPICE documentation set | On assessment |

---

## 10. Progress Monitoring and Reporting

### 10.1 Monitoring Approach

| Activity | Method | Frequency |
|---|---|---|
| Build and test status | GitHub Actions CI badge on README | Continuous (per commit) |
| Test pass rate | `cstylecheck_tests.yml` — pytest result matrix | Per commit to `develop`/`main` |
| Naming convention compliance | `cstylecheck_rules.yml` CI job | Per commit touching `src/` |
| Code coverage | `pytest-cov` — `coverage.xml` artefact | Per CI run on Python 3.11 |
| Open Issues (bugs/changes) | GitHub Issues board | Reviewed weekly |
| WBS progress | Manual update to this document | Per milestone |
| Risk status | Risk register (CNC-MAN5-001) | Monthly or on new risk identified |

### 10.2 Corrective Action Triggers

| Trigger | Action |
|---|---|
| CI test failure on `develop` or `main` | Raise GitHub Issue; fix on `bugfix/` branch before next merge |
| Coverage drop below target threshold | Raise Issue; add missing tests before next release |
| Naming convention CI failure on own source | Raise Issue; fix in same commit; never merge failing source |
| Milestone slipped by >1 week | Update schedule; assess risk impact; update CNC-MAN5-001 |
| New risk identified | Add to risk register (CNC-MAN5-001); assign treatment |

---

## 11. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | | 2026-04-12 |
| Technical Reviewer | \<Name\> | | |
| Quality Assurance | \<Name\> | | |
| Approver | \<Name\> | | |

> **⚠️ Important:** This plan must be approved before the project enters Phase PH-06 (Release). Any changes to scope, schedule, or resources require a change request (SUP.10) and a revised version of this document.
