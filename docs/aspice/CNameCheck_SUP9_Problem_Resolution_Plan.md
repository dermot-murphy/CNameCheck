# Problem Resolution Management Plan

*Automotive SPICE® PAM v4.0 | SUP.9 Problem Resolution Management*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CNC-SUP9-001 | **Version** | 1.0 |
| **Project** | CNameCheck | **Date** | 2026-04-12 |
| **Status** | Draft | **Classification** | Internal |
| **Author** | Dermot Murphy | **Reviewer** | \<Reviewer Name\> |
| **Approver** | \<Approver Name\> | **Related Process** | SUP.9 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | 2026-04-12 | Dermot Murphy | Initial release |

---

## 3. Purpose & Scope

This Problem Resolution Management Plan defines the process for recording, classifying, investigating, resolving, and closing problems identified in **CNameCheck v1.0.0**. It satisfies **Automotive SPICE® PAM v4.0, SUP.9 — Problem Resolution Management**.

A **problem** is any unintended behaviour, defect, failure, or non-conformance discovered in any work product — including source code, test cases, documentation, configuration files, or CI workflows.

### 3.1 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CNC-MAN3-001 | Project Management Plan | 1.0 |
| CNC-SUP8-001 | Configuration Management Plan | 1.1 |
| CNC-SUP10-001 | Change Request Management Plan | 1.0 |
| CNC-SUP1-001 | Quality Assurance Plan | 1.0 |

---

## 4. Problem Classification

### 4.1 Severity Levels

| Severity | Label | Criteria | Target Resolution Time |
|---|---|---|---|
| SEV-1 | Critical | Crash, data loss, security vulnerability, or incorrect rule evaluation causing silent pass of invalid code | 48 hours |
| SEV-2 | Major | False positive blocking adoption; incorrect violation output data (wrong file/line/rule); exit code wrong | 1 week |
| SEV-3 | Minor | Cosmetic output issue; misleading error message; documentation inaccuracy | Next planned release |
| SEV-4 | Enhancement | Feature request or improvement (tracked as separate change request via SUP.10) | Planned release |

### 4.2 Problem States

| State | Description | Transition |
|---|---|---|
| **New** | Problem raised; not yet triaged | → Under Investigation (within 48h of receipt) |
| **Under Investigation** | Root cause analysis in progress | → In Progress (root cause found) or Rejected (not reproducible / not a defect) |
| **In Progress** | Fix being developed on `bugfix/` or `hotfix/` branch | → In Review (PR opened) |
| **In Review** | Fix submitted as pull request; awaiting CI and peer review | → Resolved (PR merged) |
| **Resolved** | Fix merged to `develop` or `main`; problem report closed | → Verified (fix confirmed in released version) |
| **Verified** | Fix confirmed in a released version (tag) | Terminal state |
| **Rejected** | Not a defect; duplicate; or by-design behaviour | Terminal state — documented reason required |

---

## 5. Problem Resolution Process

### 5.1 Problem Identification and Recording

Problems may be identified by:

- Automated CI failures (`cnamecheck_tests.yml`, `naming_convention.yml`, `docker_publish.yml`)
- Manual testing during development or qualification
- User reports via GitHub Issues
- ASPICE assessment findings
- Internal code review observations

**All problems are recorded as GitHub Issues** with the `bug` label.

Minimum required fields when raising an Issue:

| Field | Required Content |
|---|---|
| **Title** | Short description: `[BUG] <what is wrong>` |
| **Severity** | One of: `SEV-1 Critical`, `SEV-2 Major`, `SEV-3 Minor` (label applied) |
| **Affected version** | Version tag or commit SHA where problem was observed |
| **Environment** | Python version, OS, invocation command |
| **Steps to reproduce** | Minimal source file or command that triggers the problem |
| **Expected behaviour** | What the correct behaviour should be |
| **Actual behaviour** | What actually happened |
| **Affected work products** | Which CIs (e.g., CI-001 `cnamecheck.py`) are affected |

### 5.2 Triage and Investigation

1. Issue is assigned to Dermot Murphy (sole maintainer for v1.0.0)
2. Severity label is confirmed or revised
3. Root cause is investigated:
   - For code defects: identify affected unit(s) from CNC-SWE3-001
   - For test defects: identify affected test case from CNC-SWE4-001
   - For documentation defects: identify affected work product and document ID
4. If not reproducible or not a defect: close Issue as `Rejected` with explanation
5. Root cause documented in the GitHub Issue comment thread

### 5.3 Fix Implementation

| Severity | Branch Type | Target Branch |
|---|---|---|
| SEV-1 Critical | `hotfix/<issue-id>-<description>` | `main` then back-merged to `develop` |
| SEV-2 Major | `bugfix/<issue-id>-<description>` | `develop` |
| SEV-3 Minor | `bugfix/<issue-id>-<description>` | `develop` |

Fix commit messages must reference the Issue: `Fixes #<issue-id>: <description>`

### 5.4 Verification of Fix

1. CI must pass (`cnamecheck_tests.yml`) on the fix branch
2. A regression test must be added to `tests/test_improvements.py` (or appropriate test module) to prevent recurrence — this is mandatory for SEV-1 and SEV-2
3. The regression test must explicitly reference the Issue ID in a comment: `# Regression test for GitHub Issue #<id>`
4. Pull request is reviewed; at least one approval required before merge
5. After merge: Issue state → Resolved

### 5.5 Closure and Verification

- Issue is closed automatically when the fix PR is merged (via `Fixes #N` in commit message)
- For SEV-1 and SEV-2: a patch or minor release is created; Issue state updated to **Verified** once the fix appears in a tagged release
- Release notes for the fixing release must reference the Issue number

---

## 6. Problem Report Register

The GitHub Issues board at `https://github.com/dermot-murphy/CNameCheck/issues` serves as the problem report register. Filter by `bug` label for problem reports.

Summary view (updated per release):

| Issue # | Severity | Title | Status | Resolved In |
|---|---|---|---|---|
| \<Auto-populated from GitHub Issues — see Issues board\> | | | | |

### 6.1 Known Resolved Problems (v1.0.0)

The following problems were identified and resolved during v1.0.0 development:

| Problem | Root Cause | Fix | Regression Test |
|---|---|---|---|
| Spell-checker possessive stripping (`status` → `statu`) | `rstrip("'s")` strips any trailing `s` | Replaced with `re.sub(r"'s$", "", ...)` | `test_spell_check.py` |
| `plain_char_is_signed: false` ineffective | `char` moved to `_UNSIGNED_TYPES` but sign check used wrong branch | Fixed by temporarily placing `char` in `_UNSIGNED_TYPES` during check only | `test_sign_compatibility.py` |
| `_SIGNED_TYPES` global mutation | `plain_char_is_signed: false` permanently removed `char` from module-level set | Fixed with `try/finally` to restore original set | `test_sign_compatibility.py` |
| `RE_TYPEDEF_SIMPLE` missed multi-token base types | Regex only matched single-word base types | Regex updated to require trailing whitespace on each base-type word | `test_typedefs.py` |
| `function.min_length` undocumented but unimplemented | Rule config key parsed but check never invoked | Implemented check in `_check_functions()` | `test_improvements.py` |

---

## 7. Metrics and Reporting

| Metric | Measurement | Reporting Frequency |
|---|---|---|
| Open problem reports (by severity) | GitHub Issues count filtered by `bug` label and severity label | Weekly |
| Mean time to resolution (by severity) | Average days from Issue creation to closure | Per release |
| Regression test count added | Count of tests in `test_improvements.py` per release | Per release |
| Problems found post-release | Issues opened after release tag | Per release |

---

## 8. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Dermot Murphy | | 2026-04-12 |
| Technical Reviewer | \<Name\> | | |
| Quality Assurance | \<Name\> | | |
| Approver | \<Name\> | | |

> **⚠️ Important:** All SEV-1 problems must be resolved before the v1.0.0 release baseline is created. SEV-2 problems require a resolution plan approved before release. This plan must be placed under configuration management (SUP.8) upon approval.
