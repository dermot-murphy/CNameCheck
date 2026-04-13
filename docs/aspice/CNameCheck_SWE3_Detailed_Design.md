# Software Detailed Design

*Automotive SPICE® PAM v4.0 | SWE.3 Software Detailed Design and Unit Construction*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CNC-SWE3-001 | **Version** | 1.0 |
| **Project** | CNameCheck | **Date** | 2026-04-12 |
| **Status** | Draft | **Classification** | Internal |
| **Author** | Dermot Murphy | **Reviewer** | \<Reviewer Name\> |
| **Approver** | \<Approver Name\> | **Related Process** | SWE.3 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | 2026-04-12 | Dermot Murphy | Initial release |

---

## 3. Purpose & Scope

This document defines the detailed design of each software unit in **CNameCheck v1.0.0**, providing the algorithmic specification, interface contracts, and data design required for unit construction and verification. It satisfies **Automotive SPICE® PAM v4.0, SWE.3 — Software Detailed Design and Unit Construction**.

### 3.1 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CNC-SWE1-001 | CNameCheck Software Requirements Specification | 1.0 |
| CNC-SWE2-001 | CNameCheck Software Architecture Description | 1.0 |
| CNC-SWE4-001 | CNameCheck Unit Verification Specification | 1.0 |

---

## 4. Unit Catalogue

| Unit ID | Unit Name | Source Location | Component |
|---|---|---|---|
| UNIT-01 | `_read_options_file` | `cnamecheck.py:187` | COMP-01 |
| UNIT-02 | `_expand_options_file` | `cnamecheck.py:218` | COMP-01 |
| UNIT-03 | `discover_files` | `cnamecheck.py:2818` | COMP-01 |
| UNIT-04 | `_path_matches_exclude` | `cnamecheck.py:2744` | COMP-01 |
| UNIT-05 | `load_config` | `cnamecheck.py:250` | COMP-02 |
| UNIT-06 | `load_alias_file` | `cnamecheck.py:275` | COMP-02 |
| UNIT-07 | `load_exclusions_file` | `cnamecheck.py:314` | COMP-02 |
| UNIT-08 | `_disabled_rules_for_file` | `cnamecheck.py:363` | COMP-02 |
| UNIT-09 | `load_defines_file` | `cnamecheck.py:392` | COMP-02 |
| UNIT-10 | `apply_defines` | `cnamecheck.py:441` | COMP-02 |
| UNIT-11 | `_load_dict_file` | `cnamecheck.py:458` | COMP-03 |
| UNIT-12 | `_data_file` | `cnamecheck.py:477` | COMP-03 |
| UNIT-13 | `_build_spell_dict` | `cnamecheck.py:899` | COMP-03 |
| UNIT-14 | `strip_comments` | `cnamecheck.py:683` | COMP-04 |
| UNIT-15 | `strip_strings` | `cnamecheck.py:693` | COMP-04 |
| UNIT-16 | `preprocess` | `cnamecheck.py:701` | COMP-04 |
| UNIT-17 | `build_line_map` | `cnamecheck.py:874` | COMP-04 |
| UNIT-18 | `offset_to_line_col` | `cnamecheck.py:881` | COMP-04 |
| UNIT-19 | `_build_brace_depths` | `cnamecheck.py:750` | COMP-04 |
| UNIT-20 | `_comment_only_lines` | `cnamecheck.py:705` | COMP-04 |
| UNIT-21 | `Checker.__init__` | `cnamecheck.py:912` | COMP-05 |
| UNIT-22 | `Checker.run_all` | `cnamecheck.py:~1060` | COMP-05 |
| UNIT-23 | `Checker._check_variables` | `cnamecheck.py:1120` | COMP-05a |
| UNIT-24 | `Checker._check_functions` | `cnamecheck.py:1562` | COMP-05b |
| UNIT-25 | `Checker._check_defines` | `cnamecheck.py:1072` | COMP-05c |
| UNIT-26 | `Checker._check_typedefs` | `cnamecheck.py:1652` | COMP-05d |
| UNIT-27 | `Checker._check_enums` | `cnamecheck.py:1676` | COMP-05d |
| UNIT-28 | `Checker._check_structs` | `cnamecheck.py:1739` | COMP-05d |
| UNIT-29 | `Checker._check_include_guard` | `cnamecheck.py:1879` | COMP-05e |
| UNIT-30 | `Checker._check_misc` | `cnamecheck.py:1912` | COMP-05f |
| UNIT-31 | `Checker._check_yoda` | `cnamecheck.py:2245` | COMP-05f |
| UNIT-32 | `Checker._check_spelling` | `cnamecheck.py:2226` | COMP-05f |
| UNIT-33 | `Checker._check_reserved_names` | `cnamecheck.py:2348` | COMP-05f |
| UNIT-34 | `SignChecker._check_calls` | `cnamecheck.py:2688` | COMP-05g |
| UNIT-35 | `load_baseline` | `cnamecheck.py:3006` | COMP-06 |
| UNIT-36 | `write_baseline` | `cnamecheck.py:3021` | COMP-06 |
| UNIT-37 | `_baseline_key` | `cnamecheck.py:3001` | COMP-06 |
| UNIT-38 | `_violations_to_json` | `cnamecheck.py:2917` | COMP-07 |
| UNIT-39 | `_violations_to_sarif` | `cnamecheck.py:2949` | COMP-07 |
| UNIT-40 | `print_summary` | `cnamecheck.py:3045` | COMP-07 |
| UNIT-41 | `Violation.__str__` | `cnamecheck.py:165` | COMP-07 |
| UNIT-42 | `Violation.github_annotation` | `cnamecheck.py:158` | COMP-07 |
| UNIT-43 | `matches_case` | `cnamecheck.py:618` | COMP-05 (shared) |
| UNIT-44 | `matches_case_abbrev` | `cnamecheck.py:623` | COMP-05 (shared) |
| UNIT-45 | `module_name` | `cnamecheck.py:654` | COMP-05 (shared) |
| UNIT-46 | `main` | `cnamecheck.py:3191` | Entry point |

---

## 5. Detailed Unit Design

### UNIT-01 — `_read_options_file(path: str) → list`

**Purpose:** Read an options file and return a flat list of shell-tokenised CLI arguments.

**Algorithm:**
1. Open file at `path`; read all lines
2. For each line: strip whitespace; skip if empty or starts with `#`
3. Apply `shlex.split()` to tokenise shell-quoted values
4. Return concatenated token list

**Error handling:** `FileNotFoundError` → caller receives empty list (non-fatal); `ValueError` (shlex parse error) → emit warning to stderr

**Constraints:** Must not modify `sys.argv` directly

---

### UNIT-02 — `_expand_options_file(argv: list) → list`

**Purpose:** Insert tokens from `--options-file FILE` before remaining argv tokens.

**Algorithm:**
1. Scan `argv` for `--options-file` token (or `--options-file=FILE` form)
2. If found: extract `FILE`; call `_read_options_file(FILE)` → `opts_tokens`
3. Return: `argv_before_flag + opts_tokens + argv_after_flag`
4. If not found: return `argv` unchanged

**Key constraint:** Direct CLI args must follow options-file args to allow override (SWE1-068)

---

### UNIT-03 — `discover_files(includes, excludes) → list[str]`

**Purpose:** Expand glob patterns into a de-duplicated, sorted list of source file paths, applying exclusions.

**Algorithm:**
1. For each include glob: call `glob_mod.glob(pattern, recursive=True)` → file list
2. Filter: keep only `.c` and `.h` files
3. For each file: check `_path_matches_exclude(filepath, excludes)` → discard if True
4. De-duplicate using `dict.fromkeys()` (preserves order)
5. Return sorted list

---

### UNIT-04 — `_path_matches_exclude(filepath: str, exclude_globs: list) → bool`

**Purpose:** Return `True` if the filepath matches any exclude glob pattern.

**Algorithm:** For each glob in `exclude_globs`: if `fnmatch.fnmatch(filepath, glob)` or `glob in filepath` → return `True`. Return `False`.

---

### UNIT-05 — `load_config(path: str) → dict`

**Purpose:** Load and return the YAML configuration as a Python dictionary.

**Algorithm:**
1. Open `path`; call `yaml.safe_load()`
2. If result is `None` or not a `dict` → `sys.exit(2)` with message
3. Return config dict

---

### UNIT-10 — `apply_defines(text: str, defines: list) → str`

**Purpose:** Substitute project-specific keywords and type aliases before rule checking.

**Algorithm:**
1. For each `(pattern, replacement)` pair in `defines`: apply `re.sub(pattern, replacement, text)`
2. Return substituted text

**Design note:** Substitutions are applied in definition-file order; order matters for overlapping patterns.

---

### UNIT-14 — `strip_comments(source: str) → str`

**Purpose:** Replace C block (`/* */`) and line (`//`) comments with whitespace, preserving line numbers.

**Algorithm:**
1. Use a state-machine regex scan over `source`
2. For each block comment: replace content with spaces (preserve newlines)
3. For each line comment: replace from `//` to end-of-line with spaces
4. Return result with identical line count to input

**Constraint:** Must not alter line count; `build_line_map` depends on unchanged newline positions.

---

### UNIT-16 — `preprocess(source: str) → str`

**Purpose:** Produce clean source text suitable for regex-based rule checks.

**Algorithm:**
1. Call `strip_comments(source)` → comment-free text
2. Call `strip_strings(result)` → string-literal-free text
3. Return result

---

### UNIT-19 — `_build_brace_depths(clean: str) → list[int]`

**Purpose:** Build a per-character brace-depth array used to determine identifier scope.

**Algorithm:**
1. Initialise `depth = 0`; `depths = []`
2. For each character `ch` in `clean`:
   - If `ch == '{'`: append current depth; increment depth
   - If `ch == '}'`: decrement depth; append current depth
   - Else: append current depth
3. Return `depths`

**Usage:** `depths[pos] == 0` → global scope; `depths[pos] == 1` → file-scope static; `depths[pos] > 1` → local scope

---

### UNIT-21 — `Checker.__init__(...)`

**Purpose:** Initialise the checker for a single source file.

**Algorithm:**
1. Store `filepath`, `source`, `cfg`
2. Call `preprocess(source)` → `self.clean`
3. Find and record typedef-close brace positions to exclude from variable detection
4. Apply `apply_defines(self.clean, defines)` if `defines` provided → update `self.clean`
5. Compute `self.module = module_name(filepath)`
6. Call `build_line_map(source)` → `self._line_map`
7. Call `_build_brace_depths(self.clean)` → `self._brace_depths`
8. Call `_comment_only_lines(source)` → `self._comment_only`
9. Store `disabled_rules`, `alias_prefixes`, `spell_dict`

---

### UNIT-22 — `Checker.run_all() → CheckResult`

**Purpose:** Orchestrate all rule checks; return aggregated `CheckResult`.

**Algorithm:** Call each enabled `_check_*` method in fixed order; each appends to `self.result.violations`. Return `self.result`.

**Order:** `_check_defines`, `_check_variables`, `_check_functions`, `_check_typedefs`, `_check_enums`, `_check_structs`, `_check_include_guard`, `_check_misc`, `_check_yoda`, `_check_spelling`, `_check_reserved_names`, `_check_copyright_header`, `_check_block_comment_spacing`, `_check_eof_comment`

---

### UNIT-23 — `Checker._check_variables() → None`

**Purpose:** Detect and validate all variable declarations against configured rules.

**Algorithm:**
1. Apply `RE_VAR_DECL` regex to `self.clean`
2. For each match: determine scope via `self._brace_depths[match.start()]`
3. Skip if position is inside a typedef-struct body (`self._typedef_close_positions`)
4. Determine if static via `static` keyword present in match
5. Extract type, pointer stars, and name
6. Check: module prefix, case, g\_/s\_ prefix, p\_/pp\_/b\_/h\_ prefix, prefix order, min/max length, numeric-in-name
7. Skip if rule in `self._disabled_rules`
8. Emit `Violation` via `self.result.add()`

---

### UNIT-25 — `Checker._check_defines() → None`

**Purpose:** Detect `#define` directives and validate macro/constant names.

**Algorithm:**
1. Apply `RE_DEFINE` regex to `self.clean`
2. Classify each match as constant (no parameters) or macro (has parameters)
3. Skip if name matches `exempt_patterns`
4. Check: UPPER\_SNAKE case, module prefix, min/max length
5. Emit violations as appropriate

---

### UNIT-31 — `Checker._check_yoda() → None`

**Purpose:** Enforce Yoda-condition ordering in equality comparisons (Barr-C 8.4).

**Algorithm:**
1. Apply `RE_YODA` regex to find `==` and `!=` comparisons
2. For each match: determine left and right operands
3. If right operand is a constant/literal and left is a variable → violation (constant must be on left)
4. Emit `misc.yoda_condition` violation with line/col

---

### UNIT-34 — `SignChecker._check_calls() → list[Violation]`

**Purpose:** Detect sign-incompatible literal arguments in function calls.

**Algorithm:**
1. Build function-signature table from all header files in `source_cache`
2. For each `.c` file: find function calls via `_extract_call_args()`
3. For each argument: classify as signed/unsigned literal via `_classify_arg()`
4. Look up parameter type from signature table; resolve typedef chain via `_signedness_of_type()`
5. Handle `plain_char_is_signed` with `try/finally` to avoid mutating `_SIGNED_TYPES` permanently
6. Emit `sign_compatibility` violation if mismatch detected

---

### UNIT-37 — `_baseline_key(v: Violation) → str`

**Purpose:** Produce a stable string key for a violation used in baseline suppression.

**Algorithm:** Return `f"{v.rule}::{v.filepath}::{v.line}::{v.message}"`

**Design note:** Line number is included so the same violation at a different location is treated as new.

---

### UNIT-38 — `_violations_to_json(violations: list, files_checked: int) → str`

**Purpose:** Serialise violations to a JSON string conforming to the documented schema.

**Algorithm:**
1. Build `summary` dict: `files_checked`, `errors`, `warnings`, `info`, `total`
2. Build `violations` list: one dict per `Violation` with all six fields
3. Return `json.dumps({"summary": summary, "violations": violations}, indent=2)`

---

### UNIT-39 — `_violations_to_sarif(violations: list, tool_version: str) → str`

**Purpose:** Serialise violations to SARIF 2.1.0 JSON.

**Algorithm:**
1. Build SARIF `tool` object with `driver.name = "CNameCheck"`, `driver.version = tool_version`
2. For each violation: build a SARIF `result` object with `ruleId`, `level`, `message.text`, `locations[0].physicalLocation`
3. Return complete SARIF document as `json.dumps(..., indent=2)`

---

## 6. Data Design

### 6.1 Configuration Schema (YAML)

The top-level configuration keys and their types:

| Key | Type | Default | Purpose |
|---|---|---|---|
| `file_prefix.enabled` | `bool` | `true` | Master enable for module-prefix rules |
| `file_prefix.separator` | `str` | `"_"` | Separator between module prefix and identifier |
| `variables.enabled` | `bool` | `true` | Master enable for variable rules |
| `variables.case` | `str` | `"lower_snake"` | Default case for all variable scopes |
| `variables.min_length` | `int` | `3` | Minimum identifier length (Barr-C 7.1.e) |
| `variables.max_length` | `int` | `40` | Maximum identifier length |
| `variables.global.g_prefix.enabled` | `bool` | `true` | Enforce `g_` prefix on globals |
| `variables.static.s_prefix.enabled` | `bool` | `true` | Enforce `s_` prefix on file-statics |
| `variables.pointer_prefix.enabled` | `bool` | `true` | Enforce `p_` on single-pointer variables |
| `functions.style` | `str` | `"object_verb"` | Function naming style |
| `functions.static_prefix.enabled` | `bool` | `false` | Enforce static function prefix |
| `misc.line_length.max` | `int` | `120` | Maximum line length in characters |
| `misc.magic_numbers.enabled` | `bool` | `true` | Detect magic number literals |

### 6.2 Violation Data Class

```
Violation:
  filepath : str   — absolute or relative path to source file
  line     : int   — 1-based line number
  col      : int   — 1-based column number
  severity : str   — one of: "error" | "warning" | "info"
  rule     : str   — dot-separated rule ID (e.g. "variable.global.case")
  message  : str   — human-readable description of the violation
```

### 6.3 Baseline File Format

```json
[
  {
    "rule": "variable.global.case",
    "filepath": "src/uart.c",
    "line": 42,
    "message": "'UartGlobalCount' should be lower_snake"
  }
]
```

---

## 7. Resource Usage

| Resource | Usage | Notes |
|---|---|---|
| Memory | O(N) where N = total source characters | Source cache holds raw text for all files |
| CPU | O(N × R) where R = number of enabled rules | Each rule applies one or more regex passes |
| Disk I/O | One read per source file | Cache eliminates second read for sign-compatibility check |
| File handles | One at a time (sequential) | No concurrent file access |

---

## 8. Traceability: SW Requirements → Units

| SW-REQ-ID | Requirement Area | Implementing Units |
|---|---|---|
| SWE1-001 to SWE1-002 | Config loading | UNIT-05 |
| SWE1-003 | Defines substitution | UNIT-09, UNIT-10 |
| SWE1-004 | Alias file | UNIT-06 |
| SWE1-005 to SWE1-006 | Exclusions | UNIT-07, UNIT-08 |
| SWE1-007 to SWE1-010 | Dictionary management | UNIT-11, UNIT-12, UNIT-13 |
| SWE1-011 to SWE1-016 | Source parsing | UNIT-14, UNIT-15, UNIT-16, UNIT-17, UNIT-18, UNIT-19, UNIT-20 |
| SWE1-017 to SWE1-029 | Variable rules | UNIT-23, UNIT-43, UNIT-44, UNIT-45 |
| SWE1-030 to SWE1-034 | Function rules | UNIT-24 |
| SWE1-035 to SWE1-039 | Constant/macro rules | UNIT-25 |
| SWE1-040 to SWE1-042 | Type rules | UNIT-26, UNIT-27, UNIT-28 |
| SWE1-043 to SWE1-044 | Include guard rules | UNIT-29 |
| SWE1-045 to SWE1-050 | Miscellaneous rules | UNIT-30, UNIT-31 |
| SWE1-051 to SWE1-053 | Cross-file sign check | UNIT-34 |
| SWE1-054 to SWE1-056 | Reserved names / spell | UNIT-32, UNIT-33 |
| SWE1-057 | Text output | UNIT-41 |
| SWE1-058 to SWE1-059 | JSON output | UNIT-38 |
| SWE1-060 | SARIF output | UNIT-39 |
| SWE1-061 | GitHub annotations | UNIT-42 |
| SWE1-063 | Summary | UNIT-40 |
| SWE1-065 to SWE1-067 | Baseline | UNIT-35, UNIT-36, UNIT-37 |
| SWE1-068 to SWE1-070 | CLI / entry point | UNIT-01, UNIT-02, UNIT-03, UNIT-04, UNIT-46 |

---

## 9. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Dermot Murphy | | 2026-04-12 |
| Technical Reviewer | \<Name\> | | |
| Quality Assurance | \<Name\> | | |
| Approver | \<Name\> | | |

> **⚠️ Important:** This document must be placed under configuration management (SUP.8) upon approval. Any post-approval changes require a change request (SUP.10) and a new document version.
