# Change Request Management Plan

*Automotive SPICE® PAM v4.0 | SUP.10 Change Request Management*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CSC-SUP10-001 | **Version** | 1.0 |
| **Project** | CStyleCheck | **Date** | 2026-04-12 |
| **Status** | Released | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SUP.10 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose & Scope

This Change Request Management Plan defines the process for requesting, evaluating, approving, implementing, and verifying changes to any controlled configuration item of **CStyleCheck v1.0.0**. It satisfies **Automotive SPICE® PAM v4.0, SUP.10 — Change Request Management**.

A **change request (CR)** covers any planned modification to a baselined work product that is not a defect fix — including new features, new rules, configuration changes, documentation updates, and process improvements. Defect fixes are handled under SUP.9 but also follow this plan for their change-control steps once the fix has been accepted.

### 3.1 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CSC-SUP8-001 | Configuration Management Plan | 1.1 |
| CSC-SUP9-001 | Problem Resolution Management Plan | 1.0 |
| CSC-MAN3-001 | Project Management Plan | 1.0 |

---

## 4. Change Request Classification

### 4.1 Change Types

| Type | Label | Description |
|---|---|---|
| **Enhancement** | `enhancement` | New rule, new output format, new CLI flag, new integration |
| **Improvement** | `improvement` | Optimisation, UX improvement, performance improvement |
| **Documentation** | `documentation` | Update to ASPICE documents, README, or in-code documentation |
| **Configuration** | `config-change` | Update to `rules.yml`, `exclusions.yml`, or dictionary files |
| **Process** | `process-change` | Update to CI workflows, Git Flow procedure, or QA activities |

### 4.2 Impact Levels

| Impact | Criteria | Approval Required |
|---|---|---|
| **Low** | Changes a single CI; no interface impact; no requirement change | Author self-review |
| **Medium** | Changes multiple CIs; impacts one interface; minor requirement change | Peer review (1 approver) |
| **High** | Changes architecture, adds/removes requirements, breaks backwards compatibility | Peer review + explicit QA sign-off |

---

## 5. Change Request Process

### 5.1 Raising a Change Request

All change requests are raised as **GitHub Issues** with the `enhancement`, `improvement`, `documentation`, `config-change`, or `process-change` label.

Minimum required fields when raising a CR Issue:

| Field | Required Content |
|---|---|
| **Title** | `[CR] <brief description of change>` |
| **Type label** | One of the type labels from §4.1 |
| **Impact level** | Low / Medium / High |
| **Motivation** | Why the change is needed; which stakeholder need or deficiency it addresses |
| **Description** | What specifically will change; which CIs (from CSC-SUP8-001 §6.1) are affected |
| **Affected documents** | Which ASPICE work products require updating |
| **Proposed target release** | Which version the change is planned for |

### 5.2 Change Evaluation

1. Issue assigned to Claude for evaluation
2. Assess: technical feasibility, effort estimate, impact on existing requirements, impact on test suite, version number implications (patch/minor/major)
3. Check for conflicts with open Issues or other planned changes
4. Evaluate impact on ASPICE documents — identify which WPs need revision
5. Record evaluation outcome in the Issue comment thread

### 5.3 Change Approval

| Impact Level | Approval Mechanism |
|---|---|
| Low | Author marks Issue as approved in comment; proceeds to implementation |
| Medium | At least one peer review approval on the implementing pull request |
| High | Explicit approval comment from QA role in the Issue thread before implementation begins |

Changes that modify requirements (CSC-SWE1-001 or CSC-SYS2-001) always require Medium or High approval regardless of other impact assessment.

### 5.4 Implementation

Accepted changes are implemented following the Git Flow process defined in CSC-SUP8-001 §7:

| Change Type | Branch | Target |
|---|---|---|
| New feature or enhancement | `feature/<issue-id>-<description>` | `develop` |
| Configuration or documentation | `feature/<issue-id>-<description>` | `develop` |
| Urgent backwards-compatible fix affecting released version | `hotfix/<issue-id>-<description>` | `main` and `develop` |

Commit messages must reference the Issue: `Implements #<issue-id>: <description>`

All implementing PRs must:
- Pass CI (`cstylecheck_tests.yml`, `rules.yml`)
- Include or update affected ASPICE documents in the same branch or a linked follow-up Issue
- Update traceability tables if requirements are added or modified

### 5.5 Verification

1. CI must pass on the implementing branch
2. If the CR adds a new rule: at least one test case must be added to the test suite demonstrating the rule fires on invalid input and passes on valid input
3. If the CR changes a requirement: the corresponding SWE.4/SWE.6 test case must be updated
4. Pull request reviewer confirms all affected documents have been updated before approving

### 5.6 Closure

- Issue is closed when the implementing PR is merged
- If the CR affects a released version: version number is incremented per semantic versioning
  - Patch (`1.0.x`): backwards-compatible bug fixes
  - Minor (`1.x.0`): new rules, new CLI flags, new output formats (backwards compatible)
  - Major (`x.0.0`): breaking changes (removed flags, changed default behaviour, incompatible config format)
- Release notes for the target release must reference the CR Issue number

---

## 6. Impact on Configuration Items

When a CR is approved, the following CIs may require update:

| CR Type | Likely Affected CIs |
|---|---|
| New rule | CI-001 (`cstylecheck.py`), CI-003 (`rules.yml`), CI-017 (test suite), CI-026 (README) |
| New CLI flag | CI-001, CI-013 (`pyproject.toml`), CI-016 (`action.yml`), CI-026 (README) |
| New output format | CI-001, CI-016 (`action.yml`), CI-026 (README) |
| Config file change | CI-003 or CI-005 to CI-010 |
| CI workflow change | CI-023 to CI-025 |
| ASPICE document update | Affected document CI (e.g., CI-027) + new version entry in §2 |

All affected CIs must be updated within the same Git Flow branch as the implementing change (or in an explicitly linked follow-up Issue tracked to the same release).

---

## 7. Change Request Register

The GitHub Issues board at `https://github.com/dermot-murphy/CStyleCheck/issues` serves as the CR register. Filter by enhancement/improvement/documentation/config-change/process-change labels.

Summary view:

| Issue # | Type | Title | Impact | Status | Target Release |
|---|---|---|---|---|---|
| \<Auto-populated from GitHub Issues — see Issues board\> | | | | | |

---

## 8. Metrics

| Metric | Measurement | Frequency |
|---|---|---|
| Open CRs | GitHub Issues count by CR-type labels | Weekly |
| CRs accepted per release | Count of closed CR Issues per release tag | Per release |
| Mean CR cycle time | Days from Issue open to PR merge | Per release |
| CRs that required document updates | Count of CRs with ASPICE document changes | Per release |

---

## 9. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | Approved | 2026-04-15 |
| Technical Reviewer | Dermot Murphy | Approved | 2026-04-15 |
| Quality Assurance | Dermot Murphy | Approved | 2026-04-15 |
| Approver | Dermot Murphy | Approved | 2026-04-15 |

> **Note:** This document is under configuration management (SUP.8). Post-approval changes require a change request (SUP.10) and a new document version.
