# Software Test Specification (STS)

## AI Investment Impact Radar

**Project:** AI Investment Impact Radar  
**Version:** 1.0  
**Status:** Initial Draft

---

## 1. Introduction

### 1.1 Purpose

This document defines the testing approach, test cases, and expected results for AI Investment Impact Radar.

The purpose is to verify that the system satisfies its functional and non-functional requirements and produces reliable, understandable, and evidence-supported investment impact assessments.

### 1.2 Testing Objectives

1. Verify news collection and event processing.
2. Verify event classification and summarization.
3. Verify industry and company impact mapping.
4. Verify financial indicator calculations.
5. Verify market activity analysis.
6. Verify AI-generated impact assessments.
7. Verify dashboard functionality.
8. Verify data accuracy and responsible AI safeguards.

### 1.3 Testing Scope

Testing covers:

- Backend API functionality.
- Database operations.
- News and event processing.
- Financial analysis.
- Market data processing.
- AI assessment generation.
- Frontend functionality.
- Error handling and data validation.

---

## 2. Testing Strategy

### 2.1 Unit Testing

Individual functions and components will be tested independently.

Examples:
- Financial ratio calculations.
- Event classification logic.
- Data validation.
- News deduplication.
- Risk classification logic.

### 2.2 Integration Testing

Integration testing will verify communication between system components.

Examples:
- FastAPI and PostgreSQL connection.
- Backend and frontend communication.
- News data processing and database storage.
- Financial analysis and risk assessment integration.
- LLM API integration when implemented.

### 2.3 System Testing

System testing will verify complete user workflows.

Examples:
- Processing a news event.
- Identifying affected companies.
- Generating a financial impact assessment.
- Displaying results on the dashboard.

### 2.4 Usability Testing

Usability testing will evaluate whether users can understand and navigate the dashboard effectively.

### 2.5 Data Validation Testing

Data validation testing will verify that financial data, market data, and external news information are handled correctly.

---

## 3. Test Environment

| Component | Testing Environment |
|---|---|
| Operating System | Windows / Linux |
| Programming Language | Python |
| Frontend | Streamlit |
| Backend | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Containerization | Docker |
| Testing Framework | Pytest |
| Version Control | Git / GitHub |

---

## 4. Test Data

The system may use the following test data:

| Data Type | Example |
|---|---|
| News Event | Middle East geopolitical escalation |
| Event Category | Geopolitical Risk |
| Affected Commodity | Crude Oil |
| Industry | Energy |
| Listed Company | PTT, PTTEP, IVL, AOT, THAI |
| Financial Data | Revenue, profit margin, debt-to-equity |
| Market Data | Stock price and trading volume |

Fictional data may be used to test expected system behavior when real data is unavailable. Fictional data must be clearly identified.

---

## 5. Test Cases

### 5.1 Database and Backend Tests

| Test ID | Requirement | Test Description | Expected Result |
|---|---|---|---|
| TEST-DB-01 | Database | Connect to PostgreSQL. | Database connection succeeds. |
| TEST-DB-02 | Database | Execute a database query. | Query returns the expected result. |
| TEST-DB-03 | Database | Attempt to retrieve a nonexistent record. | System handles missing records correctly. |
| TEST-API-01 | Backend | Send a request to the health endpoint. | API returns a successful status response. |
| TEST-API-02 | Backend | Send an invalid API request. | API returns an appropriate error response. |

### 5.2 News and Event Processing Tests

| Test ID | Requirement | Test Description | Expected Result |
|---|---|---|---|
| TEST-EVT-01 | FR-01 | Submit valid news information. | News information is accepted and stored. |
| TEST-EVT-02 | FR-01 | Submit news without a required field. | Invalid data is rejected or handled appropriately. |
| TEST-EVT-03 | FR-01 | Submit duplicate news articles. | Duplicate detection identifies matching articles where supported. |
| TEST-EVT-04 | FR-02 | Process a geopolitical news article. | Event is classified into an appropriate category. |
| TEST-EVT-05 | FR-02 | Generate an event summary. | A summary is generated from the supplied article. |
| TEST-EVT-06 | FR-02 | Process news with missing information. | Missing information is not fabricated. |

### 5.3 Industry and Company Impact Mapping Tests

| Test ID | Requirement | Test Description | Expected Result |
|---|---|---|---|
| TEST-IMP-01 | FR-03 | Process an event affecting the energy industry. | Energy is identified as a potentially affected industry. |
| TEST-IMP-02 | FR-03 | Map a company to its industry. | The company is associated with the correct industry in the available dataset. |
| TEST-IMP-03 | FR-03 | Identify multiple affected industries. | All supported relevant industries are returned. |
| TEST-IMP-04 | FR-03 | Generate an impact explanation. | The explanation provides a logical event-to-industry relationship. |
| TEST-IMP-05 | FR-03 | Evaluate an unclear company relationship. | The system identifies uncertainty rather than asserting an unsupported relationship. |

### 5.4 Financial Analysis Tests

| Test ID | Requirement | Test Description | Expected Result |
|---|---|---|---|
| TEST-FIN-01 | FR-04 | Calculate revenue growth. | The calculation matches the expected result. |
| TEST-FIN-02 | FR-04 | Calculate net profit margin. | The calculation matches the expected result. |
| TEST-FIN-03 | FR-04 | Calculate operating margin. | The calculation matches the expected result. |
| TEST-FIN-04 | FR-04 | Calculate debt-to-equity ratio. | The calculation matches the expected result. |
| TEST-FIN-05 | FR-04 | Calculate current ratio. | The calculation matches the expected result. |
| TEST-FIN-06 | FR-04 | Calculate free cash flow. | The calculation matches the defined formula and input data. |
| TEST-FIN-07 | FR-04 | Calculate ROE. | The calculation matches the expected result. |
| TEST-FIN-08 | FR-04 | Process incomplete financial data. | Missing values are identified and not treated as zero. |
| TEST-FIN-09 | FR-04 | Compare financial data across periods. | Historical values are displayed correctly. |

### 5.5 Market Activity Tests

| Test ID | Requirement | Test Description | Expected Result |
|---|---|---|---|
| TEST-MKT-01 | FR-05 | Retrieve available stock price information. | Correct price information is displayed with its timestamp. |
| TEST-MKT-02 | FR-05 | Calculate trading volume relative to historical average. | The calculated comparison is correct. |
| TEST-MKT-03 | FR-05 | Process foreign investor net flow data. | Buying and selling information is displayed correctly when available. |
| TEST-MKT-04 | FR-05 | Process institutional investor net flow data. | Buying and selling information is displayed correctly when available. |
| TEST-MKT-05 | FR-05 | Process unavailable market data. | The system identifies unavailable data. |
| TEST-MKT-06 | FR-05 | Generate an interpretation of market activity. | AI interpretation does not misrepresent observed data. |

### 5.6 AI Investment Impact Assessment Tests

| Test ID | Requirement | Test Description | Expected Result |
|---|---|---|---|
| TEST-AI-01 | FR-06 | Generate an assessment using event data. | The system produces an assessment based on available evidence. |
| TEST-AI-02 | FR-06 | Evaluate a company with strong financial health. | The assessment considers its financial resilience. |
| TEST-AI-03 | FR-06 | Evaluate a company with financial vulnerabilities. | Relevant vulnerabilities are identified. |
| TEST-AI-04 | FR-06 | Generate a risk classification. | The system returns an allowed risk category. |
| TEST-AI-05 | FR-06 | Generate an assessment with incomplete evidence. | Uncertainty and missing evidence are communicated. |
| TEST-AI-06 | FR-06 | Inspect generated supporting evidence. | Supporting sources correspond to the available input data. |
| TEST-AI-07 | FR-06 | Generate an assessment with conflicting information. | Conflicting evidence is not presented as a confirmed conclusion. |
| TEST-AI-08 | FR-06 | Generate an assessment for an event with uncertain impact. | The system communicates uncertainty. |

### 5.7 Dashboard Tests

| Test ID | Requirement | Test Description | Expected Result |
|---|---|---|---|
| TEST-UI-01 | FR-07 | Open the dashboard. | Dashboard loads successfully. |
| TEST-UI-02 | FR-07 | Display detected events. | Event information is displayed correctly. |
| TEST-UI-03 | FR-07 | Display affected companies. | Company information is displayed correctly. |
| TEST-UI-04 | FR-07 | Display financial indicators. | Financial indicators are presented correctly. |
| TEST-UI-05 | FR-07 | Display risk assessments. | Risk categories and explanations are visible. |
| TEST-UI-06 | FR-07 | Open a supporting source link. | The original source is accessible when available. |
| TEST-UI-07 | FR-07 | Display unavailable information. | Missing data is clearly identified. |

---

## 6. Non-Functional Tests

| Test ID | Requirement | Test Description | Expected Result |
|---|---|---|---|
| TEST-NFR-01 | NFR-01 | Measure dashboard loading time under normal conditions. | Loading time meets the agreed performance target. |
| TEST-NFR-02 | NFR-02 | Simulate an unavailable external data source. | The system handles the failure without crashing. |
| TEST-NFR-03 | NFR-03 | Inspect source code and repository for exposed credentials. | No private credentials are exposed. |
| TEST-NFR-04 | NFR-04 | Ask a test user to navigate the dashboard. | The user can understand the main information. |
| TEST-NFR-05 | NFR-05 | Modify an independent system component. | The change does not unnecessarily affect unrelated components. |
| TEST-NFR-06 | NFR-06 | Compare displayed financial data against test source data. | Values match the source data. |
| TEST-NFR-07 | NFR-07 | Review generated AI assessments. | The system communicates limitations and avoids guaranteed investment claims. |

---

## 7. Entry and Exit Criteria

### 7.1 Entry Criteria

Testing may begin when:

- The relevant feature has been implemented.
- Required dependencies are installed.
- The test environment is available.
- Required test data is prepared.
- The application can be executed.

### 7.2 Exit Criteria

A testing phase may be considered complete when:

- All planned test cases for that phase have been executed.
- Critical defects have been resolved.
- Test results have been recorded.
- Failed tests have been investigated.
- Relevant requirements have been verified.

---

## 8. Defect Classification

| Severity | Description |
|---|---|
| Critical | A major system function is unavailable or important data is corrupted. |
| High | An important feature produces incorrect results or cannot be used. |
| Medium | A feature has a defect but a workaround exists. |
| Low | Minor display, usability, or non-critical issues. |

---

## 9. Test Execution Results

Actual results shall be recorded after test execution.

| Test ID | Actual Result | Status | Remarks |
|---|---|---|---|
| TEST-DB-01 | Pending | Not Run | |
| TEST-API-01 | Pending | Not Run | |
| TEST-EVT-01 | Pending | Not Run | |
| TEST-IMP-01 | Pending | Not Run | |
| TEST-FIN-01 | Pending | Not Run | |
| TEST-MKT-01 | Pending | Not Run | |
| TEST-AI-01 | Pending | Not Run | |
| TEST-UI-01 | Pending | Not Run | |

**Status definitions:**
- Passed: Actual result matches expected result.
- Failed: Actual result does not match expected result.
- Blocked: Test cannot be executed due to a dependency or environment issue.
- Not Run: Test has not yet been executed.

---

## 10. Document Status

This STS defines the planned testing approach and test cases. Execution results must be updated as features are implemented and tested.