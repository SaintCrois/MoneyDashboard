"""Event-to-industry and event-to-company mapping service tests.

Database changes are rolled back after each test via the ``db`` fixture, so
the development database is never modified. Mappings are evidence-based and
labelled Uncertain when the connection cannot be determined from the article.
"""

from app.models.company import Company
from app.models.event import Event
from app.models.industry import Industry
from app.services.impact_mapping_service import (
    ImpactMappingService,
    map_event,
    VALID_IMPACT_DIRECTIONS,
    DEFAULT_IMPACT_DIRECTION,
)


def test_valid_impact_directions():
    """Allowed impact directions match the platform contract."""
    assert "Positive" in VALID_IMPACT_DIRECTIONS
    assert "Negative" in VALID_IMPACT_DIRECTIONS
    assert "Mixed" in VALID_IMPACT_DIRECTIONS
    assert "Uncertain" in VALID_IMPACT_DIRECTIONS


def test_default_impact_direction_uncertain():
    """Uncertain connections are labelled Uncertain, not presented as fact."""
    assert DEFAULT_IMPACT_DIRECTION == "Uncertain"


def test_map_event_creates_industry_mapping(db):
    """An event mentioning an industry name maps to that industry."""
    industry_name = "Map Test Alpha Industry"
    event_title = "Map Test Alpha Event"
    industry = Industry(name=industry_name, description="Test industry")
    db.add(industry)
    db.flush()

    event = Event(
        title=event_title,
        description=f"News about {industry_name} sector development today.",
        category="Industry Development",
        source_article_id=None,
    )
    db.add(event)
    db.flush()

    result = map_event(db, event)

    assert len(result["industries"]) >= 1, result
    custom = next(
        (m for m in result["industries"] if m["industry_id"] == industry.id),
        None,
    )
    assert custom is not None, result
    assert custom["impact_type"] == "Uncertain"
    assert custom["relevance_score"] is not None


def test_map_event_creates_company_mapping(db):
    """An event mentioning a company name/ticker maps to that company."""
    company_ticker = "MTST"
    company_name = "Map Test Company Limited"
    event_title = "Map Test Company Event"
    company = Company(
        ticker=company_ticker,
        name=company_name,
        exchange="SET",
    )
    db.add(company)
    db.flush()

    event = Event(
        title=event_title,
        description=f"News about {company_name} ({company_ticker}) today.",
        category="Corporate",
        source_article_id=None,
    )
    db.add(event)
    db.flush()

    result = map_event(db, event)

    custom = next(
        (m for m in result["companies"] if m["company_id"] == company.id),
        None,
    )
    assert custom is not None, result
    assert custom["impact_type"] == "Uncertain"
    assert custom["exposure_type"] == "Indirect"
    assert custom["relevance_score"] is not None


def test_map_event_idempotent(db):
    """Re-mapping an event does not create duplicate mappings."""
    industry_name = "Map Test Idempotent Industry"
    event_title = "Map Test Idempotent Event"
    industry = Industry(name=industry_name, description="Test")
    db.add(industry)
    db.flush()

    event = Event(
        title=event_title,
        description=f"News about the {industry_name} sector.",
        category="Industry Development",
        source_article_id=None,
    )
    db.add(event)
    db.flush()

    first = map_event(db, event)
    second = map_event(db, event)

    assert len(first["industries"]) == 1, first
    assert len(second["industries"]) == 0, second  # no new mappings


def test_map_event_no_match_returns_empty(db):
    """An event mentioning no industry or company returns no mappings."""
    event_title = "Map Test No Match Event"
    event = Event(
        title=event_title,
        description="Local bakery opens a new shop.",
        category="Corporate",
        source_article_id=None,
    )
    db.add(event)
    db.flush()

    result = map_event(db, event)

    assert result["industries"] == []
    assert result["companies"] == []
