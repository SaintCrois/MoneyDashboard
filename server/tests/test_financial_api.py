"""Financial API tests.

Uses the isolated ``db`` and ``client`` fixtures (transaction rolled back per test).
"""


def _create_company(client, ticker="FAPI1"):
    ind = client.post("/api/industries", json={"name": f"Ind-{ticker}", "description": "t"}).json()
    comp = client.post("/api/companies", json={
        "name": f"Company {ticker}", "ticker": ticker, "industry_id": ind["id"]
    }).json()
    return comp


def test_create_and_list_financials(client):
    company = _create_company(client, ticker="FA1")
    cid = company["id"]
    payload = {
        "fiscal_year": 2024,
        "reporting_period": "FY2024",
        "revenue": 1000.0,
        "net_profit": 120.0,
        "total_debt": 200.0,
        "shareholders_equity": 400.0,
        "data_source": "manual",
    }
    resp = client.post(f"/api/companies/{cid}/financials", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["company_id"] == cid
    assert data["fiscal_year"] == 2024

    resp = client.get(f"/api/companies/{cid}/financials")
    assert resp.status_code == 200
    records = resp.json()
    assert len(records) == 1
    assert records[0]["revenue"] == 1000.0


def test_duplicate_financial_rejected(client):
    company = _create_company(client, ticker="FA2")
    cid = company["id"]
    payload = {"fiscal_year": 2024, "revenue": 100.0}
    assert client.post(f"/api/companies/{cid}/financials", json=payload).status_code == 201
    resp = client.post(f"/api/companies/{cid}/financials", json=payload)
    assert resp.status_code == 400


def test_financial_analysis_endpoint(client):
    company = _create_company(client, ticker="FA3")
    cid = company["id"]
    client.post(f"/api/companies/{cid}/financials", json={
        "fiscal_year": 2023, "revenue": 1000.0, "net_profit": 100.0,
        "operating_income": 120.0, "total_debt": 200.0, "shareholders_equity": 400.0,
    })
    client.post(f"/api/companies/{cid}/financials", json={
        "fiscal_year": 2024, "revenue": 1200.0, "net_profit": 150.0,
        "operating_income": 180.0, "total_debt": 220.0, "shareholders_equity": 500.0,
    })

    resp = client.get(f"/api/companies/{cid}/financial-analysis")
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_id"] == cid
    assert len(data["records"]) == 2
    assert len(data["calculated_metrics"]) == 2
    latest = data["calculated_metrics"][-1]["calculated"]
    assert "revenue_growth" in latest
    assert "net_profit_margin" in latest


def test_financials_company_not_found(client):
    assert client.get("/api/companies/999999/financials").status_code == 404
    assert client.get("/api/companies/999999/financial-analysis").status_code == 404
    assert client.post("/api/companies/999999/financials", json={"fiscal_year": 2024}).status_code == 404
