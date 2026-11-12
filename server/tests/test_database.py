"""Database tests for Sprint 1.

Tests run against the configured development database using unique test data
that is cleaned up after each test. No destructive operations are performed.
"""

from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal, engine
from app.models.company import Company
from app.models.event import Event
from app.models.event_company import EventCompany
from app.models.event_industry import EventIndustry
from app.models.financial_data import FinancialData
from app.models.impact_assessment import ImpactAssessment
from app.models.industry import Industry
from app.models.market_data import MarketData
from app.models.news_article import NewsArticle

EXPECTED_TABLES = {
    "news_articles",
    "events",
    "industries",
    "companies",
    "event_industries",
    "event_companies",
    "financial_data",
    "market_data",
    "impact_assessments",
}


def _db():
    return SessionLocal()


def test_database_connection():
    """The backend can connect to PostgreSQL and run a query."""
    db = _db()
    try:
        result = db.execute(text("SELECT version()")).scalar()
        assert result is not None
        assert "PostgreSQL" in result
    finally:
        db.close()


def test_tables_created():
    """All expected SQLAlchemy tables exist in the database."""
    inspector = inspect(engine)
    actual = set(inspector.get_table_names())
    for table in EXPECTED_TABLES:
        assert table in actual, f"Missing table: {table}"


def test_create_and_read_company():
    """Basic database write then read of a company record."""
    db = _db()
    try:
        company = Company(
            ticker="TESTDB1",
            name="Test Database Company One",
            exchange="SET",
            description=None,
        )
        db.add(company)
        db.commit()
        db.refresh(company)

        fetched = db.query(Company).filter(Company.ticker == "TESTDB1").first()
        assert fetched is not None
        assert fetched.name == "Test Database Company One"
        assert fetched.exchange == "SET"
        assert fetched.id == company.id
    finally:
        db.query(Company).filter(Company.ticker == "TESTDB1").delete()
        db.commit()
        db.close()


def test_company_industry_foreign_key():
    """A company can be associated with an industry via foreign key."""
    db = _db()
    try:
        industry = Industry(name="TESTDB Industry", description="Test industry")
        db.add(industry)
        db.flush()

        company = Company(
            ticker="TESTDB2",
            name="Test Database Company Two",
            exchange="SET",
            industry_id=industry.id,
        )
        db.add(company)
        db.commit()

        fetched = (
            db.query(Company)
            .filter(Company.ticker == "TESTDB2")
            .first()
        )
        assert fetched is not None
        assert fetched.industry_id == industry.id
        assert fetched.industry is not None
        assert fetched.industry.name == "TESTDB Industry"
    finally:
        db.query(Company).filter(Company.ticker == "TESTDB2").delete()
        db.query(Industry).filter(Industry.name == "TESTDB Industry").delete()
        db.commit()
        db.close()


def test_unique_ticker_constraint():
    """Inserting a duplicate ticker raises an integrity error."""
    db = _db()
    try:
        first = Company(ticker="TESTDB3", name="First", exchange="SET")
        db.add(first)
        db.commit()

        duplicate = Company(ticker="TESTDB3", name="Second", exchange="SET")
        db.add(duplicate)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
        else:
            raise AssertionError("Expected IntegrityError for duplicate ticker")
    finally:
        db.query(Company).filter(Company.ticker == "TESTDB3").delete()
        db.commit()
        db.close()


def test_unique_company_fiscal_year_constraint():
    """Duplicate financial_data for the same company and fiscal year is rejected."""
    db = _db()
    try:
        company = Company(ticker="TESTDB4", name="Financial Co", exchange="SET")
        db.add(company)
        db.flush()

        first = FinancialData(
            company_id=company.id,
            fiscal_year=2023,
            revenue=1000,
            net_profit=100,
        )
        db.add(first)
        db.commit()

        duplicate = FinancialData(
            company_id=company.id,
            fiscal_year=2023,
            revenue=2000,
        )
        db.add(duplicate)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
        else:
            raise AssertionError(
                "Expected IntegrityError for duplicate company/fiscal_year"
            )
    finally:
        db.query(FinancialData).filter(FinancialData.company_id == company.id).delete()
        db.query(Company).filter(Company.ticker == "TESTDB4").delete()
        db.commit()
        db.close()


def test_all_model_classes_registered():
    """Every Sprint 1 model is registered on Base.metadata."""
    from app.database import Base

    registered = set(Base.metadata.tables.keys())
    for table in EXPECTED_TABLES:
        assert table in registered, f"Model not registered: {table}"


def test_event_categories_supported():
    """Event category column accepts the Sprint 1 supported categories."""
    db = _db()
    try:
        categories = [
            "GEOPOLITICAL",
            "ECONOMIC",
            "ENVIRONMENTAL",
            "REGULATORY",
            "INDUSTRY",
        ]
        for category in categories:
            event = Event(
                title=f"Test {category} event",
                description="Description",
                category=category,
            )
            db.add(event)
            db.flush()
            assert event.id is not None
    finally:
        db.query(Event).filter(Event.title.like("Test % event")).delete(
            synchronize_session=False
        )
        db.commit()
        db.close()
