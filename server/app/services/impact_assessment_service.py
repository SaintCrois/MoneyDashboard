"""AI investment impact assessment service.

Combines event information, event-to-company relationships, industry exposure,
company financial fundamentals, and historical market data to generate
evidence-backed impact assessments.

Baseline engine works without a paid LLM API. An optional LLM provider can be
integrated via environment variables in the future through the modular
interface.

Rules:
- Never fabricate financial metrics, market movements, or evidence.
- Keep source information separate from AI-generated interpretations.
- Include source references and timestamps.
- Clearly indicate incomplete information and uncertainty.
- No guaranteed stock predictions or buy/sell recommendations.
- Assessments are reproducible from recorded inputs and methodology.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.event import Event
from app.models.event_company import EventCompany
from app.models.event_industry import EventIndustry
from app.models.impact_assessment import ImpactAssessment
from app.models.industry import Industry
from app.models.news_article import NewsArticle
from app.services.financial_service import analyze_financials
from app.services.market_service import analyze_market

logger = logging.getLogger(__name__)

IMPACT_DIRECTIONS = ["Positive", "Negative", "Mixed", "Uncertain"]
IMPACT_SEVERITIES = ["Low", "Medium", "High", "Unknown"]
RISK_LEVELS = ["Low", "Medium", "High"]

METHODOLOGY_BASELINE = "baseline_rule_v1"


# ---------------------------------------------------------------------------
# Modular assessment interface
# ---------------------------------------------------------------------------

class AssessmentEngine(ABC):
    """Interface for impact assessment engines."""

    methodology: str = "base"

    @abstractmethod
    def assess(
        self,
        db: Session,
        company: Company,
        event: Event,
        event_company: Optional[EventCompany],
        financial_analysis: dict,
        market_analysis: dict,
    ) -> dict:
        """Return an assessment dict for storage."""


class BaselineAssessmentEngine(AssessmentEngine):
    """Rule-based baseline assessment engine (no external LLM required)."""

    methodology = METHODOLOGY_BASELINE

    def assess(
        self,
        db: Session,
        company: Company,
        event: Event,
        event_company: Optional[EventCompany],
        financial_analysis: dict,
        market_analysis: dict,
    ) -> dict:
        now = datetime.now(timezone.utc)

        # --- Gather evidence ---
        source_article = None
        if event.source_article_id:
            source_article = (
                db.query(NewsArticle)
                .filter(NewsArticle.id == event.source_article_id)
                .first()
            )

        event_industries = (
            db.query(EventIndustry, Industry)
            .join(Industry, Industry.id == EventIndustry.industry_id)
            .filter(EventIndustry.event_id == event.id)
            .all()
        )

        # --- Impact direction (from mapping or default Uncertain) ---
        impact_type = "Uncertain"
        relevance = None
        exposure_type = None
        mapping_explanation = None
        if event_company:
            impact_type = event_company.impact_type or "Uncertain"
            relevance = float(event_company.relevance_score) if event_company.relevance_score is not None else None
            exposure_type = event_company.exposure_type
            mapping_explanation = event_company.explanation
        if impact_type not in IMPACT_DIRECTIONS:
            impact_type = "Uncertain"

        # --- Severity and confidence from evidence completeness ---
        fin_records = financial_analysis.get("records") or []
        mkt_records = market_analysis.get("records") or []
        has_financials = len(fin_records) > 0
        has_market = len(mkt_records) > 0
        has_mapping = event_company is not None

        evidence_count = sum([has_mapping, has_financials, has_market, source_article is not None])
        if not has_mapping and not has_financials and not has_market:
            severity = "Unknown"
            confidence = 0.20
        elif evidence_count >= 4 and relevance and relevance >= 0.7:
            severity = "Medium" if impact_type in ("Positive", "Negative") else "Low"
            confidence = 0.70
        elif evidence_count >= 3:
            severity = "Medium" if impact_type in ("Positive", "Negative") else "Low"
            confidence = 0.55
        elif evidence_count >= 2:
            severity = "Low"
            confidence = 0.40
        else:
            severity = "Unknown"
            confidence = 0.25

        # Risk level heuristic
        risk_level = "Low"
        if severity == "High":
            risk_level = "High"
        elif severity == "Medium":
            risk_level = "Medium"
        elif severity == "Low":
            risk_level = "Low"
        else:
            risk_level = "Medium"  # unknown severity -> cautious medium

        # --- Financial exposure explanation ---
        fin_exposure_parts = []
        if event_company and mapping_explanation:
            fin_exposure_parts.append(
                f"Mapping evidence: {mapping_explanation}"
            )
        if exposure_type:
            fin_exposure_parts.append(f"Exposure type: {exposure_type}.")
        fin_exposure_parts.append(
            f"Event category '{event.category}' may affect {company.name} "
            f"({company.ticker}) operations or revenue sources depending on the "
            f"company's business exposure. This is an evidence-based interpretation, "
            f"not a confirmed outcome."
        )
        if not has_financials:
            fin_exposure_parts.append(
                "No financial records are available to quantify exposure."
            )
        financial_exposure = " ".join(fin_exposure_parts)

        # --- Relevant metrics/indicators summaries ---
        relevant_financial = self._summarize_financial(financial_analysis)
        relevant_market = self._summarize_market(market_analysis)

        # --- Supporting evidence ---
        evidence = []
        evidence.append({
            "type": "event",
            "description": f"Event: {event.title}",
            "category": event.category,
            "event_date": event.event_date.isoformat() if event.event_date else None,
            "timestamp": event.created_at.isoformat() if event.created_at else None,
        })
        if source_article:
            evidence.append({
                "type": "source_article",
                "description": source_article.title,
                "source_name": source_article.source,
                "url": source_article.url,
                "published_at": source_article.published_at.isoformat() if source_article.published_at else None,
            })
        for ei, ind in event_industries:
            evidence.append({
                "type": "industry_exposure",
                "industry": ind.name,
                "impact_type": ei.impact_type,
                "relevance_score": float(ei.relevance_score) if ei.relevance_score is not None else None,
                "explanation": ei.explanation,
            })
        if event_company:
            evidence.append({
                "type": "company_mapping",
                "impact_type": event_company.impact_type,
                "exposure_type": event_company.exposure_type,
                "relevance_score": relevance,
                "explanation": event_company.explanation,
            })
        for src in financial_analysis.get("data_sources", []):
            evidence.append({"type": "financial_data_source", "source": src})
        for src in market_analysis.get("data_sources", []):
            evidence.append({"type": "market_data_source", "source": src})

        # --- Missing information ---
        missing = []
        if not has_financials:
            missing.append("Company financial data is unavailable; financial exposure cannot be quantified.")
        if not has_market:
            missing.append("Market data is unavailable; market reaction cannot be assessed.")
        if not has_mapping:
            missing.append("No direct event-to-company mapping evidence was found.")
        if not source_article:
            missing.append("No linked source article; event evidence is limited to stored event fields.")
        missing.extend(financial_analysis.get("notes", []))
        missing.extend(market_analysis.get("notes", []))
        # Deduplicate while preserving order
        seen = set()
        missing_unique = []
        for m in missing:
            if m not in seen:
                seen.add(m)
                missing_unique.append(m)

        # --- Explanation (structured, evidence-backed, uncertainty explicit) ---
        explanation = self._build_explanation(
            company=company,
            event=event,
            impact_type=impact_type,
            severity=severity,
            confidence=confidence,
            has_financials=has_financials,
            has_market=has_market,
            relevant_financial=relevant_financial,
            relevant_market=relevant_market,
            missing=missing_unique,
            source_article=source_article,
        )

        # --- Input snapshot for reproducibility ---
        input_snapshot = {
            "methodology": self.methodology,
            "assessed_at": now.isoformat(),
            "company_id": company.id,
            "company_ticker": company.ticker,
            "event_id": event.id,
            "event_category": event.category,
            "event_title": event.title,
            "event_company_mapping": {
                "impact_type": event_company.impact_type if event_company else None,
                "exposure_type": event_company.exposure_type if event_company else None,
                "relevance_score": relevance,
            } if event_company else None,
            "financial_records_count": len(fin_records),
            "market_records_count": len(mkt_records),
            "financial_latest_period": financial_analysis.get("latest_period"),
            "market_latest_update": (
                market_analysis.get("latest_update").isoformat()
                if market_analysis.get("latest_update") else None
            ),
        }

        return {
            "event_id": event.id,
            "company_id": company.id,
            "impact_type": impact_type,
            "impact_severity": severity,
            "risk_level": risk_level,
            "confidence": round(confidence, 2),
            "explanation": explanation,
            "financial_exposure": financial_exposure,
            "relevant_financial_metrics": json.dumps(relevant_financial, default=str),
            "relevant_market_indicators": json.dumps(relevant_market, default=str),
            "supporting_evidence": json.dumps(evidence, default=str),
            "missing_information": json.dumps(missing_unique, default=str),
            "methodology": self.methodology,
            "input_snapshot": json.dumps(input_snapshot, default=str),
            "assessed_at": now,
        }

    def _summarize_financial(self, analysis: dict) -> dict:
        records = analysis.get("records") or []
        if not records:
            return {"available": False, "note": "No financial data available."}
        latest = records[-1]
        metrics = analysis.get("calculated_metrics") or []
        latest_calc = metrics[-1] if metrics else {}
        return {
            "available": True,
            "latest_period": analysis.get("latest_period"),
            "reported": {
                "revenue": float(latest.revenue) if latest.revenue is not None else None,
                "net_profit": float(latest.net_profit) if latest.net_profit is not None else None,
                "operating_income": float(latest.operating_income) if latest.operating_income is not None else None,
                "total_debt": float(latest.total_debt) if latest.total_debt is not None else None,
                "shareholders_equity": float(latest.shareholders_equity) if latest.shareholders_equity is not None else None,
            },
            "calculated": latest_calc.get("calculated", {}),
            "unavailable": latest_calc.get("unavailable", []),
            "data_sources": analysis.get("data_sources", []),
        }

    def _summarize_market(self, analysis: dict) -> dict:
        indicators = analysis.get("indicators") or {}
        if not indicators:
            return {"available": False, "note": "No market data available."}
        summary = {
            "available": True,
            "latest_update": indicators.get("latest_recorded_at"),
            "latest_price": indicators.get("latest_price"),
            "latest_volume": indicators.get("latest_volume"),
            "daily_change_pct": indicators.get("daily_change_pct"),
            "average_trading_volume": indicators.get("average_trading_volume"),
            "volatility": indicators.get("volatility"),
            "is_delayed": indicators.get("latest_is_delayed"),
            "is_estimate": indicators.get("latest_is_estimate"),
            "data_sources": analysis.get("data_sources", []),
        }
        if "volume_comparison" in indicators:
            summary["volume_comparison"] = indicators["volume_comparison"]
        for key in ("price_movement_5d", "price_movement_20d", "price_movement_all"):
            if key in indicators:
                summary[key] = indicators[key]
        return summary

    def _build_explanation(
        self, company, event, impact_type, severity, confidence,
        has_financials, has_market, relevant_financial, relevant_market,
        missing, source_article,
    ) -> str:
        lines = []
        lines.append(f"1. What happened: {event.title} (category: {event.category}).")
        if event.description:
            lines.append(f"   Event description (source-derived): {event.description[:400]}")
        lines.append(
            f"2. Why this could affect {company.name} ({company.ticker}): "
            f"The event is mapped to the company/industry context with potential impact "
            f"direction '{impact_type}'. This is an interpretation based on available "
            f"evidence, not a confirmed outcome."
        )
        lines.append(
            "3. Potentially affected operations/revenue sources: "
            "Dependent on the company's business exposure to the event's domain; "
            "specific segment-level exposure requires additional company disclosures."
        )
        if has_financials and relevant_financial.get("available"):
            calc = relevant_financial.get("calculated", {})
            fin_bits = []
            for k in ("revenue_growth", "net_profit_margin", "debt_to_equity", "free_cash_flow", "roe"):
                if calc.get(k) is not None:
                    fin_bits.append(f"{k}={calc[k]}")
            lines.append(
                "4. Relevant financial information (reported/calculated from stored data): "
                + (", ".join(fin_bits) if fin_bits else "available but limited calculated metrics.")
            )
        else:
            lines.append("4. Relevant financial information: unavailable (no stored financial records).")

        if has_market and relevant_market.get("available"):
            mkt_bits = []
            for k in ("latest_price", "daily_change_pct", "average_trading_volume", "volatility"):
                if relevant_market.get(k) is not None:
                    mkt_bits.append(f"{k}={relevant_market[k]}")
            lines.append(
                "5. Relevant market information (observed from stored data): "
                + (", ".join(mkt_bits) if mkt_bits else "available but limited indicators.")
            )
        else:
            lines.append("5. Relevant market information: unavailable (no stored market records).")

        lines.append(
            "6. Factors that could weaken or reverse the expected impact: "
            "company-specific mitigations, offsetting business segments, timing/duration "
            "of the event, policy responses, and broader market conditions."
        )
        lines.append(
            "7. Missing information and limitations: "
            + ("; ".join(missing) if missing else "No major gaps identified in stored inputs.")
        )
        lines.append(
            f"Assessment: impact_direction={impact_type}, severity={severity}, "
            f"confidence={confidence:.2f} (methodology={self.methodology}). "
            "This is research support, not a guaranteed prediction or buy/sell recommendation."
        )
        if source_article:
            lines.append(
                f"Source reference: {source_article.source} - {source_article.url} "
                f"(published: {source_article.published_at.isoformat() if source_article.published_at else 'unknown'})."
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

_default_engine = BaselineAssessmentEngine()


def generate_assessment(
    db: Session,
    company: Company,
    event: Event,
    engine: Optional[AssessmentEngine] = None,
) -> ImpactAssessment:
    """Generate and store an impact assessment for a company-event pair."""
    if engine is None:
        engine = _default_engine

    event_company = (
        db.query(EventCompany)
        .filter(
            EventCompany.company_id == company.id,
            EventCompany.event_id == event.id,
        )
        .first()
    )

    financial_analysis = analyze_financials(db, company)
    market_analysis = analyze_market(db, company)

    data = engine.assess(db, company, event, event_company, financial_analysis, market_analysis)

    assessment = ImpactAssessment(**data)
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def generate_assessments_for_company(
    db: Session, company: Company, event_id: Optional[int] = None
) -> list[ImpactAssessment]:
    """Generate assessments for a company.

    If event_id is provided, assess that specific event (must be mapped or exist).
    Otherwise, assess all events mapped to the company; if none mapped, return empty.
    """
    if event_id is not None:
        event = db.query(Event).filter(Event.id == event_id).first()
        if event is None:
            return []
        return [generate_assessment(db, company, event)]

    # Events mapped to this company
    mappings = (
        db.query(EventCompany)
        .filter(EventCompany.company_id == company.id)
        .all()
    )
    assessments = []
    for m in mappings:
        event = db.query(Event).filter(Event.id == m.event_id).first()
        if event:
            assessments.append(generate_assessment(db, company, event))
    return assessments


def list_assessments(
    db: Session,
    company_id: Optional[int] = None,
    event_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[ImpactAssessment]:
    query = db.query(ImpactAssessment)
    if company_id is not None:
        query = query.filter(ImpactAssessment.company_id == company_id)
    if event_id is not None:
        query = query.filter(ImpactAssessment.event_id == event_id)
    return query.order_by(ImpactAssessment.created_at.desc()).offset(skip).limit(limit).all()


def get_assessment(db: Session, assessment_id: int) -> Optional[ImpactAssessment]:
    return db.query(ImpactAssessment).filter(ImpactAssessment.id == assessment_id).first()
