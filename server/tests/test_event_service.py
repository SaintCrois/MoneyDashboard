"""Event processing service tests.

Database changes are rolled back after each test via the ``db`` fixture, so
the development database is never modified. No external services or API keys
are required.
"""

from datetime import datetime, timezone

from app.models.event import Event
from app.models.news_article import NewsArticle
from app.services.event_service import (
    EventProcessor,
    RuleBasedEventClassifier,
    SUPPORTED_CATEGORIES,
)


def test_supported_categories_nonempty():
    """The platform supports a defined set of event categories."""
    assert isinstance(SUPPORTED_CATEGORIES, list)
    assert len(SUPPORTED_CATEGORIES) > 0
    assert "Energy" in SUPPORTED_CATEGORIES


def test_rule_based_classifier_energy():
    """Keyword matching classifies energy-related articles."""
    clf = RuleBasedEventClassifier()
    category, confidence = clf.classify("Oil prices rise amid Middle East tension", None)
    assert category == "Energy"
    assert 0.0 < confidence <= 1.0


def test_rule_based_classifier_uncertain():
    """Unrelated articles are classified as Uncertain with low confidence."""
    clf = RuleBasedEventClassifier()
    category, confidence = clf.classify("Local bakery opens new shop", None)
    assert category == "Uncertain"
    assert confidence <= 0.5


def test_process_unprocessed_articles_creates_events(db):
    """Processing creates events from articles without linked events."""
    article_url = "https://example.com/event-test-unique"
    event_title = "Event Test Unique Article"
    article = NewsArticle(
        title=event_title,
        source="Test Source",
        url=article_url,
        summary="Crude oil prices increased as tensions escalated.",
        content="Crude oil prices increased as tensions escalated.",
        published_at=datetime.now(timezone.utc),
        fetched_at=datetime.now(timezone.utc),
    )
    db.add(article)
    db.flush()

    stats = EventProcessor().process_unprocessed_articles(db)

    assert stats["processed"] == 1, stats
    assert stats["errors"] == 0, stats
    event = db.query(Event).filter(Event.source_article_id == article.id).first()
    assert event is not None
    assert event.title == event_title
    assert event.category in SUPPORTED_CATEGORIES


def test_process_unprocessed_articles_prevents_duplicates(db):
    """Re-processing does not create duplicate events for the same article."""
    article_url = "https://example.com/event-dup-unique"
    event_title = "Event Dup Unique Article"
    article = NewsArticle(
        title=event_title,
        source="Test Source",
        url=article_url,
        summary="Crude oil prices increased.",
        content="Crude oil prices increased.",
        fetched_at=datetime.now(timezone.utc),
    )
    db.add(article)
    db.flush()

    first = EventProcessor().process_unprocessed_articles(db)
    assert first["processed"] == 1, first

    second = EventProcessor().process_unprocessed_articles(db)
    assert second["processed"] == 0, second
    assert second["errors"] == 0, second
