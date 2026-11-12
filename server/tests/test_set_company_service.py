"""SET company provider and sync service tests.

Uses the isolated ``db`` fixture. External HTTP calls are mocked; CSV fallback
uses a temporary file. No real SET credentials or network access required.
"""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from app.models.company import Company
from app.models.industry import Industry
from app.services.set_company_service import (
    SETCompanyAuthError,
    SETCompanyCSVProvider,
    SETCompanyProvider,
    SETCompanyProviderError,
    normalize_company_record,
    sync_companies,
)


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


def test_normalize_company_record_success():
    raw = {"symbol": "ptt", "securityName": "PTT PCL", "market": "SET", "industryName": "Energy", "sectorName": "Utilities"}
    rec = normalize_company_record(raw)
    assert rec is not None
    assert rec["ticker"] == "PTT"
    assert rec["name"] == "PTT PCL"
    assert rec["market"] == "SET"
    assert rec["industry"] == "Energy"
    assert rec["sector"] == "Utilities"


def test_normalize_company_record_missing_required():
    assert normalize_company_record({"name": "No ticker"}) is None
    assert normalize_company_record({"ticker": "ABC"}) is None
    assert normalize_company_record({}) is None


def test_csv_provider_reads_template(tmp_path):
    csv_path = tmp_path / "companies.csv"
    csv_path.write_text(
        "ticker,name,market,industry,sector,exchange\n"
        "AAA,Alpha Co,SET,Energy,Utilities,SET\n"
        "BBB,Beta Co,mai,Tech,Software,mai\n",
        encoding="utf-8",
    )
    provider = SETCompanyCSVProvider(csv_path=str(csv_path))
    rows = provider.fetch_companies()
    assert len(rows) == 2
    assert rows[0]["ticker"] == "AAA"


def test_csv_provider_missing_file_raises(tmp_path):
    provider = SETCompanyCSVProvider(csv_path=str(tmp_path / "missing.csv"))
    with pytest.raises(SETCompanyProviderError):
        provider.fetch_companies()


@patch("app.services.set_company_service.urlopen")
def test_api_provider_fetch_success(mock_urlopen):
    payload = {"data": [{"ticker": "PTT", "name": "PTT PCL", "market": "SET", "industry": "Energy"}]}
    mock_urlopen.return_value = _Resp(json.dumps(payload), status=200)
    provider = SETCompanyProvider(api_url="https://official.example/api/companies", api_key="token")
    records = provider.fetch_companies()
    assert len(records) == 1
    assert records[0]["ticker"] == "PTT"


@patch("app.services.set_company_service.urlopen")
def test_api_provider_invalid_credentials(mock_urlopen):
    from urllib.error import HTTPError
    mock_urlopen.side_effect = HTTPError("https://official.example", 401, "Unauthorized", {}, None)
    provider = SETCompanyProvider(api_url="https://official.example/api/companies", api_key="bad")
    with pytest.raises(SETCompanyAuthError):
        provider.fetch_companies()


def test_api_provider_not_configured():
    provider = SETCompanyProvider(api_url="", api_key="")
    assert provider.configured is False
    with pytest.raises(SETCompanyProviderError):
        provider.fetch_companies()


def test_sync_companies_csv_fallback_imports(db, tmp_path, monkeypatch):
    """When official API not configured, use CSV fallback and import records."""
    csv_path = tmp_path / "companies.csv"
    csv_path.write_text(
        "ticker,name,market,industry,sector,exchange\n"
        "XAA,X Alpha Co,SET,Energy,Utilities,SET\n"
        "XBB,X Beta Co,SET,Tourism,Services,SET\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SET_COMPANY_API_URL", "")
    monkeypatch.setenv("SET_COMPANY_CSV_PATH", str(csv_path))

    result = sync_companies(db)
    assert result["source"] == "csv_fallback"
    assert result["used_fallback"] is True
    assert result["retrieved"] >= 2
    assert result["imported"] == 2
    assert len(result["errors"]) == 0

    assert db.query(Company).filter(Company.ticker == "XAA").first() is not None
    assert db.query(Company).filter(Company.ticker == "XBB").first() is not None


def test_sync_companies_duplicate_prevention_and_update(db, tmp_path, monkeypatch):
    """Re-sync updates existing (ticker,market) without creating duplicates."""
    # seed existing
    ind = Industry(name="EnergySync", description=None)
    db.add(ind)
    db.flush()
    existing = Company(ticker="XCC", name="Old Name", exchange="SET", market="SET", industry_id=None, source="manual")
    db.add(existing)
    db.flush()

    csv_path = tmp_path / "companies.csv"
    csv_path.write_text(
        "ticker,name,market,industry,sector,exchange\n"
        "XCC,X Charlie Co Updated,SET,Energy,Utilities,SET\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SET_COMPANY_API_URL", "")
    monkeypatch.setenv("SET_COMPANY_CSV_PATH", str(csv_path))

    result = sync_companies(db)
    # should not create a duplicate
    count = db.query(Company).filter(Company.ticker == "XCC", Company.market == "SET").count()
    assert count == 1
    updated = db.query(Company).filter(Company.ticker == "XCC").first()
    assert updated.name == "X Charlie Co Updated"
    assert updated.last_synced_at is not None
    assert result["imported"] == 0
    assert (result["updated"] + result["duplicates_skipped"]) >= 1


def test_sync_companies_missing_fields_and_invalid_rows(db, tmp_path, monkeypatch):
    """Rows missing required fields are reported as errors/skipped, not fabricated."""
    csv_path = tmp_path / "companies.csv"
    csv_path.write_text(
        "ticker,name,market,industry,sector,exchange\n"
        ",NoTicker Co,SET,Energy,Utilities,SET\n"
        "XDD,,SET,Energy,Utilities,SET\n"
        "XEE,Valid Co,SET,,,\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SET_COMPANY_API_URL", "")
    monkeypatch.setenv("SET_COMPANY_CSV_PATH", str(csv_path))

    result = sync_companies(db)
    assert result["imported"] == 1
    assert db.query(Company).filter(Company.ticker == "XEE").first() is not None
    # invalid rows should not create companies
    assert db.query(Company).filter(Company.ticker == "XDD").first() is None
    assert len(result["errors"]) >= 1


def test_sync_companies_csv_unavailable_reports_error(db, tmp_path, monkeypatch):
    monkeypatch.setenv("SET_COMPANY_API_URL", "")
    monkeypatch.setenv("SET_COMPANY_CSV_PATH", str(tmp_path / "missing.csv"))

    result = sync_companies(db)
    assert result["retrieved"] == 0
    assert result["imported"] == 0
    assert len(result["errors"]) >= 1
    assert result["last_sync_time"] is not None


@patch("app.services.set_company_service.urlopen")
def test_sync_companies_api_failure_falls_back_to_csv(mock_urlopen, db, tmp_path, monkeypatch):
    from urllib.error import URLError
    mock_urlopen.side_effect = URLError("network down")

    csv_path = tmp_path / "companies.csv"
    csv_path.write_text(
        "ticker,name,market,industry,sector,exchange\nXFF,Fallback Co,SET,Energy,Utilities,SET\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SET_COMPANY_API_URL", "https://official.example/api/companies")
    monkeypatch.setenv("SET_COMPANY_CSV_PATH", str(csv_path))

    result = sync_companies(db)
    assert result["used_fallback"] is True
    assert result["source"] == "csv_fallback"
    assert result["imported"] == 1
    assert db.query(Company).filter(Company.ticker == "XFF").first() is not None
    assert len(result["errors"]) >= 1  # API error recorded
