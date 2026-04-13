# Supplier Monitoring Plan

*Automotive SPICE® PAM v4.0 | ACQ.4 Supplier Monitoring*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CNC-ACQ4-001 | **Version** | 1.0 |
| **Project** | CStyleCheck | **Date** | 2026-04-12 |
| **Status** | Draft | **Classification** | Internal |
| **Author** | Claude | **Reviewer** | Dermot Murphy |
| **Approver** | Dermot Murphy | **Related Process** | ACQ.4 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | 2026-04-12 | Claude | Initial release |

---

## 3. Purpose & Scope

This Supplier Monitoring Plan defines how CStyleCheck monitors and manages its external suppliers of components, tools, and services. It satisfies **Automotive SPICE® PAM v4.0, ACQ.4 — Supplier Monitoring**.

CStyleCheck is a Python-only tool with minimal external dependencies. Its suppliers are limited to:

1. **PyPI / PyYAML** — the single runtime dependency
2. **GitHub** — version control, CI/CD, container registry, and release infrastructure
3. **Docker Hub** — secondary container registry
4. **Python Software Foundation** — Python interpreter (runtime platform)
5. **Base Docker image provider** — `python:slim` official images from Docker Hub

There are no contracted Tier-1 software suppliers or subcontractors.

### 3.1 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CNC-MAN3-001 | Project Management Plan | 1.0 |
| CNC-MAN5-001 | Risk Management Plan | 1.0 |
| CNC-SUP8-001 | Configuration Management Plan | 1.1 |
| CNC-SUP9-001 | Problem Resolution Management Plan | 1.0 |

---

## 4. Supplier Register

| SUP-ID | Supplier | Component / Service | Dependency Type | Version Constraint | Risk Reference |
|---|---|---|---|---|---|
| SUP-01 | Python Packaging Authority (PyPI) | PyYAML library | Runtime dependency | `pyyaml>=6.0,<7.0` | RISK-003 |
| SUP-02 | GitHub, Inc. | Source control, CI/CD (Actions), GHCR, Releases, Issues | Platform / Infrastructure | N/A (SaaS) | RISK-004 |
| SUP-03 | Docker, Inc. | Docker Hub (secondary registry); base image hosting | Platform / Infrastructure | N/A (SaaS) | RISK-004 |
| SUP-04 | Python Software Foundation | CPython interpreter | Runtime platform | 3.10, 3.11, 3.12 | RISK-002 |
| SUP-05 | Docker, Inc. | `python:3.12-slim` base image | Container base | Pinned via `ARG PYTHON_VERSION=3.12` | RISK-008 |

---

## 5. Supplier Monitoring Activities

### 5.1 PyYAML (SUP-01)

| Activity | Method | Frequency | Owner | Evidence |
|---|---|---|---|---|
| Security advisory monitoring | Check PyPI security advisories and GitHub advisory database for `pyyaml` | Monthly | Claude | Advisory review note in GitHub Issue (if action needed) |
| Version range review | Assess whether `pyyaml>=6.0,<7.0` remains appropriate; evaluate new major versions | Per PyYAML major release | Claude | `pyproject.toml` version constraint update CR if required |
| Availability check | Verify `pip install` succeeds in CI | Per CI run | GitHub Actions | `cnamecheck_tests.yml` — install step |

**Acceptance criteria for PyYAML:**
- `pip install pyyaml>=6.0,<7.0` succeeds without error in all CI environments
- No open critical CVEs against the installed version range
- `yaml.safe_load()` used exclusively (never `yaml.load()`)

### 5.2 GitHub (SUP-02)

| Activity | Method | Frequency | Owner | Evidence |
|---|---|---|---|---|
| CI workflow availability | Monitor `cnamecheck_tests.yml`, `naming_convention.yml`, `docker_publish.yml` job completion | Per commit | GitHub Actions status | CI badge on README; Actions run log |
| GHCR availability | Verify Docker images pullable after each push | Per `docker_publish.yml` run | GitHub Actions | `docker manifest inspect` in publish job |
| Actions runner version changes | Monitor GitHub changelog for breaking changes to `ubuntu-latest` runner | Monthly | Claude | GitHub blog / changelog review |
| API deprecation notices | Monitor GitHub Actions deprecation notices (e.g., deprecated action versions) | Monthly | Claude | GitHub announcement emails |

**Actions versions pinned:**
- `actions/checkout@v6`
- `actions/setup-python@v6`
- `actions/upload-artifact@v6`

**Acceptance criteria for GitHub:**
- All three CI workflows complete successfully on every push to `develop`/`main`
- GHCR image available and pullable within 30 minutes of `docker_publish.yml` completion

### 5.3 Docker Hub (SUP-03)

| Activity | Method | Frequency | Owner | Evidence |
|---|---|---|---|---|
| Push availability | `docker_publish.yml` pushes to Docker Hub on release tags | Per release | GitHub Actions | `docker_publish.yml` job log |
| Image pullability | Verify published image pullable via `docker pull` | Post-release | Claude | Manual verification; GitHub Release checklist |

**Acceptance criteria for Docker Hub:**
- Image push succeeds without error in `docker_publish.yml`
- Published image responds correctly to `docker run cnamecheck:latest --help`

### 5.4 Python Software Foundation (SUP-04)

| Activity | Method | Frequency | Owner | Evidence |
|---|---|---|---|---|
| Version support monitoring | Track CPython release schedule for EOL of 3.10, 3.11, 3.12 | Annually | Claude | Python EOL schedule (`devguide.python.org`) |
| New minor version evaluation | Evaluate adding new Python minor version to CI matrix | Per new Python minor release | Claude | CR raised if new version added to matrix |
| Compatibility testing | `cnamecheck_tests.yml` matrix tests all supported versions | Per commit | GitHub Actions | CI matrix result |

**Current Python version policy:** Support the three most recent minor releases. When Python 3.13 is added, Python 3.10 is dropped (raise CR).

**Acceptance criteria for CPython:**
- All tests pass on all three supported versions per CI matrix
- `pyproject.toml` `requires-python` constraint updated to reflect dropped versions

### 5.5 Base Docker Image (SUP-05)

| Activity | Method | Frequency | Owner | Evidence |
|---|---|---|---|---|
| Base image security scan | Review Docker Scout / Docker Hub security advisories for `python:3.12-slim` | Monthly | Claude | Advisory review note |
| Image digest verification | Docker digest recorded in `docker_publish.yml` build log | Per build | GitHub Actions | Actions run log |
| Base image update | Bump `ARG PYTHON_VERSION` or rebuild to get updated OS packages | Per security advisory | Claude | CR raised; new Docker image pushed |

**Acceptance criteria for base image:**
- No critical CVEs unpatched in the deployed `python:3.12-slim` layer
- Image digest recorded in GitHub Actions log for each production build

---

## 6. Supplier Interface Summary

| Interface | From | To | Data Exchanged | Protocol |
|---|---|---|---|---|
| ACQ-IF-01 | `cnamecheck.py` | PyYAML (SUP-01) | YAML config file content | Python `import yaml; yaml.safe_load()` |
| ACQ-IF-02 | `cnamecheck_tests.yml` | GitHub Actions (SUP-02) | Source code; test results; coverage report | GitHub Actions event-driven |
| ACQ-IF-03 | `docker_publish.yml` | GHCR (SUP-02) | Docker image layers | Docker push; OCI registry API |
| ACQ-IF-04 | `docker_publish.yml` | Docker Hub (SUP-03) | Docker image layers | Docker push; Docker Registry API |
| ACQ-IF-05 | Dockerfile | `python:3.12-slim` (SUP-05) | Base OS + Python runtime | Docker `FROM` directive |

---

## 7. Non-Conformance Handling

If a supplier fails to meet acceptance criteria:

| Scenario | Response |
|---|---|
| PyYAML critical CVE | Raise RISK-003 impact; evaluate upgrade or workaround; raise CR; release patch |
| GitHub Actions outage | Monitor GitHub status page; retry CI when service restored; no code change required |
| GHCR push failure | Retry via `workflow_dispatch`; users fall back to Docker Hub image |
| Python version incompatibility | Raise Issue; fix in `bugfix/` branch; update CI matrix |
| Base image CVE | Rebuild Docker image with updated base; create patch release |

All non-conformances are recorded as GitHub Issues (label: `supplier-issue`) and tracked to closure.

---

## 8. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Claude | | 2026-04-12 |
| Technical Reviewer | \<Name\> | | |
| Quality Assurance | \<Name\> | | |
| Approver | \<Name\> | | |

> **⚠️ Important:** This plan must be reviewed whenever a new external dependency is added or an existing supplier relationship materially changes. All supplier non-conformances must be logged as GitHub Issues and resolved before the affected release baseline is created.
