# Software Design Specification (SDS)

## AI Investment Impact Radar

**Project:** AI Investment Impact Radar  
**Version:** 1.0  
**Status:** Initial Draft

---

## 1. Introduction

### 1.1 Purpose

This document describes the proposed software architecture, system components, database design, data flow, and technical implementation of AI Investment Impact Radar.

It provides a technical reference for developers during implementation and integration.

### 1.2 System Overview

AI Investment Impact Radar is an AI-powered investment research platform that connects real-world events with industry exposure, company financial information, and stock market activity.

The system processes information through several stages:

1. Collect external news and financial information.
2. Process and organize collected data.
3. Analyze events using AI and data-processing logic.
4. Map events to affected industries and companies.
5. Evaluate company financial health and market activity.
6. Generate investment impact assessments.
7. Present results through an interactive dashboard.

---

## 2. Technology Stack

| Component | Technology | Responsibility |
|---|---|---|
| Frontend | Streamlit | User interface and dashboard |
| Backend | FastAPI | API endpoints and business logic |
| Programming Language | Python | Main application development |
| Database | PostgreSQL | Persistent data storage |
| ORM | SQLAlchemy | Database interaction |
| Data Processing | Pandas | Financial and market data processing |
| AI Analysis | LLM API | News summarization and impact analysis |
| Containerization | Docker | Database environment |
| Version Control | Git / GitHub | Source code management |

The selected stack prioritizes Python because it supports the backend, financial analysis, data processing, and AI integration within one ecosystem.

---

## 3. System Architecture

### 3.1 High-Level Architecture

The system follows a layered architecture.

```text
                 USER
                   |
                   v
          STREAMLIT FRONTEND
                   |
                   v
             FASTAPI BACKEND
                   |
        +----------+----------+
        |          |          |
        v          v          v
    EVENT       FINANCIAL   MARKET
   PROCESSING    ANALYSIS   ANALYSIS
        |          |          |
        +----------+----------+
                   |
                   v
             AI ANALYSIS
                   |
                   v
          RISK ASSESSMENT
                   |
                   v
             POSTGRESQL
```

External data sources provide news, financial information, and market data to the backend processing components.

### 3.2 Architecture Components

#### A. Frontend Layer

**Technology:** Streamlit

Responsibilities:

- Display the main investment dashboard.
- Display recent events and news.
- Display affected industries and companies.
- Display financial health indicators.
- Display stock market activity.
- Display AI-generated impact assessments.
- Provide access to supporting sources.

#### B. Backend Layer

**Technology:** FastAPI

Responsibilities:

- Receive frontend requests.
- Provide API endpoints.
- Validate incoming data.
- Coordinate data processing.
- Retrieve and store database records.
- Execute financial analysis.
- Coordinate AI assessment generation.

#### C. Database Layer

**Technology:** PostgreSQL

Responsibilities:

- Store collected news and events.
- Store industry and company information.
- Store financial data.
- Store market activity data.
- Store generated impact assessments.
- Maintain relationships between records.

#### D. Data Processing Layer

**Technology:** Python / Pandas

Responsibilities:

- Clean collected data.
- Normalize financial information.
- Identify duplicate news articles.
- Calculate financial indicators.
- Process stock market information.
- Prepare structured input for AI analysis.

#### E. AI Analysis Layer

**Technology:** LLM API

Responsibilities:

- Summarize news articles.
- Classify real-world events.
- Identify potential economic implications.
- Explain industry and company exposure.
- Generate evidence-supported impact assessments.
- Communicate uncertainty and alternative scenarios.

---

## 4. Proposed Project Structure

```text
Hackathon/
│
├── client/
│   ├── app.py
│   ├── requirements.txt
│   ├── pages/
│   ├── components/
│   └── tests/
│
├── server/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── database.py
│   │   │
│   │   ├── api/
│   │   │   └── __init__.py
│   │   │
│   │   ├── models/
│   │   │   └── __init__.py
│   │   │
│   │   ├── schemas/
│   │   │   └── __init__.py
│   │   │
│   │   └── services/
│   │       └── __init__.py
│   │
│   ├── tests/
│   │   └── test_db.py
│   │
│   └── requirements.txt
│
├── database/
│   └── init.sql
│
├── docker-compose.yml
├── .env.example
├── .env
├── .gitignore
└── README.md
```

### 4.1 Directory Responsibilities

| Directory/File | Responsibility |
|---|---|
| client/app.py | Main Streamlit application. |
| client/pages/ | Dashboard pages and additional views. |
| client/components/ | Reusable frontend components. |
| server/app/main.py | FastAPI application entry point. |
| server/app/database.py | Database connection and session configuration. |
| server/app/api/ | API route definitions. |
| server/app/models/ | SQLAlchemy database models. |
| server/app/schemas/ | Request and response schemas. |
| server/app/services/ | Business logic and processing services. |
| server/tests/ | Backend test cases. |
| database/init.sql | Initial database setup. |
| docker-compose.yml | PostgreSQL container configuration. |
| .env.example | Example environment configuration. |
| .env | Local environment variables. |

---

## 5. Database Design

### 5.1 Overview

PostgreSQL will be used to store system information and maintain relationships between events, industries, companies, financial data, market information, and impact assessments.

The following tables are proposed for the initial system design.

### 5.2 Proposed Database Tables

#### Table: events

Stores detected real-world events.

| Field | Data Type | Description |
|---|---|---|
| event_id | SERIAL PRIMARY KEY | Unique event identifier. |
| title | VARCHAR(500) | Event title. |
| summary | TEXT | Event summary. |
| category | VARCHAR(100) | Event category. |
| location | VARCHAR(255) | Event location. |
| event_date | TIMESTAMP | Date of the event. |
| created_at | TIMESTAMP | Record creation timestamp. |

#### Table: news_articles

Stores collected news articles.

| Field | Data Type | Description |
|---|---|---|
| article_id | SERIAL PRIMARY KEY | Unique article identifier. |
| event_id | INTEGER FOREIGN KEY | Related event. |
| title | VARCHAR(500) | Article title. |
| description | TEXT | Article description. |
| source_name | VARCHAR(255) | News source. |
| source_url | TEXT | Original article URL. |
| published_at | TIMESTAMP | Publication date. |
| created_at | TIMESTAMP | Record creation timestamp. |

#### Table: industries

Stores industry information.

| Field | Data Type | Description |
|---|---|---|
| industry_id | SERIAL PRIMARY KEY | Unique industry identifier. |
| industry_name | VARCHAR(255) | Industry name. |
| description | TEXT | Industry description. |

#### Table: companies

Stores publicly listed company information.

| Field | Data Type | Description |
|---|---|---|
| company_id | SERIAL PRIMARY KEY | Unique company identifier. |
| ticker_symbol | VARCHAR(50) UNIQUE | Stock ticker. |
| company_name | VARCHAR(255) | Company name. |
| exchange | VARCHAR(100) | Stock exchange. |
| industry_id | INTEGER FOREIGN KEY | Related industry. |
| business_description | TEXT | Company business description. |

#### Table: event_industries

Connects events with potentially affected industries.

| Field | Data Type | Description |
|---|---|---|
| event_industry_id | SERIAL PRIMARY KEY | Unique relationship identifier. |
| event_id | INTEGER FOREIGN KEY | Related event. |
| industry_id | INTEGER FOREIGN KEY | Related industry. |
| impact_type | VARCHAR(50) | Positive, Negative, Mixed, or Uncertain. |
| explanation | TEXT | Impact explanation. |

#### Table: event_companies

Connects events with potentially affected companies.

| Field | Data Type | Description |
|---|---|---|
| event_company_id | SERIAL PRIMARY KEY | Unique relationship identifier. |
| event_id | INTEGER FOREIGN KEY | Related event. |
| company_id | INTEGER FOREIGN KEY | Related company. |
| impact_type | VARCHAR(50) | Potential impact classification. |
| exposure_type | VARCHAR(50) | Direct or indirect exposure. |
| explanation | TEXT | Company impact explanation. |

#### Table: financial_data

Stores company financial information.

| Field | Data Type | Description |
|---|---|---|
| financial_id | SERIAL PRIMARY KEY | Unique financial record identifier. |
| company_id | INTEGER FOREIGN KEY | Related company. |
| reporting_period | VARCHAR(50) | Financial reporting period. |
| revenue | NUMERIC(20,2) | Revenue. |
| net_profit | NUMERIC(20,2) | Net profit. |
| operating_profit | NUMERIC(20,2) | Operating profit. |
| total_debt | NUMERIC(20,2) | Total debt. |
| total_equity | NUMERIC(20,2) | Total equity. |
| current_assets | NUMERIC(20,2) | Current assets. |
| current_liabilities | NUMERIC(20,2) | Current liabilities. |
| operating_cash_flow | NUMERIC(20,2) | Operating cash flow. |
| capital_expenditure | NUMERIC(20,2) | Capital expenditure. |
| source_name | VARCHAR(255) | Data source. |
| recorded_at | TIMESTAMP | Record timestamp. |

#### Table: market_data

Stores stock market information.

| Field | Data Type | Description |
|---|---|---|
| market_data_id | SERIAL PRIMARY KEY | Unique market record identifier. |
| company_id | INTEGER FOREIGN KEY | Related company. |
| recorded_at | TIMESTAMP | Market data timestamp. |
| stock_price | NUMERIC(20,4) | Stock price. |
| trading_volume | BIGINT | Trading volume. |
| foreign_net_flow | NUMERIC(20,2) | Foreign investor net flow. |
| institutional_net_flow | NUMERIC(20,2) | Institutional investor net flow. |
| source_name | VARCHAR(255) | Data source. |

#### Table: impact_assessments

Stores generated investment impact assessments.

| Field | Data Type | Description |
|---|---|---|
| assessment_id | SERIAL PRIMARY KEY | Unique assessment identifier. |
| event_id | INTEGER FOREIGN KEY | Related event. |
| company_id | INTEGER FOREIGN KEY | Related company. |
| risk_level | VARCHAR(50) | Low, Medium, or High. |
| impact_type | VARCHAR(50) | Positive, Negative, Mixed, or Uncertain. |
| explanation | TEXT | Assessment explanation. |
| risk_factors | TEXT | Identified risk factors. |
| confidence_level | VARCHAR(50) | Assessment confidence. |
| created_at | TIMESTAMP | Assessment timestamp. |

### 5.3 Database Relationships

```text
INDUSTRIES
    |
    | 1:N
    v
COMPANIES
    |
    +--------------------+
    |                    |
    | 1:N                | 1:N
    v                    v
FINANCIAL_DATA       MARKET_DATA


EVENTS
    |
    +--------------------+
    |                    |
    | 1:N                | 1:N
    v                    v
NEWS_ARTICLES       EVENT_INDUSTRIES
                         |
                         | N:1
                         v
                     INDUSTRIES


EVENTS
    |
    | 1:N
    v
EVENT_COMPANIES
    |
    | N:1
    v
COMPANIES


EVENTS + COMPANIES
          |
          v
  IMPACT_ASSESSMENTS
```

The database design is proposed and may be refined during implementation.

---

## 6. API Design

### 6.1 General API Structure

The backend will expose REST API endpoints through FastAPI.

Base URL during local development:

`http://127.0.0.1:8000`

### 6.2 Proposed API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | /health | Check backend availability. |
| GET | /api/events | Retrieve collected events. |
| GET | /api/events/{event_id} | Retrieve event details. |
| POST | /api/events | Create an event record. |
| GET | /api/companies | Retrieve listed companies. |
| GET | /api/companies/{company_id} | Retrieve company details. |
| GET | /api/companies/{company_id}/financials | Retrieve company financial data. |
| GET | /api/companies/{company_id}/market | Retrieve company market data. |
| GET | /api/assessments | Retrieve investment impact assessments. |
| GET | /api/assessments/{assessment_id} | Retrieve a specific assessment. |
| POST | /api/assessments | Generate or store an assessment. |

These endpoints describe the planned API. They are not necessarily implemented yet.

---

## 7. Main System Workflows

### 7.1 News Processing Workflow

```text
External News Sources
        |
        v
  Retrieve Articles
        |
        v
  Validate and Clean Data
        |
        v
  Detect Duplicates
        |
        v
  Classify and Summarize
        |
        v
  Identify Event Details
        |
        v
  Store in PostgreSQL
```

### 7.2 Impact Mapping Workflow

```text
       Detected Event
              |
              v
     Identify Economic Effects
              |
              v
      Identify Industries
              |
              v
       Identify Companies
              |
              v
    Evaluate Business Exposure
              |
              v
      Generate Explanations
```

### 7.3 Financial Analysis Workflow

```text
      Company Information
              |
              v
      Retrieve Financial Data
              |
              v
       Validate Financial Data
              |
              v
      Calculate Financial Ratios
              |
              v
      Evaluate Financial Health
              |
              v
       Store Analysis Results
```

### 7.4 AI Impact Assessment Workflow

```text
       Event Information
              |
              v
      Company Exposure Data
              |
              v
      Financial Health Data
              |
              v
       Market Activity Data
              |
              v
        AI Analysis Engine
              |
              v
       Risk Assessment
              |
              v
     Evidence and Explanation
              |
              v
       Display on Dashboard
```

---

## 8. Financial Analysis Design

The system will calculate financial indicators using available company financial statements.

| Indicator | Formula |
|---|---|
| Revenue Growth | (Current Revenue - Previous Revenue) / Previous Revenue × 100 |
| Net Profit Margin | Net Profit / Revenue × 100 |
| Operating Margin | Operating Profit / Revenue × 100 |
| Debt-to-Equity | Total Debt / Total Equity |
| Current Ratio | Current Assets / Current Liabilities |
| Free Cash Flow | Operating Cash Flow - Capital Expenditure |
| ROE | Net Profit / Average Shareholders' Equity × 100 |

### 8.1 Calculation Rules

- Calculations must use validated input data.
- Missing values must not be silently replaced with zero.
- Division by zero must be handled appropriately.
- Reporting periods must be identified.
- Financial values must retain their source information.
- The system should communicate limitations when required data is unavailable.

---

## 9. AI Analysis Design

### 9.1 Input Information

The AI analysis engine may receive:

- Event summaries.
- Event categories.
- Affected industries.
- Company business descriptions.
- Company financial indicators.
- Market activity observations.
- Supporting news sources.

### 9.2 Output Information

The AI engine should produce:

- Potential impact classification.
- Potential risk level.
- Main risk factors.
- Financial vulnerabilities.
- Supporting evidence.
- Confidence and uncertainty information.
- Alternative scenarios when relevant.
- Explanation of the assessment.

### 9.3 Responsible AI Design

- AI-generated explanations must be distinguishable from verified source information.
- The system must not fabricate missing financial or market information.
- Assessments should reference supporting evidence.
- Uncertain relationships should be identified as uncertain.
- AI-generated assessments must not guarantee stock price movements or investment returns.
- Human verification should remain part of investment research.

---

## 10. Security Design

The system should follow these security practices:

1. Store database credentials in environment variables.
2. Keep `.env` excluded from Git.
3. Keep API keys out of source code.
4. Validate incoming API data.
5. Handle database errors without exposing sensitive configuration.
6. Use secure configuration practices when deploying the application.

---

## 11. Deployment Design

### 11.1 Local Development Environment

The development environment uses:

- Python virtual environment for dependencies.
- Docker Compose for PostgreSQL.
- FastAPI for backend services.
- Streamlit for the frontend.

### 11.2 Local Execution

Start PostgreSQL:

```powershell
docker compose up -d
```

Start FastAPI from the project root:

```powershell
uvicorn app.main:app --reload --app-dir server
```

Start Streamlit in another terminal:

```powershell
streamlit run client/app.py
```

### 11.3 Deployment Considerations

Future deployment may use:

- A hosted PostgreSQL database.
- A cloud-hosted FastAPI backend.
- A hosted Streamlit frontend.
- Environment-based production configuration.

---

## 12. Current Implementation Status

This section distinguishes the initial development foundation from planned functionality.

| Component | Current Status |
|---|---|
| Git repository | Initialized / configured for GitHub upload. |
| Python virtual environment | Created. |
| Streamlit application | Basic application shell implemented (Dashboard, Events, Companies, Analysis). |
| FastAPI application | Implemented: `/health`, `/api/companies`, `/api/industries` endpoints. |
| PostgreSQL | Running through Docker Compose (PostgreSQL 16). |
| Database connectivity | Connection test successful. |
| Database models | Implemented (9 SQLAlchemy models with relationships, constraints, indexes). |
| Database tables | Implemented via `Base.metadata.create_all` (idempotent, non-destructive). |
| API endpoints | Health, companies, industries implemented; remaining endpoints planned. |
| Database initialization | `server/scripts/init_db.py` (reusable, non-destructive). |
| Reference data seed | `server/scripts/seed_data.py` (idempotent, illustrative only). |
| Automated tests | Implemented: 20 backend + 8 frontend tests, all passing. |
| Frontend-backend communication | Verified; Streamlit retrieves data via FastAPI only. |
| News collection | Planned (Sprint 2). |
| AI analysis | Planned (Sprint 3). |
| Financial analysis | Planned (Sprint 3). |
| Market activity analysis | Planned (Sprint 3). |
| Investment dashboard | Basic shell implemented; full dashboard planned (Sprint 4). |

### Sprint 1 Implementation Notes

- **Database design:** 9 tables (`news_articles`, `events`, `industries`, `companies`,
  `event_industries`, `event_companies`, `financial_data`, `market_data`,
  `impact_assessments`) with primary keys, foreign keys, unique constraints
  (company ticker, event–industry, event–company, company–fiscal year), and
  indexes on foreign keys and ticker. Financial values use `Numeric` precision;
  timestamps are timezone-aware.
- **API structure:** FastAPI routers under `server/app/api/` (`health`,
  `companies`, `industries`), Pydantic schemas under `server/app/schemas/`,
  reusable `get_db` session dependency in `server/app/database.py`.
- **Frontend architecture:** Streamlit single-page app (`client/app.py`) with
  sidebar navigation. All data is retrieved through the FastAPI backend;
  Streamlit never connects to PostgreSQL directly. Backend failures are handled
  gracefully with user-visible messages.
- **ORM relationships:** `Industry.companies` ↔ `Company.industry`; relationship
  rows cascade on delete for event/industry/company associations.


---

## 13. Future Design Improvements

Potential future improvements include:

- More advanced event-to-company relationship mapping.
- Automated news collection and monitoring.
- Historical market comparison.
- Advanced financial risk scoring.
- Portfolio monitoring.
- Automated notifications.
- Expanded international company coverage.

---

## 14. Document Status

This SDS describes the initial proposed architecture and design of AI Investment Impact Radar. Database structures, API endpoints, and workflows may be updated as implementation progresses.