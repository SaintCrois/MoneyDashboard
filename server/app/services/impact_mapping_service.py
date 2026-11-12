"""Event-to-industry and event-to-company impact mapping service.

Maps events to potentially affected industries and companies using keyword
matching against industry names, company names, and tickers found in the event
title and description. Every mapping is evidence-based: when the connection is
uncertain it is labelled ``Uncertain`` rather than presented as fact.

Mappings store impact_direction, relevance_score, and an explanation. The
source article remains reachable through the linked event.
"""

import logging
import re
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.event import Event
from app.models.event_company import EventCompany
from app.models.event_industry import EventIndustry
from app.models.industry import Industry

logger = logging.getLogger(__name__)

VALID_IMPACT_DIRECTIONS = ["Positive", "Negative", "Mixed", "Uncertain"]
DEFAULT_IMPACT_DIRECTION = "Uncertain"


def _tokenize(text: Optional[str]) -> List[str]:
    if not text:
        return []
    return re.findall(r"[a-z0-9]+", text.lower())


def _match_score(tokens: List[str], keywords: List[str]) -> int:
    return sum(1 for kw in keywords if kw in tokens)


class ImpactMappingService:
    """Maps events to industries and companies based on keyword evidence."""

    def map_event(self, db: Session, event: Event) -> dict:
        """Create industry and company mappings for a single event.

        Returns a dict with the created/updated mappings. Existing mappings for
        the same event are left untouched (idempotent).
        """
        result = {
            "event_id": event.id,
            "industries": [],
            "companies": [],
        }

        text = f"{event.title} {event.description or ''}"
        tokens = _tokenize(text)

        # --- Map to industries ---
        industries = db.query(Industry).all()
        for industry in industries:
            industry_keywords = _tokenize(industry.name)
            if industry.description:
                industry_keywords += _tokenize(industry.description)
            score = _match_score(tokens, industry_keywords)
            if score == 0:
                continue
            existing = (
                db.query(EventIndustry)
                .filter(
                    EventIndustry.event_id == event.id,
                    EventIndustry.industry_id == industry.id,
                )
                .first()
            )
            if existing:
                continue
            mapping = EventIndustry(
                event_id=event.id,
                industry_id=industry.id,
                impact_type=DEFAULT_IMPACT_DIRECTION,
                relevance_score=round(min(0.99, 0.4 + 0.15 * score), 2),
                explanation=(
                    f"Event mentions terms related to the '{industry.name}' "
                    f"industry (keyword match score {score}). Impact direction "
                    f"is not determined from the article alone."
                ),
            )
            db.add(mapping)
            db.flush()
            result["industries"].append(
                {
                    "id": mapping.id,
                    "industry_id": industry.id,
                    "industry_name": industry.name,
                    "impact_type": mapping.impact_type,
                    "relevance_score": mapping.relevance_score,
                    "explanation": mapping.explanation,
                }
            )

        # --- Map to companies ---
        companies = db.query(Company).all()
        for company in companies:
            company_keywords = _tokenize(company.name) + [
                kw.lower() for kw in (company.ticker or "").split()
            ]
            score = _match_score(tokens, company_keywords)
            if score == 0:
                continue
            existing = (
                db.query(EventCompany)
                .filter(
                    EventCompany.event_id == event.id,
                    EventCompany.company_id == company.id,
                )
                .first()
            )
            if existing:
                continue
            mapping = EventCompany(
                event_id=event.id,
                company_id=company.id,
                impact_type=DEFAULT_IMPACT_DIRECTION,
                exposure_type="Indirect",
                relevance_score=round(min(0.99, 0.4 + 0.15 * score), 2),
                explanation=(
                    f"Event mentions terms related to {company.name} "
                    f"({company.ticker}) (keyword match score {score}). "
                    f"Impact direction and exposure are not determined from "
                    f"the article alone."
                ),
            )
            db.add(mapping)
            db.flush()
            result["companies"].append(
                {
                    "id": mapping.id,
                    "company_id": company.id,
                    "company_name": company.name,
                    "ticker": company.ticker,
                    "impact_type": mapping.impact_type,
                    "exposure_type": mapping.exposure_type,
                    "relevance_score": mapping.relevance_score,
                    "explanation": mapping.explanation,
                }
            )

        db.commit()
        return result

    def map_all_unmapped_events(self, db: Session) -> dict:
        """Map all events that currently have no industry/company mappings."""
        stats = {
            "events_mapped": 0,
            "industry_mappings": 0,
            "company_mappings": 0,
        }

        events = db.query(Event).all()
        for event in events:
            already_has_industry = (
                db.query(EventIndustry)
                .filter(EventIndustry.event_id == event.id)
                .first()
            )
            already_has_company = (
                db.query(EventCompany)
                .filter(EventCompany.event_id == event.id)
                .first()
            )
            if already_has_industry and already_has_company:
                continue
            result = self.map_event(db, event)
            stats["events_mapped"] += 1
            stats["industry_mappings"] += len(result["industries"])
            stats["company_mappings"] += len(result["companies"])

        return stats

__all__ = [
    "ImpactMappingService",
    "map_event",
    "VALID_IMPACT_DIRECTIONS",
    "DEFAULT_IMPACT_DIRECTION",
]


def map_event(db: Session, event: Event) -> dict:
    """Module-level helper to map a single event."""
    return ImpactMappingService().map_event(db, event)


def map_all_unmapped_events(db: Session) -> dict:
    """Module-level helper to map all unmapped events."""
    return ImpactMappingService().map_all_unmapped_events(db)
