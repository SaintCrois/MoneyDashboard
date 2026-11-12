"""Impact assessment service tests.

Uses the isolated ``db`` fixture (transaction rolled back per test).
"""

import json
from datetime import datetime, timezone

from app.models.company import Company
from app.models.event import Event
from app.models.event_company import EventCompany
from app.models.financial_data import FinancialData
from app.models.industry import Industry
from app.models.market_data import MarketData
from app.models.news_article import NewsArticle
from app.services.impact_assessment_service import (
    METHODOLOGY_BASELINE,
    BaselineAssessmentEngine,
    generate_assessment,
    generate_assessments_for_company,
    get_assessment,
    list_assessments,
)


def _setup_company_event(db, ticker="ASC1"):
    industry = Industry(name=f"IndA-{ticker}", description="test")
    db.add(industry)
    db.flush()
    company = Company(name=f"Co {ticker}", ticker=ticker, industry_id=industry.id)
    db.add(company)
    db.flush()
    article = NewsArticle(
        title=f"Article {ticker}",
        source="Test",
        url=f"https://example.com/{ticker}",
        summary="Energy policy update.",
        content="Energy policy update.",
    )
    db.add(article)
    db.flush()
    event = Event(
        title=f"Energy event {ticker}",
        description="Policy change affects energy sector.",
        category="Energy",
        event_date=datetime(2026, 11, 12, tzinfo=timezone.utc),
        source_article_id=article.id,
        classification_method="rule_based",
        confidence_score=0.8,
        processing_status="processed",
    )
    db.add(event)
    db.flush()
    mapping = EventCompany(
        event_id=event.id,
        company_id=company.id,
        impact_type="Positive",
        relevance_score=0.8,
        exposure_type="Direct",
        explanation="Direct energy exposure.",
    )
    db.add(mapping)
    db.flush()
    return company, event, article


def test_baseline_engine_generates_evidence_backed_assessment(db):
    company, event, _ = _setup_company_event(db, ticker="ASC2")
    # add financial and market data
    db.add(FinancialData(
        company_id=company.id, fiscal_year=2024, revenue=1000, net_profit=100,
        total_debt=200, shareholders_equity=400, data_source="manual",
    ))
    db.add(MarketData(
        company_id=company.id, recorded_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
        close_price=100, trading_volume=1000, data_source="manual",
    ))
    db.add(MarketData(
        company_id=company.id, recorded_at=datetime(2026, 11, 2, tzinfo=timezone.utc),
        close_price=105, trading_volume=1200, data_source="manual",
    ))
    db.flush()

    assessment = generate_assessment(db, company, event)
    assert assessment.id is not None
    assert assessment.event_id == event.id
    assert assessment.company_id == company.id
    assert assessment.impact_type == "Positive"
    assert assessment.methodology == METHODOLOGY_BASELINE
    assert assessment.confidence is not None
    assert assessment.explanation is not None
    assert "research support" in assessment.explanation.lower() or "not a guaranteed" in assessment.explanation.lower()

    evidence = json.loads(assessment.supporting_evidence)
    types = {e.get("type") for e in evidence}
    assert "event" in types
    assert "source_article" in types
    assert "company_mapping" in types

    snapshot = json.loads(assessment.input_snapshot)
    assert snapshot["company_id"] == company.id
    assert snapshot["event_id"] == event.id


def test_assessment_handles_missing_data_with_uncertainty(db):
    company, event, _ = _setup_company_event(db, ticker="ASC3")
    # no financial or market data
    assessment = generate_assessment(db, company, event)
    assert assessment.impact_type == "Positive"  # from mapping
    missing = json.loads(assessment.missing_information)
    assert any("financial" in m.lower() for m in missing)
    assert any("market" in m.lower() for m in missing)
    # confidence should be limited due to missing data
    assert float(assessment.confidence) <= 0.7


def test_assessment_without_mapping_is_uncertain(db):
    industry = Industry(name="IndA-ASC4", description="test")
    db.add(industry)
    db.flush()
    company = Company(name="Co ASC4", ticker="ASC4", industry_id=industry.id)
    db.add(company)
    event = Event(title="Unmapped event", description="desc", category="Other", processing_status="processed")
    db.add(event)
    db.flush()

    assessment = generate_assessment(db, company, event)
    assert assessment.impact_type == "Uncertain"
    missing = json.loads(assessment.missing_information)
    assert any("mapping" in m.lower() for m in missing)


def test_generate_assessments_for_company_mapped_only(db):
    company, event, _ = _setup_company_event(db, ticker="ASC5")
    # unmapped event should not be included in company-wide generation
    other = Event(title="Other", description="x", category="Other", processing_status="processed")
    db.add(other)
    db.flush()

    assessments = generate_assessments_for_company(db, company)
    assert len(assessments) == 1
    assert assessments[0].event_id == event.id


def test_generate_assessments_for_specific_event(db):
    company, event, _ = _setup_company_event(db, ticker="ASC6")
    other = Event(title="Other2", description="x", category="Other", processing_status="processed")
    db.add(other)
    db.flush()
    assessments = generate_assessments_for_company(db, company, event_id=other.id)
    assert len(assessments) == 1
    assert assessments[0].event_id == other.id


def test_list_and_get_assessment(db):
    company, event, _ = _setup_company_event(db, ticker="ASC7")
    a = generate_assessment(db, company, event)
    assert get_assessment(db, a.id).id == a.id
    listed = list_assessments(db, company_id=company.id)
    assert any(x.id == a.id for x in listed)
    listed_e = list_assessments(db, event_id=event.id)
    assert any(x.id == a.id for x in listed_e)
