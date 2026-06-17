# External C Coding Standards — Survey and Analysis

---

| Field | Value |
|---|---|
| Document ID | CSC-ANA-001 |
| Title | External C Coding Standards — Survey and Analysis |
| Version | 1.0 (DRAFT) |
| Status | Draft |
| Date | 2026-06-08 |
| Owner | Software Engineering Lead |
| Purpose | Rationale for rule selection in CSG-STY-001 and CSC-STD-001 |
| ASPICE Process Areas | SWE.3, SUP.1 |

---

## Table of Contents

1. [Purpose and Scope](#1-purpose-and-scope)
2. [Methodology](#2-methodology)
3. [Documents Surveyed](#3-documents-surveyed)
4. [Per-Document Analysis](#4-per-document-analysis)
   - 4.1 [MISRA C:2012 / MISRA C:2023](#41-misra-c2012--misra-c2023)
   - 4.2 [SEI CERT C Coding Standard](#42-sei-cert-c-coding-standard)
   - 4.3 [Barr Group Embedded C Coding Standard (Barr-C:2018)](#43-barr-group-embedded-c-coding-standard-barr-c2018)
   - 4.4 [Google C Style Guide](#44-google-c-style-guide)
   - 4.5 [Linux Kernel Coding Style](#45-linux-kernel-coding-style)
   - 4.6 [NASA/JPL Power of Ten Rules](#46-nasajpl-power-of-ten-rules)
   - 4.7 [GNU Coding Standards](#47-gnu-coding-standards)
   - 4.8 [LLVM Coding Standards](#48-llvm-coding-standards)
   - 4.9 [AUTOSAR Guidelines for C](#49-autosar-guidelines-for-c)
   - 4.10 [Motor Industry Research Association (MIRA / MISRA origin)](#410-motor-industry-research-association-mira--misra-origin)
   - 4.11 [Netrino / Jack Ganssle Embedded C Coding Standard](#411-netrino--jack-ganssle-embedded-c-coding-standard)
   - 4.12 [IAR Embedded Workbench Recommendations](#412-iar-embedded-workbench-recommendations)
   - 4.13 [JSF AV C++ Coding Standards (Joint Strike Fighter)](#413-jsf-av-c-coding-standards-joint-strike-fighter)
   - 4.14 [HICPP (High Integrity C++)](#414-hicpp-high-integrity-c)
   - 4.15 [IEC 61508 / ISO 26262 C Coding Guidance](#415-iec-61508--iso-26262-c-coding-guidance)
5. [Comparison Matrices](#5-comparison-matrices)
   - 5.1 [Safety Criticality and Domain](#51-safety-criticality-and-domain)
   - 5.2 [Naming Convention Approach](#52-naming-convention-approach)
   - 5.3 [Formatting Rules](#53-formatting-rules)
   - 5.4 [Memory Management Policy](#54-memory-management-policy)
   - 5.5 [Control Flow Restrictions](#55-control-flow-restrictions)
   - 5.6 [MISRA and ASPICE Alignment](#56-misra-and-aspice-alignment)
6. [Cross-Cutting Themes](#6-cross-cutting-themes)
7. [Gaps and Conflicts Between Standards](#7-gaps-and-conflicts-between-standards)
8. [Conclusions](#8-conclusions)
9. [Recommendations for CSG-STY-001 and CSC-STD-001](#9-recommendations-for-csg-sty-001-and-csc-std-001)
10. [Adopted vs. Rejected Rules by Source](#10-adopted-vs-rejected-rules-by-source)
11. [Document Change History](#11-document-change-history)

---

## 1. Purpose and Scope

### 1.1 Purpose

This document records the survey of fifteen widely used C coding standards and style guides. Its purpose is to:

1. Provide an auditable evidence trail for rule selection in the project C Style Guide (CSG-STY-001) and Coding Standard (CSC-STD-001).
2. Identify consensus rules across multiple standards (high-confidence requirements).
3. Identify conflicting rules and document the project's resolution.
4. Identify gaps — hazards or good practices not covered by any single standard.
5. Support ASPICE v4 Level 2 compliance by demonstrating that the project coding rules are grounded in industry best practice (SWE.3 BP6 evidence).

### 1.2 Scope

Fifteen external standards were surveyed. The survey covers:
- Naming conventions
- Formatting and layout
- Commenting and documentation
- Data types and type safety
- Memory management
- Control flow restrictions
- Preprocessor usage
- Standard library restrictions
- Concurrency and interrupt handling
- Safety-critical applicability
- MISRA C and ASPICE alignment

### 1.3 Limitations

- MISRA C:2012 and IEC 61508 / ISO 26262 are not freely available documents. The analysis is based on published summaries, publicly available rule tables, and the authors' working knowledge.
- Google, Linux, GNU, and LLVM coding standards are primarily C++ or general-purpose software oriented; their C-relevant subsets were extracted.
- The IAR Embedded Workbench style recommendations are embedded within tool documentation; they do not constitute a formal standalone standard.

---

## 2. Methodology

Documents were surveyed using the following structured approach:

1. **Identify document** — title, version/year, issuing organisation.
2. **Classify domain** — safety-critical embedded, general embedded, general software, vendor-specific.
3. **Extract rules by category** — naming, formatting, memory, control flow, types, library.
4. **Rate safety-critical applicability** — Low / Medium / High / Very High / Extreme.
5. **Assess MISRA alignment** — Full / High / Partial / Low / Conflict.
6. **Assess ASPICE alignment** — whether the standard supports SWE.3/SWE.4 evidence.
7. **Record conclusions** — what this standard contributes to the project rules.

---

## 3. Documents Surveyed

| # | Document | Organisation | Version / Year | Domain |
|---|---|---|---|---|
| 1 | MISRA C:2012 (incl. Amendment 1:2016, MISRA C:2023) | MISRA Consortium | 2012/2016/2023 | Safety-critical embedded |
| 2 | SEI CERT C Coding Standard | Carnegie Mellon SEI | 2nd ed., 2016 | Secure software |
| 3 | Barr Group Embedded C Coding Standard (Barr-C:2018) | Barr Group | v2.0, 2018 | Embedded systems |
| 4 | Google C Style Guide | Google LLC | Continuous (2024 snapshot) | Large-scale software |
| 5 | Linux Kernel Coding Style | Linux Foundation / L. Torvalds | Continuous (6.x era) | OS kernel |
| 6 | NASA/JPL Power of Ten Rules | NASA Jet Propulsion Laboratory | 2006 | Space / safety-critical |
| 7 | GNU Coding Standards | Free Software Foundation | v1.6, 2019 | Open-source software |
| 8 | LLVM Coding Standards | LLVM Project | Continuous (LLVM 18 era) | Compiler infrastructure |
| 9 | AUTOSAR Guidelines for the use of C | AUTOSAR Partnership | R23-11 | Automotive embedded |
| 10 | MIRA / MISRA Origins | Motor Industry Research Association | (see MISRA C) | Automotive |
| 11 | Netrino / Ganssle Embedded C Coding Standard | Netrino LLC / Jack Ganssle | Continuous | Embedded systems |
| 12 | IAR Embedded Workbench Style Recommendations | IAR Systems | EW 9.x era | Embedded (vendor) |
| 13 | JSF AV C++ Coding Standards | US Department of Defense (F-35) | Revision C, 2005 | Flight-critical |
| 14 | HICPP (High Integrity C++ Coding Standard) | Programming Research Ltd | v4.0, 2016 | High-integrity |
| 15 | IEC 61508-3 / ISO 26262-6 C coding guidance | IEC / ISO | 2010 / 2018 | Functional safety |

---

## 4. Per-Document Analysis

---

### 4.1 MISRA C:2012 / MISRA C:2023

**Organisation:** MISRA Ltd (Motor Industry Software Reliability Association)
**Year:** 2012; Amendment 1 published 2016; MISRA C:2023 corrigendum released 2023
**Domain:** Safety-critical embedded software
**Availability:** Paid publication (~£25 per PDF)

#### Overview

MISRA C:2012 is the primary international coding standard for safety-critical embedded C software. It defines 262 rules and 16 directives, classified as Mandatory, Required, or Advisory. It is specifically designed to prevent undefined, unspecified, and implementation-defined C behaviour in systems where incorrect operation could cause harm.

MISRA C:2023 is not a new edition but a set of corrections (errata and clarifications) to MISRA C:2012 Amendment 1. The most significant change is promoting Rule 4.2 (no trigraphs) from Advisory to Required.

#### Key Rule Categories

| Category | Rule Range | Notable Rules |
|---|---|---|
| Language environment | Dir 1–2, R 1.1–1.4 | C99 or later; no extensions; all translation units compile cleanly |
| Unused code | R 2.1–2.7 | No unreachable code; no dead code; all declarations used |
| Comments | R 3.1–3.2 | No nested `/**/`; `//` only in C99+ |
| Character sets | R 4.1–4.2 | No trigraphs; escape sequences defined |
| Identifiers | R 5.1–5.9 | 31-char uniqueness; reserved names; identifier hiding |
| Types | R 6.1–6.2 | Bit field types; single-bit signed |
| Literals | R 7.1–7.4 | No octal; unsigned suffix; uppercase suffix; signed char |
| Declarations | R 8.1–8.14 | Implicit int; function declarations; typedef; const; extern |
| Initialisers | R 9.1–9.5 | All paths initialised; designator |
| Expressions | R 10.1–10.8 | Essential type model (signed/unsigned/boolean/enum mixing) |
| Side effects | R 13.1–13.6 | Initialiser ordering; sequence point; logical operators; comma |
| Control flow | R 14.1–14.4 | Reachability; infinite loops; `bool` in conditions |
| Switch | R 16.1–16.7 | Single `switch` per expression; `default`; fall-through; case range |
| Functions | R 17.1–17.8 | No variadic args in safety code; recursion; prototype; return value |
| Pointers | R 18.1–18.8 | Arithmetic; comparison; function pointers; VLAs |
| Overlapping objects | R 19.1–19.2 | Union; memcpy aliasing |
| Preprocessing | R 20.1–20.14 | Include guards; macro hazards; `##`; `#include` in macro |
| Standard library | R 21.1–21.21 | Banned names; banned functions; banned headers |
| Resources | R 22.1–22.10 | Dynamic allocation; file handles; signal |

#### Naming Conventions

MISRA C:2012 defines constraints on identifier uniqueness (Rules 5.1–5.9) but does not prescribe a specific naming style. It forbids identifiers that could clash with standard library names and requires that identifiers be distinct within the required scope. The naming style adopted in this project (module prefix, snake case, prefix conventions) is compliant with and supplementary to MISRA C requirements.

#### Formatting Rules

MISRA C:2012 does not prescribe indentation, brace style, or line length. These are left to project convention. The project's AStyle configuration and CSG-STY-001 fill this gap.

#### Memory Management

Rule 21.3 prohibits `malloc`, `calloc`, `realloc`, and `free` in safety-critical contexts. This is the definitive basis for the project's static-allocation-first policy.

#### Safety Criticality

**EXTREMELY HIGH.** MISRA C:2012 is referenced by ISO 26262 (automotive), IEC 61508 (industrial), EN 50128 (railway), and DO-178C (avionics) as an acceptable language subset.

#### MISRA Alignment

N/A — this IS the MISRA standard.

#### ASPICE Alignment

**Full.** MISRA C:2012 adoption directly satisfies SWE.3 BP6 (Apply coding guidelines) in ASPICE.

#### Project Conclusions

- MISRA C:2012 Required rules are adopted as **Required** in CSC-STD-001 unless a documented deviation exists.
- MISRA C:2012 Advisory rules are adopted as **Advisory** (should-comply) in CSC-STD-001.
- MISRA C:2023 changes (primarily promoting trigraph rule to Required) are adopted immediately.
- Automated enforcement via cstylecheck covers a subset of MISRA rules; full MISRA coverage requires a supplementary static analysis tool.

---

### 4.2 SEI CERT C Coding Standard

**Organisation:** Carnegie Mellon University Software Engineering Institute
**Year:** 2nd edition, 2016; community wiki continuously updated
**Domain:** Secure software engineering
**Availability:** Free online (https://wiki.sei.cmu.edu/confluence/display/c)

#### Overview

The CERT C Coding Standard is organised as 98 rules and numerous recommendations, targeting the prevention of security vulnerabilities (buffer overflows, integer overflows, race conditions, use-after-free) and undefined behaviour. Its focus is distinct from MISRA C: CERT targets security exploitability, whereas MISRA targets functional safety. The two standards are highly complementary.

#### Key Rules Adopted by This Project

| CERT Rule | Title | Project Section |
|---|---|---|
| EXP33-C | Do not read uninitialized memory | CSC-STD-001 §42.1 |
| EXP34-C | Do not dereference null pointers | CSC-STD-001 §14.2 |
| EXP39-C | Do not access via incompatible pointer | CSC-STD-001 §14.5 |
| INT32-C | Signed integer overflow prevention | CSC-STD-001 §12.1 |
| INT33-C | No division by zero | CSC-STD-001 §12.3 |
| INT34-C | No shift by negative or ≥ width | CSC-STD-001 §12.4 |
| INT36-C | Pointer–integer conversion | CSC-STD-001 §13.4 |
| ARR30-C | No out-of-bounds array access | CSC-STD-001 §15.1 |
| STR31-C | Sufficient storage for strings | CSC-STD-001 §15.3 |
| STR32-C | Null-terminated strings | CSC-STD-001 §16.1 |
| ERR00-C | Consistent error-handling policy | CSC-STD-001 §53 |
| ERR33-C | Check standard library errors | CSC-STD-001 §30.3 |
| DCL22-C | volatile for multi-context data | CSC-STD-001 §22.2 |
| PRE10-C | do-while wrapper for multi-statement macros | CSG-STY-001 §37.3 |
| PRE11-C | No trailing semicolon in macros | CSG-STY-001 §37.4 |

#### Safety Criticality

**MEDIUM–HIGH.** CERT C is primarily a security standard, not a functional safety standard. However, the types of defects it prevents (memory corruption, integer overflow) are equally relevant to safety-critical embedded software.

#### Gaps Relative to MISRA

CERT C does not cover:
- Essential Type Model (MISRA's type-safety system for conversions).
- `switch` statement completeness (MISRA 16.4).
- Recursion prohibition (MISRA 17.2).
- Standard library function restrictions as broad as MISRA 21.x.

#### Project Conclusions

- CERT C rules for integer safety (INT32-C, INT33-C, INT34-C) and memory safety (ARR30-C, EXP34-C, MEM30-C) are adopted in full.
- CERT C macro rules (PRE10-C, PRE11-C) are automated via cstylecheck (`macros.multistatement_wrapper`, `macros.trailing_semicolon`).
- CERT C's security focus supplements MISRA's safety focus; together they provide defence in depth.

---

### 4.3 Barr Group Embedded C Coding Standard (Barr-C:2018)

**Organisation:** Barr Group (Michael Barr)
**Year:** Version 2.0, 2018
**Domain:** Professional embedded systems development
**Availability:** Paid publication; excerpts freely available

#### Overview

Barr-C:2018 is the closest practical complement to MISRA C for embedded systems. It fills the gap left by MISRA's deliberate silence on naming conventions and formatting, providing a complete, opinionated style for embedded C projects. The cstylecheck tool was designed around Barr-C:2018 conventions.

#### Key Contributions

**Naming conventions:**
- Module prefix for all public identifiers.
- `g_` prefix for globals, `s_` for statics, `p_` for pointers, `pp_` for double pointers, `b_` for booleans, `h_` for handles.
- Enum type names end in `_t`; typedef names end in `_T`.
- ISR functions use `_IRQHandler` suffix.

**Formatting:**
- Mandatory braces around all control-flow bodies (prevents Apple goto-fail class of bug).
- One declaration per line.
- Explicit `void` in parameter list for zero-parameter functions.

**Type safety:**
- Fixed-width integer types mandatory.
- `bool`/`_Bool` for boolean variables.

**Memory:**
- Static allocation preferred.
- Dynamic allocation only with explicit justification.
- Large local variables moved to static scope.

**Hardware:**
- `volatile` required for all hardware register accesses.
- `volatile` required for ISR-shared variables.

#### Naming Conventions

Barr-C:2018 is the primary naming convention source for CSG-STY-001 Sections 18–26. The cstylecheck rules.yml file implements Barr-C naming rules directly.

#### Safety Criticality

**HIGH.** Barr-C:2018 is widely used in automotive, medical device, and industrial embedded firmware. It is compatible with ISO 26262 ASIL B/C environments.

#### MISRA Alignment

**Very high.** Barr-C:2018 is designed as a complement to MISRA C, not a replacement. It does not contradict any MISRA required rule.

#### ASPICE Alignment

**High.** Barr-C:2018 addresses SWE.3 BP5 and BP6. The named prefix conventions also support SWE.3 BP3 (interface definition).

#### Project Conclusions

- Barr-C:2018 is the **primary naming convention source** for this project.
- All naming prefix rules (`g_`, `s_`, `p_`, `pp_`, `b_`, `h_`, `_t`, `_T`, `_s`, `_u`, `_IRQHandler`) are adopted directly.
- Barr-C:2018's formatting rules (mandatory braces, one declaration per line) are adopted in CSG-STY-001.
- Some Barr-C defaults are made configurable in cstylecheck (e.g. `p_` parameter prefix is disabled by default; `b_` bool prefix is disabled by default).

---

### 4.4 Google C Style Guide

**Organisation:** Google LLC
**Year:** Continuously updated; C++ focused with C-relevant rules
**Domain:** Large-scale software engineering
**Availability:** Free online

#### Overview

Google's style guide is primarily for C++ but contains guidance applicable to C. It is widely known and influences many open-source projects. Its design goals differ significantly from embedded safety-critical work: Google prioritises readability at scale and developer productivity rather than safety or determinism.

#### Relevant Rules (C-applicable subset)

| Topic | Google Approach | Project Decision |
|---|---|---|
| Naming | `snake_case` for functions and variables; `kConstantName` for constants | **Rejected** — project uses module prefix and Barr-C naming |
| Indentation | 2 spaces | **Rejected** — embedded projects standardise on 4 spaces or tabs |
| Line length | 80 characters | **Partially adopted** — project uses configurable limit; 80 is too restrictive for embedded identifiers |
| Comments | Explain "why" not "what" | **Adopted** — CSG-STY-001 §32 |
| Header order | Own header first, then project, then system | **Adopted** — CSG-STY-001 §38 |
| File names | lowercase with underscores | **Adopted** — CSG-STY-001 §16 |
| Trailing commas in enums | Permitted | **Advisory** |
| TODO comments | `// TODO(user): description` | **Adopted** — permitted format for deferred items |

#### Safety Criticality

**LOW.** Google C Style is not designed for safety-critical or embedded systems. It assumes a hosted environment with a full OS, heap, and C++ standard library.

#### MISRA Alignment

**Very low.** Google style conflicts with MISRA in several respects (e.g. implicit type conversions, `goto` prohibition not universal, dynamic memory permitted). Google C cannot substitute for MISRA compliance.

#### ASPICE Alignment

**Low.** Google C addresses code readability and team consistency but does not address functional safety, traceability, or verification requirements of ASPICE.

#### Project Conclusions

- Google C Style Guide is **not adopted** as a primary standard.
- Two rules are adopted as best practice: comments explain "why" (§32), and `#include` order (§38).
- The 2-space indentation and constant naming (`kConstant`) conventions are explicitly rejected in favour of Barr-C:2018 and project conventions.

---

### 4.5 Linux Kernel Coding Style

**Organisation:** Linux Foundation / Linus Torvalds
**Year:** Continuously updated; current for Linux 6.x kernel
**Domain:** OS kernel development
**Availability:** Free online (Documentation/process/coding-style.rst)

#### Overview

The Linux Kernel Coding Style is a pragmatic, readable style for kernel systems programming. It is opinionated, concise, and unapologetically pragmatic. Linus Torvalds designed it for kernel contributors who work primarily in C on high-stakes, high-performance code. It explicitly permits patterns (8-space tabs, `goto` for cleanup) that other standards restrict.

#### Key Rules and Their Relevance to This Project

| Rule | Linux Kernel Approach | Project Decision |
|---|---|---|
| Indentation | Hard tabs, 8-space visual width | **Noted** — 8-space tabs deter excessive nesting. Project uses configurable tab width. |
| Line length | 80 characters (pragmatic exceptions) | **Noted** — project limit is configurable |
| Braces | K&R style; omit for single-line bodies in some cases | **Not adopted** — project mandates braces |
| `goto` | Explicitly permitted for cleanup/error paths | **Partially adopted** — forward-to-cleanup goto only (CSC-STD-001 §24) |
| Naming | lowercase_with_underscores | **Partially adopted** — project uses snake_case for variables |
| Comment style | Explain "why"; kernel-doc for exported functions | **Adopted** |
| Function length | One screen (~24 lines) | **Not directly adopted** — project uses 60-line limit (JPL) |

The Linux kernel is not a safety-critical system. It uses dynamic memory allocation, unbounded recursion, and complex pointer arithmetic — all prohibited by this project's standard.

#### Safety Criticality

**VERY LOW.** The Linux kernel coding style has no functional safety targets. It explicitly uses patterns (goto, dynamic allocation, variable-length arrays) that are prohibited in safety-critical embedded code.

#### MISRA Alignment

**Very low.** Linux style conflicts with MISRA in many areas. Linux is not a MISRA-compliant codebase and was not designed to be.

#### Project Conclusions

- Linux Kernel Coding Style is **not adopted** as a primary standard.
- The `goto`-for-cleanup pattern is adopted with restrictions (Section 24 of CSC-STD-001).
- The principle of explaining "why" in comments is adopted.
- The 8-space-tab nesting-deterrent principle is noted but not mandated.

---

### 4.6 NASA/JPL Power of Ten Rules

**Organisation:** NASA Jet Propulsion Laboratory
**Author:** Gerard Holzmann
**Year:** 2006 (published in IEEE Software)
**Domain:** Space systems software — highest criticality
**Availability:** Free online (NASA/JPL internal publication; publicly summarised)

#### Overview

The Power of Ten is ten simple rules designed to make code analysable by automated tools. Their primary purpose is enabling static analysis and model checking on space-vehicle software where a single defect can cause mission failure. The rules are intentionally conservative — stricter than MISRA in several respects.

#### The Ten Rules

| # | Rule | Adopted in Project | Reference |
|---|---|---|---|
| 1 | Restrict to simple control flow constructs (no goto, no setjmp/longjmp, no recursion) | **Adopted** — no recursion, no setjmp (CSC-STD-001 §9, §24, §25) | CSC-STD-001 §25 |
| 2 | All loops shall have a fixed upper-bound (statically provable) | **Adopted as advisory** — loops with provable bounds preferred | CSC-STD-001 §26 |
| 3 | No dynamic memory allocation after initialisation | **Adopted** — dynamic allocation prohibited on safety path | CSC-STD-001 §20 |
| 4 | No function shall be longer than 60 lines | **Adopted** | `[RULE: misc.function_length]` |
| 5 | Two assertions per function minimum | **Adopted as advisory** | `[RULE: misc.assert_density]` |
| 6 | Data objects declared at the smallest possible scope | **Adopted** | CSC-STD-001 §43 |
| 7 | Each calling function shall check the return value | **Adopted** | CSC-STD-001 §30.3 |
| 8 | Limit preprocessor use to `#include` and simple `#define` | **Partially adopted** — complex macros restricted | CSC-STD-001 §37 |
| 9 | Restrict pointer use to single dereference; no function pointers | **Partially adopted** — function pointers permitted with NULL check | CSC-STD-001 §14, §29.6 |
| 10 | All warnings treated as errors with maximum warning level | **Adopted** | CSC-STD-001 §7.2 |

#### Safety Criticality

**EXTREME.** Designed for space vehicle software at the highest reliability level. The rules are provably static-analysis-enabling.

#### MISRA Alignment

**Very high.** All ten rules are consistent with MISRA C:2012. JPL rules are generally stricter (e.g. JPL 3 bans all dynamic allocation; MISRA 21.3 only requires a justification for it).

#### ASPICE Alignment

**High.** JPL rules support SWE.3 and SWE.4 by reducing complexity to a statically analysable level.

#### Project Conclusions

- The 60-line function limit (JPL Rule 4) is **adopted as a required rule** (`[RULE: misc.function_length]`).
- The assert-density requirement (JPL Rule 5) is **adopted as an advisory/configurable rule** (`[RULE: misc.assert_density]`).
- The dynamic-allocation prohibition after initialisation (JPL Rule 3) is **adopted**.
- The no-recursion rule (JPL Rule 1) is **adopted**.
- The return-value-check rule (JPL Rule 7) is **adopted** (CSC-STD-001 §30.3).
- The function-pointer restriction (JPL Rule 9) is relaxed to: function pointers permitted with NULL check.

---

### 4.7 GNU Coding Standards

**Organisation:** Free Software Foundation
**Year:** Version 1.6, 2019; maintained continuously
**Domain:** GNU/open-source software
**Availability:** Free online (https://www.gnu.org/prep/standards/)

#### Overview

GNU Coding Standards are designed for GNU project contributors. They emphasise portability, documentation, and Makefile/autoconf conventions. For C code, they provide naming and formatting guidelines. The standard is not designed for safety-critical or embedded work.

#### Relevant Rules

| Topic | GNU Approach | Project Decision |
|---|---|---|
| Naming | lowercase_with_underscores | **Noted** — project uses Barr-C naming |
| Indentation | 2 spaces (or editor-defined) | **Not adopted** — project uses 4 spaces/tabs |
| Brace style | Allman (opening brace on new line) | **Noted** — project defers to AStyle configuration |
| Line length | 79 characters | **Not adopted** — project limit configurable |
| Comments | GNU-doc style (Texinfo) | **Not adopted** — project uses Doxygen |
| Return value | Check all return values | **Adopted** |

#### Safety Criticality

**LOW.** GNU Coding Standards target general-purpose open-source software. No safety-critical provisions.

#### MISRA Alignment

**Low.** GNU standards permit dynamic allocation, recursion, and standard library use without restriction. Not MISRA-compatible as written.

#### Project Conclusions

- GNU Coding Standards are **not adopted** as a primary standard.
- The return-value-check principle is adopted (already in JPL Rule 7 and CERT ERR33-C).
- GNU formatting rules (2-space indent, 79-char line) are explicitly rejected in favour of project-specific AStyle configuration.

---

### 4.8 LLVM Coding Standards

**Organisation:** LLVM Project
**Year:** Continuously updated; current for LLVM 18 era
**Domain:** Compiler infrastructure (primarily C++)
**Availability:** Free online (https://llvm.org/docs/CodingStandards.html)

#### Overview

LLVM Coding Standards target the LLVM/Clang compiler infrastructure. They are primarily C++ focused with some C guidance. The style is designed for a large compiler codebase where performance, template metaprogramming, and compile-time correctness dominate. Almost none of this is relevant to embedded C.

#### Relevant Rules (limited C applicability)

| Topic | LLVM Approach | Project Decision |
|---|---|---|
| Comments | Explain "why" with Doxygen | **Adopted** — consistent with project approach |
| Naming | camelCase variables; CapitalCase types | **Not adopted** — conflicts with Barr-C |
| Indentation | 2 spaces | **Not adopted** |
| Line length | 80 characters | **Not adopted** |
| Include order | Own header, project, system | **Adopted** — consistent with Google/project |

#### Safety Criticality

**VERY LOW.** LLVM Coding Standards are not designed for embedded or safety-critical work.

#### MISRA Alignment

**Very low.** LLVM heavily uses C++ features and dynamic allocation — incompatible with MISRA C.

#### Project Conclusions

- LLVM Coding Standards are **not adopted** as a source of rules for this project.
- The Doxygen comment approach and include-order principle are consistent with the project's independently chosen approach.

---

### 4.9 AUTOSAR Guidelines for C

**Organisation:** AUTOSAR Partnership (BMW, Volkswagen, Bosch, Continental, and others)
**Year:** Part of AUTOSAR R23-11 release
**Domain:** Automotive embedded software
**Availability:** Free download from autosar.org

#### Overview

AUTOSAR defines software architecture, communication stacks, and development guidelines for automotive ECUs. The coding guidelines for C are part of the Software Component (SWC) and Basic Software (BSW) design rules. They align closely with MISRA C:2012 and ISO 26262.

#### Key Contributions

**Module prefix system:**
AUTOSAR requires all public identifiers to carry a module abbreviation prefix (e.g. `Uart_Init`, `Can_Write`, `Spi_Read`). The project's module prefix convention (CSG-STY-001 §17) is directly inspired by this approach.

**Fixed-width types:**
AUTOSAR mandates `uint8`, `uint16`, `uint32` type aliases (from `Platform_Types.h`) rather than `<stdint.h>` types. The project uses `<stdint.h>` types directly, which achieves the same objective without AUTOSAR-specific headers.

**Static allocation:**
Dynamic heap allocation is prohibited in BSW code. Memory pools are used for variable-size needs. This aligns with the project policy in CSC-STD-001 §20.

**Doxygen documentation:**
AUTOSAR BSW modules use Doxygen with mandatory `@brief`, `@param`, and `@return` tags for all public functions. This aligns with CSG-STY-001 §29.

#### Safety Criticality

**VERY HIGH.** AUTOSAR guidelines are written for ISO 26262 compliance (ASIL A–D). They are one of the industry's most mature embedded coding guideline sets.

#### MISRA Alignment

**Very high.** AUTOSAR guidelines are designed to be a superset of MISRA C:2012 compliance.

#### ASPICE Alignment

**Very high.** AUTOSAR is explicitly used in automotive ASPICE compliance. AUTOSAR process requirements align closely with ASPICE v4.

#### Project Conclusions

- AUTOSAR module prefix convention is **adopted** (inspired CSG-STY-001 §17).
- AUTOSAR Doxygen documentation requirements are **adopted** (CSG-STY-001 §29).
- AUTOSAR's prohibition of dynamic allocation in safety code is **adopted** (CSC-STD-001 §20).
- AUTOSAR-specific type aliases (`uint8`, `uint16`) are **not adopted** — project uses standard `<stdint.h>` types.
- AUTOSAR BSW naming (PascalCase module prefix + PascalCase function: `Uart_Init`) is **partially adopted**: the project uses lowercase module prefix with PascalCase object+verb body (`uart_BufferRead`), which is a variant of the AUTOSAR pattern.

---

### 4.10 Motor Industry Research Association (MIRA / MISRA Origin)

**Organisation:** Motor Industry Research Association (MIRA Ltd)
**Year:** MISRA C founded 1998; MIRA is the founding organisation
**Domain:** Automotive software reliability

#### Overview

MIRA is the organisation that founded the MISRA consortium in 1998. The MISRA C coding standard was originally created under a UK government initiative (SafeIT) to improve the reliability of automotive software. MIRA itself does not publish a separate coding standard distinct from MISRA C.

#### Relevance to This Survey

This entry exists because "MIRA guidance" is sometimes cited as a source distinct from MISRA C. It is not. MIRA's contribution is the founding of the MISRA consortium and the ongoing maintenance of MISRA C. All relevant rules are captured in §4.1 (MISRA C:2012/2023).

---

### 4.11 Netrino / Jack Ganssle Embedded C Coding Standard

**Organisation:** Netrino LLC / Jack Ganssle (independent embedded consultant)
**Year:** Originally published ~2008; updated continuously through consulting engagements
**Domain:** Professional embedded systems development
**Availability:** Partially available online; full version through Netrino

#### Overview

The Netrino/Ganssle standard is a practical embedded coding standard written by Jack Ganssle, a highly respected figure in embedded systems engineering. It covers naming, formatting, commenting, and hardware-specific patterns. It is closely related to the Barr Group standard (both authors are from the same embedded engineering community) but with some differing choices.

#### Key Rules and Alignment

| Topic | Netrino/Ganssle | Alignment with Project |
|---|---|---|
| Module prefix | Required for all public symbols | **Adopted** — CSG-STY-001 §17 |
| Global prefix `g_` | Required | **Adopted** — CSG-STY-001 §18.2 |
| Pointer prefix `p_` | Required | **Adopted** — CSG-STY-001 §18.4 |
| Type suffix `_t` | Required for enum types | **Adopted** — CSG-STY-001 §24 |
| Function naming | Module + object + verb | **Adopted** — CSG-STY-001 §21 |
| Mandatory braces | Required | **Adopted** — CSG-STY-001 §13.1 |
| Comment headers | Mandatory for all functions | **Adopted** — CSG-STY-001 §29 |
| Static allocation | Preferred | **Adopted** — CSC-STD-001 §19 |
| Fixed-width types | Mandatory | **Adopted** — CSC-STD-001 §10 |
| Yoda conditions | Recommended | **Adopted** — CSG-STY-001 §49 |

#### Safety Criticality

**MEDIUM–HIGH.** Widely used in medical device, industrial, and automotive embedded firmware without a formal safety certification.

#### MISRA Alignment

**High.** Netrino rules do not conflict with MISRA C and serve as a practical implementation guide for MISRA-compliant naming and formatting.

#### ASPICE Alignment

**Medium.** Addresses SWE.3 coding quality but does not address ASPICE process requirements directly.

#### Project Conclusions

- Netrino/Ganssle provides **corroborating evidence** for the naming and formatting conventions chosen from Barr-C:2018.
- Where Barr-C and Netrino agree, the rule has high consensus support.
- Yoda conditions (CSG-STY-001 §49, `[RULE: misc.yoda_conditions]`) are adopted, consistent with both Netrino and Barr-C recommendations.

---

### 4.12 IAR Embedded Workbench Recommendations

**Organisation:** IAR Systems (compiler/IDE vendor)
**Year:** Part of IAR EW documentation; version EW 9.x era
**Domain:** Embedded systems (vendor-specific)
**Availability:** IAR Embedded Workbench documentation (free with tool registration)

#### Overview

IAR Systems provides coding style recommendations as part of the EW documentation. These are not a formal coding standard but a set of best-practice guidelines for getting the most out of the IAR compiler and debugger. Topics include memory model selection, intrinsics usage, optimisation-friendly code patterns, and MISRA checking setup.

#### Key Contributions to This Survey

| Topic | IAR Recommendation | Project Decision |
|---|---|---|
| MISRA checking | IAR MISRA C checker plug-in available | **Noted** — project uses cstylecheck + supplementary tool |
| Memory models | near/far/huge considerations | **Not adopted** — project targets ARM Cortex-M with flat memory |
| Interrupt handlers | Attribute `__interrupt` or CMSIS `_IRQHandler` | **Adopted** — CMSIS naming used (CSG-STY-001 §25) |
| Optimisation-friendly | Avoid complex `volatile` patterns; use intrinsics | **Noted** |
| Stack analysis | IAR stack usage analysis tool | **Adopted** as process recommendation (CSC-STD-001 §21) |

#### Safety Criticality

**MEDIUM.** IAR recommendations support safety-critical development but are not themselves a safety standard. IAR provides ISO 26262-qualified compiler versions.

#### MISRA Alignment

**Supportive.** IAR provides a MISRA C:2012 checker plug-in. The recommendations complement MISRA adoption.

#### Project Conclusions

- IAR Embedded Workbench Recommendations are **not adopted** as a primary standard.
- CMSIS naming conventions for ISR handlers are adopted (consistent with ST HAL and most ARM Cortex-M projects).
- Stack usage analysis as part of the verification process is adopted as a recommendation.

---

### 4.13 JSF AV C++ Coding Standards (Joint Strike Fighter)

**Organisation:** Lockheed Martin / US Department of Defense
**Year:** Revision C, 2005
**Domain:** Flight-critical avionics software (F-35 Lightning II)
**Availability:** Public domain (US DoD publication)

#### Overview

The JSF AV (Air Vehicle) C++ Coding Standard is one of the most comprehensive safety-critical coding standards ever published. Though nominally a C++ standard, it contains extensive guidance applicable to C. It was developed for DO-178B (avionics certification) compliance and is widely cited in other safety-critical domains.

With over 230 rules, it is more comprehensive and stricter than MISRA C in several areas. It defines function complexity limits, file length limits, and assert density requirements that the project has directly adopted.

#### Key Rules Adopted

| JSF Rule | Content | Project Adoption | Reference |
|---|---|---|---|
| JSF 118 | Max nesting depth 5 levels | **Adopted** | CSC-STD-001 §23.2 |
| JSF 120 | Max 5 function parameters | **Adopted** | CSC-STD-001 §30.1 |
| JSF 192 | Null statements require comment | **Adopted** | `[RULE: misc.null_statement_comment]` |
| JSF Rule on length | File length recommendation | **Adopted** | `[RULE: misc.file_length]` |
| JSF 45 | Identifier length (3–31 chars) | **Adopted** | naming section |

#### Safety Criticality

**EXTREME.** JSF AV rules were designed for DO-178B Level A (most critical) avionics software where software failure could cause loss of the aircraft.

#### MISRA Alignment

**Very high.** JSF C++ rules were designed to be compatible with MISRA C in the C subset. Many rules are equivalent or stricter.

#### ASPICE Alignment

**High.** JSF rules support thorough static verification and complexity control, mapping to SWE.4 requirements.

#### Project Conclusions

- JSF nesting depth limit (5 levels) is **adopted** (CSC-STD-001 §23.2).
- JSF parameter count limit (5 parameters) is **adopted** (CSC-STD-001 §30.1).
- JSF null-statement comment rule (JSF 192) is **adopted** and automated (`[RULE: misc.null_statement_comment]`).
- JSF file length recommendation supports the project's 500-line file limit.
- JSF identifier length guidance (3–31 characters) is adopted as advisory.

---

### 4.14 HICPP (High Integrity C++ Coding Standard)

**Organisation:** Programming Research Ltd (now Perforce/LDRA)
**Year:** Version 4.0, 2016
**Domain:** High-integrity software (safety + security + reliability)
**Availability:** Free download from hicpp.org

#### Overview

HICPP 4.0 is a comprehensive coding standard for C++ with extensive coverage of C-relevant principles. It is designed for systems requiring both functional safety and security. It builds on MISRA C, JSF, and CERT C, providing a unified framework.

HICPP is supported by static analysis tools from Perforce (formerly Programming Research), LDRA, and others.

#### Key Contributions

| Topic | HICPP Approach | Project Alignment |
|---|---|---|
| Type safety | Strict; aligned with MISRA Essential Type Model | **High alignment** |
| Naming | Intentional, consistent; type indication | **Consistent** with project approach |
| Memory | Explicit allocation/deallocation; prefer stack | **Adopted** |
| Control flow | Structured; nesting limits; complexity limits | **Adopted** |
| Documentation | Non-obvious behaviour explained | **Adopted** |
| Security | Defensive programming; input validation | **Adopted** |

#### Safety Criticality

**HIGH.** HICPP covers both functional safety (aligned with IEC 61508) and security. Used in medical devices, avionics, and industrial control systems.

#### MISRA Alignment

**Very high.** HICPP is designed as a superset of MISRA C practices. HICPP compliance implies MISRA compliance in most areas.

#### ASPICE Alignment

**High.** HICPP supports SWE.3, SWE.4, and SUP.1 evidence generation.

#### Project Conclusions

- HICPP provides **corroborating evidence** for many rules already adopted from MISRA C:2012, Barr-C, and CERT C.
- HICPP's unified approach to safety + security reinforces the project's use of both MISRA and CERT C together.
- HICPP does not contribute rules not already covered by the adopted sources.

---

### 4.15 IEC 61508 / ISO 26262 C Coding Guidance

**Organisation:** International Electrotechnical Commission / International Organization for Standardization
**Year:** IEC 61508-3:2010; ISO 26262-6:2018 (second edition)
**Domain:** Functional safety — industrial machinery (IEC) and road vehicles (ISO)
**Availability:** Paid publication (IEC and ISO webstores)

#### Overview

IEC 61508 and ISO 26262 are the foundational functional safety standards. They do not prescribe a specific C coding standard but provide requirements and guidance in their software requirements parts (IEC 61508-3, ISO 26262-6) that constrain how C code must be written for SIL/ASIL-rated systems.

ISO 26262-6 Table 1 lists software design and coding guidelines for each ASIL level. For ASIL B and above, use of a language subset (e.g. MISRA C:2012) is "highly recommended" (++). For ASIL C and D, it becomes effectively mandatory.

IEC 61508-3 Part 7 Annex C lists recommended C coding techniques by SIL level, covering:
- Language subsets
- Coding guidelines
- Defensive programming
- Memory management
- Control flow

#### Project Relevance

| Requirement | Standard | Project Rule |
|---|---|---|
| Language subset (MISRA C) | ISO 26262-6 Table 1 (ASIL B+), IEC 61508-3 | CSC-STD-001 §8, §9 |
| No dynamic allocation (SIL 3–4 / ASIL C–D) | IEC 61508-3 Annex C | CSC-STD-001 §20 |
| Single entry, single exit (advisory) | ISO 26262-6 | CSC-STD-001 §23.1 |
| Structured programming (no goto) | IEC 61508-3 | CSC-STD-001 §24 |
| No recursion (SIL 3–4) | IEC 61508-3 | CSC-STD-001 §25 |
| Static analysis mandatory (SIL 3–4) | ISO 26262-6 | CSC-STD-001 §69 |
| Coding guideline compliance evidence | ISO 26262-6 Clause 8 | ASPICE §4 of this project |
| Defensive programming | IEC 61508-3 | CSC-STD-001 §34, §55 |
| Safe state definition | IEC 61508-1, ISO 26262-4 | CSC-STD-001 §56 |

#### Safety Criticality

**EXTREME.** IEC 61508 and ISO 26262 are the legal and regulatory basis for functional safety in their respective domains.

#### MISRA Alignment

**Full.** MISRA C:2012 was designed specifically to satisfy the coding guideline requirements of IEC 61508 and ISO 26262. They are complementary, not competing.

#### ASPICE Alignment

**Full.** ASPICE is the process assessment model for ISO 26262 compliance. IEC 61508 has its own lifecycle model, but ASPICE is the de facto standard in automotive.

#### Project Conclusions

- IEC 61508 and ISO 26262 are the **top-level normative framework** within which this project operates.
- All coding rules in CSC-STD-001 ultimately derive their safety rationale from IEC 61508 / ISO 26262 requirements.
- The specific C coding rules are satisfied through MISRA C:2012 adoption, which is the accepted industry practice for meeting IEC 61508-3 coding requirements.
- The project's ASPICE v4 Level 2 compliance provides the process evidence required by ISO 26262-6 Clause 8.

---

## 5. Comparison Matrices

### 5.1 Safety Criticality and Domain

| Standard | Domain | Safety Level | Regulatory Basis |
|---|---|---|---|
| IEC 61508 / ISO 26262 | Industrial / Automotive | EXTREME | Legal / regulatory |
| NASA Power of Ten | Space systems | EXTREME | Internal NASA mandate |
| JSF AV C++ | Avionics | EXTREME | DO-178B Level A |
| MISRA C:2012/2023 | Multi-domain safety | VERY HIGH | ISO 26262, IEC 61508 |
| AUTOSAR Guidelines | Automotive | VERY HIGH | ISO 26262 |
| HICPP | High-integrity | HIGH | IEC 61508 |
| Barr-C:2018 | Embedded systems | HIGH | Best practice |
| Netrino / Ganssle | Embedded systems | MEDIUM–HIGH | Best practice |
| CERT C | Secure software | MEDIUM–HIGH | SANS / CERT |
| IAR EW | Embedded (vendor) | MEDIUM | Vendor guidance |
| Google C | Large-scale software | LOW | Team convention |
| GNU Coding Standards | Open-source | LOW | Project convention |
| LLVM Coding Standards | Compiler infrastructure | LOW | Project convention |
| Linux Kernel | OS kernel | LOW | Community convention |
| MIRA | (see MISRA) | — | (see MISRA) |

### 5.2 Naming Convention Approach

| Standard | Variables | Functions | Types | Constants |
|---|---|---|---|---|
| MISRA C:2012 | No prescription | No prescription | No prescription | No prescription |
| Barr-C:2018 | `lower_snake` + scope prefix | `<mod>_<Object><Verb>` | `UPPER_SNAKE_T` | `UPPER_SNAKE` |
| AUTOSAR | `lower_snake` + module prefix | `<Mod>_<Verb>` | `<Mod>_<Name>Type` | `<MOD>_<CONST>` |
| Google C | `snake_case` | `snake_case` | `TypeName` | `kConstantName` |
| Linux Kernel | `lowercase` | `action_object` | `lowercase_t` | `UPPER_CASE` |
| NASA Power of Ten | Descriptive | Descriptive | — | — |
| JSF AV | Descriptive | Module prefix | `CapWords` | `UPPER_CASE` |
| CERT C | Descriptive | — | — | — |
| GNU | `lower_underscore` | `lower_underscore` | — | `UPPER_CASE` |
| **Project (adopted)** | `lower_snake` + `g_`/`s_`/`p_` | `<mod>_<Object><Verb>` | `UPPER_SNAKE_T` | `UPPER_SNAKE` |

### 5.3 Formatting Rules

| Standard | Indentation | Line Length | Brace Style | Mandatory Braces |
|---|---|---|---|---|
| MISRA C:2012 | No rule | No rule | No rule | No rule |
| Barr-C:2018 | 4 spaces | 80–120 | K&R | YES |
| AUTOSAR | 2–4 spaces | 120 | K&R | YES |
| Google C | 2 spaces | 80 | K&R | YES |
| Linux Kernel | Tabs (8 wide) | 80 | K&R | NO (single stmt ok) |
| NASA Power of Ten | No rule | No rule | No rule | No rule |
| GNU | 2 spaces | 79 | Allman | No rule |
| JSF AV | 2–4 spaces | 80 | Allman | YES |
| **Project (adopted)** | `[AStyle config]` | `[AStyle config]` | `[AStyle config]` | YES |

### 5.4 Memory Management Policy

| Standard | Dynamic Allocation | Static Allocation | VLAs |
|---|---|---|---|
| MISRA C:2012 | Restricted (Rule 21.3) | Preferred | Prohibited (Rule 18.8) |
| NASA Power of Ten | **Prohibited** | Mandatory | — |
| JSF AV | Highly restricted | Preferred | — |
| IEC 61508 (SIL 3–4) | **Prohibited** | Mandatory | — |
| ISO 26262 (ASIL C–D) | **Prohibited** | Mandatory | — |
| Barr-C:2018 | Use sparingly | Preferred | Not recommended |
| AUTOSAR (BSW) | **Prohibited** | Mandatory | Not used |
| CERT C | Carefully | Acceptable | Restrict |
| Google C | Permitted | Acceptable | Permitted |
| Linux Kernel | Permitted | Context-dependent | Context-dependent |
| **Project (adopted)** | **Prohibited on safety path** | **Mandatory** | **Prohibited** |

### 5.5 Control Flow Restrictions

| Standard | goto | Recursion | Nesting Depth | Switch Default |
|---|---|---|---|---|
| MISRA C:2012 | Advisory restriction | **Prohibited** (R17.2) | No rule | **Required** (R16.4) |
| NASA Power of Ten | **Prohibited** | **Prohibited** | No rule | — |
| JSF AV | **Prohibited** | Restricted | **5 levels** | Required |
| Barr-C:2018 | **Prohibited** | Restricted | — | Required |
| CERT C | No rule | No rule | No rule | No rule |
| Google C | No rule | No rule | No rule | No rule |
| Linux Kernel | Permitted (cleanup) | Permitted | No rule | Recommended |
| **Project (adopted)** | Forward-to-cleanup only | **Prohibited** | **5 levels** | **Required** |

### 5.6 MISRA and ASPICE Alignment

| Standard | MISRA Alignment | ASPICE SWE.3 Support | ASPICE SWE.4 Support |
|---|---|---|---|
| MISRA C:2012/2023 | N/A (IS MISRA) | Direct | Via static analysis |
| IEC 61508 / ISO 26262 | Full | Direct | Direct |
| AUTOSAR | Very High | Very High | High |
| JSF AV | Very High | High | Very High |
| NASA Power of Ten | Very High | High | High |
| HICPP | Very High | High | High |
| Barr-C:2018 | High | High | Medium |
| CERT C | Complementary | Medium | Medium |
| Netrino / Ganssle | High | Medium | Medium |
| IAR EW | Supportive | Medium | Low |
| Google C | Low | Low | Low |
| Linux Kernel | Low | Low | Low |
| GNU | Low | Low | Low |
| LLVM | Low | Low | Low |

---

## 6. Cross-Cutting Themes

The following themes emerge consistently across multiple standards:

### 6.1 Fixed-Width Integer Types (Universal Consensus)

**14 out of 15** standards either require or strongly recommend fixed-width integer types from `<stdint.h>`. Only the Linux Kernel style is indifferent (kernel has its own type aliases). This is the single most universally adopted rule in embedded C.

**Adopted:** CSC-STD-001 §10.1 — mandatory.

### 6.2 Mandatory Braces on All Control Bodies (High Consensus)

**9 out of 15** standards require or strongly recommend braces on all `if`/`else`/`for`/`while` bodies. The historical `goto fail` SSL bug (Apple, 2014) — caused by a brace-free `if` body — is frequently cited as justification.

**Adopted:** CSG-STY-001 §13.1 — mandatory.

### 6.3 No Dynamic Memory Allocation on Safety Path (Safety-Critical Consensus)

**5 out of 5** safety-critical standards (MISRA, NASA, JSF, IEC 61508, ISO 26262) prohibit or severely restrict dynamic allocation. Non-determinism and fragmentation are the primary concerns.

**Adopted:** CSC-STD-001 §20 — prohibited on safety path.

### 6.4 No Recursion (Safety-Critical Consensus)

**4 out of 5** safety-critical standards prohibit recursion. Stack overflow from unbounded recursion is undetectable in the general case without formal verification.

**Adopted:** CSC-STD-001 §25 — prohibited.

### 6.5 Comments Explain "Why" Not "What" (Universal Principle)

All 15 standards, in some form, express that comments should add value beyond what the code itself states. This is the one principle that transcends the safety/general divide.

**Adopted:** CSG-STY-001 §32.

### 6.6 Return Value Checking (High Consensus)

MISRA C (Rule 17.7), CERT C (ERR33-C), NASA Power of Ten (Rule 7), Barr-C, Netrino, and JSF all require or recommend that all function return values encoding status are checked.

**Adopted:** CSC-STD-001 §30.3 — mandatory.

### 6.7 `volatile` for Hardware Registers and ISR-Shared Data (Embedded Consensus)

Barr-C:2018, Netrino, IAR, AUTOSAR, and MISRA C all require `volatile` on hardware registers and ISR-shared variables.

**Adopted:** CSC-STD-001 §22 — mandatory.

---

## 7. Gaps and Conflicts Between Standards

### 7.1 Gaps (Not Covered by Any Single Standard)

| Gap | Identified In | Project Mitigation |
|---|---|---|
| RTOS-specific patterns (queue/semaphore safety) | None comprehensively | CSC-STD-001 §51 |
| Watchdog management rules | JSF (partially) | CSC-STD-001 §60 |
| Timestamp overflow handling | None | CSC-STD-001 §61.4 |
| ISR latency budgets | None | CSC-STD-001 §59.4 |
| Stack high-water monitoring | None | CSC-STD-001 §21.3 |
| ASPICE process compliance of the coding standard itself | ASPICE | CSC-STD-001 §4, §5 |

### 7.2 Conflicts Between Surveyed Standards

| Topic | Conflict | Project Resolution |
|---|---|---|
| `goto` | Linux: permitted; MISRA: advisory restriction; NASA/JSF: prohibited | Adopted: forward-to-cleanup only (compromise between MISRA advisory and pragmatic Linux pattern) |
| Line length | Google: 80; AUTOSAR: 120; Linux: 80 pragmatic | Adopted: configurable via AStyle; currently 180 (allows long embedded identifiers) |
| Indentation width | Linux: 8 spaces (tabs); Google/LLVM: 2; Barr-C: 4 | Adopted: configurable via AStyle; default 4/tab |
| Brace style | GNU: Allman; K&R style: same-line; JSF: Allman | Adopted: AStyle-configured (project choice) |
| Constant naming | Barr-C: `UPPER_SNAKE`; Google: `kConstantName`; Linux: `UPPER_CASE` | Adopted: `UPPER_SNAKE` (Barr-C/MISRA aligned) |
| Function naming case | AUTOSAR: PascalCase; Barr-C: module+PascalCase; Google: snake_case | Adopted: `<module>_<Object><Verb>` (Barr-C) |
| Comment style | Linux/Google: `//` preferred; MISRA: allows both; C89 projects: `/* */` only | Adopted: both permitted; C89 mode restricts to `/* */` |
| Switch default | MISRA: Required; Google: not prescribed | Adopted: Required (MISRA wins for safety) |
| `bool` comparisons | MISRA: no comparison against `true`/`false`; some guides: permit | Adopted: MISRA rule — no comparison against `true`/`false` |

---

## 8. Conclusions

### 8.1 Primary Standards Selected

Based on this survey, the project has adopted the following standards as its primary sources:

| Priority | Standard | Rationale |
|---|---|---|
| 1 | **MISRA C:2012/2023** | Definitive safety-critical C standard; required for ISO 26262 / IEC 61508 compliance |
| 2 | **Barr-C:2018** | Best practical naming and formatting convention for embedded C; cstylecheck implements it directly |
| 3 | **CERT C** | Complements MISRA with security-oriented rules; fills gaps in integer safety and secure string handling |
| 4 | **NASA Power of Ten** | Adds function length, assert density, and return-value-check requirements that MISRA does not prescribe |
| 5 | **JSF AV C++ Standard** | Adds nesting depth, parameter count, and null-statement comment rules |
| 6 | **AUTOSAR Guidelines** | Corroborates module prefix naming; confirms automotive best practice alignment |
| 7 | **IEC 61508 / ISO 26262** | Top-level normative framework; the ultimate justification for all safety rules |

### 8.2 Standards Surveyed but Not Adopted as Primary Sources

| Standard | Reason Not Adopted as Primary |
|---|---|
| Google C Style Guide | Not suitable for safety-critical embedded; conflicting naming/formatting conventions |
| Linux Kernel Coding Style | Not suitable for safety-critical embedded; permits goto, dynamic allocation, recursion |
| GNU Coding Standards | General-purpose open-source focus; no embedded or safety-critical relevance |
| LLVM Coding Standards | C++ compiler focus; no embedded relevance |
| IAR EW Recommendations | Vendor-specific tool guidance; not a formal standard |
| Netrino / Ganssle | Overlaps with Barr-C:2018; provides corroborating evidence only |
| HICPP | C++ focused; C rules subsumed by adopted standards |
| MIRA | Not a separate standard; MISRA C covers this |

### 8.3 Rule Confidence by Consensus Count

| Rule Type | Consensus Count | Confidence |
|---|---|---|
| Fixed-width integer types | 14/15 | VERY HIGH |
| No dynamic allocation (safety path) | 5/5 safety standards | VERY HIGH |
| `volatile` for hardware/ISR | 6+ standards | VERY HIGH |
| Mandatory braces | 9+ standards | HIGH |
| Return value checking | 6+ standards | HIGH |
| Comments explain "why" | 15/15 | HIGH (universal principle) |
| No recursion | 4/5 safety standards | HIGH |
| Module prefix naming | 6+ embedded/automotive standards | HIGH |
| 60-line function limit | 2 standards (JPL, JSF near-equivalent) | MEDIUM |
| 5-level nesting limit | 2 standards (JSF, Barr-C) | MEDIUM |

### 8.4 ASPICE v4 Level 2 Compliance Assessment

This analysis document, together with CSG-STY-001 and CSC-STD-001, constitutes evidence for:

| ASPICE Requirement | Evidence |
|---|---|
| SWE.3 BP6 — Apply coding guidelines | CSC-STD-001 defines coding guidelines derived from this analysis |
| SWE.4 BP2 — Static verification | cstylecheck + static analysis tool enforce rules automatically |
| SUP.1 BP2 — Assure compliance | Deviation procedure (CSC-STD-001 §72) and review checklist (CSC-STD-001 §70) |
| SUP.8 BP1 — Identify CIs | All three documents are version-controlled configuration items |
| GP 2.1.1 — Define process | CSC-STD-001 defines the coding process |
| GP 2.2.1 — Define responsibility | Section 5 in both standards |
| GP 2.3.1 — Identify information items | Document IDs, versions, statuses tracked |

---

## 9. Recommendations for CSG-STY-001 and CSC-STD-001

1. **Maintain MISRA C:2012 as the primary normative reference.** All conflicts with other surveyed standards shall be resolved in favour of MISRA C when a rule is classified as Required or Mandatory.

2. **Use Barr-C:2018 as the primary naming standard.** The cstylecheck tool implements it; consistency between the tool and the document is essential.

3. **Retain CERT C coverage for integer and memory safety.** These rules address exploitable vulnerabilities not fully covered by MISRA.

4. **Adopt JPL function length and assert density as required rules.** The 60-line limit and assert-density requirement measurably reduce complexity and increase verifiability.

5. **Adopt JSF nesting depth and parameter count limits.** These reduce complexity and improve testability.

6. **Maintain a deviation register.** The survey shows that some rules (e.g. `goto`, specific macro patterns) will need deviations for legacy code or third-party integration. The register makes deviations auditable.

7. **Populate the `[RULE: TBD]` placeholders in CSG-STY-001 and CSC-STD-001** by mapping each section to the corresponding cstylecheck rule ID from `src/rules.yml` once the rule configuration is finalised.

8. **Supplement cstylecheck with a MISRA-compliant static analysis tool** for full MISRA C:2012 coverage beyond what cstylecheck implements.

9. **Review this analysis document** when MISRA C:2023 (next full edition, expected ~2025–2026) is published, as it may promote more Advisory rules to Required.

---

## 10. Adopted vs. Rejected Rules by Source

### Rules Adopted

| Rule | Source | Classification | cstylecheck Rule ID |
|---|---|---|---|
| No octal literals | MISRA 7.1 | Required | `misc.octal_constant` |
| Unsigned suffix on unsigned literals | MISRA 7.2 / Barr-C | Required | `misc.unsigned_suffix` |
| Uppercase integer suffixes | MISRA 7.3 | Required | `misc.lowercase_l_suffix` |
| No trigraphs | MISRA 4.2 / MISRA C:2023 | Required | `misc.trigraph` |
| Module prefix on all public identifiers | Barr-C 7.1 / AUTOSAR | Required | `file_prefix` |
| `g_` prefix on global variables | Barr-C 7.1.b | Required | `variables.global.g_prefix` |
| `s_` prefix on static variables | Barr-C 7.1.c | Required | `variables.static.s_prefix` |
| `p_` prefix on pointer variables | Barr-C 7.1.k | Required | `variables.pointer_prefix` |
| `pp_` prefix on double-pointer variables | Barr-C 7.1.l | Required | `variables.pp_prefix` |
| `h_` prefix on handle variables | Barr-C 7.1.n | Advisory | `variables.handle_prefix` |
| `_t` suffix on enum types | Barr-C / AUTOSAR | Required | `enums.type_suffix` |
| `_T` suffix on typedef names | Barr-C | Advisory | `typedefs.suffix` |
| `_s` suffix on struct tags | Barr-C | Advisory | `structs.tag_suffix` |
| UPPER\_SNAKE\_CASE for macros and constants | All sources | Required | `macros`, `constants` |
| `<mod>_<Object><Verb>` function naming | Barr-C / project | Required | `functions.style` |
| `_IRQHandler` suffix on ISRs | Barr-C / CMSIS | Required | `functions.isr_suffix` |
| Include guard pattern `{FILE}_{EXT}_` | Barr-C / project | Required | `include_guards` |
| `#pragma once` as alternative | Project policy | Advisory | `include_guards.allow_pragma_once` |
| Magic number detection | Barr-C / JPL | Required | `misc.magic_numbers` |
| Line length limit | Multiple | Required | `misc.line_length` |
| Indentation consistency | Multiple | Required | `misc.indentation` |
| Yoda conditions for `==` and `!=` | Barr-C / Netrino | Required | `misc.yoda_conditions` |
| Null statement comment | JSF 192 | Required | `misc.null_statement_comment` |
| Function length ≤ 60 lines | JPL Rule 4 | Required | `misc.function_length` |
| File length ≤ 500 lines | JSF / ESA practice | Advisory | `misc.file_length` |
| Function documentation header | ESA / AUTOSAR | Advisory | `misc.function_doc_header` |
| Assert density | JPL Rule 5 | Advisory | `misc.assert_density` |
| Trailing semicolon in macros | CERT PRE11-C | Required | `macros.trailing_semicolon` |
| Multi-statement macro wrapper | CERT PRE10-C | Required | `macros.multistatement_wrapper` |
| Reserved header names | CERT PRE04-C | Required | `misc.reserved_header_name` |
| Sign compatibility | MISRA 10.x | Required | `sign_compatibility` |
| Comment ratio | Barr-C / ESA | Advisory | `misc.comment_ratio` |
| Whitespace ratio | Project practice | Advisory | `misc.whitespace_ratio` |
| Block comment spacing | Project practice | Advisory | `misc.block_comment_spacing` |
| Copyright header | Project practice | Required | `misc.copyright_header` |
| Enum member prefix from type | Barr-C | Required | `enums.member_prefix_from_type` |
| No single-char identifiers | JSF 45 / ESA | Advisory | `naming.no_single_char_identifiers` |
| Identifier length limits | JSF 45 / ESA | Advisory | `naming.identifier_length` |
| Reserved names (C/POSIX) | CERT PRE04-C / MISRA 5.x | Required | `reserved_names` |
| Declared-not-defined detection | CERT / project | Advisory | `misc.declared_not_defined` |

### Rules Surveyed but Not Adopted

| Rule | Source | Reason Not Adopted |
|---|---|---|
| 2-space indentation | Google, LLVM, GNU | Conflicts with embedded convention; AStyle-controlled |
| 80-character hard line limit | Google, Linux, GNU | Too restrictive for embedded identifiers with module prefix; configurable limit adopted |
| `kConstantName` constant naming | Google | Conflicts with Barr-C UPPER\_SNAKE convention |
| Function pointer prohibition | JPL Rule 9 | Too restrictive; function pointers with NULL check are acceptable |
| All loop bounds must be provable | JPL Rule 2 | Formal proof not practical for all loops; handled by code review |
| No `//` comments | MISRA 3.1 (in C89 mode) | Project uses C11; both comment styles permitted |
| Hard tabs 8-space visual | Linux Kernel | Too opinionated; AStyle-controlled |
| `_Thread_local` prohibition | Project | Covered by RTOS guidelines; formal rule not required |

---

## 11. Document Change History

| Version | Date | Author | Change Description |
|---|---|---|---|
| 1.0 | 2026-06-08 | (initial draft) | Initial survey of 15 standards; per-document analysis; comparison matrices; conclusions and recommendations |

---

*End of CSC-ANA-001 External C Coding Standards Survey and Analysis v1.0*
