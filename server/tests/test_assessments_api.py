"""Impact assessment API tests.

Uses the isolated ``db`` and ``client`` fixtures (transaction rolled back per test).
"""

from datetime import datetime, timezone


def _setup(client, ticker="ASAPI1"):
    ind = client.post("/api/industries", json={"name": f"Ind-{ticker}", "description": "t"}).json()
    comp = client.post("/api/companies", json={
        "name": f"Company {ticker}", "ticker": ticker, "industry_id": ind["id"]
    }).json()
    # seed an article and process event so mapping exists
    # create via DB through a helper endpoint flow is hard; instead rely on event processing
    # easiest: ingest not possible without sources, so insert event mapping by generating via direct DB? no direct DB.
    # We'll create assessment generation for a specific event by first creating event via processing path:
    # create news article through DB not exposed; but we can use existing seed approach: create article by calling internals not possible.
    # Alternative: use /api/events/process is not helpful without articles. So we'll just test 404/validation and generation-without-mapped-events behavior.
    return comp


def test_generate_assessments_company_not_found(client):
    resp = client.post("/api/assessments/generate", json={"company_id": 999999})
    assert resp.status_code == 404


def test_generate_assessments_event_not_found(client):
    comp = _setup(client, ticker="AS1")
    resp = client.post("/api/assessments/generate", json={"company_id": comp["id"], "event_id": 999999})
    assert resp.status_code == 404


def test_generate_assessments_no_mapped_events_returns_empty(client):
    comp = _setup(client, ticker="AS2")
    resp = client.post("/api/assessments/generate", json={"company_id": comp["id"]})
    assert resp.status_code == 201
    assert resp.json() == []


def test_list_assessments_empty(client):
    resp = client.get("/api/assessments")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_assessment_not_found(client):
    resp = client.get("/api/assessments/999999")
    assert resp.status_code == 404


def test_company_assessments_not_found(client):
    resp = client.get("/api/companies/999999/assessments")
    assert resp.status_code == 404


def test_event_assessments_not_found(client):
    resp = client.get("/api/events/999999/assessments")
    assert resp.status_code == 404


def test_full_assessment_flow_via_db(db, client):
    """Create article/event/mapping via DB fixture, then generate assessment via API."""
    from app.models.company import Company
    from app.models.event import Event
    from app.models.event_company import EventCompany
    from app.models.industry import Industry
    from app.models.news_article import NewsArticle
    from app.models.financial_data import FinancialData
    from app.models.market_data import MarketData

    industry = Industry(name="Ind-ASFlow", description="t")
    db.add(industry)
    db.flush()
    company = Company(name="Co ASFlow", ticker="ASF", industry_id=industry.id)
    db.add(company)
    db.flush()
    article = NewsArticle(title="Flow Article", source="Test", url="https://example.com/asflow", summary="s")
    db.add(article)
    db.flush()
    event = Event(
        title="Flow Event", description="desc", category="Energy",
        source_article_id=article.id, processing_status="processed",
        event_date=datetime(2026, 11, 12, tzinfo=timezone.utc),
    )
    db.add(event)
    db.flush()
    db.add(EventCompany(event_id=event.id, company_id=company.id, impact_type="Positive",
                        relevance_score=0.8, exposure_type="Direct", explanation="Direct"))
    db.add(FinancialData(company_id=company.id, fiscal_year=2024, revenue=1000, net_profit=100,
                         total_debt=200, shareholders_equity=400, data_source="manual"))
    db.add(MarketData(company_id=company.id, recorded_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
                      close_price=100, trading_volume=1000, data_source="manual"))
    db.add(MarketData(company_id=company.id, recorded_at=datetime(2026, 11, 2, tzinfo=timezone.utc),
                      close_price=105, trading_volume=1200, data_source="manual"))
    db.flush()

    resp = client.post("/api/assessments/generate", json={"company_id": company.id})
    assert resp.status_code == 201, resp.text
    items = resp.json()
    assert len(items) == 1
    a = items[0]
    assert a["company_id"] == company.id
    assert a["event_id"] == event.id
    assert a["impact_type"] == "Positive"
    assert a["methodology"] is not None
    assert a["explanation"] is not None
    assert isinstance(a.get("supporting_evidence"), (list, dict, str, type(None)))

    aid = a["id"]
    assert client.get(f"/api/assessments/{aid}").status_code == 200
    assert client.get(f"/api/companies/{company.id}/assessments").status_code == 200
    assert client.get(f"/api/events/{event.id}/assessments").status_code == 200
    assert len(client.get(f"/api/companies/{company.id}/assessments").json()) == 1
    assert len(client.get(f"/api/events/{event.id}/assessments").json()) == 1
