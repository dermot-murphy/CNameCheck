# CStyleCheck

Embedded C Style Compliance Checker for GitHub Actions, pre-commit hooks, and Docker.
Implements **Barr-C:2018** and MISRA-C complementary rules across **72 rule IDs**.

[![Tests](https://github.com/dermot-murphy/CStyleCheck/actions/workflows/cstylecheck_tests.yml/badge.svg)](https://github.com/dermot-murphy/CStyleCheck/actions/workflows/cstylecheck_tests.yml)
[![Docker](https://github.com/dermot-murphy/CStyleCheck/actions/workflows/docker_publish.yml/badge.svg)](https://github.com/dermot-murphy/CStyleCheck/actions/workflows/docker_publish.yml)

📖 **[Full documentation and source](https://github.com/dermot-murphy/CStyleCheck)**

---

## Quick start

```bash
# Mount your project at /repo and scan all C/H files
docker run --rm \
  -v "$(pwd):/repo" \
  dermot-murphy/cstylecheck:latest \
  --config /app/rules.yml \
  /repo/source/**/*.c /repo/source/**/*.h
```

Use `--include` for reliable glob expansion inside the container:

```bash
docker run --rm \
  -v "$(pwd):/repo" \
  dermot-murphy/cstylecheck:latest \
  --config /app/rules.yml \
  --include "/repo/source/**/*.c" \
  --include "/repo/source/**/*.h"
```

**Windows CMD:**

```cmd
docker run --rm -v "C:/MyProject:/repo" dermot-murphy/cstylecheck:latest ^
  --config /app/rules.yml ^
  --include "/repo/source/**/*.c" --include "/repo/source/**/*.h"
```

---

## GitHub Actions

```yaml
# .github/workflows/cstylecheck.yml
- uses: dermot-murphy/CStyleCheck@v1
  with:
    config: src/rules.yml
    include: |
      source/**/*.c
      source/**/*.h
    fail-on: error
    sarif-file: results/cstylecheck.sarif

- name: Upload to GitHub Code Scanning
  uses: github/codeql-action/upload-sarif@v3
  if: always()
  with:
    sarif_file: results/cstylecheck.sarif
```

---

## pre-commit

```yaml
# .pre-commit-config.yml
repos:
  - repo: https://github.com/dermot-murphy/CStyleCheck
    rev: v1.5.0
    hooks:
      - id: cstylecheck
        args:
          - --config
          - rules.yml
```

---

## Key CLI flags

| Flag | Purpose |
|---|---|
| `--config FILE` | YAML rule config (default: `rules.yml`) |
| `--include GLOB` | Source glob to scan (repeatable) |
| `--exclude GLOB` | Path/directory to exclude (repeatable) |
| `--output-format FORMAT` | `text` (default), `json`, `sarif`, or `html` |
| `--summary` | Print per-file violation summary table |
| `--github-actions` | Emit `::error`/`::warning` annotations |
| `--warnings-as-errors` | Promote all warnings to errors |
| `--baseline-file FILE` | Suppress violations in saved baseline |
| `--write-baseline FILE` | Write current violations as baseline |
| `--fix` | Auto-fix safe mechanical violations in-place |
| `--dry-run` | With `--fix`: show diff without writing |
| `--per-dir-config` | Walk upward for `.cstylecheck.yml` overrides |
| `--init` | Interactive config wizard |
| `--preset PRESET` | Pre-built config (`barr-c`, `minimal`, `misra`) |
| `--verbose` | Print file being scanned |
| `--exit-zero` | Always exit 0 (warning-only CI steps) |

**Exit codes:** `0` clean · `1` errors found · `2` config/invocation error.

---

## Rule categories (72 rule IDs)

| Category | Rule IDs |
|---|---|
| Constants / macros | `constant.case` `constant.min_length` `constant.max_length` `constant.prefix` `macro.case` `macro.min_length` `macro.max_length` `macro.prefix` `macro.trailing_semicolon` `macro.multistatement_wrapper` |
| Variables | `variable.global.case` `variable.global.prefix` `variable.global.g_prefix` `variable.static.case` `variable.static.prefix` `variable.static.s_prefix` `variable.local.case` `variable.parameter.case` `variable.parameter.p_prefix` `variable.min_length` `variable.max_length` `variable.pointer_prefix` `variable.pp_prefix` `variable.bool_prefix` `variable.handle_prefix` `variable.no_numeric_in_name` `variable.prefix_order` |
| Functions | `function.prefix` `function.style` `function.min_length` `function.max_length` `function.static_prefix` |
| Types | `typedef.case` `typedef.suffix` `enum.type_case` `enum.type_suffix` `enum.member_case` `enum.member_prefix` `struct.tag_case` `struct.tag_suffix` `struct.member_case` |
| Include guards | `include_guard.missing` `include_guard.format` |
| Naming | `naming.identifier_length` `naming.no_single_char_identifiers` |
| Misc | `misc.copyright_header` `misc.eof_comment` `misc.line_length` `misc.indentation` `misc.magic_number` `misc.unsigned_suffix` `misc.lowercase_l_suffix` `misc.yoda_condition` `misc.block_comment_spacing` `misc.comment_ratio` `misc.whitespace_ratio` `misc.declared_not_defined` `misc.function_length` `misc.function_doc_header` `misc.assert_density` `misc.null_statement_comment` `misc.declaration_spacing` `misc.file_length` `misc.reserved_header_name` `misc.non_ascii_source` |
| Other | `reserved_name` `spell_check` `sign_compatibility` |

---

## Inline suppression

```c
uint32_t g_counter = 42;  // cstylecheck: disable=variable.global.g_prefix

// cstylecheck: disable-next-line=misc.magic_number
uint8_t mask = 0xA5;

// cstylecheck: disable=misc.unsigned_suffix
uint32_t raw_a = 1;
uint32_t raw_b = 2;
// cstylecheck: enable=misc.unsigned_suffix
```

---

## Baseline suppression (legacy codebases)

```bash
# Record all existing violations once
python src/cstylecheck.py --write-baseline .cstylecheck-baseline.json \
    --include "source/**"

# CI now only fails on NEW violations
python src/cstylecheck.py --baseline-file .cstylecheck-baseline.json \
    --include "source/**"
```

---

## Output formats

### JSON
```bash
docker run --rm -v "$(pwd):/repo" dermot-murphy/cstylecheck:latest \
  --output-format json --include "/repo/source/**" \
  | python -c "import sys,json; d=json.load(sys.stdin); print(d['summary'])"
```

### SARIF (GitHub Code Scanning)
```bash
docker run --rm -v "$(pwd):/repo" dermot-murphy/cstylecheck:latest \
  --output-format sarif --include "/repo/source/**" \
  --log /repo/results.sarif
```

### HTML report
```bash
docker run --rm -v "$(pwd):/repo" dermot-murphy/cstylecheck:latest \
  --output-format html --include "/repo/source/**" \
  --log /repo/report.html
```

---

## Image tags

| Tag | Description |
|---|---|
| `latest` | Latest `main` branch build |
| `1.5.0` / `1.5` / `1` | Specific semantic version |
| `sha-<short>` | Exact commit SHA |

Images are available for `linux/amd64` and `linux/arm64`.

---

## Dictionary files (runtime override)

The image ships default dictionaries at `/app/`. Override at runtime:

```bash
docker run --rm -v "$(pwd):/repo" dermot-murphy/cstylecheck:latest \
  --keywords-file /repo/my_keywords.txt \
  --stdlib-file   /repo/my_stdlib.txt   \
  --spell-dict    /repo/my_words.txt    \
  /repo/source/**/*.c
```

---

## Links

- **Source / full docs**: https://github.com/dermot-murphy/CStyleCheck
- **Rules reference**: https://github.com/dermot-murphy/CStyleCheck/blob/main/Rules-and-Configuration.md
- **GHCR image**: `ghcr.io/dermot-murphy/cstylecheck`
- **Issues / contributions**: https://github.com/dermot-murphy/CStyleCheck/issues
