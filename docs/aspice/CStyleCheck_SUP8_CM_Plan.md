# Configuration Management Plan

*Automotive SPICE® PAM v4.0 | SUP.8 Configuration Management*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CSC-SUP8-001 | **Version** | 1.1 |
| **Project** | CStyleCheck | **Date** | 2026-04-12 |
| **Status** | Released | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | SUP.8 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | 2026-04-11 | Claude | Initial release |
| 1.1 | 2026-04-12 | Claude | Updated branching strategy to Git Flow; clarified PR/Issue terminology throughout |

---

## 3. Purpose & Scope

### 3.1 Purpose

This Configuration Management (CM) Plan defines the processes, tools, methods, and responsibilities used to identify, control, store, and audit all configuration items (CIs) produced during the development and maintenance of **CStyleCheck v1.0.0** — an embedded C naming-convention linter implementing Barr-C:2018 and MISRA-C complementary rules.

This plan satisfies the requirements of **Automotive SPICE® PAM v4.0, SUP.8 — Configuration Management**.

### 3.2 Scope

This plan applies to all configuration items produced by the CStyleCheck project, including:

- Source code and supporting scripts
- Test suite and test data
- Configuration and rule definition files
- CI/CD workflow definitions
- Packaging and container artefacts
- Project documentation (including this plan)

### 3.3 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| ASPICE PAM v4.0 | Automotive SPICE Process Assessment Model | 4.0 |
| CSC-SUP9-001 | CStyleCheck Problem Resolution Management Plan | 1.0 |
| CSC-SUP10-001 | CStyleCheck Change Request Management Plan | 1.0 |
| CSC-SWE1-001 | CStyleCheck Software Requirements Specification | 1.0 |

---

## 4. Configuration Management Objectives

The CM process for CStyleCheck shall ensure that:

1. All configuration items are uniquely identified and versioned
2. Changes to CIs are controlled, reviewed, and traceable
3. Baselines are established at defined project milestones
4. The integrity of the software and its artefacts is maintained at all times
5. All releases are reproducible from a known, auditable baseline
6. Problem reports and change requests are linked to affected CIs

---

## 5. Configuration Management Tool & Repository

### 5.1 Version Control System

| Attribute | Value |
|---|---|
| **Tool** | Git |
| **Hosting Platform** | GitHub |
| **Repository URL** | `https://github.com/dermot-murphy/CStyleCheck` |
| **Visibility** | Public |
| **Default Branch** | `main` |
| **Access Control** | GitHub repository permissions (Owner: Claude) |

### 5.2 Container Registry

| Attribute | Value |
|---|---|
| **Registry** | GitHub Container Registry (GHCR) |
| **Image Path** | `ghcr.io/<org>/cstylecheck` |
| **Secondary Registry** | Docker Hub |
| **Image Build** | Automated via `docker_publish.yml` on push to `main` or version tag |

### 5.3 Artefact Storage

| Artefact Type | Storage Location |
|---|---|
| Source code | GitHub repository (`main` branch + tags) |
| Docker images | GHCR + Docker Hub |
| Test coverage reports | GitHub Actions artefacts (retention: 30 days) |
| Release packages | GitHub Releases (pip-installable `.whl` / `.tar.gz`) |

---

## 6. Configuration Item Identification

### 6.1 Configuration Item List

All items in the following table are placed under configuration control.

| CI ID | Item | Path in Repository | Type |
|---|---|---|---|
| CI-001 | Main linter source | `src/cstylecheck.py` | Source code |
| CI-002 | Version file | `src/_version.py` | Generated / version |
| CI-003 | Production naming convention config | `src/rules.yml` | Configuration |
| CI-004 | CLI options defaults file | `src/options.txt` | Configuration |
| CI-005 | Exclusions configuration | `src/exclusions.yml` | Configuration |
| CI-006 | Project preprocessor defines | `src/defines.txt` | Configuration |
| CI-007 | Module alias map | `src/aliases.txt` | Configuration |
| CI-008 | C keyword dictionary | `src/c_keywords.txt` | Data file |
| CI-009 | C stdlib name dictionary | `src/c_stdlib_names.txt` | Data file |
| CI-010 | Spell-check dictionary | `src/c_spell_dict.txt` | Data file |
| CI-011 | Dockerfile | `Dockerfile/Dockerfile` | Build / container |
| CI-012 | Docker ignore file | `Dockerfile/.dockerignore` | Build / container |
| CI-013 | Package metadata | `pyproject.toml` | Build / packaging |
| CI-014 | pip dependencies | `requirements.txt` | Build / packaging |
| CI-015 | pre-commit hook definition | `.pre-commit-hooks.yml` | Integration |
| CI-016 | GitHub Action definition | `action.yml` | Integration |
| CI-017 | Test suite (all test files) | `tests/test_*.py` | Test |
| CI-018 | Test naming convention config | `tests/rules.yml` | Test configuration |
| CI-019 | Test harness | `tests/harness.py` | Test |
| CI-020 | Test keyword dictionary | `tests/c_keywords.txt` | Test data |
| CI-021 | Test stdlib dictionary | `tests/c_stdlib_names.txt` | Test data |
| CI-022 | Test spell dictionary | `tests/c_spell_dict.txt` | Test data |
| CI-023 | CI — test workflow | `.github/workflows/cstylecheck_tests.yml` | CI/CD |
| CI-024 | CI — naming convention workflow | `.github/workflows/rules.yml` | CI/CD |
| CI-025 | CI — Docker publish workflow | `.github/workflows/docker_publish.yml` | CI/CD |
| CI-026 | Project README | `README.md` | Documentation |
| CI-027 | This CM Plan | `CStyleCheck_SUP8_CM_Plan.md` | Documentation |

### 6.2 Identification Scheme

- **Source files** are identified by file path within the repository and Git commit SHA
- **Releases** are identified by semantic version tag in the format `vMAJOR.MINOR.PATCH` (e.g., `v1.0.0`)
- **Docker images** are tagged using the scheme:
  - On version tag `v1.2.3`: `:1.2.3`, `:1.2`, `:1`, `:latest`
  - On branch push: `:main`, `:sha-<short>`
- **CI artefacts** (coverage reports) are identified by workflow run ID and Python version matrix entry
- **Documents** use the ID scheme `CSC-<PROCESS>-<NNN>` (e.g., `CSC-SUP8-001`)

---

## 7. Branching Strategy

CStyleCheck uses the **Git Flow** branching model. The following branches are defined and maintained under configuration control.

### 7.1 Permanent Branches

| Branch | Purpose | Protection Rules |
|---|---|---|
| `main` | Production-ready code only; reflects the latest release baseline | Direct push prohibited; merged from `release/*` or `hotfix/*` only; every merge creates a version tag |
| `develop` | Integration branch for completed features; always buildable | Direct push restricted; merged from `feature/*` and `bugfix/*` via pull request; CI must pass |

### 7.2 Supporting Branches

| Branch Pattern | Created From | Merges Into | Purpose |
|---|---|---|---|
| `feature/<issue-id>-<short-description>` | `develop` | `develop` | New feature or enhancement; one branch per GitHub Issue |
| `bugfix/<issue-id>-<short-description>` | `develop` | `develop` | Non-critical bug fix targeting the next release |
| `release/<version>` | `develop` | `main` and `develop` | Release preparation; version bump, final testing, and docs only — no new features |
| `hotfix/<issue-id>-<short-description>` | `main` | `main` and `develop` | Critical production defect requiring immediate patch release |

### 7.3 Branch Naming Convention

Supporting branches shall be named using the following scheme:

- `feature/42-add-misra-rule-15` — feature branch for GitHub Issue #42
- `bugfix/67-fix-typedef-false-positive` — bug fix for GitHub Issue #67
- `release/1.1.0` — release preparation for version 1.1.0
- `hotfix/89-null-pointer-crash` — hotfix for critical Issue #89

### 7.4 Git Flow Lifecycle

```
develop ──────────────────────────────────────────────────►
         ↑   ↑                   ↑
         │   └── feature/* ──────┘
         │
release/* branch ──► main ──► tag v1.0.0
                  └──────────► develop (back-merge)

main ──► hotfix/* ──► main ──► tag v1.0.1
                   └────────► develop (back-merge)
```

### 7.5 CI Enforcement

- All merges to `develop` and `main` require CI (`cstylecheck_tests.yml`) to pass
- The `rules.yml` workflow runs the linter against the project's own source on every commit touching C files, enforcing self-hosting of the tool's own rules
- Supporting branches are deleted after merge

> **📋 Note:** The `release/*` branch is the only branch where version-bump commits (`_version.py`, `pyproject.toml`) and release notes updates are permitted outside of `develop`. No new features may be introduced on a `release/*` branch.

---

## 8. Baseline Management

### 8.1 Baseline Types

| Baseline Type | Trigger | Git Mechanism | Contents |
|---|---|---|---|
| **Development Baseline** | Successful CI run on `main` | Commit SHA on `main` | Latest passing source + tests |
| **Release Baseline** | Manual decision to release | Annotated Git tag `v*.*.*` | Full repository snapshot at that commit |
| **Container Baseline** | Docker publish workflow | GHCR image digest + tag | Immutable Docker image layer set |

### 8.2 Release Baseline Procedure

1. A `release/<version>` branch is created from `develop`; all CI checks pass (unit tests across Python 3.10 / 3.11 / 3.12, naming convention check, Docker build)
2. `_version.py` reflects the intended release version (generated via `git describe --tags`)
3. The `release/<version>` branch is merged into `main` and back-merged into `develop`
4. An annotated tag is created on `main`: `git tag -a v1.0.0 -m "Release v1.0.0"`
5. Tag is pushed: `git push origin v1.0.0`
6. `docker_publish.yml` automatically builds and pushes the tagged image to GHCR and Docker Hub
7. A GitHub Release entry is created with release notes derived from the change log
8. The `release/<version>` branch is deleted

### 8.3 Baseline Integrity

- Git SHA is the primary integrity mechanism for source baselines
- Docker image digest (SHA-256) provides integrity verification for container baselines
- The `build-and-push` job prints the image digest to the Actions log as an audit record
- Layer caching uses a dedicated `:buildcache` tag in GHCR to speed incremental builds without affecting release tags

---

## 9. Change Control

Changes to controlled configuration items shall follow the change control process defined in **CSC-SUP10-001 (Change Request Management Plan)**. In summary:

1. A change request (CR) or problem resolution record is raised as a **GitHub Issue**, labelled appropriately (`bug`, `enhancement`, `change-request`)
2. The Issue is linked in all related branch names and commit messages (e.g., `Closes #42`)
3. The change is implemented on the appropriate Git Flow branch (`feature/*`, `bugfix/*`, or `hotfix/*`) per §7
4. A pull request is opened targeting `develop` (or `main` for hotfixes); CI must pass and at least one review approval is required before merge
5. The merged commit SHA is recorded in the GitHub Issue closure comment
6. If the change affects a release, a `release/*` branch is created and a new version tag applied per §8.2

> **Note:** This document is under configuration management (SUP.8). Post-approval changes require a change request (SUP.10) and a new document version.

---

## 10. Configuration Status Accounting

### 10.1 Status Tracking

| Mechanism | What It Tracks |
|---|---|
| GitHub commit history | Full chronological record of all changes to every CI |
| GitHub Issues | Problem resolution records and change requests, linked to commits and pull requests |
| GitHub Pull Requests | Review record, CI pass/fail, approvals, merge commit, and linked Issue closure |
| GitHub Actions run log | CI execution evidence per commit; coverage artefact per run |
| GitHub Releases | Named release baselines with artefact links |
| GHCR image tags | Container release history with immutable digests |

### 10.2 Reporting

Configuration status shall be accessible at any time via:

- `git log --oneline` — commit history
- `git tag -l` — all release baselines
- GitHub Releases page — named releases with notes
- GHCR package page — container image history and digests

---

## 11. Configuration Audits

### 11.1 Functional Configuration Audit (FCA)

Performed prior to each release baseline to verify:

- [ ] All CI-001 to CI-027 items are present and committed
- [ ] Version in `_version.py` (CI-002) matches the intended tag
- [ ] All unit tests pass on Python 3.10, 3.11, 3.12
- [ ] Naming convention workflow passes on current source
- [ ] Docker image builds without error
- [ ] `pyproject.toml` version (CI-013) matches `_version.py`
- [ ] `README.md` is up to date with the release

### 11.2 Physical Configuration Audit (PCA)

Performed after tagging to verify:

- [ ] Git tag points to the correct commit
- [ ] Docker image digest is recorded in the GitHub Actions run log
- [ ] GitHub Release entry references the correct tag and digest
- [ ] No uncommitted changes exist on `main` at the point of tagging

### 11.3 Audit Schedule

| Audit Type | Frequency |
|---|---|
| Functional Configuration Audit | Before every release |
| Physical Configuration Audit | After every release tag |
| Informal CM Review | Monthly, or on any SUP.10 change request affecting CIs |

---

## 12. Roles & Responsibilities

| Role | Responsibility |
|---|---|
| **CM Manager** (Claude) | Owns this plan; approves baselines; creates release tags; manages GHCR |
| **Developer** | Creates Git Flow branches; raises GitHub Issues; opens pull requests; links commits and PRs to Issues |
| **Reviewer** | Dermot Murphy |
| **CI System** (GitHub Actions) | Automated enforcement: runs tests, linting, Docker build on every push/PR |

---

## 13. Backup & Recovery

| Item | Mechanism | Recovery |
|---|---|---|
| Source repository | GitHub hosted (distributed Git — every clone is a backup) | Re-clone from GitHub or any developer's local copy |
| Docker images | GHCR + Docker Hub (dual registry) | Pull from either registry by tag or digest |
| CI artefacts | GitHub Actions artefacts (30-day retention) | Re-run the workflow from the same commit SHA to regenerate |

> **📋 Note:** Because Git is a distributed VCS, every developer's local clone constitutes an independent backup of all commits and tags up to their last `fetch`. The primary risk is loss of GitHub-hosted Issues and pull request history; this is mitigated by GitHub's platform reliability and the requirement to reference Issue numbers in all commit messages and branch names.

---

## 14. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | Approved | 2026-04-15 |
| Technical Reviewer | Dermot Murphy | Approved | 2026-04-15 |
| Quality Assurance | Dermot Murphy | Approved | 2026-04-15 |
| Approver | Dermot Murphy | Approved | 2026-04-15 |

> **Note:** This document is under configuration management (SUP.8). Post-approval changes require a change request (SUP.10) and a new document version.
