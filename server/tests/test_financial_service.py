"""Financial service and calculation tests.

Uses the isolated ``db`` fixture (transaction rolled back per test).
"""

from datetime import datetime, timezone

import pytest

from app.models.company import Company
from app.models.financial_data import FinancialData
from app.models.industry import Industry
from app.services.financial_service import (
    analyze_financials,
    calculate_debt_to_equity,
    calculate_free_cash_flow,
    calculate_net_profit_margin,
    calculate_operating_margin,
    calculate_revenue_growth,
    calculate_roe,
    create_financial_record,
    get_financials,
    import_financials_from_csv,
)


def _make_company(db, name="TestFinCo", ticker="TFC"):
    industry = Industry(name=f"Ind-{ticker}", description="test")
    db.add(industry)
    db.flush()
    company = Company(name=name, ticker=ticker, industry_id=industry.id)
    db.add(company)
    db.flush()
    return company


# --- Pure calculation tests ---

def test_revenue_growth_calculation():
    assert round(calculate_revenue_growth(120, 100), 4) == 20.0
    assert round(calculate_revenue_growth(80, 100), 4) == -20.0


def test_revenue_growth_unavailable_on_missing_or_zero():
    assert calculate_revenue_growth(None, 100) is None
    assert calculate_revenue_growth(100, None) is None
    assert calculate_revenue_growth(100, 0) is None  # division by zero guarded


def test_net_profit_margin():
    assert round(calculate_net_profit_margin(25, 100), 4) == 25.0
    assert calculate_net_profit_margin(25, 0) is None
    assert calculate_net_profit_margin(None, 100) is None


def test_debt_to_equity():
    assert round(calculate_debt_to_equity(50, 100), 4) == 0.5
    assert calculate_debt_to_equity(50, 0) is None
    assert calculate_debt_to_equity(None, 100) is None


def test_free_cash_flow():
    assert calculate_free_cash_flow(100, 30) == 70
    assert calculate_free_cash_flow(None, 30) is None
    assert calculate_free_cash_flow(100, None) is None


def test_operating_margin_and_roe():
    assert round(calculate_operating_margin(20, 100), 4) == 20.0
    assert calculate_operating_margin(20, 0) is None
    assert round(calculate_roe(15, 100), 4) == 15.0
    assert calculate_roe(15, 0) is None


# --- Service/DB tests ---

def test_create_and_get_financials(db):
    company = _make_company(db, ticker="FIN1")
    record, err = create_financial_record(db, company.id, {
        "fiscal_year": 2024,
        "reporting_period": "FY2024",
        "revenue": 1000.0,
        "net_profit": 120.0,
        "operating_income": 150.0,
        "total_debt": 300.0,
        "shareholders_equity": 600.0,
        "operating_cash_flow": 200.0,
        "capital_expenditure": 50.0,
        "data_source": "manual",
    })
    assert err is None
    assert record is not None
    assert record.company_id == company.id
    assert record.fiscal_year == 2024

    records = get_financials(db, company.id)
    assert len(records) == 1
    assert records[0].revenue == 1000.0


def test_duplicate_financial_record_rejected(db):
    company = _make_company(db, ticker="FIN2")
    _, err1 = create_financial_record(db, company.id, {"fiscal_year": 2024, "revenue": 100.0})
    assert err1 is None
    _, err2 = create_financial_record(db, company.id, {"fiscal_year": 2024, "revenue": 200.0})
    assert err2 is not None
    assert "already exists" in err2


def test_analyze_financials_calculates_metrics(db):
    company = _make_company(db, ticker="FIN3")
    create_financial_record(db, company.id, {
        "fiscal_year": 2023, "revenue": 1000.0, "net_profit": 100.0,
        "operating_income": 120.0, "total_debt": 200.0, "shareholders_equity": 400.0,
        "operating_cash_flow": 150.0, "capital_expenditure": 50.0,
    })
    create_financial_record(db, company.id, {
        "fiscal_year": 2024, "revenue": 1200.0, "net_profit": 150.0,
        "operating_income": 180.0, "total_debt": 220.0, "shareholders_equity": 500.0,
        "operating_cash_flow": 180.0, "capital_expenditure": 60.0,
    })

    analysis = analyze_financials(db, company)
    assert analysis["company_id"] == company.id
    assert len(analysis["records"]) == 2
    assert len(analysis["calculated_metrics"]) == 2

    latest = analysis["calculated_metrics"][-1]
    calc = latest["calculated"]
    assert round(calc["revenue_growth"], 2) == 20.0
    assert round(calc["net_profit_margin"], 2) == 12.5
    assert round(calc["debt_to_equity"], 2) == 0.44
    assert "free_cash_flow" in calc


def test_analyze_financials_handles_missing_data(db):
    company = _make_company(db, ticker="FIN4")
    # Only first year, so revenue growth unavailable; missing equity -> D/E unavailable
    create_financial_record(db, company.id, {"fiscal_year": 2024, "revenue": 1000.0, "net_profit": 100.0})

    analysis = analyze_financials(db, company)
    assert len(analysis["records"]) == 1
    latest = analysis["calculated_metrics"][0]
    assert "revenue_growth" in latest["unavailable"]
    assert "debt_to_equity" in latest["unavailable"]
    # net profit margin should be calculable
    assert "net_profit_margin" in latest["calculated"]


def test_analyze_financials_no_records(db):
    company = _make_company(db, ticker="FIN5")
    analysis = analyze_financials(db, company)
    assert analysis["records"] == []
    assert "all" in analysis["unavailable_metrics"]
    assert any("No financial data" in n for n in analysis["notes"])


def test_import_financials_from_csv(db):
    company = _make_company(db, ticker="FIN6")
    csv_content = (
        "fiscal_year,reporting_period,revenue,net_profit,total_debt,shareholders_equity\n"
        "2023,FY2023,1000,100,200,400\n"
        "2024,FY2024,1200,150,220,500\n"
        "2024,FY2024,999,99,99,99\n"  # duplicate
    )
    stats = import_financials_from_csv(db, company.id, csv_content)
    assert stats["inserted"] == 2
    assert stats["skipped_duplicate"] == 1
    assert stats["errors"] == 0
    assert len(get_financials(db, company.id)) == 2


def test_import_financials_csv_missing_fiscal_year(db):
    company = _make_company(db, ticker="FIN7")
    csv_content = "fiscal_year,revenue\n,1000\n2024,1200\n"
    stats = import_financials_from_csv(db, company.id, csv_content)
    assert stats["inserted"] == 1
    assert stats["errors"] == 1
