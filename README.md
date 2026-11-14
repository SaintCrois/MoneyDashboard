# AI Investment Impact Radar

## Dashboard demo (no AI API required)

On Dashboard, select a company and click **ประมวลผล (Demo)**. The app loads up
to 100 recent stored news articles and ranks them locally using company/ticker,
industry, and business keyword matches. Exact normalized headline duplicates are
removed; at most eight matching articles are shown. This is a keyword shortlist,
not semantic analysis or an exhaustive search of the database.

The processing panel lists the shortlisted news, explicitly says no real AI is
used, and displays approximately two seconds of simulated progress. It then
opens a summary view with prepared, conditional impact scenarios, the matching
news, and items to verify. The back button returns to company selection. No
provider call, key, token charge, or assessment database write occurs in this
flow. An empty/unavailable news feed or no matching articles is reported without
fabricating news or results. The result snapshot stays only in Streamlit session
state; it is separate from actual assessments. News is still collected through
the existing backend on Events.

## Optional AI assessment API

The optional backend AI analysis uses the OpenAI Responses API with validated structured output.
Existing baseline endpoints remain rule-based unless `use_ai: true` is requested.

In the backend `.env`, configure:

```dotenv
AI_ENABLED=true
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=your_supported_model
```

Choose a model available to your API account that supports Responses Structured
Outputs, then restart FastAPI. No additional Python package or schema migration
is needed for this feature. Never commit the key. AI is disabled by default.

Real AI is available only through an explicit API request (see below); Dashboard
now uses the local demo journey. Each AI company/event request is potentially
billable. Saved AI results are labelled `llm_openai_v1` and can be inspected through
the API or existing Analysis assessment view.

The provider receives the selected article excerpt, company profile and stored
financial/market summaries. Requests disable provider response storage with
`store: false`. The complete input snapshot and model name are retained locally.
No real API call is made by the automated tests.

AI can examine indirect exposure without a pre-existing ticker mapping. These
interpretations do not create or overwrite evidence-based EventCompany mappings.
Missing company business descriptions (including the initial seed profiles) limit
how specifically the model can explain exposure; populate `Company.description`
and its `source` from verified business disclosures for useful segment analysis.
No financial or price data is invented to fill missing inputs. Model confidence
is subjective, not a calibrated probability. This is research assistance.

Provider timeout, refusal, invalid output, and unknown evidence references return
a clear error without saving a baseline result as AI. Check existing saved results
before retrying a client timeout.

API: `GET /api/analysis/status` returns readiness without secrets.
`POST /api/assessments/generate` accepts
`{"company_id": 1, "event_id": 2, "use_ai": true}`. AI requires one explicit
event; bulk background inference and automatic re-analysis are not enabled.

Reference: https://developers.openai.com/api/docs/guides/structured-outputs

From Global Events to Investment Insights.

An AI-powered investment research platform that monitors global and local events,
identifies potentially affected industries and publicly listed companies, analyzes
company financial health and market activity, and generates evidence-backed
investment impact assessments.

The initial MVP focuses on selected Thai publicly listed companies and one or two
industries.

## Technology Stack

- Python
- Streamlit — frontend
- FastAPI — backend
- PostgreSQL 16 — database
- SQLAlchemy — ORM
- Pandas — data processing
- Docker Compose — PostgreSQL containerization
- Pytest — automated testing
- python-dotenv — environment configuration

## Project Structure

```text
Hackathon/
├── client/
│   ├── app.py               # Streamlit frontend (Dashboard/Events/Companies/Analysis)
│   ├── requirements.txt
│   └── tests/
├── server/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── database.py      # SQLAlchemy connection & session
│   │   ├── api/             # health, companies, industries, news, events, financials, market, assessments
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   └── services/        # news ingestion/relevance, event/mapping, SET sync, financial/market/assessment
│   ├── data/
│   │   └── set_companies_template.csv  # documented SET company CSV fallback template
│   ├── scripts/
│   │   ├── init_db.py
│   │   ├── seed_data.py
│   │   ├── migrate_sprint2.py
│   │   ├── migrate_sprint3.py
│   │   └── migrate_news_matching.py
│   ├── tests/               # API, service, integration, regression tests
│   └── requirements.txt
├── database/
│   └── init.sql
├── documents/
│   ├── srs.md, sts.md, sds.md, plan.md
├── docker-compose.yml
├── .env.example
└── README.md
```

## Prerequisites

- Python 3.10+
- Docker Desktop (for PostgreSQL 16)
- Git

## Installation

1. Clone or open the repository:

   ```powershell
   cd <PROJECT_DIRECTORY>
   ```

2. Create and activate the Python virtual environment (already present at `.venv`):

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. Install backend dependencies:

   ```powershell
   pip install -r server/requirements.txt
   ```

4. Install frontend dependencies:

   ```powershell
   pip install -r client/requirements.txt
   ```

## Environment Configuration

Configuration is driven by environment variables. Copy `.env.example` to `.env`
and adjust values as needed:

```powershell
copy .env.example .env
```

`.env.example` contains required and optional variables:

| Variable | Description | Example |
|---|---|---|
| POSTGRES_DB | PostgreSQL database name | investment_radar |
| POSTGRES_USER | PostgreSQL user | radar_user |
| POSTGRES_PASSWORD | PostgreSQL password | change_this_password |
| DATABASE_URL | SQLAlchemy database URL | postgresql://radar_user:...@localhost:5432/investment_radar |
| BACKEND_URL | FastAPI backend base URL | http://localhost:8000 |
| SET_COMPANY_API_URL | (Optional) Official/authorized SET company reference API endpoint | *(unset by default)* |
| SET_COMPANY_API_KEY | (Optional) API credential for SET company API | *(unset by default)* |
| SET_COMPANY_API_KEY_HEADER | (Optional) Header name for API key (default Authorization) | Authorization |
| SET_COMPANY_CSV_PATH | (Optional) Path to documented company CSV fallback | server/data/set_companies_template.csv |
| NEWS_SOURCES_JSON | (Optional) JSON override for configured news sources | *(unset by default)* |

### Security

- `.env` is ignored by Git (see `.gitignore`).
- `.venv`, `__pycache__`, and generated files are ignored by Git.
- Never commit `.env` or any secrets/credentials.
- SET/company sync uses official/authorized APIs when configured; credentials must come from environment variables. No undocumented scraping or access bypass is implemented. If official API access is unavailable/unauthorized, a documented CSV fallback can be used.

## PostgreSQL Startup

Start the PostgreSQL 16 container with Docker Compose:

```powershell
docker compose up -d
```

This starts the `investment_radar_db` container (PostgreSQL 16), mounts a named
volume for data persistence, and applies `database/init.sql` on first init.

Verify the container is healthy:

```powershell
docker ps
```

## Database Initialization

Create all SQLAlchemy tables (idempotent, non-destructive):

```powershell
python -m server.scripts.init_db
```

Optionally seed illustrative reference data (idempotent, safe to re-run):

```powershell
python -m server.scripts.seed_data
```

The seed inserts Industries (Energy, Tourism, Petrochemicals) and Companies
(PTT, PTTEP, AOT, IVL) only. It never inserts fabricated financial or market
data.

Apply the Sprint 2 additive schema migration (idempotent, non-destructive)
to add Sprint 2 columns and constraints to an existing Sprint 1 database:

```powershell
python -m server.scripts.migrate_sprint2
```

## Backend Startup

Start the FastAPI backend:

```powershell
uvicorn app.main:app --reload --app-dir server
```

The backend listens on `http://localhost:8000`. The existing `/health` endpoint
responds `{"status": "ok"}`, and tables are created automatically on startup.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Backend health check. |
| GET | `/api/companies` | List companies (optional `industry_id` filter). |
| GET | `/api/companies/{id}` | Get a single company (404 if missing). |
| POST | `/api/companies` | Create a company (rejects duplicate ticker). |
| GET | `/api/industries` | List all industries. |
| POST | `/api/industries` | Create an industry (rejects duplicate name). |
| GET | `/api/news` | List news articles (paginated). |
| GET | `/api/news/{id}` | Get a single news article (404 if missing). |
| POST | `/api/news/ingest` | Ingest articles from configured sources. |
| GET | `/api/events` | List events (optional `category` filter). |
| GET | `/api/events/{id}` | Get a single event (404 if missing). |
| POST | `/api/events/process` | Process articles into structured events. |
| GET | `/api/events/categories` | List supported event categories. |
| GET | `/api/events/{id}/industries` | Industries potentially affected by an event. |
| GET | `/api/events/{id}/companies` | Companies potentially affected by an event. |
| GET | `/api/companies/{id}/events` | Events potentially affecting a company. |

## Frontend Startup

Start the Streamlit frontend in a separate terminal:

```powershell
streamlit run client/app.py
```

The frontend listens on `http://localhost:8501` by default and retrieves all
data through the FastAPI backend (it never connects to PostgreSQL directly).

## Test Execution

Run the backend test suite:

```powershell
python -m pytest server/tests -v
```

Run the frontend test suite:

```powershell
python -m pytest client/tests -v
```

Run all tests:

```powershell
python -m pytest server/tests client/tests -v
```

## Test Execution

Tests use a per-test rolled-back transaction, so the development database is
never modified. External news sources are mocked in automated tests.

Run the backend test suite:

```powershell
python -m pytest server/tests -v
```

Run the frontend test suite:

```powershell
python -m pytest client/tests -v
```

Run all tests:

```powershell
python -m pytest server/tests client/tests -v
```

## Current Implementation Status

Sprint 1 (Foundation and Database) is complete:

- [x] Reproducible Python development environment (`.venv`, `requirements.txt`)
- [x] PostgreSQL 16 running via Docker Compose
- [x] Environment-variable-based configuration (`.env` / `.env.example`)
- [x] `.env`, `.venv`, `__pycache__` ignored by Git
- [x] SQLAlchemy models for all 9 Sprint 1 tables with relationships, constraints, and indexes
- [x] Non-destructive database initialization (`server/scripts/init_db.py`)
- [x] Idempotent reference-data seed (`server/scripts/seed_data.py`)
- [x] FastAPI backend with `/health`, `/api/companies`, `/api/industries` endpoints
- [x] Streamlit frontend shell (Dashboard, Events, Companies, Analysis)
- [x] Frontend retrieves data through FastAPI, handles backend failures gracefully
- [x] Automated tests passing

Sprint 2 (News and Event Intelligence) is complete:

- [x] News ingestion from configurable RSS sources (`server/services/news_service.py`, `news_sources.py`)
- [x] Duplicate article prevention via unique URL constraint
- [x] Graceful source-failure handling (no crash, application keeps working)
- [x] Rule-based event extraction and classification (`server/services/event_service.py`)
- [x] Event categories: Economic, Political, Regulatory, Natural Disaster, Geopolitical, Industry Development, Corporate, Energy, Tourism, Technology
- [x] Event-to-industry and event-to-company mapping (`server/services/impact_mapping_service.py`)
- [x] Additive, non-destructive schema migration (`server/scripts/migrate_sprint2.py`)
- [x] News and events API endpoints
- [x] Streamlit Events page (articles, events, mappings, ingestion/processing buttons, filters, search)
- [x] Automated tests: 28 Sprint 1 + 36 Sprint 2 = 64 passing

Sprint 3+ features (financial analysis, market analysis, AI impact assessment,
advanced dashboard analytics) are intentionally not implemented.
