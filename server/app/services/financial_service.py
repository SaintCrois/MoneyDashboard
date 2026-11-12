"""Financial data collection, storage, and analysis service.

Provides CRUD operations for company financial records, a modular provider
interface, CSV import fallback, and financial ratio calculations.

Rules:
- Never fabricate financial data.
- Never silently replace missing values with zero.
- Avoid division by zero.
- Clearly identify unavailable metrics.
- Distinguish reported figures from calculated ratios.
- Preserve original values and reporting periods.
"""

import csv
import io
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.financial_data import FinancialData

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Provider interface (modular, extensible)
# ---------------------------------------------------------------------------

class FinancialDataProvider(ABC):
    """Interface for external financial data providers."""

    name: str = "base"

    @abstractmethod
    def fetch_financials(self, company: Company) -> list[dict]:
        """Return a list of financial record dicts for the company.

        Each dict should contain keys matching FinancialData fields.
        Return an empty list if no data is available.
        """


class ManualFinancialProvider(FinancialDataProvider):
    """Fallback provider: no external fetch, supports manual/CSV entry only."""

    name = "manual"

    def fetch_financials(self, company: Company) -> list[dict]:
        return []


# ---------------------------------------------------------------------------
# Calculations (pure functions)
# ---------------------------------------------------------------------------

def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_revenue_growth(current_revenue: Any, previous_revenue: Any) -> Optional[float]:
    """(Current - Previous) / Previous * 100. Returns None if unavailable or div-by-zero."""
    curr = _to_float(current_revenue)
    prev = _to_float(previous_revenue)
    if curr is None or prev is None:
        return None
    if prev == 0:
        return None  # division by zero - unavailable
    return ((curr - prev) / prev) * 100.0


def calculate_net_profit_margin(net_income: Any, revenue: Any) -> Optional[float]:
    """Net Income / Revenue * 100. Returns None if unavailable or div-by-zero."""
    ni = _to_float(net_income)
    rev = _to_float(revenue)
    if ni is None or rev is None:
        return None
    if rev == 0:
        return None
    return (ni / rev) * 100.0


def calculate_debt_to_equity(total_debt: Any, shareholders_equity: Any) -> Optional[float]:
    """Total Debt / Shareholders' Equity. Returns None if unavailable or div-by-zero."""
    debt = _to_float(total_debt)
    equity = _to_float(shareholders_equity)
    if debt is None or equity is None:
        return None
    if equity == 0:
        return None
    return debt / equity


def calculate_free_cash_flow(operating_cash_flow: Any, capital_expenditure: Any) -> Optional[float]:
    """Operating Cash Flow - Capital Expenditure. Returns None if inputs unavailable."""
    ocf = _to_float(operating_cash_flow)
    capex = _to_float(capital_expenditure)
    if ocf is None or capex is None:
        return None
    return ocf - capex


def calculate_operating_margin(operating_income: Any, revenue: Any) -> Optional[float]:
    """Operating Income / Revenue * 100."""
    oi = _to_float(operating_income)
    rev = _to_float(revenue)
    if oi is None or rev is None:
        return None
    if rev == 0:
        return None
    return (oi / rev) * 100.0


def calculate_roe(net_profit: Any, shareholders_equity: Any) -> Optional[float]:
    """Net Profit / Shareholders' Equity * 100 (ROE)."""
    np = _to_float(net_profit)
    eq = _to_float(shareholders_equity)
    if np is None or eq is None:
        return None
    if eq == 0:
        return None
    return (np / eq) * 100.0


def enrich_with_calculations(record: dict, previous_record: Optional[dict] = None) -> dict:
    """Return a copy of record with calculated ratios filled where possible.

    Calculated values do not override explicitly provided reported/calculated
    values (i.e. only fill if currently None). Reported figures are preserved.
    """
    out = dict(record)

    # Revenue growth (needs previous period)
    if out.get("revenue_growth") is None and previous_record is not None:
        rg = calculate_revenue_growth(out.get("revenue"), previous_record.get("revenue"))
        if rg is not None:
            out["revenue_growth"] = round(rg, 4)

    # Net profit margin
    if out.get("net_profit_margin") is None:
        npm = calculate_net_profit_margin(out.get("net_profit"), out.get("revenue"))
        if npm is not None:
            out["net_profit_margin"] = round(npm, 4)

    # Operating margin
    if out.get("operating_margin") is None:
        om = calculate_operating_margin(out.get("operating_income"), out.get("revenue"))
        if om is not None:
            out["operating_margin"] = round(om, 4)

    # Debt-to-equity
    if out.get("debt_to_equity") is None:
        de = calculate_debt_to_equity(out.get("total_debt"), out.get("shareholders_equity"))
        if de is not None:
            out["debt_to_equity"] = round(de, 4)

    # Free cash flow
    if out.get("free_cash_flow") is None:
        fcf = calculate_free_cash_flow(
            out.get("operating_cash_flow"), out.get("capital_expenditure")
        )
        if fcf is not None:
            out["free_cash_flow"] = round(fcf, 2)

    # ROE
    if out.get("roe") is None:
        roe = calculate_roe(out.get("net_profit"), out.get("shareholders_equity"))
        if roe is not None:
            out["roe"] = round(roe, 4)

    return out


# ---------------------------------------------------------------------------
# CRUD and analysis
# ---------------------------------------------------------------------------

_FINANCIAL_FIELDS = [
    "fiscal_year", "reporting_period",
    "revenue", "net_profit", "operating_income",
    "total_assets", "total_liabilities", "total_debt", "shareholders_equity",
    "operating_cash_flow", "capital_expenditure", "eps",
    "operating_margin", "net_profit_margin", "debt_to_equity",
    "current_ratio", "free_cash_flow", "roe", "revenue_growth",
    "data_source", "reported_at", "is_estimate",
]


def _apply_fields(obj: FinancialData, data: dict) -> None:
    for field in _FINANCIAL_FIELDS:
        if field in data:
            setattr(obj, field, data[field])


def get_financials(db: Session, company_id: int) -> list[FinancialData]:
    return (
        db.query(FinancialData)
        .filter(FinancialData.company_id == company_id)
        .order_by(FinancialData.fiscal_year.asc())
        .all()
    )


def create_financial_record(
    db: Session, company_id: int, data: dict
) -> tuple[Optional[FinancialData], Optional[str]]:
    """Create a financial record. Returns (record, error_message)."""
    # Prevent duplicate (company_id, fiscal_year)
    existing = (
        db.query(FinancialData)
        .filter(
            FinancialData.company_id == company_id,
            FinancialData.fiscal_year == data.get("fiscal_year"),
        )
        .first()
    )
    if existing:
        return None, "Financial record for this company and fiscal year already exists"

    record = FinancialData(company_id=company_id)
    _apply_fields(record, data)
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None, "Financial record for this company and fiscal year already exists"
    db.refresh(record)
    return record, None


def import_financials_from_csv(
    db: Session, company_id: int, csv_content: str, data_source: str = "CSV import"
) -> dict:
    """Import financial records from CSV content. Returns summary stats."""
    stats = {"inserted": 0, "skipped_duplicate": 0, "errors": 0, "rows": []}
    reader = csv.DictReader(io.StringIO(csv_content))
    for i, row in enumerate(reader, start=1):
        try:
            data = _parse_csv_row(row)
            if data.get("data_source") is None:
                data["data_source"] = data_source
            if data.get("fiscal_year") is None:
                stats["errors"] += 1
                stats["rows"].append({"row": i, "error": "Missing fiscal_year"})
                continue
            _, err = create_financial_record(db, company_id, data)
            if err:
                if "already exists" in err:
                    stats["skipped_duplicate"] += 1
                    stats["rows"].append({"row": i, "skipped": err})
                else:
                    stats["errors"] += 1
                    stats["rows"].append({"row": i, "error": err})
            else:
                stats["inserted"] += 1
                stats["rows"].append({"row": i, "status": "inserted"})
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error importing CSV row %s", i)
            stats["errors"] += 1
            stats["rows"].append({"row": i, "error": str(exc)})
    return stats


def _parse_csv_row(row: dict) -> dict:
    """Parse a CSV row into a financial data dict, preserving None for blanks."""
    def _num(key: str) -> Optional[float]:
        val = row.get(key)
        if val is None:
            return None
        val = str(val).strip()
        if val == "" or val.lower() in ("null", "none", "n/a", "na", "-"):
            return None
        try:
            return float(val)
        except ValueError:
            return None

    def _int(key: str) -> Optional[int]:
        v = _num(key)
        return int(v) if v is not None else None

    def _str(key: str) -> Optional[str]:
        val = row.get(key)
        if val is None:
            return None
        val = str(val).strip()
        return val if val else None

    def _bool(key: str) -> bool:
        val = row.get(key)
        if val is None:
            return False
        return str(val).strip().lower() in ("true", "1", "yes")

    return {
        "fiscal_year": _int("fiscal_year"),
        "reporting_period": _str("reporting_period"),
        "revenue": _num("revenue"),
        "net_profit": _num("net_profit"),
        "operating_income": _num("operating_income"),
        "total_assets": _num("total_assets"),
        "total_liabilities": _num("total_liabilities"),
        "total_debt": _num("total_debt"),
        "shareholders_equity": _num("shareholders_equity"),
        "operating_cash_flow": _num("operating_cash_flow"),
        "capital_expenditure": _num("capital_expenditure"),
        "eps": _num("eps"),
        "operating_margin": _num("operating_margin"),
        "net_profit_margin": _num("net_profit_margin"),
        "debt_to_equity": _num("debt_to_equity"),
        "current_ratio": _num("current_ratio"),
        "free_cash_flow": _num("free_cash_flow"),
        "roe": _num("roe"),
        "revenue_growth": _num("revenue_growth"),
        "data_source": _str("data_source"),
        "is_estimate": _bool("is_estimate"),
    }


def analyze_financials(db: Session, company: Company) -> dict:
    """Build a financial analysis summary for a company.

    Returns reported records, calculated metrics per period, unavailable metrics,
    data sources, and notes. Missing values are identified, never treated as zero.
    """
    records = get_financials(db, company.id)

    calculated_metrics = []
    unavailable: set[str] = set()
    notes: list[str] = []
    data_sources = sorted({r.data_source for r in records if r.data_source})

    if not records:
        notes.append("No financial data available for this company.")
        return {
            "company_id": company.id,
            "company_ticker": company.ticker,
            "company_name": company.name,
            "records": [],
            "calculated_metrics": [],
            "unavailable_metrics": ["all"],
            "data_sources": [],
            "latest_period": None,
            "notes": notes,
        }

    prev: Optional[FinancialData] = None
    for rec in records:
        # Build a view of what can be calculated for this period
        metrics: dict[str, Any] = {
            "fiscal_year": rec.fiscal_year,
            "reporting_period": rec.reporting_period or str(rec.fiscal_year),
            "reported": {},
            "calculated": {},
            "unavailable": [],
        }

        # Reported figures
        for field in ("revenue", "net_profit", "operating_income", "total_assets",
                      "total_liabilities", "total_debt", "shareholders_equity",
                      "operating_cash_flow", "capital_expenditure", "eps"):
            val = getattr(rec, field)
            metrics["reported"][field] = float(val) if val is not None else None

        # Calculated / derived metrics
        # Revenue growth
        if prev is not None:
            rg = calculate_revenue_growth(rec.revenue, prev.revenue)
            if rg is not None:
                metrics["calculated"]["revenue_growth"] = round(rg, 4)
            elif rec.revenue_growth is not None:
                metrics["calculated"]["revenue_growth"] = float(rec.revenue_growth)
            else:
                metrics["unavailable"].append("revenue_growth")
                unavailable.add("revenue_growth")
        else:
            if rec.revenue_growth is not None:
                metrics["calculated"]["revenue_growth"] = float(rec.revenue_growth)
            else:
                metrics["unavailable"].append("revenue_growth")
                unavailable.add("revenue_growth")
                notes.append(
                    f"Revenue growth unavailable for {rec.fiscal_year}: no prior period for comparison."
                )

        # Net profit margin
        npm = calculate_net_profit_margin(rec.net_profit, rec.revenue)
        if npm is not None:
            metrics["calculated"]["net_profit_margin"] = round(npm, 4)
        elif rec.net_profit_margin is not None:
            metrics["calculated"]["net_profit_margin"] = float(rec.net_profit_margin)
        else:
            metrics["unavailable"].append("net_profit_margin")
            unavailable.add("net_profit_margin")

        # Operating margin
        om = calculate_operating_margin(rec.operating_income, rec.revenue)
        if om is not None:
            metrics["calculated"]["operating_margin"] = round(om, 4)
        elif rec.operating_margin is not None:
            metrics["calculated"]["operating_margin"] = float(rec.operating_margin)
        else:
            metrics["unavailable"].append("operating_margin")
            unavailable.add("operating_margin")

        # Debt-to-equity
        de = calculate_debt_to_equity(rec.total_debt, rec.shareholders_equity)
        if de is not None:
            metrics["calculated"]["debt_to_equity"] = round(de, 4)
        elif rec.debt_to_equity is not None:
            metrics["calculated"]["debt_to_equity"] = float(rec.debt_to_equity)
        else:
            metrics["unavailable"].append("debt_to_equity")
            unavailable.add("debt_to_equity")

        # Free cash flow
        fcf = calculate_free_cash_flow(rec.operating_cash_flow, rec.capital_expenditure)
        if fcf is not None:
            metrics["calculated"]["free_cash_flow"] = round(fcf, 2)
        elif rec.free_cash_flow is not None:
            metrics["calculated"]["free_cash_flow"] = float(rec.free_cash_flow)
        else:
            metrics["unavailable"].append("free_cash_flow")
            unavailable.add("free_cash_flow")

        # ROE
        roe = calculate_roe(rec.net_profit, rec.shareholders_equity)
        if roe is not None:
            metrics["calculated"]["roe"] = round(roe, 4)
        elif rec.roe is not None:
            metrics["calculated"]["roe"] = float(rec.roe)
        else:
            metrics["unavailable"].append("roe")
            unavailable.add("roe")

        # Current ratio (reported/calculated only, not derivable from current model fields)
        if rec.current_ratio is not None:
            metrics["calculated"]["current_ratio"] = float(rec.current_ratio)
        else:
            metrics["unavailable"].append("current_ratio")
            unavailable.add("current_ratio")

        calculated_metrics.append(metrics)
        prev = rec

    latest = records[-1]
    return {
        "company_id": company.id,
        "company_ticker": company.ticker,
        "company_name": company.name,
        "records": records,
        "calculated_metrics": calculated_metrics,
        "unavailable_metrics": sorted(unavailable),
        "data_sources": data_sources,
        "latest_period": latest.reporting_period or str(latest.fiscal_year),
        "notes": notes,
    }
