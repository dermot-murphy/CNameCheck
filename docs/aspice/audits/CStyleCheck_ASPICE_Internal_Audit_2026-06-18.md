# CStyleCheck ASPICE Internal Audit — CSC-AUD-007

| Field | Value |
|---|---|
| **Audit ID** | CSC-AUD-007 |
| **Date** | 2026-06-18 |
| **Branch** | `main` (v1.4.0, commit tag `v1.4.0`) |
| **Auditor** | AI-assisted internal audit (Claude, per CSC-DEV-001) |
| **Scope** | CL2 re-assessment of all 17 processes against the current `main` baseline; resolution check on `CSC-PA2-001` §6 staleness |
| **Overall Status** | **CL2 Achieved, with one open corrective action** |
| **Test count (actual)** | 1152 / 49 modules |
| **Rule count (actual)** | 75 |

---

## 1. Purpose and Trigger

`CSC-PA2-001` §6 ("ASPICE CL2 Coverage Summary") still carried the verdict **"CL2 NOT YET ACHIEVED"**, citing three processes (SYS.4, SYS.5, SWE.5) rated **P** due to open issue #152. This is stale:

- Issue #152 was closed 2026-05-28, with execution evidence populated into CSC-SYS4-001, CSC-SYS5-001, and CSC-SWE5-001.
- A second internal audit, **CSC-AUD-002** (2026-05-29), already re-rated those three processes (P→L, P→L, P→F) and concluded the v1.2.1 release met CL2 requirements (all 17 processes L or F).
- Five subsequent revisions of `CSC-PA2-001` (1.5 through 1.9) updated test counts and baseline tables but never synchronised §6 with CSC-AUD-002's findings — an oversight, not a real regression.

Rather than mechanically copy CSC-AUD-002's v1.2.1 ratings forward, this audit re-assesses the **current** `main` baseline (v1.4.0), since three releases (v1.3.0, v1.4.0, and an unreleased package refactor) and four accuracy audits (CSC-AUD-003 through CSC-AUD-006) have landed since CSC-AUD-002.

---

## 2. Carried-Forward Findings (No Regression)

All ten issues referenced in the stale §6 table are closed: #146, #147, #148, #149, #150, #151, #152, #153, #154, #155. No evidence of regression was found for SYS.2, SWE.1, SWE.2, SWE.3, SWE.4, MAN.3, MAN.5, SUP.1, SUP.8, SUP.9, SUP.10, ACQ.4 — these carry forward their CSC-AUD-002 ratings unchanged (SYS.2 L, SWE.1 F, SWE.2 F, SWE.3 F, SWE.4 F, MAN.3 F, MAN.5 L, SUP.1 L, SUP.8 F, SUP.9 F, SUP.10 F, ACQ.4 L).

CSC-AUD-006 (tracked as issue #254, closed 2026-06-18) already corrected the test/module-count drift (965→1152, 33→49 modules) that would otherwise have affected SWE.4 and CSC-SVD-001 evidence currency.

---

## 3. New Finding — AUD7-F-001: v1.3.0/v1.4.0 rules have no integration/system/qualification test coverage

**Severity: High** | **Affects: SWE.5, SYS.4, SYS.5, SWE.6**

The 11 rules added across v1.3.0/v1.4.0 (issues #221–#232, SWE1-078 to SWE1-088) are fully covered at the requirements (SWE.1), design (SWE.3), and unit-test (SWE.4) levels — each has a dedicated `_check_*` method, a UNIT-XXX design entry, and a `test_*.py` unit test module. However:

- **SWE.5** (`CSC-SWE5-001`): no SIT-XXX test case references any of the 11 new rules. SIT-001 to SIT-018 cover only pre-v1.3.0 functionality.
- **SYS.4** (`CSC-SYS4-001`): no SITC-XXX test case references any of the 11 new rules. SITC-001 to SITC-014 are unchanged since before v1.3.0.
- **SYS.5** (`CSC-SYS5-001`): `SYS-VTC-003` ("Full Rule Coverage") still says **"53 Rule IDs"** — its objective, RTM entries (§ "SYS-F-011 to F-024 → Covered"), and `SYS-F-020` itself (the umbrella system requirement SWE1-078–088 trace to) were never updated to mention the 11 new checks. `SYS-F-020`'s own text still only describes the pre-v1.3.0 misc rules (line length, indentation, magic numbers, unsigned suffix, yoda conditions, block comment spacing).
- **SWE.6** (`CSC-SWE6-001`): `SWQ-003` ("All Rule IDs Detected") likewise still says **"53 Rule IDs"** and its rule-category breakdown table omits the `macro.*` and the 6 new `misc.*`/`naming.*` rules entirely.

**Impact:** the documented integration/system/qualification verification work products do not demonstrate that 11 of the product's 75 rules — roughly 15% of total functionality — were verified above the unit level for the current release. This is a genuine, currently-open gap, not a stale-documentation artefact like the §6 table issue.

**Disposition:** SWE.5 and SWE.6 downgrade from **F** (CSC-AUD-002) to **L** — base practices are performed and work products exist and are controlled, but evidence of complete verification scope is not yet objective. SYS.4 and SYS.5 remain **L** (unchanged — they already carried this caveat implicitly; CSC-AUD-002 did not anticipate the rule additions that came after it).

This does **not** block CL2 — L is a passing rating — but it is the top corrective-action item for the v1.5.0 cycle. Tracked as a new issue (see §6).

---

## 4. Updated CL2 Coverage Summary (supersedes CSC-AUD-001 data in CSC-PA2-001 §6)

| Process | CSC-AUD-001 (2026-05-28) | CSC-AUD-002 (2026-05-29) | **CSC-AUD-007 (2026-06-18, current)** | Open Issue(s) |
|---|---|---|---|---|
| SYS.2 | L | L | **L** | — |
| SYS.3 | L | F | **F** | — |
| SYS.4 | P | L | **L** | AUD7-F-001, #261 |
| SYS.5 | P | L | **L** | AUD7-F-001, #261 |
| SWE.1 | F | F | **F** | — |
| SWE.2 | L | F | **F** | — |
| SWE.3 | L | F | **F** | — |
| SWE.4 | L | F | **F** | — |
| SWE.5 | P | F | **L** ↓ | AUD7-F-001, #261 |
| SWE.6 | F | F | **L** ↓ | AUD7-F-001, #261 |
| MAN.3 | L | F | **F** | — |
| MAN.5 | L | L | **L** | — |
| SUP.1 | L | L | **L** | — |
| SUP.8 | L | F | **F** | — |
| SUP.9 | F | F | **F** | — |
| SUP.10 | F | F | **F** | — |
| ACQ.4 | L | L | **L** | — |

> **📋 Rating scale:** N = Not achieved (0–15%), P = Partially achieved (15–50%), L = Largely achieved (50–85%), F = Fully achieved (85–100%). All processes must achieve **L or F** at PA 2.1 and PA 2.2 for CL2 to be awarded.

### 4.1 Overall CL2 Verdict

**✅ ASPICE CL2 IS ACHIEVED at v1.4.0.** All 17 processes rate **L or F** (9 F, 8 L, 0 P/N). The `CSC-PA2-001` §6 table's "NOT YET ACHIEVED" verdict was stale — it predated both the closure of issue #152 (2026-05-28) and the superseding re-assessment CSC-AUD-002 (2026-05-29) by several weeks, and was never refreshed across five subsequent document revisions.

One corrective action remains open (AUD7-F-001/#261: extend SWE.5/SYS.4/SYS.5/SWE.6 verification scope to the 11 rules added in v1.3.0/v1.4.0), tracked for the v1.5.0 cycle. It does not affect the CL2 award since the affected processes still rate L.

---

## 5. Conclusion

CL2 was actually achieved on 2026-05-29 (CSC-AUD-002, at v1.2.1) and remains achieved at v1.4.0, modulo one newly-identified verification-scope gap (AUD7-F-001) that downgrades SWE.5 and SWE.6 from F to L without affecting the overall award. The root cause of the "NOT YET ACHIEVED" message the project saw was a documentation-sync defect in `CSC-PA2-001` §6, not an actual capability gap — corrected by this audit.

---

## 6. Actions Required

| Action | Finding | Owner | Target Version |
|---|---|---|---|
| Sync `CSC-PA2-001` §6 to this audit's ratings and verdict | (this audit) | Claude | v1.4.0 (immediate, this PR) |
| Add `CSC-AUD-002` and `CSC-AUD-007` rows to `CSC-PA2-001` §5.4 baseline table | (this audit) | Claude | v1.4.0 (immediate, this PR) |
| Add SIT/SITC/SYS-VTC/SWQ test cases for the 11 rules from #221–#232; update `SYS-F-020` and rule-count text (53→75) in `SYS-VTC-003`/`SWQ-003` | AUD7-F-001, #261 | Dermot Murphy | v1.5.0 |

---

## 7. Sign-off

| Role | Name | Date | Signature |
|---|---|---|---|
| Auditor | Claude (AI-assisted) | 2026-06-18 | *per CSC-DEV-001* |
| Audit Owner / Reviewer | Dermot Murphy | — | *pending manual review* |

> **Note:** This audit was conducted by an AI tool (Claude) acting in the auditor role as documented in CSC-DEV-001. The solo-developer independent-review constraint is formally acknowledged in CSC-DEV-002. The Audit Owner signature above constitutes the required management review approval for this ASPICE-internal document.

---

*Erratum (v1.1, 2026-06-18): §4.1 summary corrected from "11 F, 6 L" to "9 F, 8 L" to match the §4 table; the row-by-row ratings and the CL2 ACHIEVED verdict were already correct and are unaffected.*

*Document: CSC-AUD-007 · Version 1.1 · 2026-06-18*
*Location: `docs/aspice/audits/CStyleCheck_ASPICE_Internal_Audit_2026-06-18.md`*
