# Process Deviation — Reviewer and Approver Are the Same Person

*Automotive SPICE® PAM v4.0 | SUP.9 Problem Resolution / Deviation Record*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CSC-DEV-002 | **Version** | 1.0 |
| **Project** | CStyleCheck | **Date** | 2026-05-28 |
| **Status** | Approved | **Classification** | Internal |
| **Author** | Dermot Murphy | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | PA 2.2, GP 2.2.3 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | 2026-05-28 | Dermot Murphy | Initial deviation record — closes issue #61 |

---

## 3. Deviation Summary

| Field | Value |
|---|---|
| **Deviation ID** | CSC-DEV-002 |
| **Problem Record** | CSC-SUP10 Change Request #61 |
| **Severity** | SEV-3 Minor |
| **Standard Clause** | ASPICE PAM v4.0, GP 2.2.3 — Review and Adjust Work Products |
| **Affected Documents** | All 21 ASPICE work products in `docs/aspice/` |
| **Disposition** | **Accepted with justification** |

---

## 4. Non-Conformance Description

### 4.1 What the Standard Requires

ASPICE PAM v4.0, Generic Practice **GP 2.2.3 — Review and Adjust Work Products** requires that:

> *"Work products are reviewed in accordance with planned arrangements to ensure that they are suitable for use."*

Assessment practice under PA 2.2 — Work Product Management expects the reviewer of a work product to be **independent of the author**. The intent is that an independent perspective is applied to catch errors, omissions, and inconsistencies before a work product is approved for use. Independence means, at minimum, that the reviewer is not the same individual who authored the document.

ASPICE assessors typically look for:

- A named reviewer who is not the document author
- Evidence that the reviewer actively examined the content (e.g., review comments, a signed review record, or a separate review checklist)
- A named approver who accepts responsibility for the content after review

### 4.2 Actual State

All 21 ASPICE work products in `docs/aspice/` carry the following in their Document Identification header:

| Field | Value |
|---|---|
| Author | Claude (AI assistant) / Dermot Murphy |
| Reviewer | Dermot Murphy |
| Approver | Dermot Murphy |

In every document, the **Reviewer and Approver are the same person: Dermot Murphy**.

Furthermore, `Dermot Murphy` is also the accountable human for all work products where `Author: Claude` appears (see CSC-DEV-001). In effect, the same individual (Dermot Murphy) holds the Author, Reviewer, and Approver roles simultaneously on every document.

### 4.3 Root Cause

CStyleCheck is a personal open-source project. **Dermot Murphy is the sole human team member.** There is no second employee, contractor, or independent colleague available to act as reviewer. The requirement for independent review cannot be met in a single-person organisation without engaging an external third party, which is disproportionate to the project's scope and risk profile.

---

## 5. Justification for Acceptance

### 5.1 Project Context

CStyleCheck is a **personal open-source project with one human participant: Dermot Murphy**. The project has:

- No employees, contractors, or other team members
- No organisational hierarchy (no QA department, no separate reviewer pool)
- A benign risk profile: it is a linting tool for embedded C style compliance, not safety-critical firmware, medical device software, or automotive control software
- An MIT licence: users are responsible for assessing fitness for their own use

In this context, requiring independent review — as would be appropriate in an organisation with multiple engineers — would be structurally impossible without artificially importing a third party solely to satisfy a process checkbox.

### 5.2 Compensating Controls

Although the Reviewer and Approver are the same person, the following compensating controls provide equivalent assurance:

| Control | Description | Evidence |
|---|---|---|
| **AI-assisted review** | Every document was drafted or reviewed with Claude, providing an independent analytical perspective before Dermot Murphy's human review | Commit history; CSC-DEV-001 |
| **CI quality gates** | All source code and test changes pass automated CI (unit tests × 3 Python versions, mypy, ruff, CStyleCheck self-check) before any work product is approved | GitHub Actions CI log for each PR |
| **Pull request review** | Every change to a controlled work product is submitted as a GitHub Pull Request. The PR mechanism creates a structured review record (diff, CI status, approval timestamp) | GitHub PR history |
| **Version-controlled audit trail** | All work product changes are committed to Git with a descriptive message. The commit history is immutable and publicly auditable | GitHub repository |
| **Systematic self-review** | Before approval, Dermot Murphy explicitly reads the document in the context of the standard clause it satisfies, comparing content against the corresponding ASPICE GP requirements | Issue-close evidence in each PR |

### 5.3 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Assessor rates GP 2.2.3 as "Not Achieved" due to lack of independent reviewer | Medium | Medium | This deviation document is the formal rebuttal; compensating controls in §5.2 provide equivalent assurance |
| Document quality is lower than it would be with a second reviewer | Low | Low | AI-assisted review and CI quality gates provide independent challenge of content and correctness |
| Future team growth makes deviation obsolete | Low | None | Deviation can be retired when a second qualified reviewer joins the project; no ongoing maintenance cost |

**Residual risk: LOW** — the single-person context is transparent and documented; compensating controls are demonstrable to an assessor.

### 5.4 ASPICE Assessment Interpretation

ASPICE PAM v4.0 is written for organisational contexts with multiple team members. Several Automotive SPICE user groups (intacs, VDA QMC) acknowledge that process tailoring is permissible for small projects and personal-scale software, provided the intent of each GP is addressed. The intent of GP 2.2.3 is:

> *"Work products are checked against their requirements before use, so that errors are found and corrected before they propagate."*

The compensating controls in §5.2 collectively satisfy this intent. An assessor may award this practice **"Largely Achieved" (L)** rather than "Fully Achieved (F)" on the independence criterion, but the project accepts this outcome as proportionate.

---

## 6. Corrective Action

No change is made to the Reviewer/Approver fields in any work product. **Dermot Murphy remains both Reviewer and Approver on all 21 ASPICE documents.** This is explicitly accepted as a permanent deviation for the lifetime of CStyleCheck as a single-person project.

If a second qualified reviewer joins the project in future, this deviation shall be retired and the affected documents updated to name separate Reviewer and Approver individuals.

**Actions required:**

| Action | Owner | Target Date | Status |
|---|---|---|---|
| Create this deviation document (CSC-DEV-002) | Dermot Murphy | 2026-05-28 | ✅ Complete |
| Add CSC-DEV-002 reference to CSC-PA2-001 §5.3 (GP 2.2.3) | Dermot Murphy | 2026-05-28 | ✅ Complete |
| Add CSC-DEV-002 to CSC-SUP8-001 CI list | Dermot Murphy | 2026-05-28 | ✅ Complete |
| Add CSC-DEV-002 footnote to Document Identification section of SWE1-001, SWE4-001, SWE6-001 | Dermot Murphy | 2026-05-28 | ✅ Complete |

---

## 7. Approval

This deviation is accepted on the basis that CStyleCheck is a single-person project with no available independent reviewer, that the intent of GP 2.2.3 is satisfied by the compensating controls documented in §5.2, and that the residual risk is low.

| Role | Name | Signature | Date |
|---|---|---|---|
| Author | Dermot Murphy | Approved | 2026-05-28 |
| Approver | Dermot Murphy | Approved | 2026-05-28 |

---

## 8. Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CSC-DEV-001 | Process Deviation — AI-Assisted Authorship | 1.1 |
| CSC-PA2-001 | Process Capability Records | 1.1 |
| CSC-SUP8-001 | Configuration Management Plan | 1.1 |
| CSC-SUP9-001 | Problem Resolution Management Plan | 1.0 |
| CSC-SUP10-001 | Change Request Plan | 1.0 |
| GitHub Issue #61 | Designate independent reviewer (not approver) for SWE1, SWE4, SWE6 work products | — |
