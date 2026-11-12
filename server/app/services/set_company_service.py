"""SET company reference data integration service.

Objective:
- Support importing/synchronizing available SET-listed company information.
- Use official/authorized sources when configured and accessible.
- Never scrape undocumented endpoints or bypass access restrictions.
- Never fabricate records or claim success without verification.

Provider strategy:
1. Official/authorized API provider (if credentials/config are provided and
   endpoint is accessible). Configuration is environment-driven:
   - SET_COMPANY_API_URL: base/endpoint URL for company reference data
   - SET_COMPANY_API_KEY: bearer/API key if required (optional)
   - SET_COMPANY_API_KEY_HEADER: header name for API key (default: Authorization)
   - SET_COMPANY_API_TIMEOUT: request timeout seconds (default: 15)
2. CSV fallback provider using a documented template/path:
   - SET_COMPANY_CSV_PATH (default: server/data/set_companies_template.csv)

CSV template columns (documented):
  ticker,name,market,industry,sector,exchange
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.industry import Industry

logger = logging.getLogger(__name__)

DEFAULT_MARKET = "SET"
DEFAULT_EXCHANGE = "SET"


class SETCompanyProviderError(Exception):
    """Base provider error."""


class SETCompanyAuthError(SETCompanyProviderError):
    """Raised when credentials are invalid/missing for a protected endpoint."""


class SETCompanyProvider:
    """Modular provider for SET-listed company reference data."""

    name = "set_official_api"

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_key_header: Optional[str] = None,
        timeout: int = 15,
    ) -> None:
        self.api_url = (api_url or os.getenv("SET_COMPANY_API_URL") or "").strip()
        self.api_key = (api_key or os.getenv("SET_COMPANY_API_KEY") or "").strip()
        self.api_key_header = (
            api_key_header or os.getenv("SET_COMPANY_API_KEY_HEADER") or "Authorization"
        ).strip()
        self.timeout = int(os.getenv("SET_COMPANY_API_TIMEOUT", str(timeout)) or timeout)

    @property
    def configured(self) -> bool:
        return bool(self.api_url)

    def fetch_companies(self) -> list[dict]:
        """Fetch company records from configured official API.

        Returns a list of raw dicts. Raises SETCompanyProviderError on failure.
        Never fabricates records.
        """
        if not self.api_url:
            raise SETCompanyProviderError(
                "Official SET company API is not configured (SET_COMPANY_API_URL missing)."
            )

        headers = {
            "Accept": "application/json",
            "User-Agent": "AI-Investment-Radar/1.0 (SET company sync)",
        }
        if self.api_key:
            if self.api_key_header.lower() == "authorization" and not self.api_key.lower().startswith("bearer "):
                headers[self.api_key_header] = f"Bearer {self.api_key}"
            else:
                headers[self.api_key_header] = self.api_key

        req = Request(self.api_url, headers=headers)
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                status = getattr(resp, "status", None) or resp.getcode()
                body = resp.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            if exc.code in (401, 403):
                raise SETCompanyAuthError(
                    f"Invalid or unauthorized SET API credentials (HTTP {exc.code})."
                ) from exc
            raise SETCompanyProviderError(
                f"SET company API request failed (HTTP {exc.code})."
            ) from exc
        except (URLError, OSError, TimeoutError) as exc:
            raise SETCompanyProviderError(f"SET company API unreachable: {exc}") from exc

        if status and int(status) >= 400:
            if int(status) in (401, 403):
                raise SETCompanyAuthError(
                    f"Invalid or unauthorized SET API credentials (HTTP {status})."
                )
            raise SETCompanyProviderError(f"SET company API returned HTTP {status}.")

        try:
            payload = json.loads(body)
        except Exception as exc:  # noqa: BLE001
            raise SETCompanyProviderError("SET company API returned non-JSON response.") from exc

        records = _extract_records(payload)
        return records


class SETCompanyCSVProvider:
    """CSV fallback provider using a documented template."""

    name = "csv_fallback"

    def __init__(self, csv_path: Optional[str] = None) -> None:
        default_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data",
            "set_companies_template.csv",
        )
        self.csv_path = (csv_path or os.getenv("SET_COMPANY_CSV_PATH") or default_path).strip()

    def fetch_companies(self) -> list[dict]:
        if not self.csv_path or not os.path.exists(self.csv_path):
            raise SETCompanyProviderError(
                f"CSV fallback unavailable: file not found at '{self.csv_path}'."
            )
        try:
            with open(self.csv_path, "r", encoding="utf-8-sig", newline="") as f:
                content = f.read()
        except Exception as exc:  # noqa: BLE001
            raise SETCompanyProviderError(f"Unable to read CSV fallback: {exc}") from exc

        reader = csv.DictReader(io.StringIO(content))
        return [dict(row) for row in reader]


def _extract_records(payload: Any) -> list[dict]:
    """Best-effort extraction of company records from common JSON shapes."""
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if isinstance(payload, dict):
        for key in ("data", "companies", "results", "items", "securities"):
            val = payload.get(key)
            if isinstance(val, list):
                return [r for r in val if isinstance(r, dict)]
        # single object
        if any(k in payload for k in ("ticker", "symbol", "name")):
            return [payload]
    return []


def normalize_company_record(raw: dict) -> Optional[dict]:
    """Normalize a raw provider record to the app's company fields.

    Required: ticker and name. Missing optional fields are left as None.
    """
    def _pick(*keys: str) -> Optional[str]:
        for k in keys:
            v = raw.get(k)
            if v is None:
                continue
            s = str(v).strip()
            if s:
                return s
        return None

    ticker = _pick("ticker", "symbol", "securitySymbol", "stockSymbol")
    name = _pick("name", "companyName", "securityName", "company_name")
    if not ticker or not name:
        return None

    market = _pick("market", "marketName") or DEFAULT_MARKET
    exchange = _pick("exchange") or market or DEFAULT_EXCHANGE
    industry = _pick("industry", "industryName")
    sector = _pick("sector", "sectorName")

    return {
        "ticker": ticker.upper(),
        "name": name,
        "market": market,
        "exchange": exchange,
        "industry": industry,
        "sector": sector,
    }


def _get_or_create_industry(db: Session, name: Optional[str]) -> Optional[Industry]:
    if not name:
        return None
    existing = db.query(Industry).filter(Industry.name == name).first()
    if existing:
        return existing
    industry = Industry(name=name, description=None)
    db.add(industry)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = db.query(Industry).filter(Industry.name == name).first()
        if existing:
            return existing
        raise
    return industry


def sync_companies(db: Session) -> dict:
    """Synchronize companies using official API with CSV fallback.

    Returns a result dict with counts and errors. Never fabricates records.
    Duplicate prevention uses (ticker, market). Existing companies are updated
    without overwriting unrelated fields with empty values.
    """
    result = {
        "retrieved": 0,
        "imported": 0,
        "updated": 0,
        "duplicates_skipped": 0,
        "errors": [],
        "source": "unknown",
        "used_fallback": False,
        "last_sync_time": None,
        "message": None,
    }

    raw_records: list[dict] = []
    api_provider = SETCompanyProvider()
    csv_provider = SETCompanyCSVProvider()

    # Try official API first when configured.
    if api_provider.configured:
        try:
            raw_records = api_provider.fetch_companies()
            result["source"] = api_provider.name
        except SETCompanyAuthError as exc:
            result["errors"].append(str(exc))
            # Fall back to CSV if available; do not claim API success.
            try:
                raw_records = csv_provider.fetch_companies()
                result["source"] = csv_provider.name
                result["used_fallback"] = True
                result["message"] = "Official API unauthorized; used CSV fallback."
            except SETCompanyProviderError as exc2:
                result["errors"].append(str(exc2))
                result["message"] = "Official API unauthorized and CSV fallback unavailable."
                result["last_sync_time"] = datetime.now(timezone.utc)
                return result
        except SETCompanyProviderError as exc:
            result["errors"].append(str(exc))
            # Fallback to CSV if available
            try:
                raw_records = csv_provider.fetch_companies()
                result["source"] = csv_provider.name
                result["used_fallback"] = True
                result["message"] = "Official API unavailable; used CSV fallback."
            except SETCompanyProviderError as exc2:
                result["errors"].append(str(exc2))
                result["message"] = "Official API unavailable and CSV fallback unavailable."
                result["last_sync_time"] = datetime.now(timezone.utc)
                return result
    else:
        # No official API configured -> try CSV fallback
        try:
            raw_records = csv_provider.fetch_companies()
            result["source"] = csv_provider.name
            result["used_fallback"] = True
            result["message"] = (
                "Official SET API not configured (SET_COMPANY_API_URL unset). "
                "Used documented CSV fallback."
            )
        except SETCompanyProviderError as exc:
            result["errors"].append(str(exc))
            result["message"] = "Official SET API not configured and CSV fallback unavailable."
            result["last_sync_time"] = datetime.now(timezone.utc)
            return result

    if not raw_records:
        result["message"] = (result.get("message") or "") + " No company records retrieved."
        result["last_sync_time"] = datetime.now(timezone.utc)
        return result

    # Normalize and dedupe within payload by (ticker, market)
    normalized: list[dict] = []
    seen_keys: set[tuple[str, str]] = set()
    for raw in raw_records:
        rec = normalize_company_record(raw)
        if not rec:
            result["errors"].append("Skipped record with missing ticker or name.")
            continue
        key = (rec["ticker"], (rec.get("market") or rec.get("exchange") or DEFAULT_MARKET))
        if key in seen_keys:
            result["duplicates_skipped"] += 1
            continue
        seen_keys.add(key)
        normalized.append(rec)

    result["retrieved"] = len(normalized) + result["duplicates_skipped"]

    now = datetime.now(timezone.utc)
    for rec in normalized:
        try:
            ticker = rec["ticker"]
            market = rec.get("market") or rec.get("exchange") or DEFAULT_MARKET
            existing = (
                db.query(Company)
                .filter(Company.ticker == ticker)
                .filter((Company.market == market) | ((Company.market.is_(None)) & (Company.exchange == market)))
                .first()
            )
            industry = _get_or_create_industry(db, rec.get("industry"))

            if existing:
                changed = False
                # Update fields without overwriting unrelated/non-empty existing data with blanks
                if rec.get("name") and rec["name"] != existing.name:
                    existing.name = rec["name"]
                    changed = True
                if rec.get("exchange") and (not existing.exchange or existing.exchange == "SET"):
                    existing.exchange = rec["exchange"]
                    changed = True
                if market and existing.market != market:
                    existing.market = market
                    changed = True
                if rec.get("sector") and rec["sector"] != existing.sector:
                    existing.sector = rec["sector"]
                    changed = True
                if industry and existing.industry_id != industry.id and existing.industry_id is None:
                    existing.industry_id = industry.id
                    changed = True
                # Always record sync metadata/source
                existing.source = result["source"]
                existing.last_synced_at = now
                if changed:
                    result["updated"] += 1
                else:
                    # touched/verified but no material field change
                    result["duplicates_skipped"] += 1
            else:
                company = Company(
                    ticker=ticker,
                    name=rec["name"],
                    exchange=rec.get("exchange") or DEFAULT_EXCHANGE,
                    market=market,
                    sector=rec.get("sector"),
                    industry_id=industry.id if industry else None,
                    description=None,
                    source=result["source"],
                    last_synced_at=now,
                )
                db.add(company)
                db.flush()
                result["imported"] += 1
        except IntegrityError:
            db.rollback()
            result["duplicates_skipped"] += 1
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            logger.exception("Error syncing company record %s", rec.get("ticker"))
            result["errors"].append(f"{rec.get('ticker')}: {exc}")

    try:
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        result["errors"].append(f"Commit failed: {exc}")

    result["last_sync_time"] = now
    # Trim overly verbose error lists
    if len(result["errors"]) > 20:
        extra = len(result["errors"]) - 20
        result["errors"] = result["errors"][:20] + [f"... and {extra} more errors"]
    return result


__all__ = [
    "SETCompanyProvider",
    "SETCompanyCSVProvider",
    "SETCompanyProviderError",
    "SETCompanyAuthError",
    "normalize_company_record",
    "sync_companies",
]
