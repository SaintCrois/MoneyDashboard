"""Event-to-industry and event-to-company mapping service tests.

Database changes are rolled back after each test via the ``db`` fixture, so
the development database is never modified. Mappings are evidence-based and
labelled Uncertain when the connection cannot be determined from the article.
"""

from app.models.company import Company
from app.models.event import Event
from app.models.industry import Industry
from app.models.news_article import NewsArticle
from app.services.impact_mapping_service import (
    DEFAULT_IMPACT_DIRECTION,
    VALID_IMPACT_DIRECTIONS,
    evaluate_company_match,
    map_event,
)


def _get_or_create_company(db, ticker, name, market="SET"):
    company = (
        db.query(Company)
        .filter(Company.ticker == ticker)
        .filter((Company.market == market) | ((Company.market.is_(None)) & (Company.exchange == market)))
        .first()
    )
    if company:
        return company
    company = Company(ticker=ticker, name=name, exchange=market, market=market)
    db.add(company)
    db.flush()
    return company



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
    industry = Industry(name="Map Test Alpha Industry", description="Test industry")
    db.add(industry)
    db.flush()

    event = Event(
        title="Map Test Alpha Event",
        description="News about Map Test Alpha Industry sector development today.",
        category="Industry Development",
    )
    db.add(event)
    db.flush()

    result = map_event(db, event)

    assert len(result["industries"]) >= 1, result
    custom = next((m for m in result["industries"] if m["industry_id"] == industry.id), None)
    assert custom is not None, result
    assert custom["impact_type"] == "Uncertain"
    assert custom["relevance_score"] is not None


def test_map_event_creates_company_mapping_with_evidence(db):
    """An event explicitly mentioning a company name maps with high confidence."""
    company = Company(ticker="MTST", name="Map Test Company Limited", exchange="SET", market="SET")
    db.add(company)
    db.flush()

    event = Event(
        title="Map Test Company Limited announces expansion",
        description="Map Test Company Limited announced a new project in Thailand.",
        category="Corporate",
    )
    db.add(event)
    db.flush()

    result = map_event(db, event)

    custom = next((m for m in result["companies"] if m["company_id"] == company.id), None)
    assert custom is not None, result
    assert custom["impact_type"] == "Uncertain"
    assert custom["exposure_type"] == "Direct"
    assert custom["match_confidence"] == "High"
    assert "Explicit company name" in (custom.get("match_reason") or "")


def test_map_event_idempotent(db):
    """Re-mapping an event does not create duplicate mappings."""
    industry = Industry(name="Map Test Idempotent Industry", description="Test")
    db.add(industry)
    db.flush()
    company = Company(ticker="MIDP", name="Map Idempotent Company Limited", exchange="SET", market="SET")
    db.add(company)
    db.flush()

    event = Event(
        title="Map Idempotent Company Limited sector update",
        description="News about the Map Test Idempotent Industry sector.",
        category="Industry Development",
    )
    db.add(event)
    db.flush()

    first = map_event(db, event)
    second = map_event(db, event)

    assert len(first["industries"]) == 1, first
    assert len(first["companies"]) == 1, first
    assert len(second["industries"]) == 0, second
    assert len(second["companies"]) == 0, second


def test_map_event_no_match_returns_empty(db):
    """An event mentioning no industry or company returns no mappings."""
    event = Event(
        title="Local bakery opens a new shop",
        description="A neighborhood bakery opened downtown.",
        category="Corporate",
    )
    db.add(event)
    db.flush()

    result = map_event(db, event)

    assert result["industries"] == []
    assert result["companies"] == []


# --- Company matching rule tests (critical) ---

def test_exact_company_name_match(db):
    company = Company(ticker="XEX1", name="XExact Test Company Limited", exchange="SET", market="SET")
    db.add(company)
    db.flush()
    match = evaluate_company_match(company, "XExact Test Company Limited announces earnings.")
    assert match.confidence == "High"
    assert match.evidence


def test_verified_alias_match(db):
    company = Company(ticker="XAL1", name="XAlias Test Company Limited", exchange="SET", market="SET")
    db.add(company)
    db.flush()
    match = evaluate_company_match(company, "XAlias Test Company announces a new investment in Thailand's energy infrastructure.")
    assert match.confidence == "High"


def test_valid_ticker_with_context_is_medium(db):
    company = Company(ticker="XTK1", name="XTick Test Company Limited", exchange="SET", market="SET")
    db.add(company)
    db.flush()
    text = "SET-listed XTK1 shares rose after the company reported strong profit."
    match = evaluate_company_match(company, text)
    assert match.confidence == "Medium"


def test_ambiguous_acronym_ticker_without_context_not_matched(db):
    company = Company(ticker="XAM1", name="XAmbig Test Company Limited", exchange="SET", market="SET")
    db.add(company)
    db.flush()
    text = "Officials discussed an XAM1 framework in a foreign policy meeting."
    match = evaluate_company_match(company, text)
    assert match.confidence == "Low"


def test_industry_only_mention_does_not_match_company(db):
    company = Company(ticker="XID1", name="XIndustry Test Company Limited", exchange="SET", market="SET")
    db.add(company)
    db.flush()
    text = "Global oil and gas prices rose, affecting the energy sector outlook."
    match = evaluate_company_match(company, text)
    assert match.confidence == "Low"
    event = Event(title="Oil prices rise", description=text, category="Energy")
    db.add(event)
    db.flush()
    result = map_event(db, event)
    assert all(m["company_id"] != company.id for m in result["companies"])


def test_foreign_organization_similar_name_not_matched(db):
    company = _get_or_create_company(db, "PTT", "PTT Public Company Limited")
    text = "PTT Global Chemical Europe announced restructuring in Rotterdam."
    event = Event(title="Foreign PTTGC Europe restructuring", description=text, category="Corporate")
    db.add(event)
    db.flush()
    result = map_event(db, event)
    assert all(m["company_id"] != company.id for m in result["companies"]), result


def test_article_mentioning_no_relevant_company(db):
    company = Company(ticker="XNR1", name="XNoRel Test Company Limited", exchange="SET", market="SET")
    db.add(company)
    db.flush()
    event = Event(
        title="Tourism arrivals increase in Phuket",
        description="Thailand sees higher tourist arrivals this quarter.",
        category="Tourism",
    )
    db.add(event)
    db.flush()
    result = map_event(db, event)
    assert result["companies"] == []


def test_ptt_uk_civil_servant_regression(db):
    """Regression: unrelated UK civil servant article must NOT associate PTT/PTTEP."""
    ptt = _get_or_create_company(db, "PTT", "PTT Public Company Limited")
    pttep = _get_or_create_company(db, "PTTEP", "PTT Exploration and Production Public Company Limited")
    aot = _get_or_create_company(db, "AOT", "Airports of Thailand Public Company Limited")

    article = NewsArticle(
        title="UK civil servants face new pension policy",
        source="Bangkok Post Business",
        url="https://example.com/uk-civil-servants-pension",
        summary="The United Kingdom announced changes to civil servant pensions.",
        content="UK civil servants face new pension policy changes announced by the government in London.",
    )
    db.add(article)
    db.flush()

    event = Event(
        title=article.title,
        description=article.summary or article.title,
        category="Political",
        source_article_id=article.id,
    )
    db.add(event)
    db.flush()

    result = map_event(db, event)
    matched_ids = {m["company_id"] for m in result["companies"]}
    assert ptt.id not in matched_ids, result
    assert pttep.id not in matched_ids, result
    assert aot.id not in matched_ids, result


def test_low_confidence_matches_not_persisted(db):
    """Low-confidence/ambiguous matches must remain unassigned."""
    company = _get_or_create_company(db, "PTT", "PTT Public Company Limited")
    event = Event(
        title="New PTT framework discussed abroad",
        description="An unrelated PTT framework was mentioned without company context.",
        category="Political",
    )
    db.add(event)
    db.flush()
    result = map_event(db, event)
    assert all(m["company_id"] != company.id for m in result["companies"])

