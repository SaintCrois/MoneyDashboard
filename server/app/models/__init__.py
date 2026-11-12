"""SQLAlchemy database models package.

Importing this package registers every model with ``Base.metadata`` so that
``Base.metadata.create_all`` can create all tables.
"""

from app.models.company import Company  # noqa: F401
from app.models.event import Event  # noqa: F401
from app.models.event_company import EventCompany  # noqa: F401
from app.models.event_industry import EventIndustry  # noqa: F401
from app.models.financial_data import FinancialData  # noqa: F401
from app.models.impact_assessment import ImpactAssessment  # noqa: F401
from app.models.industry import Industry  # noqa: F401
from app.models.market_data import MarketData  # noqa: F401
from app.models.news_article import NewsArticle  # noqa: F401

__all__ = [
    "Company",
    "Event",
    "EventCompany",
    "EventIndustry",
    "FinancialData",
    "ImpactAssessment",
    "Industry",
    "MarketData",
    "NewsArticle",
]
