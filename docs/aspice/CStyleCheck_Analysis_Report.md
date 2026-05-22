# CStyleCheck — Repository Analysis Report

*Automotive SPICE® V4 · MISRA C · CI/CD · Code Quality | Generated 2026-04-17*

| Metric | Count |
|---|---|
| Files analysed | 87 |
| Python source lines | 3,637 |
| ASPICE work products reviewed | 18 |
| CI workflows reviewed | 3 |

## Summary Scorecard

| Severity | Count |
|---|---|
| 🔴 Critical | 6 |
| 🟡 Warning | 10 |
| 🔵 Info / Improvement | 5 |
| ✅ Well handled | 4 |

---

## 1 · CI / CD Workflows

### ✅ Action versions are correct — `@v6` is the current latest

`actions/checkout@v6` (v6.0.2, released January 2026), `actions/setup-python@v6`, and `actions/upload-artifact@v6` are all confirmed current on the GitHub Marketplace. No change required.

---

### 🟡 Warning — `actions/checkout@v6` breaking change: explicit token required

`checkout@v6` changed how authentication is handled compared to v5. Workflows using bare `uses: actions/checkout@v6` without an explicit `token:` input can fail with credential errors. The trend job already passes `token: ${{ secrets.GITHUB_TOKEN }}` correctly, but the initial checkout steps in all three workflows use the bare form.

**Fix — apply to all bare checkout steps:**

```yaml
- name: Checkout repository
  uses: actions/checkout@v6
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
```

---

### 🔴 Critical — Wrong filename in `docker_publish.yml` path trigger

Line 34 of `docker_publish.yml` watches `src/cstylecheck_rules.yaml`. The actual file is `src/rules.yml`. The Docker image will **never rebuild** when rules change, breaking the release pipeline silently.

**Fix:**

```yaml
# Before
- "src/cstylecheck_rules.yaml"

# After
- "src/rules.yml"
```

---

### 🔴 Critical — `|| true` silently swallows exit code 2 (config error)

Both the PR and push checker steps append `|| true` so the workflow never fails on a bad configuration (exit 2). A misconfigured `rules.yml` would pass CI undetected — a significant ASPICE GP 2.1.4 (monitor process) non-conformance.

**Fix:**

```bash
python src/cstylecheck.py ... ; CSC_EXIT=$?
if [ $CSC_EXIT -eq 2 ]; then exit 2; fi   # config error — hard fail
echo "csc_exit=$CSC_EXIT" >> $GITHUB_OUTPUT
```

---

### 🔴 Critical — No concurrency control: parallel runs corrupt `trend.jsonl`

If two pushes to `main` trigger simultaneously, both trend jobs will checkout `gh-pages`, append records, and force-push — one record silently lost or the branch diverges.

**Fix — add to `cstylecheck_rules.yml` and `cstylecheck_tests.yml`:**

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

---

### 🟡 Warning — `tj-actions/changed-files@v44` not pinned to a commit SHA

Third-party actions pinned only to a semver tag are a supply-chain attack vector. ASPICE SUP.8 requires all tools under configuration management with an immutable reference.

**Fix:**

```yaml
# Before
- uses: tj-actions/changed-files@v44

# After
- uses: tj-actions/changed-files@d6babd516b1d0b6a8be0e69a3ef3ed4c3737b028 # v44
```

---

### 🟡 Warning — `moby/buildkit:latest` floating tag in Docker workflow

The Buildx driver option `image=moby/buildkit:latest` pulls a floating tag, producing non-reproducible builds.

**Fix:**

```yaml
# Before
driver-opts: image=moby/buildkit:latest

# After
driver-opts: image=moby/buildkit:v0.19.0
```

---

### 🟡 Warning — `datetime.utcnow()` deprecated in Python 3.12

The trend append step uses `datetime.datetime.utcnow()` which raises `DeprecationWarning` in Python 3.12.

**Fix:**

```python
# Before
"date": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),

# After
"date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
```

---

### 🔵 Info — Extract long inline Python scripts from YAML

The `Generate trend HTML page` step is ~80 lines of Python embedded in YAML. Extract to `scripts/generate_trend.py` for testability and maintainability.

---

### 🔵 Info — Coverage gate (72%) vs. ASPICE SWE.4 target (90%) gap not formally tracked

The gap is acknowledged in a comment but no GitHub Issue is linked. Must be formally tracked per ASPICE SUP.10.

---

## 2 · ASPICE V4 Level 2 Compliance

### 🔴 Critical — AI listed as Author / Reviewer / Role-holder across all 18 work products

Every ASPICE document carries **Author: Claude**. PA2-001 GP 2.1.6 lists *"Lead Developer: Claude"* and *"Project Manager: Claude"*. ASPICE requires **human accountable persons** for all defined roles. An assessor will reject this without named individuals.

**Fix — in all documents:**

```markdown
| Author | Dermot Murphy |   ← replace "Claude" in every document

# PA2-001 GP 2.1.6 — replace all Claude role entries
| Lead Developer | <Human Name> |
```

---

### 🔴 Critical — Unresolved placeholders in released documents

Documents with status **Released** still contain unresolved template tokens:

| Document | Placeholder | ASPICE Impact |
|---|---|---|
| PA2-001 | `<Name>` — Reviewer role | GP 2.1.6 incomplete |
| MAN3-001 | `<TBD>` — milestone dates | GP 2.1.3 planning incomplete |
| SYS5-001 | 8× `<SYS-VTC-xxx>` and `<TBD>` | SYS.5 traceability incomplete |
| SWE6-001 | Unchecked pre-release checklist items | Release gate not met |

---

### 🔴 Critical — PA2-001 coverage target contradicts CI gate: formal non-conformance

PA2-001 §4.1 states SWE.4 performance objective as **≥ 90% statement, ≥ 85% branch**. The CI gate is `--cov-fail-under=72`. Direct contradiction requiring a formal waiver CR.

**Recommended approach:**

1. Raise a SUP.9 problem record for the coverage gap
2. Update PA2-001 §4.1: *"≥72% statement (interim baseline v1.0); target ≥90% tracked via Issue #nn"*
3. Raise the gate to 90% once subprocess coverage is wired up

---

### 🟡 Warning — All work products have a single revision: no evidence of document lifecycle

PA 2.2 requires evidence that work products are reviewed and adjusted over time. Every document shows only `v1.0 — 2026-04-12 — Initial release`. Even one controlled update satisfies GP 2.2.4.

---

### 🟡 Warning — No evidence of formal document review records (GP 2.2.3)

Documents list "Reviewer: Dermot Murphy" but no review minutes, sign-off sheets, or PR approval records are referenced. Link to a tagged PR or review checklist record in each document's §2.

---

### 🟡 Warning — Reviewer equals Approver: independence not demonstrated

In every document the same individual is both Reviewer and Approver. ASPICE PA 2.2 expects independent review. Designate a separate reviewer for at least SWE1, SWE4, and SWE6.

---

## 3 · MISRA C Rule Coverage

### 🟡 Warning — Tool scope mis-characterised: "MISRA-complementary" not "MISRA checker"

Only three MISRA rules are explicitly implemented, but `pyproject.toml` keywords include `misra`. Documentation must clearly state the tool provides **naming-convention and style checking that is complementary to — but not a replacement for — a MISRA static analyser**.

---

### 🟡 Warning — MISRA C:2023 Rule 4.2 promoted to Required but severity is still `warning`

**Fix in `rules.yml`:**

```yaml
  # MISRA C:2023 Rule 4.2 (Required)
  trigraphs:
-   severity: warning
+   severity: error   # Required rule — MISRA C:2023
```

---

### 🔵 Info — Add a MISRA C coverage matrix to documentation

| MISRA C:2012 Rule | Topic | CStyleCheck Support |
|---|---|---|
| Rule 7.3 | Unsigned literal suffix (U/u) | ✅ Implemented |
| Rule 7.1 | Octal constants | ✅ Implemented |
| Rule 4.2 | Trigraphs | ⚠️ Implemented — severity needs raising |
| Rule 5.x | Identifier naming/length | ✅ Partial (via naming rules) |
| Rule 2.2 | Dead code | ❌ Out of scope |
| Rule 10.x | Essential type model | ❌ Out of scope |
| Rule 14.x / 15.x | Control flow | ❌ Out of scope |
| Rule 17.x | Function usage | ❌ Out of scope |
| Rule 18.x | Pointer arithmetic | ❌ Out of scope |
| Rule 21.x | Standard library usage | ❌ Out of scope |

---

## 4 · Code Quality — cstylecheck.py

### 🟡 Warning — Single monolithic 3,637-line file

All rule-engine logic, CLI parsing, output formatting, and utilities in one file makes isolated unit testing difficult and contradicts the 46-unit decomposition in CSC-SWE3-001.

**Recommended refactor (aligns with CSC-SWE3-001):**

```
src/
  cstylecheck/
    __init__.py
    checker.py       # Checker class — rule engine
    sign_checker.py  # SignChecker class
    cli.py           # parse_args, main()
    output.py        # JSON/SARIF/text formatters, Tee
    config.py        # load_config, load_alias_file, etc.
    baseline.py      # load_baseline, write_baseline
    models.py        # Violation, CheckResult dataclasses
```

---

### 🟡 Warning — `_version.py` fallback mismatches `pyproject.toml`

Fallback is `"1.0.0.dev"` but `pyproject.toml` declares `version = "1.0.0"`.

**Fix:**

```python
try:
    from _version import __version__ as _VERSION
except ImportError:
    try:
        from importlib.metadata import version
        _VERSION = version("cstylecheck")
    except Exception:
        _VERSION = "0.0.0.dev"
```

---

### 🔵 Info — Missing type annotations on several public functions

Add `mypy --strict` to the CI test workflow as an additional SWE.4 static verification layer.

---

### 🔵 Info — No Python linting gate on the checker's own source

Add `ruff check src/ tests/` to the test workflow, consistent with the self-hosting naming-convention check already in CI.

---

## 5 · Well Handled

| # | Item |
|---|---|
| ✅ | **YAML divergence check (YAML-004)** — automated diff check preventing silent test-config drift is excellent practice |
| ✅ | **Comprehensive ASPICE document set** — full V-model coverage (SYS.2–SYS.5, SWE.1–SWE.6, MAN.3/5, SUP.1/8/9/10, ACQ.4, PA2) is a strong foundation for Level 2 assessment once authorship issues are resolved |
| ✅ | **Trend page with badge and gh-pages publishing** — practical implementation of ASPICE GP 2.1.4 process monitoring |
| ✅ | **Multi-platform Docker with layer caching and semver tagging** — correct `linux/amd64` + `linux/arm64` builds with semver tag promotion and registry cache |

---

## 6 · Prioritised Action Summary

| # | Priority | Action | File(s) | ASPICE Link |
|---|---|---|---|---|
| 1 | 🔴 Critical | Fix docker path trigger filename (`rules.yml`) | `docker_publish.yml` | SUP.8 |
| 2 | 🔴 Critical | Fix `\|\| true` — distinguish config errors (exit 2) from violations (exit 1) | `cstylecheck_rules.yml` | GP 2.1.4 |
| 3 | 🔴 Critical | Add concurrency group to prevent gh-pages race condition | `cstylecheck_rules.yml` | SUP.8 |
| 4 | 🔴 Critical | Replace AI author/role-holder with named humans in all 18 ASPICE docs | `docs/aspice/*.md` | GP 2.1.6, PA 2.2 |
| 5 | 🔴 Critical | Resolve all `<TBD>` / `<Name>` / `<SYS-VTC-xxx>` placeholders | PA2, MAN3, SYS5, SWE6 | PA 2.2 |
| 6 | 🔴 Critical | Reconcile PA2 coverage target (90%) with CI gate (72%) via formal waiver CR | PA2-001, test workflow | SWE.4, SUP.10 |
| 7 | 🟡 Warning | Add explicit `token: ${{ secrets.GITHUB_TOKEN }}` to all bare checkout steps | All 3 workflows | SUP.8 |
| 8 | 🟡 Warning | Pin `tj-actions/changed-files` to commit SHA | `cstylecheck_rules.yml` | SUP.8 |
| 9 | 🟡 Warning | Pin `moby/buildkit` to a specific version | `docker_publish.yml` | SUP.8 |
| 10 | 🟡 Warning | Replace `datetime.utcnow()` with timezone-aware call | `cstylecheck_rules.yml` | — |
| 11 | 🟡 Warning | Raise MISRA C:2023 Rule 4.2 severity to `error` in `rules.yml` | `src/rules.yml` | SWE.1 |
| 12 | 🟡 Warning | Add independent reviewer (≠ approver) to key work products | SWE1, SWE4, SWE6 | PA 2.2 |
| 13 | 🟡 Warning | Fix `_version.py` fallback — use `importlib.metadata` | `src/cstylecheck.py` | SUP.8 |
| 14 | 🔵 Info | Extract inline Python CI scripts to `scripts/` directory | `cstylecheck_rules.yml` | SWE.3 |
| 15 | 🔵 Info | Add MISRA C coverage matrix to `Rules-and-Configuration.md` | `Rules-and-Configuration.md` | SWE.1 |
| 16 | 🔵 Info | Plan `cstylecheck.py` module split per SWE.3 unit catalogue | `src/` | SWE.3 |
| 17 | 🔵 Info | Add `mypy --strict` and `ruff check` to CI test workflow | `cstylecheck_tests.yml` | SWE.4 |

---

*Report generated by analysis of `CStyleCheck-main` repository. All findings cross-referenced against CSC-SWE1-001, CSC-SWE4-001, CSC-PA2-001, CSC-SUP8-001, CSC-SUP9-001, CSC-SUP10-001.*
