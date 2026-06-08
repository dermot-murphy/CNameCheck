# Software Detailed Design

*Automotive SPICE® PAM v4.0 | SWE.3 Software Detailed Design and Unit Construction*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CSC-SWE3-001 | **Version** | 1.9 |
| **Project** | CStyleCheck | **Date** | 2026-06-08 |
| **Status** | Released | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SWE.3 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.9 | 2026-06-08 | Claude | Add UNIT-102 to UNIT-112 for 11 new rules (issues #221–#232); update §8 traceability |
| 1.8 | 2026-06-05 | Claude | CSC-AUD-005 corrective action — fix factual errors identified in audit |
| 1.6 | 2026-06-04 | Claude | Add UNIT-95 to UNIT-101 for five new features (inline suppression, fixer, wizard, per-dir config, HTML output); update §4.1 package structure; update §8 traceability — issues #188 #189 #190 #193 #192 |
| 1.5 | 2026-06-04 | Claude | Deep accuracy audit: correct 48 stale line numbers, add 4 missing config.py units (UNIT-91 to UNIT-94), update §4.1 package structure, update §3.1 referenced doc versions — resolves issue #163 |
| 1.4 | 2026-06-04 | Claude | Automated accuracy audit: update referenced doc versions in §3.1 — resolves issue #163 |
| 1.3 | 2026-05-28 | Claude | Update all 89 Source Location values to reflect package refactor (issue #144); add UNIT-90 (_check_whitespace_ratio); update §4.1 to show completed refactor; update run_all order — closes issues #146 #147 #148 |
| 1.2 | 2026-05-28 | Claude | Added ~25 units missing from v1.1 (load_spell_words, load_banned_names_file, load_copyright_file, to_case, is_exempt, _cfg, extract_comments, all Checker helper methods, _check_copyright_header, _body_is_object_verb, _check_comment_ratio, _check_lowercase_l_suffix, _check_octal_constants, _check_trigraphs, _is_reserved, _check_name_reserved, _ParamSig, _FuncSig, sign-checker helpers, SignChecker, DeclaredNotDefinedChecker, _strip_module_prefix, Tee, parse_args, _build_parser, _github_annotation_category, _is_constant_token, _is_variable_token). Updated all source line numbers to match v1.2.x source. Added Section 4.1 Target Package Structure documenting planned refactor (issue #65). Updated purpose to reference v1.2.x. |
| 1.1 | 2026-05-28 | Claude | Reviewed and updated for v1.1.0 release; revision history maintained per ASPICE GP 2.2.4 |
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose & Scope

This document defines the detailed design of each software unit in **CStyleCheck v1.2.x**, providing the algorithmic specification, interface contracts, and data design required for unit construction and verification. It satisfies **Automotive SPICE® PAM v4.0, SWE.3 — Software Detailed Design and Unit Construction**.

### 3.1 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CSC-SWE1-001 | CStyleCheck Software Requirements Specification | 1.8 |
| CSC-SWE2-001 | CStyleCheck Software Architecture Description | 1.7 |
| CSC-SWE4-001 | CStyleCheck Unit Verification Specification | 1.8 |

---

## 4. Unit Catalogue

All source locations refer to the current package layout under `src/cstylecheck/` (post-package-split, issue #144). The **Target Module** column is now the **actual** module; the old monolithic `src/cstylecheck.py` no longer exists.

| Unit ID | Unit Name | Source Location | Component | Module |
|---|---|---|---|---|
| UNIT-01 | `_read_options_file` | `config.py:30` | COMP-01 | `config.py` |
| UNIT-02 | `_expand_options_file` | `config.py:61` | COMP-01 | `config.py` |
| UNIT-03 | `discover_files` | `cli.py:113` | COMP-01 | `cli.py` |
| UNIT-04 | `_path_matches_exclude` | `cli.py:39` | COMP-01 | `cli.py` |
| UNIT-05 | `load_config` | `config.py:251` | COMP-02 | `config.py` |
| UNIT-06 | `load_alias_file` | `config.py:294` | COMP-02 | `config.py` |
| UNIT-07 | `load_exclusions_file` | `config.py:340` | COMP-02 | `config.py` |
| UNIT-08 | `_disabled_rules_for_file` | `config.py:389` | COMP-02 | `config.py` |
| UNIT-09 | `load_defines_file` | `config.py:418` | COMP-02 | `config.py` |
| UNIT-10 | `apply_defines` | `config.py:467` | COMP-02 | `config.py` |
| UNIT-11 | `_load_dict_file` | `config.py:484` | COMP-03 | `config.py` |
| UNIT-12 | `_data_file` | `config.py:503` | COMP-03 | `config.py` |
| UNIT-13 | `_build_spell_dict` | `config.py:642` | COMP-03 | `config.py` |
| UNIT-14 | `strip_comments` | `preprocessor.py:19` | COMP-04 | `preprocessor.py` |
| UNIT-15 | `strip_strings` | `preprocessor.py:29` | COMP-04 | `preprocessor.py` |
| UNIT-16 | `preprocess` | `preprocessor.py:44` | COMP-04 | `preprocessor.py` |
| UNIT-17 | `build_line_map` | `preprocessor.py:113` | COMP-04 | `preprocessor.py` |
| UNIT-18 | `offset_to_line_col` | `preprocessor.py:120` | COMP-04 | `preprocessor.py` |
| UNIT-19 | `_build_brace_depths` | `preprocessor.py:93` | COMP-04 | `preprocessor.py` |
| UNIT-20 | `_comment_only_lines` | `preprocessor.py:48` | COMP-04 | `preprocessor.py` |
| UNIT-21 | `Checker.__init__` | `checker.py:142` | COMP-05 | `checker.py` |
| UNIT-22 | `Checker.run_all` | `checker.py:286` | COMP-05 | `checker.py` |
| UNIT-23 | `Checker._check_variables` | `checker.py:366` | COMP-05a | `checker.py` |
| UNIT-24 | `Checker._check_functions` | `checker.py:870` | COMP-05b | `checker.py` |
| UNIT-25 | `Checker._check_defines` | `checker.py:318` | COMP-05c | `checker.py` |
| UNIT-26 | `Checker._check_typedefs` | `checker.py:960` | COMP-05d | `checker.py` |
| UNIT-27 | `Checker._check_enums` | `checker.py:984` | COMP-05d | `checker.py` |
| UNIT-28 | `Checker._check_structs` | `checker.py:1048` | COMP-05d | `checker.py` |
| UNIT-29 | `Checker._check_include_guard` | `checker.py:1190` | COMP-05e | `checker.py` |
| UNIT-30 | `Checker._check_misc` | `checker.py:1223` | COMP-05f | `checker.py` |
| UNIT-31 | `Checker._check_yoda` | `checker.py:1821` | COMP-05f | `checker.py` |
| UNIT-32 | `Checker._check_reserved_names` | `checker.py:2047` | COMP-05f | `checker.py` |
| UNIT-33 | `Checker._check_spelling` | `checker.py:1802` | COMP-05f | `checker.py` |
| UNIT-34 | `SignChecker._check_calls` | `sign_checker.py:273` | COMP-05g | `sign_checker.py` |
| UNIT-35 | `load_baseline` | `baseline.py:25` | COMP-06 | `baseline.py` |
| UNIT-36 | `write_baseline` | `baseline.py:40` | COMP-06 | `baseline.py` |
| UNIT-37 | `_baseline_key` | `baseline.py:20` | COMP-06 | `baseline.py` |
| UNIT-38 | `_violations_to_json` | `output.py:40` | COMP-07 | `output.py` |
| UNIT-39 | `_violations_to_sarif` | `output.py:72` | COMP-07 | `output.py` |
| UNIT-40 | `print_summary` | `output.py:125` | COMP-07 | `output.py` |
| UNIT-41 | `Violation.__str__` | `models.py:59` | COMP-07 | `models.py` |
| UNIT-42 | `Violation.github_annotation` | `models.py:45` | COMP-07 | `models.py` |
| UNIT-43 | `matches_case` | `utils.py:48` | COMP-05 (shared) | `utils.py` |
| UNIT-44 | `matches_case_abbrev` | `utils.py:53` | COMP-05 (shared) | `utils.py` |
| UNIT-45 | `module_name` | `utils.py:84` | COMP-05 (shared) | `utils.py` |
| UNIT-46 | `main` | `cli.py:319` | Entry point | `cli.py` |
| UNIT-47 | `append_trend_record` (script) | `scripts/ci/append_trend_record.py` | CI script | (unchanged) |
| UNIT-48 | `generate_trend` (script) | `scripts/ci/generate_trend.py` | CI script | (unchanged) |
| UNIT-49 | `update_readme_badge` (script) | `scripts/ci/update_readme_badge.py` | CI script | (unchanged) |
| UNIT-50 | `load_spell_words` | `config.py:277` | COMP-02 | `config.py` |
| UNIT-51 | `load_banned_names_file` | `config.py:540` | COMP-02 | `config.py` |
| UNIT-52 | `load_copyright_file` | `config.py:575` | COMP-02 | `config.py` |
| UNIT-53 | `to_case` | `utils.py:75` | COMP-05 (shared) | `utils.py` |
| UNIT-54 | `is_exempt` | `utils.py:88` | COMP-05 (shared) | `utils.py` |
| UNIT-55 | `_cfg` | `utils.py:98` | COMP-05 (shared) | `utils.py` |
| UNIT-56 | `extract_comments` | `preprocessor.py:69` | COMP-04 | `preprocessor.py` |
| UNIT-57 | `Checker._violation` | `checker.py:213` | COMP-05 | `checker.py` |
| UNIT-58 | `Checker._v` | `checker.py:217` | COMP-05 | `checker.py` |
| UNIT-59 | `Checker._prefix` | `checker.py:224` | COMP-05 | `checker.py` |
| UNIT-60 | `Checker._require_module_prefix` | `checker.py:230` | COMP-05 | `checker.py` |
| UNIT-61 | `Checker._depth_at` | `checker.py:263` | COMP-05 | `checker.py` |
| UNIT-62 | `Checker._strip_any_prefix` | `checker.py:268` | COMP-05 | `checker.py` |
| UNIT-63 | `Checker._check_copyright_header` | `checker.py:1089` | COMP-05f | `checker.py` |
| UNIT-64 | `Checker._body_is_object_verb` | `checker.py:838` | COMP-05b | `checker.py` |
| UNIT-65 | `Checker._check_comment_ratio` | `checker.py:1537` | COMP-05f | `checker.py` |
| UNIT-66 | `Checker._check_lowercase_l_suffix` | `checker.py:1933` | COMP-05f | `checker.py` |
| UNIT-67 | `Checker._check_octal_constants` | `checker.py:1971` | COMP-05f | `checker.py` |
| UNIT-68 | `Checker._check_trigraphs` | `checker.py:2010` | COMP-05f | `checker.py` |
| UNIT-69 | `Checker._is_reserved` | `checker.py:2029` | COMP-05f | `checker.py` |
| UNIT-70 | `Checker._check_name_reserved` | `checker.py:2039` | COMP-05f | `checker.py` |
| UNIT-71 | `Checker._is_constant_token` | `checker.py:1892` | COMP-05f | `checker.py` |
| UNIT-72 | `Checker._is_variable_token` | `checker.py:1906` | COMP-05f | `checker.py` |
| UNIT-73 | `_ParamSig` | `models.py:106` | COMP-05g | `models.py` |
| UNIT-74 | `_FuncSig` | `models.py:114` | COMP-05g | `models.py` |
| UNIT-75 | `_classify_tokens` | `sign_checker.py:70` | COMP-05g | `sign_checker.py` |
| UNIT-76 | `_signedness_of_type` | `sign_checker.py:95` | COMP-05g | `sign_checker.py` |
| UNIT-77 | `_classify_arg` | `sign_checker.py:110` | COMP-05g | `sign_checker.py` |
| UNIT-78 | `_extract_call_args` | `sign_checker.py:119` | COMP-05g | `sign_checker.py` |
| UNIT-79 | `SignChecker.__init__` | `sign_checker.py:159` | COMP-05g | `sign_checker.py` |
| UNIT-80 | `SignChecker.ingest` | `sign_checker.py:166` | COMP-05g | `sign_checker.py` |
| UNIT-81 | `SignChecker.check` | `sign_checker.py:169` | COMP-05g | `sign_checker.py` |
| UNIT-82 | `SignChecker._build_typedef_map` | `sign_checker.py:192` | COMP-05g | `sign_checker.py` |
| UNIT-83 | `SignChecker._build_signatures` | `sign_checker.py:231` | COMP-05g | `sign_checker.py` |
| UNIT-84 | `DeclaredNotDefinedChecker` (class) | `sign_checker.py:319` | COMP-05g | `sign_checker.py` |
| UNIT-85 | `_strip_module_prefix` | `utils.py:113` | COMP-05 (shared) | `utils.py` |
| UNIT-86 | `Tee` | `output.py:17` | COMP-07 | `output.py` |
| UNIT-87 | `parse_args` | `cli.py:185` | COMP-01 | `cli.py` |
| UNIT-88 | `_build_parser` | `cli.py:190` | COMP-01 | `cli.py` |
| UNIT-89 | `_github_annotation_category` | `utils.py:21` | COMP-07 | `utils.py` |
| UNIT-90 | `Checker._check_whitespace_ratio` | `checker.py:1675` | COMP-05f | `checker.py` |
| UNIT-91 | `_find_default_rules` | `config.py:93` | COMP-02 | `config.py` |
| UNIT-92 | `_deep_merge` | `config.py:114` | COMP-02 | `config.py` |
| UNIT-93 | `_collect_paths` | `config.py:137` | COMP-02 | `config.py` |
| UNIT-94 | `update_config` | `config.py:148` | COMP-02 | `config.py` |
| UNIT-95 | `parse_inline_suppressions` | `preprocessor.py` | COMP-04 | `preprocessor.py` |
| UNIT-96 | `apply_fixes` | `fixer.py` | COMP-08 | `fixer.py` |
| UNIT-97 | `unified_diff` | `fixer.py` | COMP-08 | `fixer.py` |
| UNIT-98 | `run_wizard` | `wizard.py` | COMP-09 | `wizard.py` |
| UNIT-99 | `run_preset` | `wizard.py` | COMP-09 | `wizard.py` |
| UNIT-100 | `resolve_per_dir_config` | `config.py` | COMP-10 | `config.py` |
| UNIT-101 | `_violations_to_html` | `output.py` | COMP-07 | `output.py` |
| UNIT-102 | `_check_function_length` | `checker.py` | COMP-01 | `checker.py` |
| UNIT-103 | `_check_function_doc_header` | `checker.py` | COMP-01 | `checker.py` |
| UNIT-104 | `_check_assert_density` | `checker.py` | COMP-01 | `checker.py` |
| UNIT-105 | `_check_null_statement_comment` | `checker.py` | COMP-01 | `checker.py` |
| UNIT-106 | `_check_declaration_spacing` | `checker.py` | COMP-01 | `checker.py` |
| UNIT-107 | `_check_file_length` | `checker.py` | COMP-01 | `checker.py` |
| UNIT-108 | `_check_reserved_header_name` | `checker.py` | COMP-01 | `checker.py` |
| UNIT-109 | `_check_macro_trailing_semicolon` | `checker.py` | COMP-01 | `checker.py` |
| UNIT-110 | `_check_macro_multistatement_wrapper` | `checker.py` | COMP-01 | `checker.py` |
| UNIT-111 | `_check_identifier_length` | `checker.py` | COMP-01 | `checker.py` |
| UNIT-112 | `_check_no_single_char_identifiers` | `checker.py` | COMP-01 | `checker.py` |

---

## 4.1 Package Structure

Issue #144 completed the refactor of `src/cstylecheck.py` into a Python package. The current layout is:

```
src/cstylecheck/
  __init__.py      — public re-exports, version handling
  models.py        — Violation, CheckResult, _ParamSig, _FuncSig
  preprocessor.py  — strip_comments, strip_strings, preprocess,
                     build_line_map, offset_to_line_col,
                     _build_brace_depths, _comment_only_lines,
                     extract_comments, parse_inline_suppressions
  utils.py         — matches_case, matches_case_abbrev, to_case,
                     module_name, is_exempt, _cfg,
                     _strip_module_prefix, _github_annotation_category
  config.py        — _read_options_file, _expand_options_file,
                     _find_default_rules, _deep_merge, _collect_paths,
                     update_config, load_config, load_spell_words,
                     load_alias_file, load_exclusions_file,
                     _disabled_rules_for_file, load_defines_file,
                     apply_defines, _load_dict_file, _data_file,
                     load_banned_names_file, load_copyright_file,
                     _build_spell_dict, _BUILTIN_DICT,
                     resolve_per_dir_config
  checker.py       — Checker class, all regex patterns (RE_DEFINE,
                     RE_VAR_DECL, RE_FUNCTION_DEF, …), all _check_* methods
  sign_checker.py  — SignChecker, DeclaredNotDefinedChecker,
                     sign-analysis helpers (_classify_tokens,
                     _signedness_of_type, _classify_arg,
                     _extract_call_args)
  baseline.py      — load_baseline, write_baseline, _baseline_key
  output.py        — Tee, _violations_to_json, _violations_to_sarif,
                     _violations_to_html, print_summary
  fixer.py         — apply_fixes, unified_diff
  wizard.py        — run_wizard, run_preset
  cli.py           — discover_files, _path_matches_exclude, parse_args,
                     _build_parser, main
```

`_version.py` remains a top-level module in `src/` (not inside the package) because it is generated by the build/CI system independently of the package tree. `_read_options_file` and `_expand_options_file` reside in `config.py` (not `cli.py`) in the current implementation.

**Dependency order (no circular imports):**

1. `models.py` — stdlib only
2. `preprocessor.py` — stdlib only
3. `utils.py` — stdlib only
4. `config.py` — imports from `preprocessor`, `utils`, `models`
5. `checker.py` — imports from `models`, `preprocessor`, `utils`, `config`
6. `sign_checker.py` — imports from `models`, `preprocessor`, `checker` (regex patterns)
7. `baseline.py` — imports from `models`
8. `output.py` — imports from `models`
9. `cli.py` — imports from all of the above
10. `__init__.py` — imports from all sub-modules; re-exports the public API

**Backward-compatibility guarantee:** `__init__.py` re-exports every name that was previously at module level in `cstylecheck.py`. The CLI entry point (`cstylecheck = "cstylecheck:main"` in `pyproject.toml`) and the test harness (`import cstylecheck as _mod`) continue to work without modification.

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

**Order:** `_check_copyright_header`, `_check_defines`, `_check_variables`, `_check_functions`, `_check_typedefs`, `_check_enums`, `_check_structs`, `_check_include_guard` (headers only), `_check_misc`, `_check_comment_ratio`, `_check_whitespace_ratio`, `_check_yoda`, `_check_reserved_names`, `_check_lowercase_l_suffix`, `_check_octal_constants`, `_check_trigraphs`, `_check_spelling` (when dictionary configured)

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

**Algorithm:** Return `f"{v.filepath}:{v.line}:{v.rule}:{v.message}"`

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
1. Build SARIF `tool` object with `driver.name = "CStyleCheck"`, `driver.version = tool_version`
2. For each violation: build a SARIF `result` object with `ruleId`, `level`, `message.text`, `locations[0].physicalLocation`
3. Return complete SARIF document as `json.dumps(..., indent=2)`

---

### UNIT-50 — `load_spell_words(path: str) → set`

**Purpose:** Load a plain-text file of exempt spell-check words (one per line).

**Algorithm:**
1. Read file at `path`; for each line strip whitespace, skip blank lines and `#`-comment lines
2. Add the lowercased word to result set
3. Return result set

**Error handling:** `OSError` → `sys.exit` with message

---

### UNIT-51 — `load_banned_names_file(path: str) → frozenset`

**Purpose:** Load additional banned identifier names from a plain-text file.

**Algorithm:**
1. Read file at `path`; for each line strip whitespace, skip blank and `#`-comment lines
2. Add name (case-sensitive) to result set
3. Return `frozenset(result)`

**Error handling:** `OSError` → `sys.exit` with message

---

### UNIT-52 — `load_copyright_file(path: str) → tuple`

**Purpose:** Parse a copyright header template file and return `(template_text, match_re)`.

**Algorithm:**
1. Read file at `path`; normalise line endings (CRLF → LF)
2. Extract first `/* ... */` block comment as the template
3. For each line of the template: escape literally via `re.escape`, except replace the year token on the `(C) Copyright YEAR` line with a flexible pattern `\d{4}(?:[-–]\d{4})?`
4. Compile joined pattern anchored with `\A`
5. Return `(template_text, compiled_re)`

**Error handling:** `OSError` → `sys.exit`; no block comment found → `sys.exit`

---

### UNIT-53 — `to_case(name: str, style: str) → str`

**Purpose:** Convert `name` to the given naming style — used to derive enum member prefixes.

**Algorithm:** `upper_snake`/`upper` → `name.upper()`; `lower_snake`/`lower`/`camel` → `name.lower()`; `pascal`/other → `name` unchanged.

---

### UNIT-54 — `is_exempt(name: str, patterns: list) → bool`

**Purpose:** Return `True` if `name` matches any of the exempt regex patterns.

**Algorithm:** For each pattern `p` in `patterns`: if `re.match(p, name)` matches → return `True`. Silently skip malformed patterns. Return `False`.

---

### UNIT-55 — `_cfg(cfg: dict, *keys, default=None)`

**Purpose:** Safe nested dict traversal — retrieve `cfg[k1][k2]…` returning `default` on any missing key or non-dict node.

**Algorithm:** Iteratively descend into `cfg` using each key; if any step is not a dict or key is absent, return `default`.

---

### UNIT-56 — `extract_comments(source: str) → list`

**Purpose:** Return `[(lineno, text)]` for all comments in `source`, stripped of Doxygen markers.

**Algorithm:**
1. Build line map via `build_line_map(source)`
2. Find all `/* … */` block comments via regex; strip `@\word` and leading `*` markers from text; record `(lineno, text)`
3. Find all `// …` line comments; strip Doxygen markers; record `(lineno, text)`
4. Return combined list

---

### UNIT-57 — `Checker._violation(pos, sev, rule, msg) → Violation`

**Purpose:** Helper — construct a `Violation` from a character-offset position by converting it to `(line, col)` via the line map.

---

### UNIT-58 — `Checker._v(pos, sev, rule, msg) → None`

**Purpose:** Helper — emit a `Violation` after checking per-identifier exclusions. Skips emission if the identifier name found in `msg` (quoted with `'...'`) has `rule` disabled in `self._ident_disabled`.

---

### UNIT-59 — `Checker._prefix() → str`

**Purpose:** Return the canonical module prefix string (e.g. `"uart_"`) for the current file, respecting `file_prefix.separator` and `file_prefix.case` from config.

---

### UNIT-60 — `Checker._require_module_prefix(name, pos, rule) → None`

**Purpose:** Emit a violation if `name` does not start with the module prefix or any registered alias prefix.

**Algorithm:**
1. Return immediately if `file_prefix.enabled` is false, or if module is `main` and `exempt_main` is true, or if `name` matches `exempt_patterns`
2. Build accepted prefix list (canonical + aliases)
3. If `name.lower()` starts with any accepted prefix → return (pass)
4. Emit violation with canonical prefix in message and alias hint if aliases exist

---

### UNIT-61 — `Checker._depth_at(pos: int) → int`

**Purpose:** Return the brace depth at character position `pos` in `self.clean`.

---

### UNIT-62 — `Checker._strip_any_prefix(name: str) → str`

**Purpose:** Return `name` with the longest matching module prefix (canonical or alias) removed.

---

### UNIT-63 — `Checker._check_copyright_header() → None`

**Purpose:** Verify the file begins with the configured copyright block comment template.

**Algorithm:**
1. If `self._copyright` is `None` → return (check not configured)
2. Match `compiled_re` against `self.source` at position 0
3. If no match → emit `misc.copyright_header` violation at line 1

---

### UNIT-64 — `Checker._body_is_object_verb(body, object_exclusions, abbrevs) → bool`

**Purpose:** Check whether a function name body (after the module prefix) satisfies the object_verb (or verb_object) convention.

**Algorithm:**
1. Split `body` on `_` into segments
2. If any segment appears in `object_exclusions` → return `True` (waived)
3. Otherwise every segment must be PascalCase or appear in `abbrevs`; a single-segment body (verb only) is also accepted

---

### UNIT-65 — `Checker._check_comment_ratio() → None`

**Purpose:** Enforce a minimum ratio of comment lines to code lines (issue #68).

**Algorithm:**
1. Skip if `misc.comment_ratio.enabled` is false
2. Identify and exclude the file header region (leading comment/blank lines before first code line)
3. Classify remaining lines as comment, code, blank, or Doxygen (excluded from count)
4. Skip if `code_lines < min_code_lines`
5. Compute `ratio = comment_lines / code_lines`
6. Emit `misc.comment_ratio` violation if ratio is below the warning or error threshold

---

### UNIT-66 — `Checker._check_lowercase_l_suffix() → None`

**Purpose:** Detect integer literals with lowercase `l` suffix (MISRA C:2012 Rule 7.3).

**Algorithm:** Scan `self.clean` for numeric literals ending with `l` or `L` followed by `u`/`U` in the wrong order or a bare `l`; emit `misc.lowercase_l_suffix` violation.

---

### UNIT-67 — `Checker._check_octal_constants() → None`

**Purpose:** Detect octal integer constants (leading `0` followed by digits) (MISRA C:2012 Rule 7.1).

**Algorithm:** Scan `self.clean` for tokens matching `0[0-7]+` not preceded by `0x`; emit `misc.octal_constant` violation.

---

### UNIT-68 — `Checker._check_trigraphs() → None`

**Purpose:** Detect ANSI C trigraph sequences (MISRA C:2012 Rule 4.2).

**Algorithm:** Scan `self.source` (raw, not preprocessed) for `??` followed by a trigraph character; emit `misc.trigraph` violation for each occurrence.

---

### UNIT-69 — `Checker._is_reserved(name: str) → tuple`

**Purpose:** Return `(is_reserved: bool, reason: str)` indicating whether `name` is a reserved C identifier (keyword, stdlib name, or banned name).

---

### UNIT-70 — `Checker._check_name_reserved(name, pos, sev) → None`

**Purpose:** Emit a `reserved_name` violation if `name` is reserved, using `_is_reserved()`.

---

### UNIT-71 — `Checker._is_constant_token(tok: str) → bool`

**Purpose:** Return `True` if `tok` is a constant expression token (numeric literal, `NULL`, `true`, `false`, character literal, or macro-like ALL_CAPS name).

---

### UNIT-72 — `Checker._is_variable_token(tok: str) → bool`

**Purpose:** Return `True` if `tok` looks like a variable identifier (lowercase or mixed-case, not a keyword).

---

### UNIT-73 — `_ParamSig`

**Purpose:** Dataclass holding signedness information for one function parameter: `name`, `type_str` (as written), and `signedness` (`signed` | `unsigned` | `unknown`).

---

### UNIT-74 — `_FuncSig`

**Purpose:** Dataclass holding the resolved signature of a declared function: `name` and `params` (list of `_ParamSig`).

---

### UNIT-75 — `_classify_tokens(tokens, signed_types, unsigned_types) → str`

**Purpose:** Return sign classification (`signed` | `unsigned` | `unknown`) from a list of C type/qualifier tokens.

**Algorithm:** If `unsigned` in tokens → `unsigned`; if `signed` in tokens → `signed`; otherwise look each token up in the explicit signed/unsigned type sets; return `unknown` if no match.

---

### UNIT-76 — `_signedness_of_type(type_str, tmap, signed_types, unsigned_types) → str`

**Purpose:** Resolve a full C type string to a sign classification, following typedef chains via `tmap`.

---

### UNIT-77 — `_classify_arg(expr: str) → str`

**Purpose:** Classify one call-site argument expression as `signed`, `unsigned`, `neutral` (plain positive integer, no suffix), or `unknown`.

---

### UNIT-78 — `_extract_call_args(source, paren_pos) → list | None`

**Purpose:** Extract comma-separated argument strings from a function call starting at `paren_pos` (the `(` character). Returns `None` if the call cannot be parsed.

---

### UNIT-79 — `SignChecker.__init__(cfg: dict)`

**Purpose:** Initialise the cross-file sign compatibility checker with the YAML config.

---

### UNIT-80 — `SignChecker.ingest(filepath, source) → None`

**Purpose:** Ingest one file into the checker — stores `(filepath, source, preprocess(source))` for later analysis.

---

### UNIT-81 — `SignChecker.check() → list[Violation]`

**Purpose:** Build typedef and signature tables then check every `.c` call site; return all sign-compatibility violations.

**Algorithm:** Build thread-safe local copies of sign-type sets respecting `plain_char_is_signed`; call `_build_typedef_map`, `_build_signatures`, `_check_calls` in order.

---

### UNIT-82 — `SignChecker._build_typedef_map(signed_types, unsigned_types) → None`

**Purpose:** Parse all typedef scalar declarations from ingested files and resolve each typedef name to a sign classification (following chains up to depth 8).

---

### UNIT-83 — `SignChecker._build_signatures(signed_types, unsigned_types) → None`

**Purpose:** Parse function declarations (ending with `;`) from all ingested files and build the signature table `_sigs`.

---

### UNIT-84 — `DeclaredNotDefinedChecker` (class)

**Purpose:** Cross-file declared-but-not-defined checker. Identifies C objects (`extern` variables, extern functions, forward typedef structs/enums) that are declared but for which no definition is found across all ingested files.

**Key methods:**
- `__init__(cfg)` — initialise declaration/definition sets
- `ingest(filepath, source)` — scan one file for declarations and definitions
- `check() → list[Violation]` — compare declarations against definitions; emit `misc.declared_not_defined` for unresolved items; always returns `[]` for single-file runs

---

### UNIT-85 — `_strip_module_prefix(name: str, prefix: str) → str`

**Purpose:** Return `name` with the module prefix removed (case-insensitive). Returns `name` unchanged if it does not start with `prefix`.

---

### UNIT-86 — `Tee`

**Purpose:** Write to stdout and optionally a log file simultaneously.

**Methods:**
- `__init__(log_fh=None)` — store optional file handle
- `print(*args, **kwargs)` — call built-in `print` to stdout, and to `log_fh` if set
- `close()` — close and release `log_fh`

---

### UNIT-87 — `parse_args() → argparse.Namespace`

**Purpose:** Parse the process command-line arguments using `_build_parser()`.

---

### UNIT-88 — `_build_parser() → argparse.ArgumentParser`

**Purpose:** Construct and return the fully configured `ArgumentParser` for the tool.

**Key argument groups:** help/version, positional files, config/output, include/exclude globs, defines/aliases/exclusions, copyright/banned-names, spell-check, baseline, logging, sign-compatibility, and diagnostics flags.

---

### UNIT-89 — `_github_annotation_category(rule: str) → str`

**Purpose:** Return the GitHub Actions annotation title category for a violation rule.

**Algorithm:** Map `misc.trigraph`, `misc.octal_constant`, `misc.lowercase_l_suffix` → `"MISRA"`; `sign_compatibility` → `"SignCompat"`; `spell_check` → `"SpellCheck"`; naming-convention prefixes (variable, function, constant, …) → `"NamingConvention"`; everything else → `"Misc"`.

---

### UNIT-95 — `parse_inline_suppressions(source: str) → dict`

**Purpose:** Parse `// cstylecheck: disable=…` / `enable=…` / `disable-next-line=…` directives from raw C source and return a mapping of line numbers to the set of suppressed rule IDs at that line.

**Algorithm:**
1. Scan `source` line by line; detect `cstylecheck:` directives in comments (case-insensitive)
2. For `disable=rule.a,rule.b` on the same line as code: add the rule IDs to that line's suppressed set only
3. For `disable-next-line=rule.id`: add rule IDs to the next non-blank, non-comment line's suppressed set
4. For a standalone `disable=rule.id` line: open a block suppression; accumulate affected rule IDs per line until a matching `enable=rule.id` is found; unpaired `disable=` suppresses to end of file
5. Multiple rules are comma-separated in any directive form
6. Return `dict[int, frozenset[str]]` mapping 1-based line numbers to suppressed rule IDs

---

### UNIT-96 — `apply_fixes(source: str, violations: list, safe_only: bool = False) → tuple[str, int]`

**Purpose:** Module-level function. Scans source string for fixable violations and returns (new_source, fix_count).

**Algorithm:**
1. Iterate over violations; for each fixable rule apply the mechanical substitution to the source string
2. Currently supported: `misc.unsigned_suffix` (`u`/`l` → `U`/`L`) and `misc.lowercase_l_suffix`
3. If `safe_only` flag is set: skip any fix not classified as zero-risk (currently all fixes qualify)
4. Return `(new_source, fix_count)` where `fix_count` is the number of substitutions applied

---

### UNIT-97 — `unified_diff(original: str, fixed: str, filepath: str) → str`

**Purpose:** Module-level function. Returns unified diff string comparing original and fixed source.

**Algorithm:** Call `difflib.unified_diff()` between `original` and `fixed` strings; use `filepath` as the filename label in the diff header; return the combined diff string.

---

### UNIT-98 — `run_wizard(output_path=None, prompt_fn=input, print_fn=print, overwrite=False) → int`

**Purpose:** Interactive Q&A wizard that prompts the user for project preferences, writes `.cstylecheck.yml` directly, and returns 0 on success or 1 on abort.

**Algorithm:**
1. Present a short series of prompts (project name, preferred naming style, which rule categories to enable)
2. Build a YAML-serialisable config dict based on user answers
3. Write the config to `output_path` (default `.cstylecheck.yml`); if the file exists and `overwrite` is False → return 1 (abort)
4. Return 0 on success

---

### UNIT-99 — `run_preset(preset_name: str, output_path: str | None = None, print_fn=print, overwrite: bool = False) → int`

**Purpose:** Write a pre-built config file for the named preset without running the wizard; returns 0 on success or 1 on error.

**Algorithm:**
1. Look up `preset_name` (`barr-c`, `minimal`, or `misra`) from the built-in `PRESETS` dict
2. If `output_path` exists and `overwrite` is false → emit error via `print_fn`; return 1
3. Write YAML to `output_path` (default `.cstylecheck.yml`); return 0

---

### UNIT-100 — `resolve_per_dir_config(filepath: str, root_cfg: dict, cache: dict) → dict`

**Purpose:** Walk upward from `filepath`'s directory looking for `.cstylecheck.yml` files and return a deep-merged config for that file.

**Algorithm:**
1. Check `cache[dir]`; if found return cached result
2. Walk upward from `os.dirname(filepath)`; for each directory check for `.cstylecheck.yml`
3. If found: load and collect; stop if `root: true` is present; continue otherwise
4. Deep-merge collected configs (nearest wins) on top of `root_cfg`
5. Store in `cache[dir]` and return merged result

---

### UNIT-101 — `_violations_to_html(violations: list, files_checked: int) → str`

**Purpose:** Serialise violations to a self-contained HTML report string with inline CSS.

**Algorithm:**
1. Compute counts: errors, warnings, info, total, files checked
2. Render summary cards (one per count)
3. Group violations by file; render a per-file `<table>` with line, column, severity, rule, message columns
4. Wrap in a full HTML document with embedded CSS; return the document string

---

### UNIT-102 — `Checker._check_function_length() → None`

**Purpose:** Enforce a maximum function body line count (`misc.function_length`, issue #221).

**Algorithm:**
1. Skip if `misc.function_length.enabled` is false
2. Call `_iter_function_bodies()` to yield `(fn_def_pos, fn_name, body_start, body_end)`
3. For each function body: split lines between `body_start` and `body_end`
4. If `count_comments: false`, exclude blank and comment-only lines before counting
5. If line count exceeds `max_lines`, emit `misc.function_length` at the function definition line

---

### UNIT-103 — `Checker._check_function_doc_header() → None`

**Purpose:** Require a Doxygen block comment before each non-static function (`misc.function_doc_header`, issue #222).

**Algorithm:**
1. Skip if `misc.function_doc_header.enabled` is false
2. For each function definition found via `RE_FUNCTION_DEF`: scan backwards for a block comment
3. Verify comment contains `@brief` (or `\brief`)
4. If `require_param: true`: verify each parameter has a corresponding `@param` tag
5. If `require_return: true` and return type is not `void`: verify `@return` tag is present
6. Emit `misc.function_doc_header` on any missing element

---

### UNIT-104 — `Checker._check_assert_density() → None`

**Purpose:** Enforce minimum `assert()` calls per function (`misc.assert_density`, issue #225).

**Algorithm:**
1. Skip if `misc.assert_density.enabled` is false
2. Call `_iter_function_bodies()` to yield function bodies
3. For each body: count lines; if below `min_function_lines`, skip
4. Check function name against `exempt_functions` regex patterns; skip if matched
5. Count `assert(` occurrences in body
6. If count < `min_asserts`, emit `misc.assert_density`

---

### UNIT-105 — `Checker._check_null_statement_comment() → None`

**Purpose:** Require a comment alongside null statements (`misc.null_statement_comment`, issue #227).

**Algorithm:**
1. Skip if `misc.null_statement_comment.enabled` is false
2. Scan `self.clean` for control-flow keywords immediately followed by `;` using a regex that handles one level of nested parentheses; emit violation for each match
3. Scan `self.source.splitlines()` for standalone `;` on its own line; emit violation if no comment present

---

### UNIT-106 — `Checker._check_declaration_spacing() → None`

**Purpose:** Enforce a blank line between declarations and first executable statement (`misc.declaration_spacing`, issue #224).

**Algorithm:**
1. Skip if `misc.declaration_spacing.enabled` is false
2. Call `_iter_function_bodies()` to yield function bodies
3. Within each body: identify trailing declaration lines (lines starting with a type keyword or typedef)
4. Verify the line immediately following the declaration block is blank; emit `misc.declaration_spacing` if not

---

### UNIT-107 — `Checker._check_file_length() → None`

**Purpose:** Enforce a maximum source-file line count (`misc.file_length`, issue #232).

**Algorithm:**
1. Skip if `misc.file_length.enabled` is false
2. Split `self.source` into lines
3. If `count_blank_lines: false`, exclude blank lines
4. If `count_comment_lines: false`, exclude comment-only lines
5. If remaining count > `max_lines`, emit `misc.file_length` at line 1

---

### UNIT-108 — `Checker._check_reserved_header_name() → None`

**Purpose:** Flag files and `#include` directives using standard C/POSIX header names (`misc.reserved_header_name`, issue #230).

**Algorithm:**
1. Skip if `misc.reserved_header_name.enabled` is false
2. Check `os.path.basename(self.filename)` against `_STANDARD_C_HEADERS`; emit violation at line 1 if matched
3. Scan `self.source` for `#include "..."` directives; check the included name against `_STANDARD_C_HEADERS`; emit violation at the directive line if matched

---

### UNIT-109 — `Checker._check_macro_trailing_semicolon() → None`

**Purpose:** Detect `#define` macros ending with `;` (`macro.trailing_semicolon`, issue #228).

**Algorithm:**
1. Skip if `macros.trailing_semicolon.enabled` is false
2. Iterate source lines; collect multi-line macros (continuation `\`)
3. Strip string literals, character literals, and comments from the assembled body
4. If the resulting body text ends with `;`, emit `macro.trailing_semicolon`

---

### UNIT-110 — `Checker._check_macro_multistatement_wrapper() → None`

**Purpose:** Enforce `do { ... } while (0)` for multi-statement macros (`macro.multistatement_wrapper`, issue #229).

**Algorithm:**
1. Skip if `macros.multistatement_wrapper.enabled` is false
2. Collect function-like macros; assemble multi-line bodies
3. Count `;` statement terminators in the body (excluding trailing `;` already caught by UNIT-109)
4. If count > 1 and the body is not a `do { ... } while (0)` block, emit `macro.multistatement_wrapper`

---

### UNIT-111 — `Checker._check_identifier_length() → None`

**Purpose:** Uniform min/max identifier length across all categories (`naming.identifier_length`, issue #223).

**Algorithm:**
1. Skip if `naming.identifier_length.enabled` is false
2. For each declared identifier found by the declaration scanner: check length against `[min_length, max_length]`
3. Skip names matching any pattern in `exempt_patterns`
4. Emit `naming.identifier_length` for out-of-range names

---

### UNIT-112 — `Checker._check_no_single_char_identifiers() → None`

**Purpose:** Flag single-character variable names not in the exempt list (`naming.no_single_char_identifiers`, issue #231).

**Algorithm:**
1. Skip if `naming.no_single_char_identifiers.enabled` is false
2. For each declared identifier with `len(name) == 1`: check against `exempt` list
3. Emit `naming.no_single_char_identifiers` for non-exempt single-character names

---

### UNIT-90 — `Checker._check_whitespace_ratio() → None`

**Purpose:** Enforce a minimum ratio of blank lines to code lines (issue #143), measuring code "airiness".

**Algorithm:**
1. Skip if `misc.whitespace_ratio.enabled` is false
2. Identify and exclude the file header region (leading comment/blank lines before first code line)
3. Classify remaining lines as blank, comment-only, or code; exclude comment-only lines from both counts
4. Skip if `code_lines < min_lines` (configurable minimum)
5. Compute `ratio = blank_lines / code_lines`
6. Emit `misc.whitespace_ratio` violation if ratio is below the error or warning threshold

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
| `misc.comment_ratio.enabled` | `bool` | `false` | Enforce minimum comment-to-code ratio |
| `misc.comment_ratio.warning_threshold` | `float` | `0.15` | Ratio below which a warning is emitted |
| `misc.comment_ratio.error_threshold` | `float` | `0.05` | Ratio below which an error is emitted |
| `misc.whitespace_ratio.enabled` | `bool` | `false` | Enforce minimum blank-line-to-code-line ratio |
| `misc.whitespace_ratio.warning_threshold` | `float` | `0.10` | Ratio below which a warning is emitted |
| `misc.whitespace_ratio.error_threshold` | `float` | `0.02` | Ratio below which an error is emitted |
| `misc.whitespace_ratio.min_lines` | `int` | `10` | Minimum code lines before ratio is enforced |
| `misc.lowercase_l_suffix.enabled` | `bool` | `true` | Detect `l` suffix on integer literals (MISRA 7.3) |
| `misc.octal_constant.enabled` | `bool` | `true` | Detect octal constants (MISRA 7.1) |
| `misc.trigraph.enabled` | `bool` | `true` | Detect trigraph sequences (MISRA 4.2) |
| `misc.declared_not_defined.enabled` | `bool` | `false` | Cross-file declared-but-not-defined check |
| `sign_compatibility.enabled` | `bool` | `true` | Cross-file sign-compatibility check |
| `sign_compatibility.plain_char_is_signed` | `bool` | `true` | Treat plain `char` as signed |
| `spell_check.enabled` | `bool` | `false` | Enable comment spell-check |

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
| SWE1-005 to SWE1-006 | exclusions | UNIT-07, UNIT-08 |
| SWE1-007 to SWE1-010 | Dictionary management | UNIT-11, UNIT-12, UNIT-13, UNIT-50 |
| SWE1-011 to SWE1-016 | Source parsing | UNIT-14, UNIT-15, UNIT-16, UNIT-17, UNIT-18, UNIT-19, UNIT-20, UNIT-56 |
| SWE1-017 to SWE1-029 | Variable rules | UNIT-23, UNIT-43, UNIT-44, UNIT-45, UNIT-53, UNIT-54, UNIT-55 |
| SWE1-030 to SWE1-034 | Function rules | UNIT-24, UNIT-64 |
| SWE1-035 to SWE1-039 | Constant/macro rules | UNIT-25 |
| SWE1-040 to SWE1-042 | Type rules | UNIT-26, UNIT-27, UNIT-28 |
| SWE1-043 to SWE1-044 | Include guard rules | UNIT-29 |
| SWE1-045 to SWE1-050, SWE1-071 | Miscellaneous rules | UNIT-30, UNIT-31, UNIT-65, UNIT-66, UNIT-67, UNIT-68, UNIT-90 |
| SWE1-051 to SWE1-053 | Cross-file sign check | UNIT-34, UNIT-73, UNIT-74, UNIT-75, UNIT-76, UNIT-77, UNIT-78, UNIT-79, UNIT-80, UNIT-81, UNIT-82, UNIT-83 |
| SWE1-054 to SWE1-056 | Reserved names / spell | UNIT-32, UNIT-33, UNIT-51, UNIT-69, UNIT-70 |
| SWE1-057 | Text output | UNIT-41 |
| SWE1-058 to SWE1-059 | JSON output | UNIT-38 |
| SWE1-060 | SARIF output | UNIT-39 |
| SWE1-061 | GitHub annotations | UNIT-42, UNIT-89 |
| SWE1-063 | Summary | UNIT-40 |
| SWE1-064 | Copyright header check | UNIT-52, UNIT-63 |
| SWE1-065 to SWE1-067 | Baseline | UNIT-35, UNIT-36, UNIT-37 |
| SWE1-068 to SWE1-070 | CLI / entry point | UNIT-01, UNIT-02, UNIT-03, UNIT-04, UNIT-46, UNIT-87, UNIT-88 |
| SWE1-072 to SWE1-073 | Inline suppression comments | UNIT-95 |
| SWE1-074 | Auto-fix mode | UNIT-96, UNIT-97 |
| SWE1-075 | Config wizard and presets | UNIT-98, UNIT-99 |
| SWE1-076 | Per-directory config | UNIT-100 |
| SWE1-077 | HTML report output | UNIT-101 |
| SWE1-078 | Function length | UNIT-102 |
| SWE1-079 | Function doc header | UNIT-103 |
| SWE1-080 | Assert density | UNIT-104 |
| SWE1-081 | Null statement comment | UNIT-105 |
| SWE1-082 | Declaration spacing | UNIT-106 |
| SWE1-083 | File length | UNIT-107 |
| SWE1-084 | Reserved header name | UNIT-108 |
| SWE1-085 | Macro trailing semicolon | UNIT-109 |
| SWE1-086 | Macro multistatement wrapper | UNIT-110 |
| SWE1-087 | Identifier length | UNIT-111 |
| SWE1-088 | No single-char identifiers | UNIT-112 |

> **Note (UNIT-84):** `DeclaredNotDefinedChecker` (UNIT-84) is traced via the cross-file check requirement (SWE1-051 to SWE1-053 range). SWE1-071 maps exclusively to `_check_whitespace_ratio` (UNIT-90) as shown in the `SWE1-045 to SWE1-050, SWE1-071` row above; the duplicate mapping of SWE1-071 → UNIT-84 has been removed as a CSC-AUD-005 corrective action.

---

## 9. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | Approved | 2026-05-28 |
| Technical Reviewer | Dermot Murphy | Pending | — |
| Quality Assurance | Dermot Murphy | Pending | — |
| Approver | Dermot Murphy | Pending | — |

> **Note:** This document is under configuration management (SUP.8). Post-approval changes require a change request (SUP.10) and a new document version.
