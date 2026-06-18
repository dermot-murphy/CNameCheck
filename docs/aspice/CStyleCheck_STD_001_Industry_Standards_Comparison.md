# Industry C Coding Standards — Comparative Analysis and CStyleCheck Coverage Report

*Automotive SPICE® PAM v4.0 | SUP.1 Quality Assurance — Technical Study*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CSC-STD-001 | **Version** | 1.2 |
| **Project** | CStyleCheck | **Date** | 2026-06-18 |
| **Status** | Released | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SUP.1 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.2 | 2026-06-18 | Claude | ASPICE audit #254 — sync referenced-document version citations to current versions |
| 1.1 | 2026-06-06 | Claude | Add `misc.file_length` (max lines per file) as unique opportunity #12; create change-request issues for all 12 opportunities |
| 1.0 | 2026-06-06 | Claude | Initial document — full survey of 11 industry standards with coverage matrix; closes issue #217 |

---

## 3. Purpose & Scope

This document surveys all major C coding standards that define concrete, mechanically checkable rules relevant to a style, naming, and structure checker. For each standard it assesses:

1. Whether rules can be enforced without a full compiler type-system (regex / AST-lite / pattern matching)
2. Which rules are already implemented in CStyleCheck
3. Which rules represent a unique opportunity for CStyleCheck (not already covered by a formatting linter or a MISRA C checker)
4. Which rules are not feasible without deep semantic analysis

The findings are presented in a unified coverage matrix and a prioritised list of candidate new rules.

### 3.1 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CSC-SWE1-001 | CStyleCheck Software Requirements Specification | 1.9 |
| CSC-SWE2-001 | CStyleCheck Software Architecture Design | 1.8 |
| CSC-SWE3-001 | CStyleCheck Software Detailed Design | 1.10 |

---

## 4. Standards Surveyed

| # | Standard | Publisher | Year | Availability | Primary Domain |
|---|---|---|---|---|---|
| S1 | Barr-C:2018 Embedded C Coding Standard | Barr Group | 2018 | Free PDF | Embedded C — style/naming |
| S2 | MISRA C:2012 (+AMD2) | MISRA Consortium | 2012/2023 | Paid (£25–£60) | Safety-critical C |
| S3 | SEI CERT C Coding Standard | CMU SEI | 2016 | Free (wiki + PDF) | Secure C (general purpose) |
| S4 | JPL C Coding Standard / "Power of 10" | NASA/JPL (Holzmann) | 2009 | Free PDF | Safety-critical embedded C |
| S5 | ESA C/C++ Coding Standard (BSSC 2000-1) | European Space Agency | 2000 | Free PDF | Space systems software |
| S6 | JSF AV C++ Coding Standard | Lockheed Martin | 2005 | Free PDF | Avionics C/C++ (F-35) |
| S7 | Linux Kernel Coding Style | Linux community | ongoing | Free (kernel.org) | OS / systems programming |
| S8 | AUTOSAR C++14 Guidelines | AUTOSAR Consortium | 2017–2022 | Partial (free AP) | Automotive C++ |
| S9 | IEC 61508-3 | IEC | 2010 | Paid | Functional safety (all domains) |
| S10 | DO-178C | RTCA | 2011 | Paid | Avionics software |
| S11 | ISO 26262 | ISO | 2018 | Paid | Automotive functional safety |
| S12 | FACE Technical Standard | The Open Group | 2022 | Members + free summary | Military avionics portability |
| S13 | CWE Top 25 | MITRE | ongoing | Free | Software weakness taxonomy |

---

## 5. Standards Providing No New Checkable Rules

The following standards mandate the **use** of an existing coding standard but define no new style or naming rules of their own.

| Standard | Stance | Recommended Standard |
|---|---|---|
| **IEC 61508-3** | Annex C lists language-subset techniques for SIL 2–4; defers to MISRA for C specifics | MISRA C |
| **DO-178C** | Requires a documented coding standard; does not specify rules | MISRA C or JSF AV C++ |
| **ISO 26262** | §6.4.5 recommends naming conventions (method 1h) and style guides (method 1g) but defines none | MISRA C or AUTOSAR C++14 |
| **FACE Technical Standard** | Defines C/C++ language "capability sets" (API portability); no style or naming rules | — |
| **CWE Top 25** | A weakness taxonomy, not a coding standard; maps onto CERT C | CERT C |
| **AUTOSAR C++14** | C++ focused; all C-applicable rules it adds are already in MISRA C:2012 | MISRA C |

---

## 6. Matrix Legend

All rules in the coverage matrix (§7) use the following symbols:

| Symbol | Meaning |
|---|---|
| 🟢 | **Covered by CStyleCheck** — rule is already implemented |
| ⭐ | **Unique CStyleCheck opportunity** — rule can be added and is **not** covered by astyle/uncrustify **or** a MISRA C checker |
| 🔵 | **CStyleCheck potential** — rule can be added but is already covered by astyle/uncrustify or a MISRA C checker |
| 🎨 | **Formatting linter** — covered by astyle or uncrustify |
| 📏 | **MISRA C checker** — covered by a MISRA C:2012 checker (Cppcheck `--misra`, PC-lint, QAC) |
| ❌ | **Not feasible** — requires full type system, control-flow graph, or inter-procedural analysis beyond CStyleCheck's scope |

> **Highlighting key:** In the matrix, the "CStyleCheck" column uses 🟢 for already-covered rules and ⭐ for unique opportunities not yet implemented. Rules marked ⭐ are the primary candidates for new development.

---

## 7. Coverage Matrix

### 7.1 JPL C Coding Standard / NASA "Power of Ten" (S4)

The ten rules were designed by Gerard J. Holzmann explicitly to be **mechanically verifiable** without a full compiler. They are among the most actionable rules for CStyleCheck.

| Rule | Description | CStyleCheck | astyle | MISRA C checker | Notes |
|---|---|---|---|---|---|
| P10-1 | No `goto`, `setjmp`, `longjmp` | 🔵 | — | 📏 MISRA 15.1, 21.4 | Could add `goto` check; MISRA already covers it |
| P10-2 | All loops have a fixed upper bound (no `while(1)` / `for(;;)` without a counter) | 🔵 | — | 📏 MISRA 15.4 | Partial: `for(;;)` detectable by regex |
| P10-3 | No dynamic memory after init (`malloc`/`calloc`/`realloc`/`free`) | 🔵 | — | 📏 MISRA 21.3 | Grep-detectable; MISRA 21.3 covers |
| P10-4 | Functions ≤ 60 lines (configurable) | ⭐ | — | — | **Not in MISRA or Barr-C**; line-count between braces; unique opportunity |
| P10-5 | Minimum assert density: ≥ 2 `assert()` calls per function | ⭐ | — | — | **Not in any other standard**; grep `assert(` per function scope; unique opportunity |
| P10-6 | Declare variables at smallest possible scope | 🔵 | — | 📏 MISRA 8.7 partial | MISRA 8.7 covers file-scope; function-scope harder |
| P10-7 | Check all non-void return values; validate all parameters | ❌ | — | 📏 MISRA 17.7 | Requires type analysis to know return type |
| P10-8 | Preprocessor limited to `#include` and simple `#define` | 🔵 | — | 📏 MISRA 20.x | MISRA 20.1–20.14 covers preprocessor use |
| P10-9 | No function pointer calls except simple cases | 🔵 | — | 📏 MISRA 18.6 partial | `(*fn)(…)` detectable by regex |
| P10-10 | Compile with all warnings; use static analysis | ❌ | — | — | Process/build rule, not a source-code rule |

**Summary (S4):** 2 unique opportunities (⭐), 5 already in MISRA, 2 not feasible.

---

### 7.2 SEI CERT C Coding Standard — Lightweight Subset (S3)

Most CERT C rules require type inference (integer range, pointer aliasing). The following subset is checkable without a type system.

#### 7.2.1 Preprocessor Rules (PRE)

| Rule ID | Description | CStyleCheck | astyle | MISRA C checker | Notes |
|---|---|---|---|---|---|
| PRE06-C | Header files must have include guards | 🟢 `include_guard.*` | — | 📏 MISRA Dir 4.10 | Fully covered |
| PRE04-C | Do not reuse a standard header file name | ⭐ | — | — | Filename-level check; not in MISRA; unique opportunity |
| PRE10-C | Multi-statement macros must be wrapped in `do { … } while(0)` | ⭐ | — | — | **Not in MISRA C:2012**; regex-detectable body pattern; unique opportunity |
| PRE11-C | Macro body must not end with a semicolon | ⭐ | — | — | **Not in MISRA C:2012**; simple regex `#define … ;$`; unique opportunity |
| PRE00-C | Prefer inline/static functions to function-like macros | 🔵 | — | 📏 MISRA Dir 4.9 | MISRA Dir 4.9 covers this; detectable by pattern |
| PRE01-C | Use parentheses around macro parameters | 🔵 | — | 📏 MISRA 20.7 | MISRA 20.7 requires parenthesisation |
| PRE02-C | Macro replacement lists must be parenthesised | 🔵 | — | 📏 MISRA 20.7 | MISRA 20.7 partial |
| PRE12-C | Unsafe macros must not evaluate arguments more than once | ❌ | — | — | Requires data-flow to detect multiple evaluation |

#### 7.2.2 Declarations Rules (DCL)

| Rule ID | Description | CStyleCheck | astyle | MISRA C checker | Notes |
|---|---|---|---|---|---|
| DCL37-C | No identifiers with names that begin with underscore | 🟢 `reserved_name` | — | 📏 MISRA 21.1 | Covered; MISRA 21.1 also covers |
| DCL31-C | Declare identifiers before using them | ❌ | — | 📏 MISRA 8.x | Requires forward-reference tracking |
| DCL30-C | Declare objects with appropriate storage duration | ❌ | — | — | Requires type/lifetime analysis |

#### 7.2.3 Miscellaneous Rules (MSC)

| Rule ID | Description | CStyleCheck | astyle | MISRA C checker | Notes |
|---|---|---|---|---|---|
| MSC17-C | Every `switch` case must end with `break` or explicit fall-through comment | 🔵 | — | 📏 MISRA 16.3 | MISRA 16.3 (mandatory); brace-level pattern |
| MSC12-C | No statements with no effect (e.g. bare expression `;`) | 🔵 | — | 📏 MISRA 2.2 | MISRA 2.2 covers dead code / no-effect |
| MSC07-C | Detect and remove dead code | 🔵 | — | 📏 MISRA 2.1, 2.2 | MISRA 2.1 covers unreachable code |
| MSC01-C | Switch must have a default label | 🔵 | — | 📏 MISRA 16.4 | MISRA 16.4 (required) |

**Summary (S3):** 2 already covered (🟢), 3 unique opportunities (⭐), 7 already in MISRA, 3 not feasible.

---

### 7.3 JSF AV C++ Coding Standard — C-Applicable Rules (S6)

Publicly available at stroustrup.com. The following rules apply to C (not C++ specific).

#### 7.3.1 Naming Conventions

| JSF Rule | Description | CStyleCheck | astyle | MISRA C checker | Notes |
|---|---|---|---|---|---|
| AV Rule 47 | All words in identifier separated by `_` | 🟢 Barr-C naming | — | — | CStyleCheck enforces snake_case variants |
| AV Rule 48 | Identifiers must not begin with `_` | 🟢 `reserved_name` | — | 📏 MISRA 21.1 | Fully covered |
| AV Rule 67 | Pointer types named with `p` prefix | 🟢 `variable.pointer_prefix` | — | — | Covered (Barr-C `p_` prefix) |
| AV Rule 69 | Global variables prefixed `g_` | ⭐ | — | — | **Not in Barr-C or MISRA**; requires variable scope detection; unique opportunity |
| AV Rule 71 | Constants and macros: `ALL_CAPS` | 🟢 `constant.*` / `macro.*` | — | — | Fully covered |
| AV Rule 45 | No function names longer than 31 characters | ⭐ | — | — | Identifier length limit; regex-checkable; unique opportunity |
| AV Rule 57 | All source files must have a standard header block | 🟢 `misc.copyright_header` partial | — | — | CStyleCheck copyright_header partially covers; could extend to require specific fields |

#### 7.3.2 Control Flow & Structure

| JSF Rule | Description | CStyleCheck | astyle | MISRA C checker | Notes |
|---|---|---|---|---|---|
| AV Rule 189 | Every `case` in a `switch` must terminate with `break` | 🔵 | — | 📏 MISRA 16.3 | MISRA 16.3 |
| AV Rule 192 | Null statements must be on their own line and commented | ⭐ | — | — | Bare `;` line requires a comment; unique opportunity |
| AV Rule 196 | Functions shall have a single entry point | ❌ | — | — | Always true in C; targets C++ |
| AV Rule 200 | Functions shall not be longer than 200 logical source lines | ⭐ | — | — | Function length limit (complementary to Power of 10); unique opportunity |

#### 7.3.3 No Unsafe Language Features

| JSF Rule | Description | CStyleCheck | astyle | MISRA C checker | Notes |
|---|---|---|---|---|---|
| AV Rule 111 | No variadic functions (`...` parameter) | 🔵 | — | 📏 MISRA 17.1 | MISRA 17.1 covers |
| AV Rule 119 | No recursion | 🔵 | — | 📏 MISRA 17.2 | MISRA 17.2 covers |
| AV Rule 206 | No dynamic memory (`malloc`/`free`) | 🔵 | — | 📏 MISRA 21.3 | MISRA 21.3 covers |

**Summary (S6):** 7 already covered (🟢), 5 unique opportunities (⭐), 5 already in MISRA, 1 not feasible.

---

### 7.4 ESA C/C++ Coding Standard BSSC(2000)1 (S5)

#### 7.4.1 Comment and Documentation Rules

| ESA Rule | Description | CStyleCheck | astyle | MISRA C checker | Notes |
|---|---|---|---|---|---|
| ESA-R-1 | All functions must have a header comment naming function, purpose, parameters, return value | ⭐ | — | — | **Not in MISRA or Barr-C**; regex for `@param`/`@brief`/`@return` before function; unique opportunity |
| ESA-R-2 | Comment ratio: ratio of comment lines to total lines shall be ≥ threshold | 🟢 `misc.comment_ratio` | — | — | Fully covered |
| ESA-R-3 | File header must include name, purpose, author, date | 🟢 `misc.copyright_header` partial | — | — | Copyright header check covers part of this |

#### 7.4.2 Naming and Identifier Rules

| ESA Rule | Description | CStyleCheck | astyle | MISRA C checker | Notes |
|---|---|---|---|---|---|
| ESA-R-4 | No single-character identifiers except loop counters (`i`, `j`, `k`) | ⭐ | — | — | **Not in MISRA or Barr-C explicitly**; regex `\b[a-z]\b` excluding `i`, `j`, `k`; unique opportunity |
| ESA-R-5 | No identifiers beginning or ending with underscore | 🟢 `reserved_name` | — | 📏 MISRA 21.1 | Covered |
| ESA-R-6 | No ambiguous identifiers differing only in case | ❌ | — | — | Requires cross-identifier comparison; complex |
| ESA-R-7 | Identifiers shall be at least 3 characters long (except loop counters) | ⭐ | — | — | Configurable minimum length; regex-checkable; unique opportunity |

#### 7.4.3 Structural Rules

| ESA Rule | Description | CStyleCheck | astyle | MISRA C checker | Notes |
|---|---|---|---|---|---|
| ESA-R-8 | One statement per line | 🔵 | 🎨 astyle `-j` | 📏 MISRA — | astyle enforces; MISRA-related |
| ESA-R-9 | No more than one declaration per line | 🔵 | 🎨 astyle | — | astyle can enforce |
| ESA-R-10 | Functions shall have a single `return` statement | 🔵 | — | 📏 MISRA 15.5 | MISRA 15.5 (advisory) |
| ESA-R-11 | `break` shall not be used outside `switch` | 🔵 | — | 📏 MISRA 15.3 | MISRA 15.3 |

**Summary (S5):** 3 already covered (🟢), 4 unique opportunities (⭐), 4 already in astyle/MISRA, 1 not feasible.

---

### 7.5 Linux Kernel Coding Style (S7)

Enforced mechanically by `scripts/checkpatch.pl`.

| Rule | Description | CStyleCheck | astyle | MISRA C checker | Notes |
|---|---|---|---|---|---|
| LK-1 | Indentation: hard tabs, 8-space equivalent | 🟢 `misc.indentation` | 🎨 astyle | — | CStyleCheck configurable; astyle covers |
| LK-2 | Line length ≤ 80 characters (≤ 100 with justification) | 🟢 `misc.line_length` | 🎨 astyle `-l80` | — | Fully covered |
| LK-3 | `lower_snake_case` for all variable, function, struct names | 🟢 Barr-C naming | — | — | CStyleCheck naming rules cover |
| LK-4 | `UPPER_SNAKE_CASE` for macros and constants | 🟢 `constant.*` / `macro.*` | — | — | Fully covered |
| LK-5 | No trailing whitespace at end of lines | 🔵 | 🎨 astyle `-xd` | — | astyle covers; CStyleCheck could add but low priority |
| LK-6 | K&R brace style (`{` on same line as statement) | 🔵 | 🎨 astyle `-A3` | — | astyle primary tool for this |
| LK-7 | Spaces around binary operators; no space before `(` in function calls | 🔵 | 🎨 astyle | — | astyle covers operator spacing |
| LK-8 | Blank line after last local variable declaration | ⭐ | — | — | **Not in MISRA or astyle**; blank-line pattern after last declaration block; unique opportunity |
| LK-9 | No Hungarian notation (no `iCounter`, `bFlag`, etc.) | 🟢 Barr-C naming partial | — | — | CStyleCheck naming rules discourage type prefixes |
| LK-10 | Comment style: `/* */` for multi-line, `//` only in C99+ | 🔵 | — | 📏 MISRA Dir 4.1 partial | MISRA Dir 4.1 on comment style |
| LK-11 | Descriptive names for global variables and exported functions | ❌ | — | — | Subjective; not mechanically checkable |
| LK-12 | No `typedef` for structs/enums (kernel preference) | ❌ | — | — | Contradicts Barr-C; policy choice |

**Summary (S7):** 5 already covered (🟢), 1 unique opportunity (⭐), 4 covered by astyle, 2 not feasible/policy conflicts.

---

### 7.6 Barr-C:2018 Rules Already Implemented (S1)

For completeness, the following Barr-C rule categories are already fully or substantially covered by CStyleCheck:

| Barr-C Category | CStyleCheck Rules | Coverage |
|---|---|---|
| 6.x — Functions: naming conventions | `function.*` rules | 🟢 Full |
| 7.x — Variables: naming conventions | `variable.*` rules (pointer, parameter, global, local) | 🟢 Full |
| 8.x — Constants/Macros: naming conventions | `constant.*`, `macro.*` rules | 🟢 Full |
| 5.x — Types: typedef, enum, struct naming | `typedef.*`, `enum.*`, `struct.*` rules | 🟢 Full |
| 9.8.x — Include guards | `include_guard.*` | 🟢 Full |
| 5.3 — Yoda conditions prohibited | `misc.yoda_condition` | 🟢 Full |
| 8.x — Integer literal suffixes (U/u, L/l) | `misc.unsigned_suffix`, `misc.lowercase_l_suffix` | 🟢 Full |
| 9.x — Line length | `misc.line_length` | 🟢 Full |
| 9.x — Indentation | `misc.indentation` | 🟢 Full |
| File header / copyright | `misc.copyright_header` | 🟢 Full |
| EOF comment | `misc.eof_comment` | 🟢 Full |
| Reserved identifiers | `reserved_name` | 🟢 Full |

---

### 7.7 Additional CStyleCheck Rules (Beyond Barr-C/MISRA)

Rules currently implemented in CStyleCheck that go beyond the base standards:

| CStyleCheck Rule | Description | Source inspiration |
|---|---|---|
| `misc.comment_ratio` | Minimum ratio of comment lines to total lines per file | ESA, various |
| `misc.whitespace_ratio` | Maximum ratio of blank lines to total lines per file | CStyleCheck original |
| `misc.declared_not_defined` | Cross-file: function declared in `.h` but never defined in a `.c` | CStyleCheck original |
| `misc.block_comment_spacing` | Correct spacing inside block comment delimiters | Barr-C style |
| `sign_compatibility` | Cross-file signed/unsigned parameter compatibility | CStyleCheck original |
| `spell_check` | Spell-checking identifiers against a dictionary | CStyleCheck original |

---

## 8. Consolidated Unique Opportunity Rules (⭐)

The following rules represent the highest-priority candidates for new CStyleCheck features. All are **mechanically checkable** and **not already covered** by astyle/uncrustify or a MISRA C checker:

| Priority | Rule | Source | Category | Implementation Approach |
|---|---|---|---|---|
| 🟥 1 | Function length limit (configurable, default 60 lines) | Power of 10 Rule 4, JSF AV Rule 200 | Complexity | Count source lines between matching `{` `}` for function definitions |
| 🟥 2 | Minimum `assert()` density per function (configurable, default 1) | Power of 10 Rule 5 | Reliability | Grep `assert(` within each function scope |
| 🟥 3 | Multi-statement macros must be wrapped in `do { … } while(0)` | CERT PRE10-C | Preprocessor | Regex: `#define` body with `;` and no `do{…}while(0)` wrapper |
| 🟥 4 | Macro body must not end with a trailing `;` | CERT PRE11-C | Preprocessor | Regex: `#define \S+ .+;$` |
| 🟧 5 | Mandatory function header comment (`@brief`/`@param`/`@return`) | ESA-R-1, JSF, Doxygen | Documentation | Regex for structured comment block immediately preceding function definition |
| 🟧 6 | Global variables must be prefixed `g_` (configurable) | JSF AV Rule 69 | Naming | Detect file-scope non-`static` variable declarations; check prefix |
| 🟧 7 | Identifier minimum length (configurable, default 3, exempt `i`/`j`/`k`) | ESA-R-4, ESA-R-7 | Naming | Regex: identifier token length |
| 🟧 8 | Null/empty statement must be on own line with comment | JSF AV Rule 192 | Style | Regex: bare `;` on a line with no preceding statement |
| 🟧 9 | No standard header filename reuse | CERT PRE04-C | Preprocessor | Check source filenames against a list of POSIX/C standard header names |
| 🟨 10 | Blank line required after last local variable declaration block | Linux Kernel LK-8 | Formatting | Pattern: non-declaration line after declaration block with no blank line separator |
| 🟨 11 | Identifier length maximum (configurable, default 31) | JSF AV Rule 45 | Naming | Regex: identifier token length |
| 🟨 12 | Maximum lines per file (configurable, default 500) | ESA, industry practice | Complexity | Count all source lines (including blank/comment lines) in each file; flag when exceeding threshold |

---

## 9. Rules Covered by Astyle / Uncrustify (Not CStyleCheck Primary Domain)

These rules are best handled by a dedicated formatting tool. CStyleCheck should not duplicate them.

| Rule | Tool | Notes |
|---|---|---|
| Brace placement (K&R, Allman, GNU) | astyle `-A1`/`-A3` | Formatting only |
| Indentation width and tab/space conversion | astyle `-t` / uncrustify | Formatting only |
| Operator and punctuation spacing | astyle | Formatting only |
| Trailing whitespace removal | astyle `-xd` | Formatting only |
| One statement per line | astyle `-j` | Partial; some cases |
| Blank line between functions | astyle `-xb` | Formatting only |
| Pointer alignment (`int *p` vs `int* p`) | astyle `--align-pointer` | Formatting only |

---

## 10. Comprehensive Summary Matrix

| Rule | Source | CStyleCheck | astyle | MISRA C | Feasible |
|---|---|---|---|---|---|
| Include guards in header files | CERT PRE06-C, MISRA Dir 4.10, Barr-C 9.8 | 🟢 | — | 📏 | ✅ |
| Prefer inline/static over function-like macros | CERT PRE00-C, MISRA Dir 4.9 | 🔵 | — | 📏 | ✅ |
| Parenthesise macro parameters | CERT PRE01-C, MISRA 20.7 | 🔵 | — | 📏 | ✅ |
| Do not reuse standard header names | CERT PRE04-C | ⭐ | — | — | ✅ |
| Multi-statement macros in `do{}while(0)` | CERT PRE10-C | ⭐ | — | — | ✅ |
| No trailing `;` in macro body | CERT PRE11-C | ⭐ | — | — | ✅ |
| No leading underscore in identifiers | CERT DCL37-C, MISRA 21.1 | 🟢 | — | 📏 | ✅ |
| `switch` case ends with `break` | CERT MSC17-C, MISRA 16.3, JSF 189 | 🔵 | — | 📏 | ✅ |
| `switch` must have `default` label | CERT MSC01-C, MISRA 16.4 | 🔵 | — | 📏 | ✅ |
| No dead code / unreachable code | CERT MSC07-C, MISRA 2.1 | 🔵 | — | 📏 | ⚠️ Partial |
| No statements with no effect | CERT MSC12-C, MISRA 2.2 | 🔵 | — | 📏 | ⚠️ Partial |
| No `goto` | Power of 10 R1, MISRA 15.1 | 🔵 | — | 📏 | ✅ |
| No `setjmp`/`longjmp` | Power of 10 R1, MISRA 21.4 | 🔵 | — | 📏 | ✅ |
| No recursion | Power of 10 R1, MISRA 17.2 | 🔵 | — | 📏 | ⚠️ Direct only |
| Fixed upper bound on all loops | Power of 10 R2, MISRA 15.4 | 🔵 | — | 📏 | ⚠️ Partial |
| No dynamic memory allocation | Power of 10 R3, MISRA 21.3 | 🔵 | — | 📏 | ✅ |
| **Function length limit** | **Power of 10 R4, JSF 200** | **⭐** | **—** | **—** | **✅** |
| **Minimum assert density per function** | **Power of 10 R5** | **⭐** | **—** | **—** | **✅** |
| Minimal data scope | Power of 10 R6, MISRA 8.7 | 🔵 | — | 📏 | ⚠️ |
| Check non-void return values | Power of 10 R7, MISRA 17.7 | ❌ | — | 📏 | ❌ type needed |
| Limit preprocessor to `#include`/`#define` | Power of 10 R8, MISRA 20.x | 🔵 | — | 📏 | ✅ |
| Restrict function pointers | Power of 10 R9, MISRA 18.6 | 🔵 | — | 📏 | ⚠️ |
| No variadic functions | MISRA 17.1, JSF 111 | 🔵 | — | 📏 | ✅ |
| All words in identifier separated by `_` | JSF 47, Barr-C 7.x | 🟢 | — | — | ✅ |
| **Global variables prefixed `g_`** | **JSF 69** | **⭐** | **—** | **—** | **✅** |
| Pointer variable `p` prefix | JSF 67, Barr-C 7.1.k | 🟢 | — | — | ✅ |
| Constants/macros `ALL_CAPS` | JSF 71, Barr-C 8.x | 🟢 | — | — | ✅ |
| **Mandatory function header comment** | **ESA-R-1, JSF doc rules** | **⭐** | **—** | **—** | **✅** |
| **No single-character identifiers (exc. loop counters)** | **ESA-R-4** | **⭐** | **—** | **—** | **✅** |
| **Minimum identifier length** | **ESA-R-7** | **⭐** | **—** | **—** | **✅** |
| Comment ratio ≥ threshold | ESA-R-2 | 🟢 | — | — | ✅ |
| File header block | ESA-R-3, JSF | 🟢 | — | — | ✅ |
| One statement per line | ESA-R-8 | 🔵 | 🎨 | — | ✅ |
| Single `return` per function | ESA-R-10, MISRA 15.5 | 🔵 | — | 📏 | ✅ |
| lower_snake_case for identifiers | Linux LK-3, Barr-C | 🟢 | — | — | ✅ |
| UPPER_SNAKE_CASE for macros | Linux LK-4, Barr-C | 🟢 | — | — | ✅ |
| Line length ≤ 80/100 chars | Linux LK-2, Barr-C | 🟢 | 🎨 | — | ✅ |
| Indentation consistency | Linux LK-1, Barr-C | 🟢 | 🎨 | — | ✅ |
| Trailing whitespace | Linux LK-5 | 🔵 | 🎨 | — | ✅ |
| K&R brace placement | Linux LK-6 | 🔵 | 🎨 | — | ✅ |
| **Blank line after declaration block** | **Linux LK-8** | **⭐** | **—** | **—** | **✅** |
| **Null statement on own line with comment** | **JSF 192** | **⭐** | **—** | **—** | **✅** |
| **No standard header filename reuse** | **CERT PRE04-C** | **⭐** | **—** | **—** | **✅** |
| **Maximum lines per file** | **ESA, industry practice** | **⭐** | **—** | **—** | **✅** |
| Yoda conditions | Barr-C 5.3 | 🟢 | — | — | ✅ |
| Unsigned literal suffix `U` not `u` | Barr-C 8.x | 🟢 | — | — | ✅ |
| `L` suffix not `l` | Barr-C 8.x | 🟢 | — | — | ✅ |
| Integer literal suffixes | Barr-C 8.x | 🟢 | — | — | ✅ |
| Blank-line density limit | CStyleCheck | 🟢 | — | — | ✅ |
| Cross-file: declared but not defined | CStyleCheck | 🟢 | — | — | ✅ |
| Spell-check identifiers | CStyleCheck | 🟢 | — | — | ✅ |
| EOF comment marker | CStyleCheck | 🟢 | — | — | ✅ |
| Block comment spacing | Barr-C style | 🟢 | — | — | ✅ |

---

## 11. Statistics

| Category | Count |
|---|---|
| 🟢 Rules already covered by CStyleCheck | 22 |
| ⭐ Unique CStyleCheck opportunities (not in astyle or MISRA) | 12 |
| 🔵 Could add to CStyleCheck (astyle or MISRA already covers) | 17 |
| ❌ Not feasible without type system / semantic analysis | 3 |
| 🎨 Best handled by astyle/uncrustify | 7 |
| 📏 Fully covered by MISRA C checkers | 15 |
| **Total rules assessed** | **55** |

---

## 12. Conclusions and Recommendations

### 12.1 Standards Yielding Highest Value for CStyleCheck

| Rank | Standard | Unique Rules Added | Reason |
|---|---|---|---|
| 1 | JPL/Power of 10 (S4) | 2 (function length, assert density) | Explicitly designed for mechanical checking; rules not in MISRA or Barr-C |
| 2 | CERT C — PRE/MSC (S3) | 3 (PRE10, PRE11, PRE04) | Lightweight; preprocessor correctness rules absent from MISRA C:2012 |
| 3 | JSF AV C++ (S6) | 5 (g_ prefix, identifier length, null stmt, function length, header comment) | Widely cited avionics standard; rules complement existing CStyleCheck naming suite |
| 4 | ESA BSSC (S5) | 4 (function header, min identifier length, single-char ban, comment density) | Space-grade; function header Doxygen requirement adds documentation quality |
| 5 | Linux Kernel (S7) | 1 (blank line after declarations) | Mostly covered by astyle; one unique structural rule |

### 12.2 Recommended Implementation Order

1. **Function length limit** (Power of 10 R4 / JSF Rule 200) — pure line counting; configurable threshold; high practitioner demand
2. **Multi-statement macro do-while wrapper** (CERT PRE10-C) — regex; few false positives; no similar rule in MISRA C:2012
3. **Trailing semicolon in macro body** (CERT PRE11-C) — one-line regex; catches common bug
4. **Mandatory Doxygen-style function header** (ESA / JSF) — regex for `@brief`/`@param`/`@return` block; links to existing block-comment infrastructure
5. **Minimum assert density** (Power of 10 R5) — counts `assert(` occurrences per function scope; unique reliability metric
6. **Global variable `g_` prefix** (JSF Rule 69) — file-scope variable detection; natural extension of existing naming suite
7. **Identifier length limits** (JSF Rule 45 + ESA-R-7) — min/max configurable; pure regex token check
8. **Maximum lines per file** — total line count per file; configurable threshold; natural companion to existing `misc.function_length`

### 12.3 Standards Not Recommended for Extension

- **IEC 61508**, **DO-178C**, **ISO 26262** — These are process standards that add no new checkable rules; compliance is satisfied by existing MISRA C coverage.
- **AUTOSAR C++14** — C++ focused; all C rules overlap with MISRA C:2012.
- **FACE Technical Standard** — API portability layer; no style or naming rules.

---

## 13. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | Approved | 2026-06-06 |
| Technical Reviewer | Dermot Murphy | Pending | — |
| Quality Assurance | Dermot Murphy | Pending | — |
| Approver | Dermot Murphy | Pending | — |

> **Note:** This document is under configuration management (SUP.8). Post-approval changes require a change request (SUP.10) and a new document version.

---

*End of Industry Standards Comparison Report — CSC-STD-001 v1.1*
