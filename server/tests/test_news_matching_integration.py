"""Integration tests for updated news/event/matching pipeline."""

from app.models.company import Company
from app.models.event import Event
from app.models.event_company import EventCompany
from app.models.impact_assessment import ImpactAssessment
from app.models.news_article import NewsArticle
from app.services.event_service import EventProcessor
from app.services.impact_assessment_service import generate_assessments_for_company


def test_event_processing_uses_new_matching_rules(db):
    """Event processing must not create weak/incorrect company associations."""
    ptt = Company(ticker="IPTT", name="IPTT Public Company Limited", exchange="SET", market="SET")
    db.add(ptt)
    db.flush()

    article = NewsArticle(
        title="UK civil servants face new pension policy",
        source="Bangkok Post Business",
        url="https://example.com/integration-uk-pension",
        summary="The United Kingdom announced changes to civil servant pensions.",
        content="UK civil servants face new pension policy changes announced by the government in London.",
        thailand_relevance="International",
        relevance_reason="No Thailand references.",
        language="en",
    )
    db.add(article)
    db.flush()

    stats = EventProcessor().process_unprocessed_articles(db)
    assert stats["errors"] == 0, stats

    event = db.query(Event).filter(Event.source_article_id == article.id).first()
    assert event is not None

    mappings = db.query(EventCompany).filter(EventCompany.event_id == event.id).all()
    assert all(m.company_id != ptt.id for m in mappings), [(m.company_id, m.match_confidence) for m in mappings]


def test_event_processing_creates_supported_match(db):
    """Explicit Thai company reference produces a supported, traceable mapping."""
    company = Company(ticker="IPTT2", name="IPTT2 Public Company Limited", exchange="SET", market="SET")
    db.add(company)
    db.flush()

    article = NewsArticle(
        title="IPTT2 Public Company Limited announces earnings in Bangkok",
        source="Bangkok Post Business",
        url="https://example.com/integration-ptt-earnings",
        summary="IPTT2 Public Company Limited reported quarterly profit in Thailand.",
        content="IPTT2 Public Company Limited announced earnings in Bangkok.",
        thailand_relevance="Thailand-focused",
        relevance_reason="Explicit company and Thailand reference.",
        language="en",
    )
    db.add(article)
    db.flush()

    stats = EventProcessor().process_unprocessed_articles(db)
    assert stats["errors"] == 0, stats
    event = db.query(Event).filter(Event.source_article_id == article.id).first()
    assert event is not None

    mappings = db.query(EventCompany).filter(EventCompany.event_id == event.id, EventCompany.company_id == company.id).all()
    assert len(mappings) == 1
    m = mappings[0]
    assert m.match_confidence in ("High", "Medium")
    assert m.match_reason
    assert m.evidence


def test_assessment_generation_handles_no_company_associations(db):
    """Assessment generation for company with no mapped events returns empty (no weak links)."""
    company = Company(ticker="INOMAP", name="No Map Company Limited", exchange="SET", market="SET")
    db.add(company)
    event = Event(title="Unrelated global event", description="No company links.", category="Political", processing_status="processed")
    db.add(event)
    db.flush()

    assessments = generate_assessments_for_company(db, company)
    assert assessments == []
    # existing financial/market-independent behavior: no fabricated assessments
    assert db.query(ImpactAssessment).filter(ImpactAssessment.company_id == company.id).count() == 0
