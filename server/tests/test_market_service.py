"""Market service and calculation tests.

Uses the isolated ``db`` fixture (transaction rolled back per test).
"""

from datetime import datetime, timezone

from app.models.company import Company
from app.models.industry import Industry
from app.models.market_data import MarketData
from app.services.market_service import (
    analyze_market,
    calculate_average_volume,
    calculate_daily_change_pct,
    calculate_price_movement,
    calculate_volatility,
    calculate_volume_comparison,
    create_market_record,
    get_market_data,
    import_market_data_from_csv,
)


def _make_company(db, name="TestMktCo", ticker="TMC"):
    industry = Industry(name=f"IndM-{ticker}", description="test")
    db.add(industry)
    db.flush()
    company = Company(name=name, ticker=ticker, industry_id=industry.id)
    db.add(company)
    db.flush()
    return company


def _dt(day):
    return datetime(2026, 11, day, tzinfo=timezone.utc)


# --- Pure calculation tests ---

def test_daily_change_pct():
    assert round(calculate_daily_change_pct(110, 100), 4) == 10.0
    assert round(calculate_daily_change_pct(90, 100), 4) == -10.0
    assert calculate_daily_change_pct(110, 0) is None
    assert calculate_daily_change_pct(None, 100) is None


def test_price_movement_insufficient_data(db):
    company = _make_company(db, ticker="MKT0")
    rec = MarketData(company_id=company.id, recorded_at=_dt(1), stock_price=100, close_price=100)
    db.add(rec)
    db.flush()
    assert calculate_price_movement([rec], 5) is None


def test_average_volume_and_comparison(db):
    company = _make_company(db, ticker="MKT1")
    records = []
    for i, vol in enumerate([100, 120, 110, 90, 200], start=1):
        r = MarketData(company_id=company.id, recorded_at=_dt(i), stock_price=100, close_price=100, trading_volume=vol)
        db.add(r)
        records.append(r)
    db.flush()
    assert calculate_average_volume(records) == 124.0
    cmp = calculate_volume_comparison(records, recent_n=1, baseline_n=4)
    assert cmp is not None
    assert cmp["recent_average_volume"] == 200.0
    assert round(cmp["baseline_average_volume"], 2) == 105.0
    assert cmp["volume_ratio"] > 1


def test_volatility_calculation(db):
    company = _make_company(db, ticker="MKT2")
    # daily_change_pct values provided -> volatility is stddev of them
    values = [1.0, -1.0, 2.0, -2.0]
    records = []
    for i, ch in enumerate(values, start=1):
        r = MarketData(company_id=company.id, recorded_at=_dt(i), stock_price=100, close_price=100, daily_change_pct=ch)
        db.add(r)
        records.append(r)
    db.flush()
    vol = calculate_volatility(records)
    assert vol is not None
    assert vol > 0


def test_volatility_unavailable_with_insufficient_points(db):
    company = _make_company(db, ticker="MKT3")
    r = MarketData(company_id=company.id, recorded_at=_dt(1), stock_price=100, close_price=100, daily_change_pct=1.0)
    db.add(r)
    db.flush()
    assert calculate_volatility([r]) is None


# --- Service/DB tests ---

def test_create_and_get_market_data(db):
    company = _make_company(db, ticker="MKT4")
    rec, err = create_market_record(db, company.id, {
        "recorded_at": _dt(1),
        "stock_price": 100.0,
        "open_price": 99.0,
        "high_price": 101.0,
        "low_price": 98.0,
        "close_price": 100.0,
        "trading_volume": 1000,
        "data_source": "manual",
    })
    assert err is None
    assert rec is not None
    records = get_market_data(db, company.id)
    assert len(records) == 1


def test_duplicate_market_record_rejected(db):
    company = _make_company(db, ticker="MKT5")
    _, err1 = create_market_record(db, company.id, {"recorded_at": _dt(1), "close_price": 100.0})
    assert err1 is None
    _, err2 = create_market_record(db, company.id, {"recorded_at": _dt(1), "close_price": 101.0})
    assert err2 is not None
    assert "already exists" in err2


def test_auto_daily_change_calculation(db):
    company = _make_company(db, ticker="MKT6")
    create_market_record(db, company.id, {"recorded_at": _dt(1), "close_price": 100.0})
    rec2, err = create_market_record(db, company.id, {"recorded_at": _dt(2), "close_price": 110.0})
    assert err is None
    assert rec2.daily_change_pct is not None
    assert round(float(rec2.daily_change_pct), 2) == 10.0


def test_analyze_market_with_records(db):
    company = _make_company(db, ticker="MKT7")
    for day, price, vol in [(1, 100, 1000), (2, 102, 1200), (3, 101, 900), (4, 105, 1500)]:
        create_market_record(db, company.id, {
            "recorded_at": _dt(day),
            "close_price": float(price),
            "trading_volume": vol,
            "data_source": "manual",
        })
    analysis = analyze_market(db, company)
    assert analysis["company_id"] == company.id
    assert len(analysis["records"]) == 4
    ind = analysis["indicators"]
    assert ind["latest_price"] == 105.0
    assert "average_trading_volume" in ind
    assert "volatility" in ind or "volatility" in analysis["unavailable_indicators"]


def test_analyze_market_no_records(db):
    company = _make_company(db, ticker="MKT8")
    analysis = analyze_market(db, company)
    assert analysis["records"] == []
    assert "all" in analysis["unavailable_indicators"]
    assert any("No market data" in n for n in analysis["notes"])


def test_import_market_data_from_csv(db):
    company = _make_company(db, ticker="MKT9")
    csv_content = (
        "recorded_at,close_price,trading_volume,data_source\n"
        "2026-11-01,100,1000,CSV\n"
        "2026-11-02,105,1200,CSV\n"
        "2026-11-02,106,1300,CSV\n"  # duplicate
    )
    stats = import_market_data_from_csv(db, company.id, csv_content)
    assert stats["inserted"] == 2
    assert stats["skipped_duplicate"] == 1
    assert len(get_market_data(db, company.id)) == 2
