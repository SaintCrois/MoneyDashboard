"""Market API tests.

Uses the isolated ``db`` and ``client`` fixtures (transaction rolled back per test).
"""


def _create_company(client, ticker="MAPI1"):
    ind = client.post("/api/industries", json={"name": f"IndM-{ticker}", "description": "t"}).json()
    comp = client.post("/api/companies", json={
        "name": f"Company {ticker}", "ticker": ticker, "industry_id": ind["id"]
    }).json()
    return comp


def test_create_and_list_market_data(client):
    company = _create_company(client, ticker="MA1")
    cid = company["id"]
    payload = {
        "recorded_at": "2026-11-01T00:00:00Z",
        "open_price": 99.0,
        "high_price": 101.0,
        "low_price": 98.0,
        "close_price": 100.0,
        "trading_volume": 1000,
        "data_source": "manual",
    }
    resp = client.post(f"/api/companies/{cid}/market-data", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["company_id"] == cid

    resp = client.get(f"/api/companies/{cid}/market-data")
    assert resp.status_code == 200
    records = resp.json()
    assert len(records) == 1


def test_duplicate_market_data_rejected(client):
    company = _create_company(client, ticker="MA2")
    cid = company["id"]
    payload = {"recorded_at": "2026-11-01T00:00:00Z", "close_price": 100.0}
    assert client.post(f"/api/companies/{cid}/market-data", json=payload).status_code == 201
    resp = client.post(f"/api/companies/{cid}/market-data", json=payload)
    assert resp.status_code == 400


def test_market_analysis_endpoint(client):
    company = _create_company(client, ticker="MA3")
    cid = company["id"]
    for day, price, vol in [("01", 100, 1000), ("02", 102, 1200), ("03", 101, 900)]:
        client.post(f"/api/companies/{cid}/market-data", json={
            "recorded_at": f"2026-11-{day}T00:00:00Z",
            "close_price": float(price),
            "trading_volume": vol,
            "data_source": "manual",
        })

    resp = client.get(f"/api/companies/{cid}/market-analysis")
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_id"] == cid
    assert len(data["records"]) == 3
    assert "indicators" in data
    assert data["indicators"].get("latest_price") == 101.0


def test_market_data_company_not_found(client):
    assert client.get("/api/companies/999999/market-data").status_code == 404
    assert client.get("/api/companies/999999/market-analysis").status_code == 404
    assert client.post("/api/companies/999999/market-data", json={"recorded_at": "2026-11-01T00:00:00Z"}).status_code == 404
