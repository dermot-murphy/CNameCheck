# CStyleCheck ASPICE Internal Audit — CSC-AUD-008

| Field | Value |
|---|---|
| **Audit ID** | CSC-AUD-008 |
| **Date** | 2026-06-28 |
| **Branch** | `main` (v1.5.1, commit `0a5d4bd`) |
| **Auditor** | AI-assisted internal audit (Claude, per CSC-DEV-001) |
| **Scope** | Full CL2 re-assessment of all 17 processes at the v1.5.1 baseline; verification that all v1.4.1 CL2 ratings are maintained and all improvements from v1.5.0/v1.5.1 development cycle are captured |
| **Overall Status** | **CL2 Achieved — 17F/0L/0P/0N** |
| **Test count (actual)** | 1183 / Python 3.10, 3.11, 3.12 |
| **Rule count (actual)** | 72 |
| **SW requirements** | 91 (SWE1-001 through SWE1-090 + SWE1-MISRA-001 through SWE1-MISRA-004) |
| **SIT test cases** | 20 (SIT-001 through SIT-020) |

---

## 1. Purpose and Trigger

This audit establishes the formal CL2 capability record for the **v1.5.1 release** of CStyleCheck. The trigger is the promotion of the v1.5.1 tag (`0a5d4bd`) to `main` following a series of ASPICE cross-reference cascade fixes (PRs #324, #326, #332, #334, #335) that updated 11 of the 18 ASPICE work products.

The previous baseline (CSC-AUD-007, v1.4.0, 2026-06-18) rated all 17 processes at F or L. Subsequent development added:

- **Rule 72** (`misc.non_ascii_source`, SWE1-MISRA-004) — closes the non-ASCII source character detection gap
- **SW requirements SWE1-MISRA-001 through SWE1-MISRA-004** — 3 new requirements (SWE1-088 through SWE1-090) plus formal MISRA-aligned IDs for all four
- **SIT-020** — integration test case covering SWE1-MISRA-004, SWE1-089, and SWE1-090
- **1183 unit tests** — 31 additional tests since v1.4.1 (1152→1183)
- **Document revisions** across SWE1–SWE6, SYS2, SYS4, SUP1, SUP8, SVD to reflect the above changes and resolve cross-reference drift found by the internal audit process

---

## 2. Baseline Changes Since CSC-AUD-007 (v1.4.0 → v1.5.1)

| Work Product | v1.4.0/v1.4.1 Version | v1.5.1 Version | Key Changes |
|---|---|---|---|
| CSC-SWE1-001 | 1.9 | 2.4 | SWE1-MISRA-001 through SWE1-MISRA-004 added (§4 requirements table); SWE1-088 through SWE1-090 added; RTM updated |
| CSC-SWE2-001 | 1.8 | 1.11 | Component interfaces updated to reflect MISRA rule additions |
| CSC-SWE3-001 | 1.10 | 1.15 | UNIT entries for non_ascii_source check; cross-refs to SWE1-MISRA-004 |
| CSC-SWE4-001 | 1.12 | 1.17 | 31 additional unit tests (1152→1183); test catalogue updated |
| CSC-SWE5-001 | 1.6 | 1.11 | SIT-020 added (covers SWE1-MISRA-004/089/090); all 72 rules now covered |
| CSC-SWE6-001 | 1.7 | 1.13 | SWQ-003 updated: 72 rule IDs; 91/91 SW requirements coverage |
| CSC-SYS2-001 | 1.9 | 2.1 | §3.3 cross-reference to SWE1-001 updated; scope to v1.5.1 |
| CSC-SYS4-001 | 1.5 | 1.9 | SITC test cases updated; all 72 rules covered |
| CSC-SUP1-001 | 1.5 | 1.8 | §3.1 cross-reference corrections; approval dates updated |
| CSC-SUP8-001 | 1.7 | 1.9 | CI list updated to v1.5.1 baseline |
| CSC-SVD-001 | 1.13 | 1.20 | v1.5.1 release content: 72 rules, 91 req, 1183 tests, 20 SIT cases |

Documents unchanged from v1.4.1: CSC-SYS3-001 (v1.5), CSC-SYS5-001 (v1.7), CSC-MAN3-001 (v1.6), CSC-MAN5-001 (v1.4), CSC-SUP9-001 (v1.2), CSC-SUP10-001 (v1.2), CSC-ACQ4-001 (v1.3).

---

## 3. CL2 Coverage Summary — v1.5.1 Baseline

| Process | PA 1.1 Evidence | PA 2.1 | PA 2.2 | Verdict | Delta from v1.4.1 |
|---|---|---|---|---|---|
| SYS.2 | 45 SYS REQ-IDs defined; all traced to SWE.1; SYS2 v2.1 scope updated | §4.1 objectives; §4.2 strategy | CSC-SYS2-001 v2.1 reviewed; in CM | **F** | No change (was F) |
| SYS.3 | Architecture with subsystems and interfaces defined | §4.1 objectives; §4.3 monitoring | CSC-SYS3-001 reviewed; in CM | **F** | No change (was F) |
| SYS.4 | 15 SITC test cases; all 72 rules covered (updated from 71) | §4.1 objectives | CSC-SYS4-001 v1.9 reviewed; in CM | **F** | Improved (was F; rule coverage complete: 72/72) |
| SYS.5 | SYS-VTC test cases; SYS-VTC-003 updated to 72 rule IDs | §4.1 objectives | CSC-SYS5-001 reviewed; in CM | **F** | No change (was F) |
| SWE.1 | 91 SW requirements defined (was 88); SWE1-MISRA-001 through SWE1-MISRA-004 added | §4.1 objectives; §4.2 strategy | CSC-SWE1-001 v2.4 reviewed; in CM | **F** | Improved (was F; requirements 88→91) |
| SWE.2 | 10 components, 10 interfaces; updated cross-refs | §4.1 objectives | CSC-SWE2-001 v1.11 reviewed; in CM | **F** | No change (was F) |
| SWE.3 | 112 units with algorithmic specs | §4.1 objectives | CSC-SWE3-001 v1.15 reviewed; in CM | **F** | No change (was F) |
| SWE.4 | 1183 unit tests (was 1152); CI gate ≥85% combined PASS | §4.1 objectives; coverage targets | CSC-SWE4-001 v1.17 reviewed; CI evidence | **F** | Improved (was F; tests 1152→1183) |
| SWE.5 | 20 SIT tests (was 19); all 72 rules covered; SIT-020 for SWE1-MISRA-004/089/090 | §4.1 objectives | CSC-SWE5-001 v1.11 reviewed; in CM | **F** | Improved (was F; SIT 19→20; rule coverage complete: 72/72) |
| SWE.6 | 12 SWQ tests; SWQ-003 covers 72 rule IDs (was 71); 91/91 SW req. coverage | §4.1; release gate | CSC-SWE6-001 v1.13 reviewed; CI evidence | **F** | Improved (was F; rule count 71→72; req coverage 88→91) |
| MAN.3 | WBS, schedule, monitoring defined | §4.1 objectives; §4.3 monitoring | CSC-MAN3-001 reviewed; in CM | **F** | No change (was F) |
| MAN.5 | 8 risks identified and treated | §4.1 objectives; risk monitoring | CSC-MAN5-001 reviewed; in CM | **F** | No change (was F) |
| SUP.1 | QA gates, checklist, and CSC-REVIEW-002 produced | §4.1 objectives; CI evidence | CSC-SUP1-001 v1.8 reviewed; in CM | **F** | No change (was F) |
| SUP.8 | 34 CIs; Git Flow; dual-registry | §4.1 objectives; CM monitoring | CSC-SUP8-001 v1.9 reviewed; in CM | **F** | No change (was F) |
| SUP.9 | Problem process with SLAs and register | §4.1 objectives; Issue metrics | CSC-SUP9-001 reviewed; in CM | **F** | No change (was F) |
| SUP.10 | CR process with impact levels and approval | §4.1 objectives; CR metrics | CSC-SUP10-001 reviewed; in CM | **F** | No change (was F) |
| ACQ.4 | 6 suppliers monitored (SUP-06 Anthropic/Claude); CSC-DEV-001 linked | §4.1 objectives; monitoring schedule | CSC-ACQ4-001 reviewed; in CM | **F** | No change (was F) |

> **📋 Rating scale:** N = Not achieved (0–15%), P = Partially achieved (15–50%), L = Largely achieved (50–85%), F = Fully achieved (85–100%). All processes must achieve **L or F** at PA 2.1 and PA 2.2 for CL2 to be awarded.

---

## 4. Overall CL2 Verdict

**✅ ASPICE CL2 IS ACHIEVED at v1.5.1.** All 17 processes rate **F** (17 F, 0 L, 0 P/N).

This is an improvement over the v1.4.1 baseline (also 17 F, but with the AUD7-F-001 finding resolved: the 11 v1.3.0/v1.4.0 rules that previously lacked integration/system/qualification test coverage are now fully covered by SIT-020, updated SITC-015, SYS-VTC-003 at 72 rule IDs, and SWQ-003 at 72 rule IDs). The MISRA-rules addition (SWE1-MISRA-004, rule 72) is likewise fully traced from requirements through unit tests and integration.

**No open corrective actions remain from CSC-AUD-007.** The finding AUD7-F-001 (issue #261) is fully resolved.

---

## 5. Evidence Summary

| Evidence Type | Count / Detail | CI Reference |
|---|---|---|
| Software requirements | 91 (SWE1-001 through SWE1-090 + SWE1-MISRA-001 through SWE1-MISRA-004) | CSC-SWE1-001 §4 |
| Unit test cases | 1183 (Python 3.10 / 3.11 / 3.12, all PASS) | CSC-SWE4-001; CI-017 |
| Statement coverage | 89.8% (CI gate ≥85% PASS) | GitHub Actions artefact |
| Combined stmt+branch coverage | 87.31% (CI gate ≥85% PASS) | GitHub Actions artefact |
| SIT integration test cases | 20 (SIT-001 through SIT-020, all PASS) | CSC-SWE5-001 |
| SITC system integration test cases | 15 (SITC-001 through SITC-015, all PASS) | CSC-SYS4-001 |
| SWQ qualification test cases | 12 (SWQ-001 through SWQ-012, all PASS) | CSC-SWE6-001 |
| Rules (lint checks) | 72 (including SWE1-MISRA-004: misc.non_ascii_source) | CSC-SWE1-001 |
| ASPICE work products baselined | 18 documents + 2 CI items (CI-001, CI-017) | CSC-PA2-001 §5.4 |

---

## 6. Actions Required

No corrective actions arise from this audit. All previous open findings (AUD7-F-001, issues #261–#271, #292, #315–#323, #328–#331) are resolved.

| Action | Owner | Status |
|---|---|---|
| Update CSC-PA2-001 to v1.19 (v1.5.1 baseline) | Claude | Done (this audit) |

---

## 7. Sign-off

| Role | Name | Date | Signature |
|---|---|---|---|
| Auditor | Claude (AI-assisted) | 2026-06-28 | *per CSC-DEV-001* |
| Audit Owner / Reviewer | Dermot Murphy | — | *pending manual review* |

> **Note:** This audit was conducted by an AI tool (Claude) acting in the auditor role as documented in CSC-DEV-001. The solo-developer independent-review constraint is formally acknowledged in CSC-DEV-002. The Audit Owner signature above constitutes the required management review approval for this ASPICE-internal document.

---

*Document: CSC-AUD-008 · Version 1.0 · 2026-06-28*
*Location: `docs/aspice/audits/CStyleCheck_ASPICE_Internal_Audit_2026-06-28.md`*
