# CStyleCheck — ASPICE Peer Review Template

*Template ID: CSC-REVIEW-TEMPLATE-001 · Version 1.0*

> **Instructions for use:**
> 1. Copy this file to a new document named `CStyleCheck_Review_Record_<version>.md`
> 2. Fill in all fields in §1–§3 before starting the review
> 3. Work through the checklist in §4 for each work product
> 4. Record every finding in §5
> 5. Complete §6 (summary) and §7 (sign-off) after all items are reviewed
> 6. Commit the completed record to `docs/aspice/` on the `develop` branch

---

## 1. Review Identification

| Field | Value |
|---|---|
| **Review ID** | CSC-REVIEW-`<nnn>` |
| **Review Type** | Peer Review — Work Product Quality Check |
| **Review Date** | YYYY-MM-DD |
| **Reviewer** | `<name>` |
| **Author / Review Owner** | Dermot Murphy |
| **Baseline Commit / Tag** | `<git tag or commit SHA>` |
| **Review Scope** | All ASPICE work products at `<version>` |
| **Reference Standard** | Automotive SPICE® PAM v4.0 · ASPICE GP 2.2.3 |
| **Related Documents** | CSC-PA2-001 vX.Y, CSC-DEV-001, CSC-DEV-002 |
| **Status** | Draft / Under Review / Approved |

---

## 2. Review Scope

List every work product included in this review (drawn from CSC-PA2-001).

| # | Document ID | Title | Version | File Path |
|---|---|---|---|---|
| 1 | CSC-SYS2-001 | System Requirements Analysis | x.x | `docs/aspice/CStyleCheck_SYS2_System_Requirements.md` |
| 2 | CSC-SYS3-001 | System Architecture Design | x.x | `docs/aspice/CStyleCheck_SYS3_System_Architecture.md` |
| 3 | CSC-SYS4-001 | System Integration Test | x.x | `docs/aspice/CStyleCheck_SYS4_System_Integration_Test.md` |
| 4 | CSC-SYS5-001 | System Qualification Test | x.x | `docs/aspice/CStyleCheck_SYS5_System_Verification.md` |
| 5 | CSC-SWE1-001 | Software Requirements Analysis | x.x | `docs/aspice/CStyleCheck_SWE1_SW_Requirements.md` |
| 6 | CSC-SWE2-001 | Software Architecture Design | x.x | `docs/aspice/CStyleCheck_SWE2_SW_Architecture.md` |
| 7 | CSC-SWE3-001 | Software Detailed Design | x.x | `docs/aspice/CStyleCheck_SWE3_Detailed_Design.md` |
| 8 | CSC-SWE4-001 | Software Unit Verification | x.x | `docs/aspice/CStyleCheck_SWE4_Unit_Verification.md` |
| 9 | CSC-SWE5-001 | Software Integration Test | x.x | `docs/aspice/CStyleCheck_SWE5_Integration_Test.md` |
| 10 | CSC-SWE6-001 | Software Qualification Test | x.x | `docs/aspice/CStyleCheck_SWE6_Qualification_Test.md` |
| 11 | CSC-MAN3-001 | Project Management | x.x | `docs/aspice/CStyleCheck_MAN3_Project_Management.md` |
| 12 | CSC-MAN5-001 | Risk Management | x.x | `docs/aspice/CStyleCheck_MAN5_Risk_Management.md` |
| 13 | CSC-SUP1-001 | Quality Assurance | x.x | `docs/aspice/CStyleCheck_SUP1_Quality_Assurance.md` |
| 14 | CSC-SUP8-001 | Configuration Management | x.x | `docs/aspice/CStyleCheck_SUP8_Configuration_Management.md` |
| 15 | CSC-SUP9-001 | Problem Resolution Management | x.x | `docs/aspice/CStyleCheck_SUP9_Problem_Resolution_Plan.md` |
| 16 | CSC-SUP10-001 | Change Request Management | x.x | `docs/aspice/CStyleCheck_SUP10_Change_Request_Mgmt.md` |
| 17 | CSC-ACQ4-001 | Supplier Monitoring | x.x | `docs/aspice/CStyleCheck_ACQ4_Supplier_Monitoring.md` |
| 18 | CSC-SVD-001 | Software Version Description | x.x | `docs/aspice/CStyleCheck_SVD_Software_Version_Description.md` |
| 19 | CSC-PA2-001 | Capability Records (PA 2.1/2.2) | x.x | `docs/aspice/CStyleCheck_PA2_Capability_Records.md` |
| 20 | CSC-DEV-001 | AI Authorship Deviation Record | x.x | `docs/aspice/CStyleCheck_DEV001_AI_Authorship_Deviation.md` |
| 21 | CSC-DEV-002 | Independent Review Deviation Record | x.x | `docs/aspice/CStyleCheck_DEV002_Independent_Review_Deviation.md` |

---

## 3. Review Criteria

Each work product is assessed against the following dimensions:

| Criterion | Description | Check Method |
|---|---|---|
| **C1 — Completeness** | All required sections present; no placeholder text (`<fill …>`, TBD, N/A without explanation) | Read each section |
| **C2 — Consistency** | Version numbers, rule counts, module names, test counts, and CI targets agree across documents | Cross-check PA2, SWE4, README |
| **C3 — Traceability** | Requirements trace to design; design traces to tests; tests trace to CI evidence | Check traceability matrices |
| **C4 — Correctness** | Technical content matches the actual codebase (file paths, module names, rule IDs, test names) | Compare against `src/` and `tests/` |
| **C5 — Clarity** | Text is unambiguous; definitions are consistent; no contradictions within the document | Read for understanding |

---

## 4. Per-Document Checklist

Repeat this table for each document in §2. Mark each criterion: ✅ Pass · ⚠️ Concern · ❌ Fail · N/A.

### Template Row (copy and fill for each document)

| Criterion | Result | Notes |
|---|---|---|
| C1 — Completeness | ✅ / ⚠️ / ❌ | |
| C2 — Consistency | ✅ / ⚠️ / ❌ | |
| C3 — Traceability | ✅ / ⚠️ / ❌ | |
| C4 — Correctness | ✅ / ⚠️ / ❌ | |
| C5 — Clarity | ✅ / ⚠️ / ❌ | |
| **Overall** | Pass / Conditional / Fail | |

---

## 5. Findings

Record every deviation from the review criteria.

| Finding ID | Document | Criterion | Severity | Description | Disposition |
|---|---|---|---|---|---|
| RR-`<nnn>`-001 | CSC-XXX-001 | Cx | Major / Minor / Observation | `<clear description of the issue>` | Open / Waived / Fixed-before-approval |

**Severity definitions:**
- **Major** — blocks approval; must be corrected before the work product is approved
- **Minor** — must be resolved within one release cycle; document may be conditionally approved
- **Observation** — improvement suggestion; no release impact; recorded for backlog

---

## 6. Review Summary

| Item | Value |
|---|---|
| **Total work products reviewed** | `<n>` |
| **Work products with no findings** | `<n>` |
| **Work products with findings** | `<n>` |
| **Total findings** | `<n>` |
| **— Major** | `<n>` |
| **— Minor** | `<n>` |
| **— Observation** | `<n>` |
| **Open actions** | `<n>` |
| **Review verdict** | Pass / Conditional Pass / Fail |

**Verdict rationale:**

> `<1–3 sentences summarising the overall quality of the work products and the basis for the verdict.>`

---

## 7. Sign-off

| Role | Name | Date | Notes |
|---|---|---|---|
| Reviewer | `<name>` | YYYY-MM-DD | |
| Author / Review Owner | Dermot Murphy | YYYY-MM-DD | *Solo developer — see CSC-DEV-002 for peer-review constraint* |

> **Note (CSC-DEV-002):** CStyleCheck is developed by a solo engineer. The independent peer-review requirement of ASPICE GP 2.2.3 cannot be satisfied by a separate human reviewer in the conventional sense. This review is conducted by the AI tool (Claude) acting in the reviewer role, as formally documented in CSC-DEV-002. The Review Owner signature above constitutes the required management approval of this review record.

---

*Template: CSC-REVIEW-TEMPLATE-001 · Version 1.0 · 2026-05-29*
