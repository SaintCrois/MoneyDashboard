# AI Investment Impact Radar

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
│   ├── app.py               # Streamlit frontend
│   ├── requirements.txt
│   └── tests/
│       └── test_app.py
├── server/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI entry point
│   │   ├── database.py      # SQLAlchemy connection & session
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── health.py    # GET /health
│   │   │   ├── companies.py # GET/POST /api/companies
│   │   │   └── industries.py# GET/POST /api/industries
│   │   ├── models/          # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── news_article.py
│   │   │   ├── event.py
│   │   │   ├── industry.py
│   │   │   ├── company.py
│   │   │   ├── event_industry.py
│   │   │   ├── event_company.py
│   │   │   ├── financial_data.py
│   │   │   ├── market_data.py
│   │   │   └── impact_assessment.py
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── company.py
│   │   │   └── industry.py
│   │   └── services/        # Business logic (future sprints)
│   ├── scripts/
│   │   ├── __init__.py
│   │   ├── init_db.py       # Create all tables (idempotent)
│   │   └── seed_data.py     # Idempotent reference data seed
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_database.py
│   │   └── test_api.py
│   └── requirements.txt
├── database/
│   └── init.sql
├── documents/
│   ├── srs.md
│   ├── sts.md
│   ├── sds.md
│   └── plan.md
├── docker-compose.yml
├── .env.example
├── .env
├── .gitignore
└── README.md
```

## Prerequisites

- Python 3.10+
- Docker Desktop (for PostgreSQL 16)
- Git

## Installation

1. Clone or open the repository:

   ```powershell
   cd C:\Users\Cent\Desktop\Hackathon
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

`.env.example` contains all required variables:

| Variable | Description | Example |
|---|---|---|
| POSTGRES_DB | PostgreSQL database name | investment_radar |
| POSTGRES_USER | PostgreSQL user | radar_user |
| POSTGRES_PASSWORD | PostgreSQL password | change_this_password |
| DATABASE_URL | SQLAlchemy database URL | postgresql://radar_user:...@localhost:5432/investment_radar |
| BACKEND_URL | FastAPI backend base URL | http://localhost:8000 |

### Security

- `.env` is ignored by Git (see `.gitignore`).
- `.venv`, `__pycache__`, and generated files are ignored by Git.
- Never commit `.env` or any secrets/credentials.

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

## Backend Startup

Start the FastAPI backend:

```powershell
uvicorn app.main:app --reload --app-dir server
```

The backend listens on `http://localhost:8000`. The existing `/health` endpoint
responds `{"status": "ok"}`, and tables are created automatically on startup.

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

## Current Sprint 1 Implementation Status

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
- [x] Automated tests: 20 backend + 8 frontend, all passing

Sprint 2+ features (news collection, event classification, financial analysis,
market analysis, AI impact assessment) are intentionally not implemented.
