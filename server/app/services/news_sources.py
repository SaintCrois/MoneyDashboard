"""Configurable news sources for the news ingestion pipeline.

Sources are declared here as data so the ingestion service stays source-agnostic.
No API keys or credentials are hardcoded. Add, remove, or override sources by
editing this configuration or providing environment-based overrides.
"""

import json
import os
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
        language: str = "en",
        publisher: str | None = None,
        notes: str | None = None,
    ):
        self.name = name
        self.url = url
        self.source_type = source_type
        self.enabled = enabled
        self.language = language
        self.publisher = publisher or name
        self.notes = notes

    def __repr__(self) -> str:  # pragma: no cover
        return f"<NewsSource(name={self.name!r}, url={self.url!r})>"


# Default configured sources.
# These are verified, accessible English-language RSS/XML feeds from Thai
# publishers where available. Publishers without a suitable accessible English
# RSS feed are recorded as unavailable (disabled) rather than fabricated.
DEFAULT_SOURCES: List[NewsSource] = [
    NewsSource(
        name="Bangkok Post Business",
        publisher="Bangkok Post",
        url="https://www.bangkokpost.com/rss/data/business.xml",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) - business coverage.",
    ),
    NewsSource(
        name="Bangkok Post Most Recent",
        publisher="Bangkok Post",
        url="https://www.bangkokpost.com/rss/data/most-recent.xml",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) - general recent coverage.",
    ),
    NewsSource(
        name="Bangkok Post Thailand",
        publisher="Bangkok Post",
        url="https://www.bangkokpost.com/rss/data/thailand.xml",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) on 2026-11-14 - national news.",
    ),
    NewsSource(
        name="Bangkok Post Top Stories",
        publisher="Bangkok Post",
        url="https://www.bangkokpost.com/rss/data/topstories.xml",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) on 2026-11-14 - top stories.",
    ),
    NewsSource(
        name="Bangkok Post Property",
        publisher="Bangkok Post",
        url="https://www.bangkokpost.com/rss/data/property.xml",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) on 2026-11-14 - property coverage.",
    ),
    NewsSource(
        name="Thailand Business News",
        publisher="Thailand Business News",
        url="https://www.thailand-business-news.com/feed",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) on 2026-11-14 - Thai business and economy.",
    ),
    NewsSource(
        name="Khaosod English",
        publisher="Khaosod English",
        url="https://www.khaosodenglish.com/feed/",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) on 2026-11-14 - national news.",
    ),
    NewsSource(
        name="The Thaiger",
        publisher="The Thaiger",
        url="https://thethaiger.com/feed",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) on 2026-11-14 - national news.",
    ),
    NewsSource(
        name="Thai Examiner",
        publisher="Thai Examiner",
        url="https://www.thaiexaminer.com/feed/",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) on 2026-11-14 - national news and economy.",
    ),
    NewsSource(
        name="Thai Enquirer",
        publisher="Thai Enquirer",
        url="https://www.thaienquirer.com/feed/",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) on 2026-11-14 - politics and economy.",
    ),
    # Global sources: events abroad (oil, rates, trade, conflict) that can reach
    # Thai listed companies indirectly.
    NewsSource(
        name="BBC Business",
        publisher="BBC",
        url="https://feeds.bbci.co.uk/news/business/rss.xml",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) on 2026-11-14 - global business.",
    ),
    NewsSource(
        name="BBC World",
        publisher="BBC",
        url="https://feeds.bbci.co.uk/news/world/rss.xml",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) on 2026-11-14 - world news.",
    ),
    NewsSource(
        name="Yahoo Finance",
        publisher="Yahoo Finance",
        url="https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) on 2026-11-14 - US market headlines.",
    ),
    NewsSource(
        name="CNA Business",
        publisher="Channel News Asia",
        url="https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6936",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) on 2026-11-14 - Asia business.",
    ),
    NewsSource(
        name="Investing.com",
        publisher="Investing.com",
        url="https://www.investing.com/rss/news.rss",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) on 2026-11-14 - market news.",
    ),
    NewsSource(
        name="CNBC Business",
        publisher="CNBC",
        url="https://www.cnbc.com/id/10001147/device/rss/rss.html",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) on 2026-11-14 - global business.",
    ),
    NewsSource(
        name="The Guardian Business",
        publisher="The Guardian",
        url="https://www.theguardian.com/business/rss",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) on 2026-11-14 - global business.",
    ),
    NewsSource(
        name="Al Jazeera",
        publisher="Al Jazeera",
        url="https://www.aljazeera.com/xml/rss/all.xml",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) on 2026-11-14 - world and Middle East news.",
    ),
    NewsSource(
        name="OilPrice.com",
        publisher="OilPrice.com",
        url="https://oilprice.com/rss/main",
        source_type=SOURCE_TYPE_RSS,
        enabled=True,
        language="en",
        notes="Verified accessible RSS/XML (English) on 2026-11-14 - energy and commodities.",
    ),
    NewsSource(
        name="The Nation Thailand",
        publisher="The Nation Thailand",
        url="",
        source_type=SOURCE_TYPE_RSS,
        enabled=False,
        language="en",
        notes=(
            "Unavailable: no suitable accessible RSS/XML feed endpoint verified "
            "during implementation (probed feed endpoints returned non-RSS HTML). "
            "Not fabricated."
        ),
    ),
    NewsSource(
        name="THE STANDARD Global",
        publisher="THE STANDARD",
        url="",
        source_type=SOURCE_TYPE_RSS,
        enabled=False,
        language="en",
        notes=(
            "Unavailable: accessible RSS feeds found but English-language/global "
            "feed could not be verified; available feeds appeared non-English. "
            "Not fabricated."
        ),
    ),
    NewsSource(
        name="Thai PBS World",
        publisher="Thai PBS World",
        url="",
        source_type=SOURCE_TYPE_RSS,
        enabled=False,
        language="en",
        notes=(
            "Unavailable: no suitable accessible RSS/XML feed endpoint verified "
            "during implementation (feed URL returned HTML application page). "
            "Not fabricated."
        ),
    ),
]


def _load_configured_sources() -> List[NewsSource]:
    """Return configured sources, allowing JSON override via NEWS_SOURCES_JSON.

    Environment override format (optional):
      NEWS_SOURCES_JSON='[{"name":"X","publisher":"X","url":"...","enabled":true,"language":"en"}]'
    Invalid config falls back to defaults.
    """
    raw = os.getenv("NEWS_SOURCES_JSON")
    if not raw:
        return list(DEFAULT_SOURCES)
    try:
        data = json.loads(raw)
        if not isinstance(data, list):
            return list(DEFAULT_SOURCES)
        sources: List[NewsSource] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            url = str(item.get("url") or "").strip()
            if not name:
                continue
            sources.append(
                NewsSource(
                    name=name,
                    publisher=item.get("publisher") or name,
                    url=url,
                    source_type=item.get("type") or SOURCE_TYPE_RSS,
                    enabled=bool(item.get("enabled", True)) and bool(url),
                    language=item.get("language") or "en",
                    notes=item.get("notes"),
                )
            )
        return sources or list(DEFAULT_SOURCES)
    except Exception:
        return list(DEFAULT_SOURCES)


def get_configured_sources() -> List[NewsSource]:
    """Public accessor for configured news sources."""
    return _load_configured_sources()


__all__ = [
    "NewsSource",
    "SOURCE_TYPE_RSS",
    "SOURCE_TYPE_API",
    "DEFAULT_SOURCES",
    "get_configured_sources",
]

