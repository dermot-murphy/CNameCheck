# Process Capability Records

*Automotive SPICE® PAM v4.0 | PA 2.1 Process Performance Management & PA 2.2 Work Product Management*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CSC-PA2-001 | **Version** | 1.0 |
| **Project** | CStyleCheck | **Date** | 2026-04-12 |
| **Status** | Released | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | PA 2.1, PA 2.2 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose

This document records the generic practices evidence for **Automotive SPICE® PAM v4.0 Capability Level 2** across all assessed processes. It provides a single consolidated reference for assessors to verify PA 2.1 (Process Performance Management) and PA 2.2 (Work Product Management) achievement for CStyleCheck v1.0.0.

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
| SWE.3 | All 46 units designed; algorithmic specification complete; resource usage documented | CSC-SWE3-001 §4 unit catalogue | ✅ Defined |
| SWE.4 | ≥ 90% statement, ≥ 85% branch coverage; all ≥500 unit tests PASS on Python 3.10/11/12 | CSC-SWE4-001 §4.2 coverage criteria | ✅ Defined |
| SWE.5 | All 13 SIT integration test cases PASS; all 10 SWA interfaces covered | CSC-SWE5-001 §3.3 verification criteria | ✅ Defined |
| SWE.6 | All 12 SWQ qualification test cases PASS; 100% SW requirements coverage; release gate met | CSC-SWE6-001 §3.3 qualification criteria | ✅ Defined |
| MAN.3 | All WBS work packages completed; milestones achieved within schedule | CSC-MAN3-001 §8 schedule | ✅ Defined |
| MAN.5 | All risks identified, scored, and treated; no High residual risks at release | CSC-MAN5-001 §6 risk summary | ✅ Defined |
| SUP.1 | All QA gates pass; pre-release checklist complete; zero open bug Issues | CSC-SUP1-001 §4 quality objectives | ✅ Defined |
| SUP.8 | All 27 CIs identified, version-controlled, and baselined per release | CSC-SUP8-001 §6 CI list | ✅ Defined |
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

| Role | Assigned To | Process Responsibility |
|---|---|---|
| Project Manager / CM Manager | Claude | MAN.3, MAN.5, SUP.8, ACQ.4 |
| Lead Developer | Claude | SWE.1, SWE.2, SWE.3, SWE.4 implementation |
| Test Lead | Claude | SWE.4, SWE.5, SWE.6, SYS.4, SYS.5 execution |
| Quality Assurance | Dermot Murphy | Approved | 2026-04-15 |
| Reviewer | \<Name\> | Document reviews; PR reviews |
| CI System | GitHub Actions | Automated enforcement of GATE-01, GATE-02, GATE-03 |

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

All work products are reviewed before approval according to the following schedule:

| Work Product | Review Type | Reviewer | Review Evidence |
|---|---|---|---|
| Source code changes | Pull request review | ≥ 1 peer reviewer | GitHub PR approval record |
| ASPICE documents | Formal document review | Technical reviewer + QA | Reviewer/Approver table in each document |
| Test suite additions | Pull request review | ≥ 1 peer reviewer | GitHub PR approval record |
| CI workflow changes | Pull request review | ≥ 1 peer reviewer | GitHub PR approval record |
| Release baseline | Pre-release checklist | QA role | CSC-SUP1-001 §5.4 signed checklist |

**Adjustment mechanism:** Any non-conformance found during review is raised as a GitHub Issue (SUP.9) or change request (SUP.10) and tracked to resolution before the work product is approved.

### 5.4 Work Product Baseline Status (v1.0.0)

| Document ID | Work Product | Version | Baseline Status | CM Baseline |
|---|---|---|---|---|
| CSC-SYS2-001 | System Requirements Spec | 1.0 | Released | v1.0.0 tag |
| CSC-SYS3-001 | System Architecture Description | 1.0 | Released | v1.0.0 tag |
| CSC-SYS4-001 | System Integration Test Spec | 1.0 | Released | v1.0.0 tag |
| CSC-SYS5-001 | System Verification Report | 1.0 | Released | v1.0.0 tag |
| CSC-SWE1-001 | SW Requirements Spec | 1.0 | Released | v1.0.0 tag |
| CSC-SWE2-001 | SW Architecture Description | 1.0 | Released | v1.0.0 tag |
| CSC-SWE3-001 | SW Detailed Design | 1.0 | Released | v1.0.0 tag |
| CSC-SWE4-001 | Unit Verification Spec | 1.0 | Released | v1.0.0 tag |
| CSC-SWE5-001 | Integration Test Spec | 1.0 | Released | v1.0.0 tag |
| CSC-SWE6-001 | Qualification Test Spec | 1.0 | Released | v1.0.0 tag |
| CSC-MAN3-001 | Project Management Plan | 1.0 | Released | v1.0.0 tag |
| CSC-MAN5-001 | Risk Management Plan | 1.0 | Released | v1.0.0 tag |
| CSC-SUP1-001 | Quality Assurance Plan | 1.0 | Released | v1.0.0 tag |
| CSC-SUP8-001 | Configuration Management Plan | 1.1 | Released | v1.0.0 tag |
| CSC-SUP9-001 | Problem Resolution Plan | 1.0 | Released | v1.0.0 tag |
| CSC-SUP10-001 | Change Request Plan | 1.0 | Released | v1.0.0 tag |
| CSC-ACQ4-001 | Supplier Monitoring Plan | 1.0 | Released | v1.0.0 tag |
| CSC-PA2-001 | PA 2.1 / PA 2.2 Records | 1.0 | Released | v1.0.0 tag |
| CI-001 | `cstylecheck.py` v1.0.0 | 1.0.0 | \<Baselined\> | v1.0.0 tag |
| CI-017 | Test suite | 1.0.0 | \<Baselined\> | v1.0.0 tag |

---

## 6. ASPICE CL2 Coverage Summary

The table below summarises all assessed processes and their CL2 PA achievement evidence.

| Process | PA 1.1 (Performed) | PA 2.1 (Perf. Mgmt) | PA 2.2 (WP Mgmt) | Assessment Verdict |
|---|---|---|---|---|
| SYS.2 | SYS REQ-IDs defined and traceable | Objectives: §4.1; strategy: §4.2 | CSC-SYS2-001 reviewed; in CM | \<N / P / L / F\> |
| SYS.3 | Architecture with subsystems and interfaces | Objectives: §4.1; monitoring: §4.3 | CSC-SYS3-001 reviewed; in CM | \<N / P / L / F\> |
| SYS.4 | 14 SITC test cases defined | Objectives: §4.1 | CSC-SYS4-001 reviewed; in CM | \<N / P / L / F\> |
| SYS.5 | 13 SYS-VTC test cases defined | Objectives: §4.1 | CSC-SYS5-001 reviewed; in CM | \<N / P / L / F\> |
| SWE.1 | 70 SW requirements defined | Objectives: §4.1; strategy: §4.2 | CSC-SWE1-001 reviewed; in CM | \<N / P / L / F\> |
| SWE.2 | 7 components, 10 interfaces defined | Objectives: §4.1 | CSC-SWE2-001 reviewed; in CM | \<N / P / L / F\> |
| SWE.3 | 46 units with algorithmic specs | Objectives: §4.1 | CSC-SWE3-001 reviewed; in CM | \<N / P / L / F\> |
| SWE.4 | 500+ unit tests; self-check CI | Objectives: §4.1; coverage targets | CSC-SWE4-001 reviewed; CI evidence | \<N / P / L / F\> |
| SWE.5 | 13 SIT tests covering all 10 interfaces | Objectives: §4.1 | CSC-SWE5-001 reviewed; in CM | \<N / P / L / F\> |
| SWE.6 | 12 SWQ tests; 100% SW-REQ coverage | Objectives: §4.1; release gate | CSC-SWE6-001 reviewed; CI evidence | \<N / P / L / F\> |
| MAN.3 | WBS, schedule, monitoring defined | Objectives: §4.1; §4.3 monitoring | CSC-MAN3-001 reviewed; in CM | \<N / P / L / F\> |
| MAN.5 | 8 risks identified and treated | Objectives: §4.1; risk monitoring | CSC-MAN5-001 reviewed; in CM | \<N / P / L / F\> |
| SUP.1 | QA gates and checklist defined | Objectives: §4.1; CI evidence | CSC-SUP1-001 reviewed; in CM | \<N / P / L / F\> |
| SUP.8 | 27 CIs; Git Flow; dual-registry | Objectives: §4.1; CM monitoring | CSC-SUP8-001 reviewed; in CM | \<N / P / L / F\> |
| SUP.9 | Problem process with SLAs and register | Objectives: §4.1; Issue metrics | CSC-SUP9-001 reviewed; in CM | \<N / P / L / F\> |
| SUP.10 | CR process with impact levels and approval | Objectives: §4.1; CR metrics | CSC-SUP10-001 reviewed; in CM | \<N / P / L / F\> |
| ACQ.4 | 5 suppliers monitored with criteria | Objectives: §4.1; monitoring schedule | CSC-ACQ4-001 reviewed; in CM | \<N / P / L / F\> |

> **📋 Note:** Rating scale: N = Not achieved (0–15%), P = Partially achieved (15–50%), L = Largely achieved (50–85%), F = Fully achieved (85–100%). All processes must achieve L or F at PA 2.1 and PA 2.2 for CL2 to be awarded.

---

## 7. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | Approved | 2026-04-15 |
| Technical Reviewer | Dermot Murphy | Approved | 2026-04-15 |
| Quality Assurance | Dermot Murphy | Approved | 2026-04-15 |
| Approver | Dermot Murphy | Approved | 2026-04-15 |

> **Note:** This document is under configuration management (SUP.8). Post-approval changes require a change request (SUP.10) and a new document version.
