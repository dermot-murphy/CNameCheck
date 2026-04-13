# Software Test Case Specification

*Automotive SPICE® PAM v4.0 Compliant | CL2 Ready | SWE.4 · SWE.5 · SWE.6*

---

## 1. Document Identification & Control

| Field | Value | Field | Value |
|---|---|---|---|
| **Document ID** | \<TC-[ProjectID]-[ModuleID]-[NNN]\> | **Version** | \<1.0\> |
| **Project** | \<Project Name\> | **Date** | \<YYYY-MM-DD\> |
| **Test Level** | \<Unit / Integration / Qualification\> | **Status** | \<Draft / In Review / Approved\> |
| **Author** | \<Author Name\> | **Reviewer** | \<Reviewer Name\> |
| **Related SWE Process** | \<SWE.4 / SWE.5 / SWE.6\> | **Approver** | \<Approver Name\> |

---

## 2. Revision History

| Version | Date | Author | Description of Change |
|---|---|---|---|
| 1.0 | \<YYYY-MM-DD\> | \<Author\> | Initial release |
| | | | |

> **📋 Note:** All revisions must be baselined in the project Configuration Management system (SUP.8). Version numbers must be consistent with the CM baseline label.

---

## 3. Scope & Referenced Documents

| Field | Value |
|---|---|
| **Test Scope** | \<Define what is within scope: which software units, components, interfaces, or system functions are covered by this test specification\> |
| **Exclusions** | \<What is explicitly out of scope and why\> |
| **SW Requirements Spec** | \<Document ID, Version — SWE.1 output (upstream traceability)\> |
| **SW Architecture** | \<Document ID, Version — SWE.2 output\> |
| **SW Detailed Design** | \<Document ID, Version — SWE.3 / SDD output\> |
| **Test Strategy / Plan** | \<Document ID, Version — defines verification approach\> |
| **Applicable Standards** | \<Automotive SPICE PAM v4.0; ISO 26262 (if applicable); MISRA C:2012; [OEM-specific standards]\> |

---

## 4. Verification Criteria (PA 2.1 / SWE.4 BP1)

The following criteria define the pass/fail conditions and structural coverage goals that apply across all test cases in this specification. These must be reviewed and approved before test execution begins.

| Criterion | Target / Threshold | Measurement Method | Acceptance Condition |
|---|---|---|---|
| \<Code coverage\> | \<MC/DC >= 85%\> | \<Coverage tool output\> | \<Pass if >= threshold\> |
| \<Statement coverage\> | \<100% for safety\> | \<Static analysis report\> | \<No uncovered statements\> |
| \<MISRA compliance\> | \<Zero mandatory violations\> | \<MISRA checker\> | \<Zero findings\> |
| \<Execution time\> | \<<X ms worst case\> | \<Profiler\> | \<Within budget\> |

> **📋 Note:** Structural coverage (statement, branch, MC/DC) shall be measured using an approved coverage tool and results shall be recorded in the project test report (SUP.1 objective evidence).

---

## 5. Traceability Matrix (Bidirectional — SWE.x BP / PA 2.2)

Each test case must be traceable to at least one software requirement (upstream) and one design element (downstream). Gaps in traceability indicate missing test coverage and must be resolved before test approval.

| Test Case ID | Requirement ID | Design Element ID | Test Type | Coverage Rationale |
|---|---|---|---|---|
| TC-XXX-001 | \<SWE.1-REQ-001\> | \<SDD-FUNC-001\> | \<Functional\> | \<Normal path\> |
| TC-XXX-002 | \<SWE.1-REQ-002\> | \<SDD-FUNC-002\> | \<Boundary\> | \<Limit check\> |
| TC-XXX-003 | \<SWE.1-REQ-003\> | \<SDD-ERR-001\> | \<Error/Exception\> | \<Invalid input\> |

> **⚠️ Important:** Traceability shall be maintained in the project ALM/requirements management tool and kept consistent with this document. Any change to requirements or design that affects this table must trigger a change request (SUP.10).

---

## 6. Test Environment & Configuration

| Field | Value |
|---|---|
| **Target Hardware** | \<ECU board designation, PCB revision, FPGA version if applicable\> |
| **Operating System / RTOS** | \<OS name and version; kernel configuration\> |
| **Compiler / Toolchain** | \<Compiler name, version, optimization flags — must match production build\> |
| **Test Framework** | \<Unit test framework (e.g., Unity, GoogleTest); integration test harness\> |
| **Coverage Tool** | \<Tool name and version; coverage measurement configuration\> |
| **Simulation / HIL** | \<If hardware unavailable: simulator or HIL rig description and configuration ID\> |
| **Environment Baseline ID** | \<CM baseline label for test environment configuration — traceable via SUP.8\> |

> **📋 Note:** The test environment configuration shall be baselined under configuration management (SUP.8) prior to test execution. Any deviations from the above must be recorded as observations.

---

## 7. Test Cases

Complete one block per test case. Copy and extend the block below for additional test cases. Each test case must have a unique ID, at least one requirement reference, and clearly defined pass/fail criteria.

---

### Test Case: TC-XXX-001

#### Identification & Objectives

| Field | Value |
|---|---|
| **Test Case Name** | \<Brief descriptive name of what is being tested\> |
| **Test Objective** | \<Describe what requirement / behaviour this test case verifies\> |
| **Requirement Reference(s)** | \<SWE.1-REQ-XXX, SWE.2-ARCH-XXX — traceability upstream\> |
| **Design Reference(s)** | \<SDD-FUNC-XXX, SDD-INTF-XXX — traceability to SWE.3 design\> |
| **Test Type** | \<Functional \| Boundary \| Error/Exception \| Performance \| Interface \| Regression\> |
| **Test Method** | \<Dynamic execution \| Static analysis \| Code review \| Structural coverage\> |
| **Pre-conditions** | \<Initial software state, hardware configuration, test environment setup required before execution\> |
| **Post-conditions** | \<Expected system state after test; cleanup steps if applicable\> |
| **Test Environment** | \<Target HW (e.g., ECU-123 Rev B), OS, compiler version, simulator if applicable\> |
| **Test Data / Inputs** | \<Specific input values, signal values, data files, or parameter sets\> |
| **Pass Criteria** | \<Quantitative and unambiguous acceptance condition — what constitutes PASS\> |
| **Fail Criteria** | \<What constitutes FAIL; deviation reference if applicable\> |

#### Test Steps

| Step # | Action / Stimulus | Input Data / State | Expected Result |
|---|---|---|---|
| 1 | \<Apply input signal / call function / set state\> | \<Value = X; State = Y\> | \<Output == Z; Flag set; No error\> |
| 2 | \<Verify secondary effect or timing\> | \<Elapsed time\> | \<Response within T ms\> |
| 3 | \<Apply boundary value\> | \<Value = MAX\> | \<Saturated output; no overflow\> |
| 4 | \<Apply invalid / out-of-range input\> | \<Value = MAX+1\> | \<Error code returned; safe state\> |

#### Execution Record

| Execution Date | Tester | SW Version | HW Config | Result | Deviation Ref |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |

#### Observations / Deviation Notes

\<Record any deviations, unexpected behaviour, or test environment anomalies observed during execution. Reference associated problem report (SUP.9) or change request (SUP.10) IDs.\>

---

### Test Case: TC-XXX-002

*Copy this block for each additional test case. Increment the TC ID and fill in all fields.*

#### Identification & Objectives

| Field | Value |
|---|---|
| **Test Case Name** | \<Brief descriptive name of what is being tested\> |
| **Test Objective** | \<Describe what requirement / behaviour this test case verifies\> |
| **Requirement Reference(s)** | \<SWE.1-REQ-XXX, SWE.2-ARCH-XXX — traceability upstream\> |
| **Design Reference(s)** | \<SDD-FUNC-XXX, SDD-INTF-XXX — traceability to SWE.3 design\> |
| **Test Type** | \<Functional \| Boundary \| Error/Exception \| Performance \| Interface \| Regression\> |
| **Test Method** | \<Dynamic execution \| Static analysis \| Code review \| Structural coverage\> |
| **Pre-conditions** | \<Initial software state, hardware configuration, test environment setup required before execution\> |
| **Post-conditions** | \<Expected system state after test; cleanup steps if applicable\> |
| **Test Environment** | \<Target HW (e.g., ECU-123 Rev B), OS, compiler version, simulator if applicable\> |
| **Test Data / Inputs** | \<Specific input values, signal values, data files, or parameter sets\> |
| **Pass Criteria** | \<Quantitative and unambiguous acceptance condition — what constitutes PASS\> |
| **Fail Criteria** | \<What constitutes FAIL; deviation reference if applicable\> |

#### Test Steps

| Step # | Action / Stimulus | Input Data / State | Expected Result |
|---|---|---|---|
| 1 | \<Apply input signal / call function / set state\> | \<Value = X; State = Y\> | \<Output == Z; Flag set; No error\> |
| 2 | \<Verify secondary effect or timing\> | \<Elapsed time\> | \<Response within T ms\> |
| 3 | \<Apply boundary value\> | \<Value = MAX\> | \<Saturated output; no overflow\> |
| 4 | \<Apply invalid / out-of-range input\> | \<Value = MAX+1\> | \<Error code returned; safe state\> |

#### Execution Record

| Execution Date | Tester | SW Version | HW Config | Result | Deviation Ref |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |

#### Observations / Deviation Notes

\<Record any deviations, unexpected behaviour, or test environment anomalies observed during execution. Reference associated problem report (SUP.9) or change request (SUP.10) IDs.\>

---

## 8. ASPICE CL2 Compliance Reference Matrix

This table maps each field and section of this template to the relevant Automotive SPICE PAM v4.0 Base Practice (BP) or Generic Practice (GP). Use this during internal audits and assessor interviews to demonstrate CL2 compliance.

| ASPICE BP / GP | Requirement | Evidence in this Template |
|---|---|---|
| SWE.4 BP1 | Develop unit verification criteria | Pass/Fail Criteria field; Verification Criteria table (Section 4) |
| SWE.4 BP2 | Perform static verification | Test Method field (static analysis / MISRA) |
| SWE.4 BP3 | Perform dynamic verification of software units | Test Steps table; Execution Record |
| SWE.5 BP1 | Develop integration test specification | Traceability table; architecture design references |
| SWE.6 BP1 | Develop qualification test specification | Requirement references; Pass Criteria |
| SWE.x BP (Trace) | Bidirectional traceability | Requirement Reference + Design Reference + TC ID fields |
| PA 2.1 GP2.1.1 | Define process performance objectives | Test Objective; Pass/Fail Criteria fields |
| PA 2.2 GP2.2.1 | Define requirements for work products | Header block; Document ID; Version fields |
| PA 2.2 GP2.2.2 | Store and control work products | Version under CM baseline; Document Status field |
| PA 2.2 GP2.2.3 | Review and adjust work products | Reviewer / Approver fields; Revision History table |
| SUP.8 | Configuration management | Document ID; SW Version in Execution Record |
| SUP.9 / SUP.10 | Problem & change management | Deviation Ref field in Execution Record |

> **📋 Note:** Refer to Automotive SPICE PAM v4.0, Annex B for full work product characteristics. This template satisfies WP 13-12 (Test Specification) and WP 13-13 (Test Results) characteristics as defined in the PAM.

---

## 9. Review & Approval

| Role | Name | Signature / Electronic Approval | Date |
|---|---|---|---|
| Author | | | |
| Technical Reviewer | | | |
| Quality Assurance | | | |
| Approver | | | |

> **⚠️ Important:** This document requires formal review and approval before test execution may commence. Approved documents must be placed under configuration management baseline (SUP.8). Any post-approval changes must follow the change request process (SUP.10).
