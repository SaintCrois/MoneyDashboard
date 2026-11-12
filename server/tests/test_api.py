"""API tests for Sprint 1 companies and industries endpoints.

Tests call the FastAPI TestClient against the configured database using unique
test data that is cleaned up after each test. No destructive operations are
performed against the development database.
"""

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.company import Company
from app.models.industry import Industry

client = TestClient(app)


def _db():
    return SessionLocal()


def _seed_industry(name="TESTAPI Industry"):
    db = _db()
    industry = Industry(name=name, description="API test industry")
    db.add(industry)
    db.commit()
    db.refresh(industry)
    industry_id = industry.id
    db.close()
    return industry_id


def _cleanup_industry(name):
    db = _db()
    db.query(Industry).filter(Industry.name == name).delete()
    db.commit()
    db.close()


def _seed_company(ticker="TESTAPI1", name="API Test Company", industry_id=None):
    db = _db()
    company = Company(
        ticker=ticker, name=name, exchange="SET", industry_id=industry_id
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    company_id = company.id
    db.close()
    return company_id


def _cleanup_company(ticker):
    db = _db()
    db.query(Company).filter(Company.ticker == ticker).delete()
    db.commit()
    db.close()


def test_health_endpoint():
    """GET /health returns status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_companies():
    """GET /api/companies returns companies including seeded records."""
    industry_id = _seed_industry("TESTAPI Industries")
    company_id = _seed_company("TESTAPI1", "API Test Company One", industry_id)
    try:
        response = client.get("/api/companies")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(c["ticker"] == "TESTAPI1" for c in data)
        matched = next(c for c in data if c["ticker"] == "TESTAPI1")
        assert matched["name"] == "API Test Company One"
        assert matched["exchange"] == "SET"
        assert matched["industry_name"] == "TESTAPI Industries"
    finally:
        _cleanup_company("TESTAPI1")
        _cleanup_industry("TESTAPI Industries")


def test_get_companies_industry_filter():
    """GET /api/companies supports an optional industry filter."""
    energy_id = _seed_industry("TESTAPI Energy")
    tourism_id = _seed_industry("TESTAPI Tourism")
    _seed_company("TESTAPIF1", "Filter Energy Co", energy_id)
    _seed_company("TESTAPIF2", "Filter Tourism Co", tourism_id)
    try:
        response = client.get(f"/api/companies?industry_id={energy_id}")
        assert response.status_code == 200
        data = response.json()
        assert all(c["industry_id"] == energy_id for c in data)
        assert len(data) >= 1
    finally:
        _cleanup_company("TESTAPIF1")
        _cleanup_company("TESTAPIF2")
        _cleanup_industry("TESTAPI Energy")
        _cleanup_industry("TESTAPI Tourism")


def test_get_company_by_id():
    """GET /api/companies/{company_id} returns a single company."""
    company_id = _seed_company("TESTAPI2", "API Test Company Two")
    try:
        response = client.get(f"/api/companies/{company_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == company_id
        assert data["ticker"] == "TESTAPI2"
    finally:
        _cleanup_company("TESTAPI2")


def test_get_company_not_found():
    """GET /api/companies/{company_id} returns 404 for a missing company."""
    response = client.get("/api/companies/999999")
    assert response.status_code == 404


def test_create_company():
    """POST /api/companies creates and returns a company."""
    payload = {
        "ticker": "TESTAPI3",
        "name": "API Created Company",
        "exchange": "SET",
        "industry_id": None,
        "description": "Created via API",
    }
    try:
        response = client.post("/api/companies", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["ticker"] == "TESTAPI3"
        assert data["name"] == "API Created Company"
        assert data["id"] is not None
    finally:
        _cleanup_company("TESTAPI3")


def test_create_company_duplicate_ticker():
    """POST /api/companies rejects a duplicate ticker with 400."""
    _seed_company("TESTAPIDUP", "Duplicate Target")
    try:
        payload = {
            "ticker": "TESTAPIDUP",
            "name": "Duplicate Attempt",
            "exchange": "SET",
        }
        response = client.post("/api/companies", json=payload)
        assert response.status_code == 400
    finally:
        _cleanup_company("TESTAPIDUP")


def test_create_company_missing_required_field():
    """POST /api/companies rejects a request missing required fields."""
    payload = {"name": "No Ticker"}
    response = client.post("/api/companies", json=payload)
    assert response.status_code in (400, 422)


def test_get_industries():
    """GET /api/industries returns all industries including seeded records."""
    industry_id = _seed_industry("TESTAPI Industries Listed")
    try:
        response = client.get("/api/industries")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(i["name"] == "TESTAPI Industries Listed" for i in data)
    finally:
        _cleanup_industry("TESTAPI Industries Listed")


def test_create_industry():
    """POST /api/industries creates and returns an industry."""
    payload = {"name": "TESTAPI Created Industry", "description": "Created via API"}
    try:
        response = client.post("/api/industries", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "TESTAPI Created Industry"
        assert data["id"] is not None
    finally:
        _cleanup_industry("TESTAPI Created Industry")


def test_create_industry_duplicate_name():
    """POST /api/industries rejects a duplicate industry name with 400."""
    _seed_industry("TESTAPIDUPIND")
    try:
        payload = {"name": "TESTAPIDUPIND"}
        response = client.post("/api/industries", json=payload)
        assert response.status_code == 400
    finally:
        _cleanup_industry("TESTAPIDUPIND")


def test_create_industry_missing_name():
    """POST /api/industries rejects a request missing the required name."""
    response = client.post("/api/industries", json={"description": "No name"})
    assert response.status_code in (400, 422)
