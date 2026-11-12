"""Event extraction and classification service.

Converts collected news articles into structured Event records using a modular,
replaceable classifier. The default baseline is rule-based (keyword matching),
so the application works without any external AI API key.

Source information is preserved (source_article_id) and automated
interpretations are tagged with classification_method and confidence_score so
they are distinguishable from verified source facts.
"""

import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.news_article import NewsArticle
from app.services.impact_mapping_service import map_event

logger = logging.getLogger(__name__)

# Canonical event categories supported by the platform.
SUPPORTED_CATEGORIES: List[str] = [
    "Economic",
    "Political",
    "Regulatory",
    "Natural Disaster",
    "Geopolitical",
    "Industry Development",
    "Corporate",
    "Energy",
    "Tourism",
    "Technology",
]

DEFAULT_CONFIDENCE = 0.50
UNCERTAIN_CONFIDENCE = 0.30


class EventClassifier(ABC):
    """Interface for event classification methods.

    Implementations convert an article's title/summary into a (category,
    confidence_score) tuple. The service layer is independent of the concrete
    classifier so methods can be swapped (e.g. rule-based now, LLM later).
    """

    @abstractmethod
    def classify(self, title: str, summary: Optional[str]) -> Tuple[str, float]:
        """Return (category, confidence_score) for an article."""


class RuleBasedEventClassifier(EventClassifier):
    """Keyword-based baseline event classifier.

    Matches title and summary text against per-category keyword lists. Returns
    the best matching category with a confidence proportional to match strength,
    or "Uncertain" with low confidence when no category matches.
    """

    KEYWORDS = {
        "Economic": [
            "economy", "economic", "inflation", "interest rate", "gdp",
            "recession", "growth", "fiscal", "budget", "trade",
        ],
        "Political": [
            "election", "government", "minister", "prime minister", "parliament",
            "political", "policy", "senate", "cabinet",
        ],
        "Regulatory": [
            "regulation", "regulator", "law", "legislation", "compliance",
            "rule", "license", "permit", "standard", "directive",
        ],
        "Natural Disaster": [
            "flood", "earthquake", "storm", "typhoon", "drought", "tsunami",
            "wildfire", "landslide", "disaster", "cyclone",
        ],
        "Geopolitical": [
            "war", "conflict", "sanction", "border", "territory", "diplomat",
            "geopolitical", "invasion", "treaty", "alliance",
        ],
        "Industry Development": [
            "industry", "sector", "investment", "factory", "plant", "manufacturing",
            "expansion", "production", "supply chain",
        ],
        "Corporate": [
            "company", "corporate", "ceo", "earnings", "merger", "acquisition",
            "board", "shareholder", "dividend", "subsidiary",
        ],
        "Energy": [
            "oil", "gas", "energy", "power plant", "electricity", "renewable",
            "solar", "wind", "petroleum", "fuel",
        ],
        "Tourism": [
            "tourism", "tourist", "visitor", "hotel", "travel", "airline",
            "resort", "destination", "hospitality",
        ],
        "Technology": [
            "technology", "tech", "digital", "software", "ai", "artificial intelligence",
            "innovation", "startup", "platform", "internet",
        ],
    }

    def classify(self, title: str, summary: Optional[str]) -> Tuple[str, float]:
        text = f"{title} {summary or ''}".lower()
        scores: dict[str, int] = {}
        for category, keywords in self.KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[category] = score

        if not scores:
            return "Uncertain", UNCERTAIN_CONFIDENCE

        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]
        # Confidence scales with match strength, capped.
        confidence = min(0.90, DEFAULT_CONFIDENCE + 0.10 * best_score)
        return best_category, round(confidence, 2)


def _extract_event_date(published_at) -> Optional[datetime]:
    return published_at


def _default_description(title: str, summary: Optional[str]) -> str:
    if summary:
        return summary[:1000]
    return title


class EventProcessor:
    """Processes unprocessed news articles into Event records."""

    def __init__(self, classifier: Optional[EventClassifier] = None):
        self.classifier = classifier or RuleBasedEventClassifier()

    def process_unprocessed_articles(self, db: Session) -> dict:
        """Create events for articles that have no linked event yet.

        Returns stats about processed, skipped, and errored articles.
        """
        stats = {"processed": 0, "skipped": 0, "errors": 0, "events": []}

        articles = (
            db.query(NewsArticle)
            .outerjoin(Event, Event.source_article_id == NewsArticle.id)
            .filter(Event.id.is_(None))
            .all()
        )

        for article in articles:
            try:
                event = self._create_event_for_article(db, article)
                if event is None:
                    stats["skipped"] += 1
                    continue
                db.flush()
                # Map the new event to industries and companies automatically.
                try:
                    map_event(db, event)
                except Exception:  # noqa: BLE001 - mapping must not abort processing
                    logger.exception("Failed to map event %s", event.id)
                stats["processed"] += 1
                stats["events"].append(
                    {
                        "id": event.id,
                        "title": event.title,
                        "category": event.category,
                        "source_article_id": event.source_article_id,
                    }
                )
            except Exception as exc:  # noqa: BLE001 - one article must not abort the batch
                logger.exception(
                    "Failed to process article %s: %s", article.id, exc
                )
                stats["errors"] += 1
                continue

        db.commit()
        return stats

    def _create_event_for_article(
        self, db: Session, article: NewsArticle
    ) -> Optional[Event]:
        category, confidence = self.classifier.classify(article.title, article.summary)

        # Avoid duplicate events for the same underlying article occurrence.
        existing = (
            db.query(Event)
            .filter(Event.source_article_id == article.id)
            .first()
        )
        if existing:
            return None

        event = Event(
            title=article.title[:500],
            description=_default_description(article.title, article.summary),
            category=category,
            location=None,
            event_date=_extract_event_date(article.published_at),
            source_article_id=article.id,
            classification_method="rule_based",
            confidence_score=confidence,
            processing_status="processed",
        )
        db.add(event)
        return event

__all__ = [
    "EventProcessor",
    "EventClassifier",
    "RuleBasedEventClassifier",
    "SUPPORTED_CATEGORIES",
    "process_unprocessed_articles",
]


def process_unprocessed_articles(db: Session) -> dict:
    """Module-level helper that processes unprocessed articles."""
    return EventProcessor().process_unprocessed_articles(db)
