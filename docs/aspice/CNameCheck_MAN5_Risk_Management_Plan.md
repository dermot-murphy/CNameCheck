# Risk Management Plan

*Automotive SPICE® PAM v4.0 | MAN.5 Risk Management*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | CNC-MAN5-001 | **Version** | 1.0 |
| **Project** | CNameCheck | **Date** | 2026-04-12 |
| **Status** | Draft | **Classification** | Internal |
| **Author** | Dermot Murphy | **Reviewer** | \<Reviewer Name\> |
| **Approver** | \<Approver Name\> | **Related Process** | MAN.5 |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | 2026-04-12 | Dermot Murphy | Initial release |

---

## 3. Purpose & Scope

This Risk Management Plan defines the risk identification, analysis, treatment, and monitoring approach for **CNameCheck v1.0.0**. It satisfies **Automotive SPICE® PAM v4.0, MAN.5 — Risk Management**.

### 3.1 Referenced Documents

| Document ID | Title | Version |
|---|---|---|
| CNC-MAN3-001 | Project Management Plan | 1.0 |
| CNC-SUP8-001 | Configuration Management Plan | 1.1 |
| CNC-SUP10-001 | Change Request Management Plan | 1.0 |

---

## 4. Risk Management Strategy

### 4.1 Risk Scoring

**Likelihood:**

| Score | Label | Description |
|---|---|---|
| 1 | Rare | < 10% probability in project lifetime |
| 2 | Unlikely | 10–30% probability |
| 3 | Possible | 30–60% probability |
| 4 | Likely | 60–85% probability |
| 5 | Almost Certain | > 85% probability |

**Impact:**

| Score | Label | Description |
|---|---|---|
| 1 | Negligible | No effect on schedule, quality, or users |
| 2 | Minor | < 1 week delay; minor quality reduction |
| 3 | Moderate | 1–4 week delay; notable quality reduction |
| 4 | Major | >1 month delay or significant user impact |
| 5 | Critical | Project failure or safety/compliance breach |

**Risk Priority Number (RPN):** `Likelihood × Impact`

| RPN Range | Rating | Action Required |
|---|---|---|
| 1–4 | Low | Monitor; no immediate action |
| 5–9 | Medium | Treatment plan required |
| 10–16 | High | Immediate treatment; escalate |
| 17–25 | Critical | Stop work; escalate immediately |

### 4.2 Risk Treatment Options

| Option | Description |
|---|---|
| **Avoid** | Eliminate the source of risk |
| **Mitigate** | Reduce likelihood or impact |
| **Transfer** | Assign risk to another party |
| **Accept** | Accept risk with monitoring |

---

## 5. Risk Register

### RISK-001 — Regex False Positives / False Negatives

| Field | Value |
|---|---|
| **Risk ID** | RISK-001 |
| **Source** | Technical — regex-based parsing without full C parser |
| **Undesirable Event** | Linter incorrectly flags valid code (false positive) or misses violations (false negative) |
| **Likelihood** | 3 (Possible) |
| **Impact** | 3 (Moderate) — user trust erosion; adoption blocked |
| **RPN** | 9 (Medium) |
| **Treatment Option** | Mitigate |
| **Treatment Activities** | Comprehensive test suite (500+ tests); `test_improvements.py` regression suite for each bug fixed; `naming_convention.yml` self-hosting verification; baseline suppression feature for legacy adoption |
| **Residual Likelihood** | 2 |
| **Residual Impact** | 2 |
| **Residual RPN** | 4 (Low) |
| **Owner** | Dermot Murphy |
| **Review Date** | Per release |
| **Status** | Active — monitored via CI |

---

### RISK-002 — Python Version Incompatibility

| Field | Value |
|---|---|
| **Risk ID** | RISK-002 |
| **Source** | Technical — language version differences |
| **Undesirable Event** | Tool fails on a supported Python version (3.10, 3.11, or 3.12) due to syntax or stdlib changes |
| **Likelihood** | 2 (Unlikely) |
| **Impact** | 3 (Moderate) — users on affected version blocked |
| **RPN** | 6 (Medium) |
| **Treatment Option** | Mitigate |
| **Treatment Activities** | `cnamecheck_tests.yml` matrix tests all three versions on every commit; `pyproject.toml` specifies `requires-python = ">=3.10"` |
| **Residual Likelihood** | 1 |
| **Residual Impact** | 2 |
| **Residual RPN** | 2 (Low) |
| **Owner** | Dermot Murphy |
| **Review Date** | Per Python minor release |
| **Status** | Active — monitored via CI matrix |

---

### RISK-003 — PyYAML Security Vulnerability

| Field | Value |
|---|---|
| **Risk ID** | RISK-003 |
| **Source** | External dependency — PyYAML |
| **Undesirable Event** | A CVE is published against PyYAML affecting the `6.x` range; users exposed via `pip install` |
| **Likelihood** | 2 (Unlikely) |
| **Impact** | 3 (Moderate) — security advisory required; patched release needed |
| **RPN** | 6 (Medium) |
| **Treatment Option** | Mitigate |
| **Treatment Activities** | Pin `pyyaml>=6.0,<7.0` in `pyproject.toml`; use `yaml.safe_load()` (never `yaml.load()`); monitor PyPI security advisories |
| **Residual Likelihood** | 2 |
| **Residual Impact** | 2 |
| **Residual RPN** | 4 (Low) |
| **Owner** | Dermot Murphy |
| **Review Date** | Monthly |
| **Status** | Active |

---

### RISK-004 — GitHub Platform Dependency

| Field | Value |
|---|---|
| **Risk ID** | RISK-004 |
| **Source** | External — GitHub hosted infrastructure |
| **Undesirable Event** | GitHub Actions, GHCR, or GitHub Releases become unavailable or change pricing/API, breaking CI/CD pipeline |
| **Likelihood** | 1 (Rare) |
| **Impact** | 4 (Major) — CI, Docker builds, and release process disrupted |
| **RPN** | 4 (Low) |
| **Treatment Option** | Accept + Mitigate |
| **Treatment Activities** | Distributed Git (every developer clone is a source backup); Docker Hub as secondary registry; `docker_publish.yml` pushes to both registries simultaneously |
| **Residual Likelihood** | 1 |
| **Residual Impact** | 3 |
| **Residual RPN** | 3 (Low) |
| **Owner** | Dermot Murphy |
| **Review Date** | Quarterly |
| **Status** | Accepted |

---

### RISK-005 — Single Developer Resource Risk

| Field | Value |
|---|---|
| **Risk ID** | RISK-005 |
| **Source** | Resource — sole developer project |
| **Undesirable Event** | Developer unavailability delays release, bug fixing, or ASPICE assessment response |
| **Likelihood** | 2 (Unlikely) |
| **Impact** | 4 (Major) — schedule slip; open Issues unaddressed |
| **RPN** | 8 (Medium) |
| **Treatment Option** | Mitigate |
| **Treatment Activities** | Comprehensive documentation (README, ASPICE doc set) enables knowledge transfer; MIT licence enables community contributions; all work tracked via GitHub Issues for continuity |
| **Residual Likelihood** | 2 |
| **Residual Impact** | 3 |
| **Residual RPN** | 6 (Medium) |
| **Owner** | Dermot Murphy |
| **Review Date** | Per milestone |
| **Status** | Active |

---

### RISK-006 — Barr-C Standard Interpretation Divergence

| Field | Value |
|---|---|
| **Risk ID** | RISK-006 |
| **Source** | Technical — normative standard interpretation |
| **Undesirable Event** | CNameCheck's interpretation of a Barr-C or MISRA-C rule differs from user expectation, causing adoption friction |
| **Likelihood** | 3 (Possible) |
| **Impact** | 2 (Minor) — user confusion; support burden |
| **RPN** | 6 (Medium) |
| **Treatment Option** | Mitigate |
| **Treatment Activities** | Each rule documented in README with rationale and Barr-C section reference; all rules configurable (enable/disable/severity); `exclusions.yml` allows per-file suppression |
| **Residual Likelihood** | 2 |
| **Residual Impact** | 1 |
| **Residual RPN** | 2 (Low) |
| **Owner** | Dermot Murphy |
| **Review Date** | Per major release |
| **Status** | Active |

---

### RISK-007 — ASPICE Assessment Non-Compliance

| Field | Value |
|---|---|
| **Risk ID** | RISK-007 |
| **Source** | Process — ASPICE CL2 documentation gaps |
| **Undesirable Event** | ASPICE assessor identifies missing or insufficient work products, resulting in CL2 not achieved |
| **Likelihood** | 2 (Unlikely) |
| **Impact** | 4 (Major) — CL2 not achieved; re-assessment required |
| **RPN** | 8 (Medium) |
| **Treatment Option** | Mitigate |
| **Treatment Activities** | Full CL2 documentation set produced (SYS.2–5, SWE.1–6, MAN.3, MAN.5, SUP.1, SUP.8–10, ACQ.4, PA 2.1, PA 2.2); internal pre-assessment using ASPICE compliance matrices in each document; bidirectional traceability maintained |
| **Residual Likelihood** | 1 |
| **Residual Impact** | 3 |
| **Residual RPN** | 3 (Low) |
| **Owner** | Dermot Murphy |
| **Review Date** | Pre-assessment |
| **Status** | Active |

---

### RISK-008 — Docker Image Supply Chain Attack

| Field | Value |
|---|---|
| **Risk ID** | RISK-008 |
| **Source** | Security — container supply chain |
| **Undesirable Event** | Base Python image or dependencies compromised; malicious image published to GHCR |
| **Likelihood** | 1 (Rare) |
| **Impact** | 4 (Major) — users of Docker image impacted |
| **RPN** | 4 (Low) |
| **Treatment Option** | Mitigate |
| **Treatment Activities** | Pin base image to specific Python version (`ARG PYTHON_VERSION=3.12`); use official `python:slim` images; image digest recorded in Actions log per build; dual-registry publication makes single-registry compromise detectable |
| **Residual Likelihood** | 1 |
| **Residual Impact** | 3 |
| **Residual RPN** | 3 (Low) |
| **Owner** | Dermot Murphy |
| **Review Date** | Per Docker build |
| **Status** | Active |

---

## 6. Risk Summary

| Risk ID | Title | RPN (Initial) | RPN (Residual) | Rating | Status |
|---|---|---|---|---|---|
| RISK-001 | Regex false positives/negatives | 9 | 4 | Low | Active |
| RISK-002 | Python version incompatibility | 6 | 2 | Low | Active |
| RISK-003 | PyYAML security vulnerability | 6 | 4 | Low | Active |
| RISK-004 | GitHub platform dependency | 4 | 3 | Low | Accepted |
| RISK-005 | Single developer resource | 8 | 6 | Medium | Active |
| RISK-006 | Barr-C interpretation divergence | 6 | 2 | Low | Active |
| RISK-007 | ASPICE assessment non-compliance | 8 | 3 | Low | Active |
| RISK-008 | Docker supply chain attack | 4 | 3 | Low | Active |

> **📋 Note:** No risks currently exceed the High threshold (RPN ≥ 10) after treatment. RISK-005 (single developer) remains Medium residual and is monitored monthly.

---

## 7. Risk Monitoring Schedule

| Activity | Frequency | Owner |
|---|---|---|
| Review open GitHub Issues for new risk indicators | Weekly | Dermot Murphy |
| Check PyYAML CVE advisories | Monthly | Dermot Murphy |
| Update risk register residual scores | Per milestone | Dermot Murphy |
| Review RISK-005 (resource) | Per milestone | Dermot Murphy |
| Pre-assessment risk review | Before ASPICE assessment | Dermot Murphy |

---

## 8. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | Dermot Murphy | | 2026-04-12 |
| Technical Reviewer | \<Name\> | | |
| Quality Assurance | \<Name\> | | |
| Approver | \<Name\> | | |

> **⚠️ Important:** This document must be maintained throughout the project lifecycle. New risks must be added within 5 business days of identification. Any risk reaching High (RPN ≥ 10) residual must be escalated immediately.
