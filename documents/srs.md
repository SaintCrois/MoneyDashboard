# Software Requirements Specification (SRS)

## AI Investment Impact Radar

**Project:** AI Investment Impact Radar  
**Project Type:** AI-Powered Financial Technology Platform  
**Version:** 1.0  
**Status:** Initial Draft

---

## 1. Introduction

### 1.1 Purpose

This document defines the functional and non-functional requirements of AI Investment Impact Radar.

The system is designed to monitor real-world events, analyze their potential effects on industries and publicly listed companies, evaluate company financial health, and examine stock market activity.

This document serves as the foundation for system development, implementation, and testing.

### 1.2 Project Overview

AI Investment Impact Radar is an AI-powered investment research platform that connects global and local events with financial and market information.

Unlike traditional financial news platforms that primarily provide news summaries, the system aims to explain how external events may influence industries, business operations, company financial performance, and investment risks.

The initial MVP focuses on Thai publicly listed companies and selected industries.

### 1.3 Objectives

1. Monitor relevant global and local news and economic events.
2. Identify industries and publicly listed companies potentially affected by detected events.
3. Analyze company financial health using financial indicators.
4. Examine stock market activity and investor participation.
5. Generate transparent, evidence-based investment impact assessments.
6. Present findings through an interactive dashboard.

### 1.4 Intended Users

| User | Description |
|---|---|
| Investors | Individuals who want to understand potential risks affecting companies and industries. |
| Securities Analysts | Professionals who research companies, financial performance, and market developments. |
| General Users | Users interested in understanding the relationship between real-world events and financial markets. |

### 1.5 Definitions

| Term | Definition |
|---|---|
| Event | A real-world occurrence that may influence economic or business activities. |
| Impact Mapping | Connecting events to potentially affected industries and companies. |
| Financial Health | The financial condition of a company based on financial indicators. |
| Market Activity | Observable stock price, trading volume, and investor activity. |
| Risk Assessment | An evaluation of potential business and financial risks. |
| LLM | Large Language Model used for natural language processing and AI analysis. |
| MVP | Minimum Viable Product. |

---

## 2. Overall Description

### 2.1 Product Perspective

The system consists of five major components:

1. Data Collection Layer
2. Data Processing Layer
3. AI Analysis Engine
4. Risk Assessment Engine
5. User Interface

These components work together to transform external information into understandable investment research insights.

### 2.2 Product Functions

The system is expected to provide:

- News and global event monitoring.
- Event classification and summarization.
- Industry and company impact mapping.
- Company financial health analysis.
- Stock market activity analysis.
- AI-generated investment impact assessments.
- Interactive investment dashboard.
- Supporting evidence and original source references.

### 2.3 Operating Environment

| Component | Technology |
|---|---|
| Frontend | Python / Streamlit |
| Backend | Python / FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Data Processing | Pandas |
| AI Analysis | LLM API |
| Containerization | Docker |
| Version Control | Git / GitHub |

### 2.4 Constraints

- The initial MVP focuses on Thai publicly listed companies.
- The initial implementation should prioritize one or two selected industries.
- Financial and market data availability depends on external data providers.
- AI-generated assessments may contain uncertainty and must be supported by evidence.
- The system must not guarantee stock performance or investment returns.
- External API availability may affect data collection and analysis.

### 2.5 Assumptions and Dependencies

- External news sources or APIs provide relevant news information.
- Financial data providers provide company financial information.
- Market data providers provide stock prices and trading information.
- An LLM API will be available for AI-powered analysis when integrated.
- Users have access to an internet connection.

---

## 3. Scope

### 3.1 Included Scope

The initial MVP includes:

1. News and global event monitoring.
2. Event classification and summarization.
3. Industry and company impact mapping.
4. Financial health analysis.
5. Stock market activity analysis.
6. AI investment impact assessment.
7. Interactive dashboard.

### 3.2 Excluded Scope

The initial MVP does not include:

- Automatic stock trading.
- Guaranteed stock price predictions.
- Automatic investment decisions.
- Direct brokerage integration.
- Comprehensive coverage of every global stock market.
- Advanced personalized portfolio optimization.

These features may be considered for future development.

---

## 4. Functional Requirements

### FR-01: News and Event Collection

**Description:** The system shall collect relevant news and real-world event information from available external sources.

**Requirements:**
- FR-01.1: The system shall retrieve news articles from supported sources.
- FR-01.2: The system shall store article titles, descriptions, publication dates, and source links when available.
- FR-01.3: The system shall support different event categories, including geopolitical, economic, environmental, regulatory, and industry events.
- FR-01.4: The system should identify duplicate articles covering the same event.
- FR-01.5: The system shall preserve original source references.

### FR-02: Event Classification and Summarization

**Description:** The system shall process collected news and identify important event information.

**Requirements:**
- FR-02.1: The system shall generate summaries of collected news.
- FR-02.2: The system shall classify events into relevant categories.
- FR-02.3: The system shall identify relevant locations, commodities, industries, and entities when possible.
- FR-02.4: The system shall identify potential economic implications.
- FR-02.5: The system shall distinguish extracted facts from AI-generated interpretations.

### FR-03: Industry and Company Impact Mapping

**Description:** The system shall identify industries and publicly listed companies potentially affected by detected events.

**Requirements:**
- FR-03.1: The system shall identify potentially affected industries.
- FR-03.2: The system shall map relevant companies to their industries.
- FR-03.3: The system shall identify possible direct and indirect business exposure.
- FR-03.4: The system shall explain the cause-and-effect relationship between an event and a company.
- FR-03.5: The system shall classify potential impact as Positive, Negative, Mixed, or Uncertain.

### FR-04: Financial Health Analysis

**Description:** The system shall evaluate the financial condition of affected companies.

**Requirements:**
- FR-04.1: The system shall analyze revenue growth.
- FR-04.2: The system shall analyze net profit margin.
- FR-04.3: The system shall analyze operating margin.
- FR-04.4: The system shall analyze debt-to-equity ratio.
- FR-04.5: The system shall analyze current ratio.
- FR-04.6: The system shall analyze free cash flow.
- FR-04.7: The system shall analyze return on equity (ROE).
- FR-04.8: The system should support historical financial comparisons.
- FR-04.9: The system should identify potential financial vulnerabilities.

### FR-05: Market Activity Analysis

**Description:** The system shall examine available stock market information for potentially affected companies.

**Requirements:**
- FR-05.1: The system shall display available stock price information.
- FR-05.2: The system shall analyze trading volume.
- FR-05.3: The system should identify unusual trading volume relative to historical averages.
- FR-05.4: The system should display foreign investor net buying or selling when data is available.
- FR-05.5: The system should display institutional investor net buying or selling when data is available.
- FR-05.6: The system should examine stock price volatility.
- FR-05.7: The system shall distinguish actual market observations from AI-generated interpretations.

### FR-06: AI Investment Impact Assessment

**Description:** The system shall combine event information, company exposure, financial health, and market activity to generate an investment impact assessment.

**Requirements:**
- FR-06.1: The system shall generate a potential risk classification of Low, Medium, or High.
- FR-06.2: The system shall identify potential positive, negative, or mixed impacts.
- FR-06.3: The system shall identify relevant risk factors.
- FR-06.4: The system shall identify financial vulnerabilities.
- FR-06.5: The system shall provide supporting evidence and source references.
- FR-06.6: The system shall communicate confidence levels and uncertainty.
- FR-06.7: The system should present alternative scenarios when relevant.
- FR-06.8: The system shall provide an explanation for its assessment.

### FR-07: Investment Dashboard

**Description:** The system shall present investment impact information through an interactive dashboard.

**Requirements:**
- FR-07.1: The dashboard shall display relevant detected events.
- FR-07.2: The dashboard shall display affected industries.
- FR-07.3: The dashboard shall display potentially affected listed companies.
- FR-07.4: The dashboard shall display risk classifications.
- FR-07.5: The dashboard shall display financial health indicators.
- FR-07.6: The dashboard shall display available market activity information.
- FR-07.7: The dashboard shall provide access to supporting news sources.
- FR-07.8: The dashboard shall display AI-generated explanations.

### FR-08: Event Monitoring and Assessment Updates

**Description:** The system should support monitoring developments related to previously detected events.

**Requirements:**
- FR-08.1: The system should identify newly collected information related to existing events.
- FR-08.2: The system should support updating event assessments when new evidence becomes available.
- FR-08.3: The system should preserve assessment timestamps.
- FR-08.4: The system may notify users when significant developments change an assessment.

---

## 5. Non-Functional Requirements

### NFR-01: Performance

- The dashboard should load within a reasonable time under normal operating conditions.
- Data processing should complete within a reasonable time for the MVP dataset.
- The system should avoid unnecessary repeated external API requests.

### NFR-02: Reliability

- The system should handle unavailable external data sources gracefully.
- Failed data retrieval should not corrupt previously stored information.
- The system should distinguish missing data from zero values.

### NFR-03: Security

- Database credentials and API keys shall not be exposed in source code.
- Sensitive configuration shall be stored using environment variables.
- The system should validate external and user-provided data.
- Access to system resources should be appropriately controlled.

### NFR-04: Usability

- The dashboard should present information clearly.
- Financial indicators should include understandable labels.
- Risk assessments should provide explanations rather than unexplained scores.
- Source links and data timestamps should be visible where applicable.

### NFR-05: Maintainability

- The system should use a modular architecture.
- Frontend, backend, database, and analysis logic should be separated.
- Code should be organized for future feature expansion.

### NFR-06: Data Accuracy

- Financial and market information should retain source and timestamp information.
- AI-generated claims should be linked to supporting evidence where possible.
- The system should identify incomplete or unavailable data.

### NFR-07: Responsible AI

- The system shall not guarantee investment returns.
- The system shall not present AI-generated analysis as confirmed financial facts.
- The system shall communicate uncertainty and limitations.
- The system shall support human decision-making rather than replace it.

---

## 6. Business Rules

| ID | Business Rule |
|---|---|
| BR-01 | An event may affect multiple industries. |
| BR-02 | An industry may contain multiple publicly listed companies. |
| BR-03 | A company may be exposed to multiple events. |
| BR-04 | Company impact must consider its business model and available evidence. |
| BR-05 | Financial health must be evaluated using actual financial data when available. |
| BR-06 | Market activity must be based on observable market data. |
| BR-07 | Increased trading volume does not automatically indicate buying activity. |
| BR-08 | AI-generated assessments must communicate uncertainty. |
| BR-09 | Missing financial or market data must not be treated as zero. |
| BR-10 | The system provides research assistance and does not guarantee investment outcomes. |

---

## 7. Acceptance Criteria

The initial MVP will be considered acceptable when:

1. The system can collect or load relevant news information.
2. The system can classify and summarize an event.
3. The system can identify potentially affected industries.
4. The system can map selected Thai listed companies to relevant industries.
5. The system can display available financial health indicators.
6. The system can display available stock market information.
7. The system can generate an explained investment impact assessment.
8. The assessment includes supporting evidence and uncertainty limitations.
9. The dashboard can present the complete analysis in one interface.
10. The system handles missing or unavailable data without presenting misleading results.

---

## 8. Future Enhancements

Potential future developments include:

- Portfolio-specific risk monitoring.
- Automated notifications.
- Advanced supply chain mapping.
- Historical event comparisons.
- Thai and English news support.
- Automated company research reports.
- Expanded coverage of international stock markets.

---

## 9. Document Status

This SRS describes the intended system requirements. Requirements may be refined as the MVP is developed and validated.