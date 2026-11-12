"""Configurable news sources for the news ingestion pipeline.

Sources are declared here as data so the ingestion service stays source-agnostic.
No API keys or credentials are hardcoded. Add, remove, or override sources by
editing this file or the SOURCES list at runtime.
"""

from typing import List

# Source type constants.
SOURCE_TYPE_RSS = "rss"
SOURCE_TYPE_API = "api"


class NewsSource:
    """A single configured news source."""

    def __init__(
        self,
        name: str,
        url: str,
        source_type: str = SOURCE_TYPE_RSS,
        enabled: bool = True,
    ):
        self.name = name
        self.url = url
        self.source_type = source_type
        self.enabled = enabled

    def __repr__(self) -> str:  # pragma: no cover
        return f"<NewsSource(name={self.name!r}, url={self.url!r})>"


# Default configured sources. These are example public RSS feeds. External
# sources may be unavailable at runtime; the ingestion service handles source
# failures gracefully so the application keeps working with stored articles.
DEFAULT_SOURCES: List[NewsSource] = [
    NewsSource(
        name="Bangkok Post",
        url="https://www.bangkokpost.com/rss/data.xml",
        source_type=SOURCE_TYPE_RSS,
    ),
    NewsSource(
        name="The Nation Thailand",
        url="https://www.nationthailand.com/rss/",
        source_type=SOURCE_TYPE_RSS,
    ),
    NewsSource(
        name="Reuters Business",
        url="https://www.reuters.com/business/finance/rss",
        source_type=SOURCE_TYPE_RSS,
    ),
]

__all__ = ["NewsSource", "SOURCE_TYPE_RSS", "SOURCE_TYPE_API", "DEFAULT_SOURCES"]
