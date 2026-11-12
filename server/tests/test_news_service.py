"""News ingestion service tests.

External news sources are mocked so tests run without internet access or API
keys. Database changes are rolled back after each test via the ``db`` fixture,
so the development database is never modified.
"""

from unittest.mock import patch

from app.models.news_article import NewsArticle
from app.services.news_service import ingest_articles, _normalize_url
from app.services.news_sources import NewsSource, SOURCE_TYPE_RSS

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Test Feed</title>
  <item>
    <title>Oil prices rise amid Middle East tension</title>
    <link>https://example.com/oil-prices-rise</link>
    <pubDate>Mon, 12 Nov 2026 08:00:00 GMT</pubDate>
    <description>Crude oil prices increased as tensions escalated.</description>
  </item>
  <item>
    <title>PTT announces new energy investment</title>
    <link>https://example.com/ptt-investment</link>
    <pubDate>Mon, 12 Nov 2026 09:00:00 GMT</pubDate>
    <description>PTT announced a new energy investment.</description>
  </item>
</channel>
</rss>
"""


def test_normalize_url_strips_query_and_trailing_slash():
    """URL normalization dedups consistently."""
    assert _normalize_url("https://example.com/a?utm=x") == "https://example.com/a"
    assert _normalize_url("https://example.com/a/") == "https://example.com/a"
    assert _normalize_url("") is None
    assert _normalize_url(None) is None


@patch("app.services.news_service._fetch_rss", return_value=SAMPLE_RSS)
def test_ingest_articles_creates_records(mock_fetch, db):
    """Valid articles are ingested and stored."""
    source = NewsSource(
        name="Test Feed", url="https://example.com/rss",
        source_type=SOURCE_TYPE_RSS, enabled=True,
    )
    stats = ingest_articles(db, sources=[source])

    assert stats["ingested"] == 2, stats
    assert stats["errors"] == 0, stats
    assert db.query(NewsArticle).filter(
        NewsArticle.url == "https://example.com/oil-prices-rise"
    ).first() is not None
    assert db.query(NewsArticle).filter(
        NewsArticle.url == "https://example.com/ptt-investment"
    ).first() is not None


@patch("app.services.news_service._fetch_rss", return_value=SAMPLE_RSS)
def test_ingest_articles_prevents_duplicates(mock_fetch, db):
    """Re-ingesting the same URL skips duplicates."""
    source = NewsSource(
        name="Test Feed", url="https://example.com/rss",
        source_type=SOURCE_TYPE_RSS, enabled=True,
    )
    first = ingest_articles(db, sources=[source])
    assert first["ingested"] == 2, first

    second = ingest_articles(db, sources=[source])
    assert second["skipped_duplicate"] == 2, second
    assert second["ingested"] == 0, second


@patch(
    "app.services.news_service._fetch_rss",
    side_effect=Exception("source unavailable"),
)
def test_ingest_articles_handles_source_failure(mock_fetch, db):
    """A failing source is logged and does not crash ingestion."""
    source = NewsSource(
        name="Bad Feed", url="https://bad.example.com/rss",
        source_type=SOURCE_TYPE_RSS, enabled=True,
    )
    stats = ingest_articles(db, sources=[source])

    assert stats["errors"] == 1, stats
    assert stats["ingested"] == 0
    assert stats["sources"][0]["error"] is not None


def test_ingest_articles_missing_fields_skipped(db):
    """Articles missing title or url are skipped gracefully."""
    bad_rss = """<?xml version="1.0"?>
    <rss version="2.0"><channel>
      <item><title>Valid Title</title><link>https://example.com/valid</link></item>
      <item><description>No title or link</description></item>
    </channel></rss>
    """
    with patch(
        "app.services.news_service._fetch_rss", return_value=bad_rss
    ):
        source = NewsSource(
            name="Test Feed", url="https://example.com/rss",
            source_type=SOURCE_TYPE_RSS, enabled=True,
        )
        stats = ingest_articles(db, sources=[source])
        assert stats["ingested"] == 1, stats
        assert db.query(NewsArticle).filter(
            NewsArticle.url == "https://example.com/valid"
        ).first() is not None
