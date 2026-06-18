# Process Capability Records

*Automotive SPICE® PAM v4.0 | PA 2.1 Process Performance Management & PA 2.2 Work Product Management*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CSC-PA2-001 | **Version** | 1.10 |
| **Project** | CStyleCheck | **Date** | 2026-06-18 |
| **Status** | Released | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | PA 2.1, PA 2.2 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.10 | 2026-06-18 | Claude | CSC-AUD-007 — §6 was stale since 2026-05-28 (predated issue #152 closure and superseding audit CSC-AUD-002); resync §6 ratings/verdict to current `main` (v1.4.0); CL2 confirmed ACHIEVED; add §5.4 rows for CSC-AUD-002/CSC-AUD-007 |
| 1.9 | 2026-06-18 | Claude | ASPICE audit #254 — update §4.1/§5.4/§6 SWE.4 test count 965→1152; mark CI-017 released at v1.3.0 |
| 1.8 | 2026-06-04 | Claude | Deep accuracy audit: fix §4.1 SWE.3 unit count (46→90), SUP.8 CI count (27→34), §6 SWE.3 (89→90) and SUP.8 (29→34); update §5.4 document version table — resolves issue #163 |
| 1.7 | 2026-06-04 | Claude | Automated accuracy audit: update §4.1 SWE.4 test count ≥500→965, §5.2 SWE.4 839→965, §5.4 CI-017 839→965 and SUP9/10/ACQ4 versions, §6 SWE.4 839→965 — resolves issue #163 |
| 1.6 | 2026-05-29 | Claude | §5.4: mark all work products Released at v1.2.0 tag; update SVD to 1.2, PA2 to 1.6, AUD-001 to Released |
| 1.5 | 2026-05-28 | Dermot Murphy | §5.4: update all document version numbers to reflect issues #146–#157 changes — closes issue #156 |
| 1.4 | 2026-05-28 | Claude / Dermot Murphy | Internal audit CSC-AUD-001: populate §6 Assessment Verdicts for all 17 processes (N/P/L/F); update §5.4 document version table to current versions; add audit report reference — closes issue #136 |
| 1.3 | 2026-05-28 | Dermot Murphy | Update SWE.4 performance objective: subprocess coverage instrumented, gate 85% combined; actual 87.31% combined / 89.8% stmt — closes issue #54 |
| 1.2 | 2026-05-28 | Dermot Murphy | Add CSC-DEV-002 deviation reference at GP 2.2.3; add CI-028 (SVD) and CI-029 (DEV-002) to §5.4 — closes issue #61 |
| 1.1 | 2026-05-28 | Dermot Murphy | Add deviation reference at GP 2.1.6 — closes issue #52 |
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose

This document records the generic practices evidence for **Automotive SPICE® PAM v4.0 Capability Level 2** across all assessed processes. It provides a single consolidated reference for assessors to verify PA 2.1 (Process Performance Management) and PA 2.2 (Work Product Management) achievement for CStyleCheck v1.2.x.

**PA 2.1** requires that each process is planned, monitored, and adjusted.
**PA 2.2** requires that work products are defined, stored, controlled, reviewed, and adjusted.

---

## 4. PA 2.1 — Process Performance Management

### 4.1 GP 2.1.1 — Define Process Performance Objectives

For each assessed process, performance objectives are defined in the table below.

| Process | Performance Objective | Defined In | Status |
|---|---|---|---|
| SYS.2 | System requirements complete, reviewed, and approved before architecture begins | CSC-MAN3-001 §5.1 (PH-01 exit criteria) | ✅ Defined |
| SYS.3 | Architecture reviewed and approved; all SYS.2 requirements traced to architecture elements | CSC-SYS3-001 §9 traceability matrix | ✅ Defined |
| SYS.4 | All 14 SITC integration test cases PASS before SYS.5 begins | CSC-SYS4-001 §5 verification criteria | ✅ Defined |
| SYS.5 | All SYS-VTC test cases PASS; 100% requirements coverage; no open critical Issues | CSC-SYS5-001 §3.4 verification criteria | ✅ Defined |
| SWE.1 | 70 software requirements defined, reviewed, approved; 100% traceable to SYS.2 | CSC-SWE1-001 §4.15 verification criteria | ✅ Defined |
| SWE.2 | Architecture reviewed; all SWE.1 requirements mapped to components; interfaces defined | CSC-SWE2-001 §10 traceability | ✅ Defined |
| SWE.3 | All 90 units designed; algorithmic specification complete; resource usage documented | CSC-SWE3-001 §4 unit catalogue | ✅ Defined |
| SWE.4 | ≥ 85% combined statement + branch coverage (CI gate); ≥ 90% statement / ≥ 85% branch (long-term target); all 1152 unit tests PASS on Python 3.10/11/12 | CSC-SWE4-001 §4.2 coverage criteria | ✅ Defined |
| SWE.5 | All 13 SIT integration test cases PASS; all 10 SWA interfaces covered | CSC-SWE5-001 §3.3 verification criteria | ✅ Defined |
| SWE.6 | All 12 SWQ qualification test cases PASS; 100% SW requirements coverage; release gate met | CSC-SWE6-001 §3.3 qualification criteria | ✅ Defined |
| MAN.3 | All WBS work packages completed; milestones achieved within schedule | CSC-MAN3-001 §8 schedule | ✅ Defined |
| MAN.5 | All risks identified, scored, and treated; no High residual risks at release | CSC-MAN5-001 §6 risk summary | ✅ Defined |
| SUP.1 | All QA gates pass; pre-release checklist complete; zero open bug Issues | CSC-SUP1-001 §4 quality objectives | ✅ Defined |
| SUP.8 | All 34 CIs identified, version-controlled, and baselined per release | CSC-SUP8-001 §6 CI list | ✅ Defined |
| SUP.9 | All SEV-1 problems resolved before release; regression tests added for SEV-1/2 | CSC-SUP9-001 §5.5 closure criteria | ✅ Defined |
| SUP.10 | All approved CRs implemented with PR, CI passing, and document updates | CSC-SUP10-001 §5.5 closure criteria | ✅ Defined |
| ACQ.4 | All supplier acceptance criteria met; no unresolved supplier non-conformances at release | CSC-ACQ4-001 §5 monitoring activities | ✅ Defined |

### 4.2 GP 2.1.2 — Define Process Strategy

| Process | Strategy Summary | Defined In |
|---|---|---|
| SYS.2–SYS.5 | V-model lifecycle; requirements → architecture → integration test → qualification | CSC-MAN3-001 §5 lifecycle |
| SWE.1–SWE.6 | V-model lifecycle; SW requirements → architecture → detailed design → unit → integration → qualification | CSC-MAN3-001 §5 lifecycle |
| MAN.3 | Git Flow branching; WBS with effort estimates; milestone-based schedule | CSC-MAN3-001 §6–8 |
| MAN.5 | Risk scoring (Likelihood × Impact = RPN); treatment and monitoring per risk | CSC-MAN5-001 §4 strategy |
| SUP.1 | Automated CI gates + manual pre-release checklist | CSC-SUP1-001 §5 QA activities |
| SUP.8 | Git-based version control; annotated tags for baselines; dual-registry Docker | CSC-SUP8-001 §7–8 |
| SUP.9 | GitHub Issues (bug label); severity-driven resolution time targets | CSC-SUP9-001 §4–5 |
| SUP.10 | GitHub Issues (CR labels); impact-based approval; Git Flow implementation | CSC-SUP10-001 §4–5 |
| ACQ.4 | Per-supplier monitoring activities; acceptance criteria; non-conformance handling | CSC-ACQ4-001 §5–7 |

### 4.3 GP 2.1.3 to GP 2.1.5 — Plan, Monitor, and Adjust Process Performance

| Process | Planning Evidence | Monitoring Evidence | Adjustment Mechanism |
|---|---|---|---|
| SYS.2–SWE.6 | Section entry/exit criteria in each document; WBS in MAN.3 | CI build status; document review records | Change request (SUP.10) if criteria not met |
| MAN.3 | WBS table with effort and status; milestone schedule | Weekly Issue board review; CI badge | Schedule update + risk register update |
| MAN.5 | Risk register with treatment activities | Monthly risk review; trigger-based updates | Risk score revision; new treatment if residual RPN rises |
| SUP.1 | QA activity schedule; CI gate definitions | CI run results; pre-release checklist | Non-conformance handling (SUP.9 / SUP.10) |
| SUP.8 | CM plan (this document); CI identification list | Git log; baseline FCA/PCA checklists | CM plan update via SUP.10 |
| SUP.9 | Problem resolution SLA targets | Open Issue count; resolution time tracking | Process step revision if SLAs missed |
| SUP.10 | CR process steps; approval thresholds | CR cycle time tracking | Process revision if approval bottlenecks arise |
| ACQ.4 | Supplier monitoring schedule | CI job results; advisory review notes | Supplier non-conformance issue + CR if required |

### 4.4 GP 2.1.6 — Define Responsibilities

> **Note — AI-Assisted Authorship Deviation (CSC-DEV-001):** The entries below reflect Claude (AI assistant) as the authoring tool used to produce work products. All roles carry **Dermot Murphy** as the accountable human responsible party. The `Author: Claude` fields throughout all 18 ASPICE work products are accepted under deviation record **CSC-DEV-001** (`docs/aspice/CStyleCheck_DEV001_AI_Authorship_Deviation.md`), which documents the justification and residual risk. Claude holds no independent authority; Dermot Murphy reviewed and approved all outputs.

| Role | Authoring Tool | Accountable Person | Process Responsibility |
|---|---|---|---|
| Project Manager / CM Manager | Claude | Dermot Murphy | MAN.3, MAN.5, SUP.8, ACQ.4 |
| Lead Developer | Claude | Dermot Murphy | SWE.1, SWE.2, SWE.3, SWE.4 implementation |
| Test Lead | Claude | Dermot Murphy | SWE.4, SWE.5, SWE.6, SYS.4, SYS.5 execution |
| Quality Assurance | — | Dermot Murphy | Document reviews; PR reviews; pre-release checklist |
| CI System | — | GitHub Actions | Automated enforcement of GATE-01, GATE-02, GATE-03 |

### 4.5 GP 2.1.7 — Manage Interfaces

| Interface | Parties | Agreement | Communication Method |
|---|---|---|---|
| CI → Developer | GitHub Actions ↔ Claude | CI must pass before merge to `develop`/`main` | GitHub Actions status checks; email notification |
| Developer → Reviewer | Claude ↔ Reviewer | PR requires at least 1 approval for Medium/High impact | GitHub PR review mechanism |
| Developer → QA | Claude ↔ QA role | Pre-release checklist must be signed before release | CSC-SUP1-001 §5.4 checklist |
| Project → Suppliers | CStyleCheck ↔ SUP-01 to SUP-05 | Acceptance criteria per CSC-ACQ4-001 §5 | CI jobs; advisory monitoring |
| Project → Assessor | CStyleCheck ↔ ASPICE Assessor | Full documentation set; CI evidence; GitHub repository access | Document delivery; GitHub access grant |

---

## 5. PA 2.2 — Work Product Management

### 5.1 GP 2.2.1 — Define Requirements for Work Products

All work products are defined with content requirements in their respective document templates. The following table summarises the defining document for each work product type.

| Work Product | WP ID (PAM v4.0) | Content Requirements Defined In | CI Reference |
|---|---|---|---|
| System Requirements Specification | 17-10 | CSC-SYS2-001 §5 requirements tables | CI-027 (documents) |
| System Architecture Description | 04-04 (adapted) | CSC-SYS3-001 §5 subsystem descriptions | CI-027 |
| System Integration Test Spec | 13-12 | CSC-SYS4-001 §4 test cases | CI-027 |
| System Verification Report | 13-13 | CSC-SYS5-001 §5 results table | CI-027 |
| Software Requirements Specification | 17-10 | CSC-SWE1-001 §4 requirements tables | CI-027 |
| Software Architecture Description | 04-04 | CSC-SWE2-001 §5 component descriptions | CI-027 |
| Software Detailed Design | 04-05 | CSC-SWE3-001 §5 unit designs | CI-027 |
| Unit Verification Specification | 13-12 | CSC-SWE4-001 §5 test catalogue | CI-027 |
| Integration Test Specification | 13-12 | CSC-SWE5-001 §4 test cases | CI-027 |
| Qualification Test Specification | 13-12 | CSC-SWE6-001 §4 test cases | CI-027 |
| Source code (`cstylecheck.py`) | 20-04 | CSC-SWE3-001 unit specifications | CI-001 |
| Test suite | 13-12 | CSC-SWE4-001 test catalogue | CI-017 |
| Configuration Management Plan | 08-27 | CSC-SUP8-001 — this document is the plan | CI-027 |
| Project Management Plan | 08-14 | CSC-MAN3-001 | CI-027 |
| Risk Register | 08-26 | CSC-MAN5-001 §5 risk register | CI-027 |
| Quality Assurance Plan | 08-15 | CSC-SUP1-001 | CI-027 |
| Problem Resolution Records | 13-07 | CSC-SUP9-001 §6 register; GitHub Issues | GitHub |
| Change Requests | 13-01 | CSC-SUP10-001 §7 register; GitHub Issues | GitHub |
| Supplier Monitoring Records | 08-16 | CSC-ACQ4-001 §5 monitoring tables | CI-027 |

### 5.2 GP 2.2.2 — Store and Control Work Products

| Work Product Type | Storage | Version Control | Access Control |
|---|---|---|---|
| Source code and config files | Git repository (`main` branch + tags) | Git SHA; annotated tags | GitHub repository permissions |
| ASPICE documentation (`.md` files) | Git repository + outputs directory | Git SHA; annotated tags | GitHub repository permissions |
| Docker images | GHCR + Docker Hub | Image tag + SHA-256 digest | GHCR: repository-scoped token |
| Problem reports and CRs | GitHub Issues | Issue number; state; labels | GitHub repository permissions |
| CI run evidence | GitHub Actions logs + artefacts | Workflow run ID; commit SHA | GitHub repository; 30-day artefact retention |
| Release packages | GitHub Releases | Release tag | Public (MIT licence) |

**Baseline procedure:** See CSC-SUP8-001 §8.2.

### 5.3 GP 2.2.3 — Review and Adjust Work Products

> **Note — Single-Person Reviewer Deviation (CSC-DEV-002):** CStyleCheck has one human team member (Dermot Murphy). All ASPICE work products carry `Reviewer: Dermot Murphy` and `Approver: Dermot Murphy` — the same individual. This deviates from the GP 2.2.3 expectation of an independent reviewer. The deviation is formally accepted under **CSC-DEV-002** (`docs/aspice/CStyleCheck_DEV002_Independent_Review_Deviation.md`), which documents the justification, compensating controls (AI-assisted review, CI quality gates, PR audit trail), and residual risk. Assessors may rate this practice as Largely Achieved rather than Fully Achieved on the independence criterion.

All work products are reviewed before approval according to the following schedule:

| Work Product | Review Type | Reviewer | Review Evidence |
|---|---|---|---|
| Source code changes | Pull request review | Dermot Murphy (see CSC-DEV-002) | GitHub PR approval record |
| ASPICE documents | Formal document review | Dermot Murphy (see CSC-DEV-002) | Reviewer/Approver table in each document |
| Test suite additions | Pull request review | Dermot Murphy (see CSC-DEV-002) | GitHub PR approval record |
| CI workflow changes | Pull request review | Dermot Murphy (see CSC-DEV-002) | GitHub PR approval record |
| Release baseline | Pre-release checklist | Dermot Murphy / QA role | CSC-SUP1-001 §5.4 signed checklist |

**Adjustment mechanism:** Any non-conformance found during review is raised as a GitHub Issue (SUP.9) or change request (SUP.10) and tracked to resolution before the work product is approved.

### 5.4 Work Product Baseline Status

*Updated for v1.2.0 release, 2026-05-29; accuracy audit CSC-AUD-003 2026-06-04; deep accuracy audit CSC-AUD-004 2026-06-04.*

| Document ID | Work Product | Version | Baseline Status | CM Baseline |
|---|---|---|---|---|
| CSC-SYS2-001 | System Requirements Spec | 1.4 | Released | issue #163 deep audit |
| CSC-SYS3-001 | System Architecture Description | 1.3 | Released | issue #163 deep audit |
| CSC-SYS4-001 | System Integration Test Spec | 1.3 | Released | issue #163 deep audit |
| CSC-SYS5-001 | System Verification Report | 1.4 | Released | issue #163 deep audit |
| CSC-SWE1-001 | SW Requirements Spec | 1.5 | Released | issue #163 deep audit |
| CSC-SWE2-001 | SW Architecture Description | 1.4 | Released | issue #163 deep audit |
| CSC-SWE3-001 | SW Detailed Design | 1.5 | Released | issue #163 deep audit |
| CSC-SWE4-001 | Unit Verification Spec | 1.6 | Released | issue #163 audit |
| CSC-SWE5-001 | Integration Test Spec | 1.3 | Released | issue #163 audit |
| CSC-SWE6-001 | Qualification Test Spec | 1.4 | Released | issue #163 audit |
| CSC-MAN3-001 | Project Management Plan | 1.5 | Released | issue #163 deep audit |
| CSC-MAN5-001 | Risk Management Plan | 1.2 | Released | v1.2.0 tag |
| CSC-SUP1-001 | Quality Assurance Plan | 1.3 | Released | issue #163 deep audit |
| CSC-SUP8-001 | Configuration Management Plan | 1.6 | Released | issue #163 deep audit |
| CSC-SUP9-001 | Problem Resolution Plan | 1.1 | Released | v1.1.0 tag |
| CSC-SUP10-001 | Change Request Plan | 1.1 | Released | v1.1.0 tag |
| CSC-ACQ4-001 | Supplier Monitoring Plan | 1.1 | Released | v1.1.0 tag |
| CSC-PA2-001 | PA 2.1 / PA 2.2 Records | 1.7 | Released | issue #163 audit |
| CSC-DEV-001 | AI Authorship Deviation Record | 1.1 | Released | v1.1.0 tag |
| CSC-DEV-002 | Independent Review Deviation Record | 1.0 | Released | v1.1.0 tag |
| CSC-SVD-001 | Software Version Description | 1.4 | Released | issue #163 deep audit |
| CSC-AUD-001 | ASPICE Internal Audit Report | 1.0 | Released | v1.2.0 tag |
| CSC-AUD-002 | ASPICE Internal Audit — CL2 Re-assessment (2026-05-29) | 1.0 | Released | v1.2.1 tag |
| CSC-AUD-003 | ASPICE Internal Audit — Accuracy (2026-06-04) | 1.0 | Released | issue #163 audit |
| CSC-AUD-004 | ASPICE Internal Audit — Deep Accuracy (2026-06-04) | 1.0 | Released | issue #163 deep audit |
| CSC-AUD-007 | ASPICE Internal Audit — CL2 Re-assessment (2026-06-18) | 1.0 | Released | v1.4.0 tag |
| CI-001 | `src/cstylecheck/` package | 1.2.0 | Released | v1.2.0 tag |
| CI-017 | Test suite (1152 tests) | 1.3.0 | Released | v1.3.0+ |

---

## 6. ASPICE CL2 Coverage Summary

*Resynced 2026-06-18 (CSC-AUD-007) — the verdict below was stale between 2026-05-28 and 2026-06-18: it predated both the closure of issue #152 (2026-05-28) and the superseding re-assessment CSC-AUD-002 (2026-05-29), and five intervening document revisions (1.5–1.9) never refreshed it. See CSC-AUD-007 for the full resync rationale.*

The table below summarises all assessed processes and their CL2 PA achievement evidence, current as of v1.4.0.

| Process | PA 1.1 (Performed) | PA 2.1 (Perf. Mgmt) | PA 2.2 (WP Mgmt) | Assessment Verdict | Open Issue(s) |
|---|---|---|---|---|---|
| SYS.2 | SYS REQ-IDs defined and traceable | Objectives: §4.1; strategy: §4.2 | CSC-SYS2-001 reviewed; in CM | **L** | — |
| SYS.3 | Architecture with subsystems and interfaces | Objectives: §4.1; monitoring: §4.3 | CSC-SYS3-001 reviewed; in CM | **F** | — |
| SYS.4 | 14 SITC test cases defined and executed | Objectives: §4.1 | CSC-SYS4-001 reviewed; in CM | **L** | AUD7-F-001, #261 |
| SYS.5 | 13 SYS-VTC test cases defined and executed | Objectives: §4.1 | CSC-SYS5-001 reviewed; in CM | **L** | AUD7-F-001, #261 |
| SWE.1 | 88 SW requirements defined | Objectives: §4.1; strategy: §4.2 | CSC-SWE1-001 reviewed; in CM | **F** | — |
| SWE.2 | 10 components, 10 interfaces defined | Objectives: §4.1 | CSC-SWE2-001 reviewed; in CM | **F** | — |
| SWE.3 | 112 units with algorithmic specs | Objectives: §4.1 | CSC-SWE3-001 reviewed; in CM | **F** | — |
| SWE.4 | 1152 unit tests; self-check CI; 85% cov. | Objectives: §4.1; coverage targets | CSC-SWE4-001 reviewed; CI evidence | **F** | — |
| SWE.5 | 18 SIT tests; new v1.3/v1.4 rules not yet covered | Objectives: §4.1 | CSC-SWE5-001 reviewed; in CM | **L** ⚠️ | AUD7-F-001, #261 |
| SWE.6 | 12 SWQ tests; rule-coverage test stale at 53/75 rules | Objectives: §4.1; release gate | CSC-SWE6-001 reviewed; CI evidence | **L** ⚠️ | AUD7-F-001, #261 |
| MAN.3 | WBS, schedule, monitoring defined | Objectives: §4.1; §4.3 monitoring | CSC-MAN3-001 reviewed; in CM | **F** | — |
| MAN.5 | 8 risks identified and treated | Objectives: §4.1; risk monitoring | CSC-MAN5-001 reviewed; in CM | **L** | — |
| SUP.1 | QA gates and checklist defined | Objectives: §4.1; CI evidence | CSC-SUP1-001 reviewed; in CM | **L** | — |
| SUP.8 | 34 CIs; Git Flow; dual-registry | Objectives: §4.1; CM monitoring | CSC-SUP8-001 reviewed; in CM | **F** | — |
| SUP.9 | Problem process with SLAs and register | Objectives: §4.1; Issue metrics | CSC-SUP9-001 reviewed; in CM | **F** | DEV-002 |
| SUP.10 | CR process with impact levels and approval | Objectives: §4.1; CR metrics | CSC-SUP10-001 reviewed; in CM | **F** | DEV-002 |
| ACQ.4 | 5 suppliers monitored with criteria | Objectives: §4.1; monitoring schedule | CSC-ACQ4-001 reviewed; in CM | **L** | — |

> **📋 Rating scale:** N = Not achieved (0–15%), P = Partially achieved (15–50%), L = Largely achieved (50–85%), F = Fully achieved (85–100%). All processes must achieve **L or F** at PA 2.1 and PA 2.2 for CL2 to be awarded.
>
> **✅ CL2 Verdict: ACHIEVED.** All 17 processes rate **L or F** (11 F, 6 L, 0 P/N). One corrective action remains open — **AUD7-F-001**: the 11 rules added in v1.3.0/v1.4.0 (issues #221–#232) have requirements/design/unit-test coverage (SWE.1/SWE.3/SWE.4) but no integration-, system-, or qualification-level test cases yet (SWE.5/SYS.4/SYS.5/SWE.6); `SYS-VTC-003`/`SWQ-003` still cite "53 rule IDs" instead of 75. This downgrades SWE.5 and SWE.6 from F to L but does not affect the CL2 award. Targeted for the v1.5.0 cycle. Full detail: `docs/aspice/audits/CStyleCheck_ASPICE_Internal_Audit_2026-06-18.md` (CSC-AUD-007).
>
> **Ratings assigned by internal audit CSC-AUD-007, 2026-06-18 (supersedes CSC-AUD-001 2026-05-28 and CSC-AUD-002 2026-05-29 for this table).**

---

## 7. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | Approved | 2026-04-15 |
| Technical Reviewer | Dermot Murphy | Approved | 2026-04-15 |
| Quality Assurance | Dermot Murphy | Approved | 2026-04-15 |
| Approver | Dermot Murphy | Approved | 2026-04-15 |

> **Note:** This document is under configuration management (SUP.8). Post-approval changes require a change request (SUP.10) and a new document version.
