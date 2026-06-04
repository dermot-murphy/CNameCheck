# ASPICE Internal Audit Report — CSC-AUD-004

*Automotive SPICE® PAM v4.0 | Deep Accuracy and Consistency Audit*

---

## 1. Document Identification

| Field | Value |
|---|---|
| **Audit ID** | CSC-AUD-004 |
| **Date** | 2026-06-04 |
| **Auditor** | Claude (automated) |
| **Scope** | All ASPICE work products in `docs/aspice/` |
| **Trigger** | Issue #163 — follow-up deep audit after CSC-AUD-003 |
| **Related** | CSC-AUD-001 (2026-05-28), CSC-AUD-002 (2026-05-29), CSC-AUD-003 (2026-06-04) |

---

## 2. Audit Objectives

Verify ASPICE work product accuracy, consistency, clarity, and ASPICE compliance across all 15+ documents:

1. All referenced document versions match current post-AUD-003 document headers
2. Purpose/scope version text (v1.0.0) updated to v1.2.x throughout
3. SWE2 architecture component list matches actual implemented functions
4. SWE3 unit catalogue line numbers match actual source locations
5. SWE3 unit catalogue is complete (no missing implemented functions)
6. PA2 process performance objectives reflect accurate counts (unit count, CI count)
7. SUP8 CI inventory file names match actual repository files
8. SUP1 referenced document versions are current
9. SYS document referenced doc versions are current

---

## 3. Ground Truth (Verified from Codebase)

| Metric | Pre-Audit Value | Actual Value | Source |
|---|---|---|---|
| SWE3 unit count | 89 (in PA2 §6) / 46 (in PA2 §4.1) | **90 (UNIT-01 to UNIT-90) + 4 new = 94** | SWE3 §4 catalogue |
| Total CI count | 27 (PA2 §4.1) / 29 (PA2 §6) | **34** | SUP8 §6.1 CI-001..CI-034 |
| Workflow file name | `rules.yml` (in SUP8 CI-024) | **`cstylecheck_rules.yml`** | `.github/workflows/` listing |
| COMP-05f functions (SWE2) | `_check_block_comment_spacing`, `_check_eof_comment` listed | **Don't exist; `_check_comment_ratio` and `_check_whitespace_ratio` are the actual functions** | `checker.py` grep |
| config.py line numbers | Stale (pre-4-function-addition) | **Updated** (+158 for load_config, +173 for all others) | `config.py` grep |
| 4 missing config functions | Not in SWE3 catalogue | **`_find_default_rules` (93), `_deep_merge` (114), `_collect_paths` (137), `update_config` (148)** | `config.py` grep |

---

## 4. Findings and Corrections

### F-001 — SYS3/SYS4/SYS5 Referenced Doc Versions Stale (MAJOR)

**Severity:** Major  
**Documents affected:** CSC-SYS3-001 §3.2; CSC-SYS4-001 §3.3; CSC-SYS5-001 §3.2  
**Finding:** SYS3, SYS4, SYS5 all referenced SYS2/SYS3/SYS4/SYS5/SUP8 at v1.0 (pre-CSC-AUD-003 versions). CSC-AUD-003 updated SYS2/SYS5 content but did not update these cross-reference tables.  
**Correction:** Updated all SYS3/SYS4/SYS5 referenced doc tables to current post-AUD-003 versions.  
**Status:** ✅ RESOLVED

### F-002 — SYS3/SYS4/SYS5 Purpose Text References v1.0.0 (MAJOR)

**Severity:** Major  
**Documents affected:** CSC-SYS3-001 §3.1; CSC-SYS4-001 §3.1; CSC-SYS5-001 §3.1  
**Finding:** All three system documents stated "CStyleCheck v1.0.0" in their purpose sections, two major versions out of date.  
**Correction:** Updated to "v1.2.x" throughout.  
**Status:** ✅ RESOLVED

### F-003 — SYS4 §3.2 Deployment Mode Count Incorrect (MINOR)

**Severity:** Minor  
**Document:** CSC-SYS4-001 §3.2  
**Finding:** SYS4 stated "four deployment modes" but SYS3 §6.1 documents five (adding pre-commit hook).  
**Correction:** Updated to "five deployment modes" with pre-commit listed.  
**Status:** ✅ RESOLVED

### F-004 — SYS5 §3.3 Configuration Version Text v1.0.0 (MODERATE)

**Severity:** Moderate  
**Document:** CSC-SYS5-001 §3.3  
**Finding:** System configuration table still showed Software Version 1.0.0, Git Tag v1.0.0, CM Baseline v1.0.0 release tag.  
**Correction:** Updated to Software Version 1.2.0, Git Tag v1.2.0, CM Baseline v1.2.0 release tag.  
**Status:** ✅ RESOLVED

### F-005 — SWE1 Referenced Doc Versions Partially Stale (MAJOR)

**Severity:** Major  
**Document:** CSC-SWE1-001 §3.2  
**Finding:** CSC-SWE2-001 still referenced as 1.2 (actual: 1.3 post-AUD-003, now 1.4); CSC-SUP8-001 still referenced as 1.4 (actual: 1.5 post-AUD-003, now 1.6).  
**Correction:** Updated both references to current versions.  
**Status:** ✅ RESOLVED

### F-006 — SWE1 Purpose Text References v1.0.0 (MODERATE)

**Severity:** Moderate  
**Document:** CSC-SWE1-001 §3.1  
**Finding:** Purpose stated "CStyleCheck v1.0.0".  
**Correction:** Updated to "v1.2.x".  
**Status:** ✅ RESOLVED

### F-007 — SWE2 COMP-05f Lists Non-Existent Functions (CRITICAL)

**Severity:** Critical  
**Document:** CSC-SWE2-001 §4 architecture tree, §5 COMP-05f table  
**Finding:** COMP-05f listed `_check_block_comment_spacing()` and `_check_eof_comment()`. Grep of checker.py confirms these functions do not exist. The actual functions `_check_comment_ratio()` and `_check_whitespace_ratio()` were missing from the architecture description entirely.  
**Correction:** Removed non-existent functions; added actual `_check_comment_ratio()` (checker.py:1537) and `_check_whitespace_ratio()` (checker.py:1675) to both architecture tree and COMP-05f table.  
**Status:** ✅ RESOLVED

### F-008 — SWE2 §8.1 Execution Sequence Missing Checks (MODERATE)

**Severity:** Moderate  
**Document:** CSC-SWE2-001 §8.1  
**Finding:** The per-file processing execution sequence omitted `_check_comment_ratio()` and `_check_whitespace_ratio()` from the list of `run_all()` steps.  
**Correction:** Added both checks after `_check_misc()` in §8.1 execution diagram.  
**Status:** ✅ RESOLVED

### F-009 — SWE2 §10 RTM Missing SWE1-071 and MISRA Rows (MODERATE)

**Severity:** Moderate  
**Document:** CSC-SWE2-001 §10  
**Finding:** Requirements SWE1-071 (whitespace_ratio) and SWE1-MISRA-001/002/003 (MISRA C lexical rules) exist in SWE1 but were absent from SWE2's traceability matrix.  
**Correction:** Added two rows covering SWE1-071 and SWE1-MISRA-001 to SWE1-MISRA-003.  
**Status:** ✅ RESOLVED

### F-010 — SWE2 COMP-02 Missing config.py Utility Functions (MAJOR)

**Severity:** Major  
**Document:** CSC-SWE2-001 §4 architecture tree, §5 COMP-02 description  
**Finding:** Four functions (`_find_default_rules`, `_deep_merge`, `_collect_paths`, `update_config`) exist in config.py but were absent from the COMP-02 architecture description.  
**Correction:** Added all four functions to both the §4 tree and §5 COMP-02 source functions list.  
**Status:** ✅ RESOLVED

### F-011 — SWE3 Unit Catalogue: 4 Missing Config Functions (CRITICAL)

**Severity:** Critical  
**Document:** CSC-SWE3-001 §4 unit catalogue  
**Finding:** `_find_default_rules()` (config.py:93), `_deep_merge()` (config.py:114), `_collect_paths()` (config.py:137), and `update_config()` (config.py:148) are fully implemented in config.py with no unit catalogue entries. `update_config()` implements the `--update-config` CLI flag.  
**Correction:** Added UNIT-91, UNIT-92, UNIT-93, UNIT-94 for these four functions. Updated §4.1 package structure to list all config.py functions in the correct order.  
**Status:** ✅ RESOLVED

### F-012 — SWE3 Unit Catalogue: 48 Stale Line Numbers (MAJOR)

**Severity:** Major  
**Document:** CSC-SWE3-001 §4 unit catalogue  
**Finding:** 48 unit catalogue entries had incorrect line numbers due to code changes since the last SWE3 update:
- **config.py (13 units):** `load_config` and all subsequent functions shifted +158 to +173 lines when 4 new utility functions were inserted at lines 93-250
- **cli.py (5 units):** Small +1 to +8 line offsets (minor code growth)
- **preprocessor.py (2 units):** `build_line_map`, `offset_to_line_col` shifted +3
- **sign_checker.py (11 units):** Systematic +1 line offset throughout
- **checker.py (17 units):** Mixed -2 to -6 line offsets (minor code shrinkage/refactoring)  
**Correction:** Updated all 48 line numbers to match actual source file locations.  
**Status:** ✅ RESOLVED

### F-013 — PA2 §4.1 SWE.3 Unit Count: 46 vs 90 (CRITICAL)

**Severity:** Critical  
**Document:** CSC-PA2-001 §4.1 GP 2.1.1  
**Finding:** PA2 §4.1 SWE.3 performance objective stated "All 46 units designed" — mathematically incorrect (90 units in UNIT-01..UNIT-90, plus 4 new = 94 total).  
**Correction:** Updated to "All 90 units designed" (reflecting UNIT-01..UNIT-90 per SWE3 v1.4; the 4 new units UNIT-91..94 are added in SWE3 v1.5 by this audit).  
**Status:** ✅ RESOLVED

### F-014 — PA2 §4.1 and §6 SUP.8 CI Count: 27/29 vs 34 (CRITICAL)

**Severity:** Critical  
**Document:** CSC-PA2-001 §4.1 and §6  
**Finding:** PA2 §4.1 SUP.8 objective stated "All 27 CIs identified" while §6 stated "29 CIs; Git Flow; dual-registry". SUP8 §6.1 lists 34 CIs (CI-001..CI-034).  
**Correction:** Updated both §4.1 (27→34) and §6 (29→34).  
**Status:** ✅ RESOLVED

### F-015 — SUP8 CI-024 Wrong Workflow Filename (CRITICAL)

**Severity:** Critical  
**Document:** CSC-SUP8-001 §6.1 CI-024, §7.5  
**Finding:** CI-024 documented `.github/workflows/rules.yml` but actual filename is `.github/workflows/cstylecheck_rules.yml`. File `rules.yml` does not exist in the repository. §7.5 prose also referenced `rules.yml`.  
**Correction:** Updated CI-024 path and §7.5 text to `cstylecheck_rules.yml`.  
**Status:** ✅ RESOLVED

### F-016 — MAN3 Purpose Text References v1.0.0 (MAJOR)

**Severity:** Major  
**Document:** CSC-MAN3-001 §3 Purpose  
**Finding:** MAN3 §3 stated "CStyleCheck v1.0.0" while §3.1 product version table correctly showed 1.2.0.  
**Correction:** Updated to "v1.2.0".  
**Status:** ✅ RESOLVED

### F-017 — MAN3 §3.2 SWE1 Version Stale (MODERATE)

**Severity:** Moderate  
**Document:** CSC-MAN3-001 §3.2  
**Finding:** CSC-SWE1-001 referenced as 1.3 (actual: 1.5 post-audit).  
**Correction:** Updated to 1.5.  
**Status:** ✅ RESOLVED

### F-018 — SUP1 Referenced Documents 5+ Versions Stale (CRITICAL)

**Severity:** Critical  
**Document:** CSC-SUP1-001 §3.1  
**Finding:** All five referenced documents were severely stale:

| Document | Was | Should Be |
|---|---|---|
| CSC-MAN3-001 | 1.0 | 1.5 |
| CSC-SUP8-001 | 1.1 | 1.6 |
| CSC-SUP9-001 | 1.0 | 1.1 |
| CSC-SUP10-001 | 1.0 | 1.1 |
| CSC-SWE4-001 | 1.0 | 1.6 |

**Correction:** Updated all five to current versions.  
**Status:** ✅ RESOLVED

### F-019 — SUP1 Purpose Text References v1.0.0 (MAJOR)

**Severity:** Major  
**Document:** CSC-SUP1-001 §3  
**Finding:** Purpose stated "CStyleCheck v1.0.0".  
**Correction:** Updated to "v1.2.0".  
**Status:** ✅ RESOLVED

### F-020 — SUP1 QO-006 and §5.4 Checklist Reference v1.0.0 (MAJOR)

**Severity:** Major  
**Document:** CSC-SUP1-001 §4 QO-006, §5.4  
**Finding:** Quality objective QO-006 stated "Zero open bug-labelled Issues at v1.0.0 tag" and §5.4 pre-release checklist referenced "targeting v1.0.0". Both reference a release that shipped ~6 weeks ago.  
**Correction:** Updated both to "v1.2.0".  
**Status:** ✅ RESOLVED

### F-021 — SUP1 §7 Version-Specific Language (MINOR)

**Severity:** Minor  
**Document:** CSC-SUP1-001 §7  
**Finding:** Non-conformance handling procedure stated "Assign to responsible party (Claude for v1.0.0)" — version-specific language that makes the procedure appear inapplicable to current/future releases.  
**Correction:** Updated to "Assign to responsible party (Dermot Murphy / Claude)" — version-independent.  
**Status:** ✅ RESOLVED

---

## 5. Post-Audit Document Version Map

| Document ID | Pre-Audit Version | Post-Audit Version |
|---|---|---|
| CSC-SVD-001 | 1.3 | **1.4** |
| CSC-SYS3-001 | 1.2 | **1.3** |
| CSC-SYS4-001 | 1.2 | **1.3** |
| CSC-SYS5-001 | 1.3 | **1.4** |
| CSC-SWE1-001 | 1.4 | **1.5** |
| CSC-SWE2-001 | 1.3 | **1.4** |
| CSC-SWE3-001 | 1.4 | **1.5** |
| CSC-SWE4-001 | 1.6 | 1.6 (no change) |
| CSC-SWE5-001 | 1.3 | 1.3 (no change) |
| CSC-SWE6-001 | 1.4 | 1.4 (no change) |
| CSC-SYS2-001 | 1.3 | 1.3 (no change) |
| CSC-MAN3-001 | 1.4 | **1.5** |
| CSC-SUP8-001 | 1.5 | **1.6** |
| CSC-SUP1-001 | 1.2 | **1.3** |
| CSC-PA2-001 | 1.7 | **1.8** |

---

## 6. Audit Verdict

| Category | Findings | Critical | Major | Moderate | Minor |
|---|---|---|---|---|---|
| SYS doc versions/text | F-001, F-002, F-003, F-004 | — | 2 | 1 | 1 |
| SWE1 versions/text | F-005, F-006 | — | 1 | 1 | — |
| SWE2 architecture accuracy | F-007, F-008, F-009, F-010 | 1 | 1 | 2 | — |
| SWE3 unit catalogue | F-011, F-012 | 1 | 1 | — | — |
| PA2 count accuracy | F-013, F-014 | 2 | — | — | — |
| SUP8 CI inventory | F-015 | 1 | — | — | — |
| MAN3 version/text | F-016, F-017 | — | 1 | 1 | — |
| SUP1 versions/text/QO | F-018, F-019, F-020, F-021 | 1 | 2 | — | 1 |
| **Total** | **21** | **6** | **8** | **5** | **2** |

**All Critical and Major findings have been resolved in this audit session.**

**Overall Audit Verdict: PASS (all critical and major defects resolved)**

> **Note — Deferred items from CSC-AUD-003:** F-012 (PA2 §4.1 CI count 27 vs §6 29) has now been resolved as F-014 of CSC-AUD-004. The PA2 §5.4 observation about missing GP 2.2.4 explicit coverage section is noted but deferred (evidence exists in SCM/change history; ASPICE assessor discretion applies).

---

*End of CSC-AUD-004*
