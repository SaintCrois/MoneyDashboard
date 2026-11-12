"""Market data collection, storage, and analysis service.

Provides CRUD operations for company market records, a modular provider
interface, CSV import fallback, and market indicator calculations.

Rules:
- Never fabricate market data.
- Never silently replace missing values with zero.
- Preserve timestamps and trading dates.
- Handle missing trading days.
- Distinguish delayed/estimated data from reported data.
- Display data source and latest update time.
- Avoid presenting estimates as actual market prices.
"""

import csv
import io
import logging
import math
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.market_data import MarketData

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Provider interface
# ---------------------------------------------------------------------------

class MarketDataProvider(ABC):
    """Interface for external market data providers."""

    name: str = "base"

    @abstractmethod
    def fetch_market_data(self, company: Company) -> list[dict]:
        """Return a list of market data dicts for the company."""


class ManualMarketProvider(MarketDataProvider):
    """Fallback provider: no external fetch, supports manual/CSV entry only."""

    name = "manual"

    def fetch_market_data(self, company: Company) -> list[dict]:
        return []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Calculations
# ---------------------------------------------------------------------------

def calculate_daily_change_pct(
    current_price: Any, previous_close: Any
) -> Optional[float]:
    """Daily % change: (current - previous_close) / previous_close * 100."""
    curr = _to_float(current_price)
    prev = _to_float(previous_close)
    if curr is None or prev is None:
        return None
    if prev == 0:
        return None
    return ((curr - prev) / prev) * 100.0


def calculate_price_movement(records: list[MarketData], period: int) -> Optional[dict]:
    """Price movement over the last `period` records (chronological).

    Returns dict with start_price, end_price, change, change_pct or None if
    insufficient data.
    """
    if len(records) < 2:
        return None
    window = records[-period:] if period < len(records) else records
    if len(window) < 2:
        return None
    start = _effective_price(window[0])
    end = _effective_price(window[-1])
    if start is None or end is None:
        return None
    change = end - start
    change_pct = ((end - start) / start * 100.0) if start != 0 else None
    return {
        "period_records": len(window),
        "start_price": round(start, 4),
        "end_price": round(end, 4),
        "change": round(change, 4),
        "change_pct": round(change_pct, 4) if change_pct is not None else None,
        "start_date": window[0].recorded_at.isoformat() if window[0].recorded_at else None,
        "end_date": window[-1].recorded_at.isoformat() if window[-1].recorded_at else None,
    }


def calculate_average_volume(records: list[MarketData]) -> Optional[float]:
    volumes = [r.trading_volume for r in records if r.trading_volume is not None]
    if not volumes:
        return None
    return sum(volumes) / len(volumes)


def calculate_volume_comparison(
    records: list[MarketData], recent_n: int = 1, baseline_n: int = 20
) -> Optional[dict]:
    """Compare recent average volume against a historical baseline.

    Returns ratio and interpretation data, or None if insufficient data.
    """
    if len(records) < 2:
        return None
    recent = records[-recent_n:] if len(records) >= recent_n else records
    baseline_pool = records[:-recent_n] if len(records) > recent_n else records
    # Use last baseline_n of baseline_pool
    baseline_pool = baseline_pool[-baseline_n:] if len(baseline_pool) > baseline_n else baseline_pool

    recent_vols = [r.trading_volume for r in recent if r.trading_volume is not None]
    baseline_vols = [r.trading_volume for r in baseline_pool if r.trading_volume is not None]
    if not recent_vols or not baseline_vols:
        return None
    recent_avg = sum(recent_vols) / len(recent_vols)
    baseline_avg = sum(baseline_vols) / len(baseline_vols)
    if baseline_avg == 0:
        return None
    ratio = recent_avg / baseline_avg
    return {
        "recent_average_volume": round(recent_avg, 2),
        "baseline_average_volume": round(baseline_avg, 2),
        "volume_ratio": round(ratio, 4),
        "baseline_records": len(baseline_vols),
    }


def calculate_volatility(records: list[MarketData]) -> Optional[float]:
    """Basic volatility: standard deviation of daily % changes (population).

    Returns None if fewer than 2 data points with calculable changes.
    """
    changes = []
    # Prefer stored daily_change_pct, otherwise compute from effective prices
    for i, rec in enumerate(records):
        if rec.daily_change_pct is not None:
            changes.append(float(rec.daily_change_pct))
        elif i > 0:
            prev = _effective_price(records[i - 1])
            curr = _effective_price(rec)
            if prev is not None and curr is not None and prev != 0:
                changes.append(((curr - prev) / prev) * 100.0)
    if len(changes) < 2:
        return None
    mean = sum(changes) / len(changes)
    variance = sum((c - mean) ** 2 for c in changes) / len(changes)
    return math.sqrt(variance)


def _effective_price(record: MarketData) -> Optional[float]:
    """Return the best available price for a record (close > stock_price > open)."""
    for val in (record.close_price, record.stock_price, record.open_price):
        if val is not None:
            return float(val)
    return None


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

_MARKET_FIELDS = [
    "recorded_at", "stock_price", "open_price", "high_price", "low_price",
    "close_price", "trading_volume", "daily_change_pct",
    "foreign_net_value", "institutional_net_value",
    "data_source", "is_delayed", "is_estimate",
]


def _apply_fields(obj: MarketData, data: dict) -> None:
    for field in _MARKET_FIELDS:
        if field in data:
            setattr(obj, field, data[field])


def get_market_data(db: Session, company_id: int) -> list[MarketData]:
    return (
        db.query(MarketData)
        .filter(MarketData.company_id == company_id)
        .order_by(MarketData.recorded_at.asc())
        .all()
    )


def create_market_record(
    db: Session, company_id: int, data: dict
) -> tuple[Optional[MarketData], Optional[str]]:
    """Create a market record. Returns (record, error_message)."""
    recorded_at = data.get("recorded_at")
    if recorded_at is None:
        return None, "recorded_at is required"

    existing = (
        db.query(MarketData)
        .filter(
            MarketData.company_id == company_id,
            MarketData.recorded_at == recorded_at,
        )
        .first()
    )
    if existing:
        return None, "Market data for this company and recorded_at already exists"

    # Auto-calc daily change if not provided and previous record exists
    if data.get("daily_change_pct") is None:
        prev = (
            db.query(MarketData)
            .filter(
                MarketData.company_id == company_id,
                MarketData.recorded_at < recorded_at,
            )
            .order_by(MarketData.recorded_at.desc())
            .first()
        )
        if prev is not None:
            curr_price = data.get("close_price") or data.get("stock_price")
            prev_price = _effective_price(prev)
            pct = calculate_daily_change_pct(curr_price, prev_price)
            if pct is not None:
                data = {**data, "daily_change_pct": round(pct, 4)}

    record = MarketData(company_id=company_id)
    _apply_fields(record, data)
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None, "Market data for this company and recorded_at already exists"
    db.refresh(record)
    return record, None


def import_market_data_from_csv(
    db: Session, company_id: int, csv_content: str, data_source: str = "CSV import"
) -> dict:
    """Import market records from CSV. Returns summary stats."""
    stats = {"inserted": 0, "skipped_duplicate": 0, "errors": 0, "rows": []}
    reader = csv.DictReader(io.StringIO(csv_content))
    for i, row in enumerate(reader, start=1):
        try:
            data = _parse_csv_row(row)
            if data.get("data_source") is None:
                data["data_source"] = data_source
            if data.get("recorded_at") is None:
                stats["errors"] += 1
                stats["rows"].append({"row": i, "error": "Missing recorded_at"})
                continue
            _, err = create_market_record(db, company_id, data)
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
            logger.exception("Error importing market CSV row %s", i)
            stats["errors"] += 1
            stats["rows"].append({"row": i, "error": str(exc)})
    return stats


def _parse_csv_row(row: dict) -> dict:
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

    def _dt(key: str) -> Optional[datetime]:
        val = row.get(key)
        if val is None:
            return None
        val = str(val).strip()
        if not val:
            return None
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(val, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        return None

    return {
        "recorded_at": _dt("recorded_at"),
        "stock_price": _num("stock_price"),
        "open_price": _num("open_price"),
        "high_price": _num("high_price"),
        "low_price": _num("low_price"),
        "close_price": _num("close_price"),
        "trading_volume": _int("trading_volume"),
        "daily_change_pct": _num("daily_change_pct"),
        "foreign_net_value": _num("foreign_net_value"),
        "institutional_net_value": _num("institutional_net_value"),
        "data_source": _str("data_source"),
        "is_delayed": _bool("is_delayed"),
        "is_estimate": _bool("is_estimate"),
    }


def analyze_market(db: Session, company: Company) -> dict:
    """Build a market analysis summary for a company."""
    records = get_market_data(db, company.id)
    notes: list[str] = []
    unavailable: list[str] = []
    data_sources = sorted({r.data_source for r in records if r.data_source})

    if not records:
        notes.append("No market data available for this company.")
        return {
            "company_id": company.id,
            "company_ticker": company.ticker,
            "company_name": company.name,
            "records": [],
            "indicators": {},
            "unavailable_indicators": ["all"],
            "data_sources": [],
            "latest_update": None,
            "notes": notes,
        }

    indicators: dict[str, Any] = {}

    # Latest
    latest = records[-1]
    indicators["latest_price"] = _effective_price(latest)
    indicators["latest_volume"] = latest.trading_volume
    indicators["latest_recorded_at"] = latest.recorded_at.isoformat() if latest.recorded_at else None
    indicators["latest_is_delayed"] = latest.is_delayed
    indicators["latest_is_estimate"] = latest.is_estimate

    # Daily % change (latest)
    if latest.daily_change_pct is not None:
        indicators["daily_change_pct"] = float(latest.daily_change_pct)
    elif len(records) >= 2:
        pct = calculate_daily_change_pct(
            _effective_price(latest), _effective_price(records[-2])
        )
        if pct is not None:
            indicators["daily_change_pct"] = round(pct, 4)
        else:
            unavailable.append("daily_change_pct")
    else:
        unavailable.append("daily_change_pct")
        notes.append("Daily % change unavailable: insufficient price history.")

    # Price movement (selected periods)
    for label, period in (("5d", 5), ("20d", 20), ("all", len(records))):
        mv = calculate_price_movement(records, period)
        if mv is not None:
            indicators[f"price_movement_{label}"] = mv
        else:
            unavailable.append(f"price_movement_{label}")

    # Average volume
    avg_vol = calculate_average_volume(records)
    if avg_vol is not None:
        indicators["average_trading_volume"] = round(avg_vol, 2)
    else:
        unavailable.append("average_trading_volume")
        notes.append("Average trading volume unavailable: no volume data.")

    # Volume comparison
    vol_cmp = calculate_volume_comparison(records)
    if vol_cmp is not None:
        indicators["volume_comparison"] = vol_cmp
    else:
        unavailable.append("volume_comparison")
        notes.append("Volume comparison unavailable: insufficient volume history.")

    # Volatility
    vol = calculate_volatility(records)
    if vol is not None:
        indicators["volatility"] = round(vol, 4)
    else:
        unavailable.append("volatility")
        notes.append("Volatility unavailable: insufficient price history (need >= 2 data points).")

    # Note missing trading days (gaps) - best effort informational note
    if len(records) >= 2:
        indicators["records_count"] = len(records)

    return {
        "company_id": company.id,
        "company_ticker": company.ticker,
        "company_name": company.name,
        "records": records,
        "indicators": indicators,
        "unavailable_indicators": sorted(set(unavailable)),
        "data_sources": data_sources,
        "latest_update": latest.recorded_at,
        "notes": notes,
    }
