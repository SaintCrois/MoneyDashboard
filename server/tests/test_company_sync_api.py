"""Company sync API tests."""

import json
from unittest.mock import patch


@patch("app.services.set_company_service.urlopen")
def test_sync_companies_endpoint_success_api(mock_urlopen, client, monkeypatch, tmp_path):
    """POST /api/companies/sync returns sync results from configured API."""
    payload = {"data": [{"ticker": "SYN1", "name": "Sync One", "market": "SET", "industry": "Energy"}]}

    class _Resp:
        def __init__(self, body, status=200):
            self._body = body
            self.status = status
        def read(self):
            return self._body.encode("utf-8")
        def getcode(self):
            return self.status
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False

    mock_urlopen.return_value = _Resp(json.dumps(payload), status=200)
    monkeypatch.setenv("SET_COMPANY_API_URL", "https://official.example/api/companies")
    monkeypatch.setenv("SET_COMPANY_API_KEY", "test-key")
    # ensure csv fallback path not accidentally used
    monkeypatch.setenv("SET_COMPANY_CSV_PATH", str(tmp_path / "missing.csv"))

    resp = client.post("/api/companies/sync")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "retrieved" in data
    assert "imported" in data
    assert "updated" in data
    assert "duplicates_skipped" in data
    assert "errors" in data
    assert "last_sync_time" in data
    assert data["source"] == "set_official_api"
    assert data["imported"] >= 1


@patch("app.services.set_company_service.urlopen")
def test_sync_companies_endpoint_invalid_credentials_fallback(mock_urlopen, client, monkeypatch, tmp_path):
    """Invalid API credentials are reported; CSV fallback used if available."""
    from urllib.error import HTTPError
    mock_urlopen.side_effect = HTTPError("https://official.example", 401, "Unauthorized", {}, None)

    csv_path = tmp_path / "companies.csv"
    csv_path.write_text(
        "ticker,name,market,industry,sector,exchange\nSYN2,Sync Two,SET,Energy,Utilities,SET\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SET_COMPANY_API_URL", "https://official.example/api/companies")
    monkeypatch.setenv("SET_COMPANY_API_KEY", "bad")
    monkeypatch.setenv("SET_COMPANY_CSV_PATH", str(csv_path))

    resp = client.post("/api/companies/sync")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["used_fallback"] is True
    assert data["source"] == "csv_fallback"
    assert data["imported"] == 1
    assert any("401" in e or "Unauthorized" in e or "unauthorized" in e.lower() for e in data["errors"])


def test_sync_companies_endpoint_csv_fallback_only(client, monkeypatch, tmp_path):
    """Without official API config, documented CSV fallback is used."""
    csv_path = tmp_path / "companies.csv"
    csv_path.write_text(
        "ticker,name,market,industry,sector,exchange\nSYN3,Sync Three,SET,Tourism,Services,SET\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SET_COMPANY_API_URL", "")
    monkeypatch.setenv("SET_COMPANY_CSV_PATH", str(csv_path))

    resp = client.post("/api/companies/sync")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["used_fallback"] is True
    assert data["source"] == "csv_fallback"
    assert data["retrieved"] == 1
    assert data["imported"] == 1


def test_sync_companies_endpoint_no_source_available(client, monkeypatch, tmp_path):
    """When no API and no CSV available, endpoint reports failure without fabrication."""
    monkeypatch.setenv("SET_COMPANY_API_URL", "")
    monkeypatch.setenv("SET_COMPANY_CSV_PATH", str(tmp_path / "missing.csv"))

    resp = client.post("/api/companies/sync")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["retrieved"] == 0
    assert data["imported"] == 0
    assert len(data["errors"]) >= 1
    assert data["last_sync_time"] is not None
