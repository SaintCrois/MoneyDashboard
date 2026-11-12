"""News ingestion service tests.

External news sources are mocked so tests run without internet access or API
keys. Database changes are rolled back after each test via the ``db`` fixture,
so the development database is never modified.
"""

from unittest.mock import patch
from urllib.error import HTTPError

from app.models.news_article import NewsArticle
from app.services.news_service import ingest_articles, _normalize_url, _parse_rss_feed
from app.services.news_sources import DEFAULT_SOURCES, NewsSource, SOURCE_TYPE_RSS

VALID_RSS = """<?xml version="1.0" encoding="UTF-8" ?>
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

EMPTY_RSS = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Empty Feed</title>
</channel>
</rss>
"""

MALFORMED_XML = "this is not xml at all"

VALID_ATOM = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Atom Test Feed</title>
  <entry>
    <title>Atom article one</title>
    <link href="https://example.com/atom-one"/>
    <published>2026-11-12T08:00:00Z</published>
    <summary>First atom article summary.</summary>
  </entry>
  <entry>
    <title>Atom article two</title>
    <link href="https://example.com/atom-two"/>
    <updated>2026-11-12T09:00:00Z</updated>
    <summary>Second atom article summary.</summary>
  </entry>
</feed>
"""


VALID_FEED_RESPONSE = {"body": VALID_RSS, "http_status": 200, "content_type": "application/rss+xml"}
EMPTY_FEED_RESPONSE = {"body": EMPTY_RSS, "http_status": 200, "content_type": "application/rss+xml"}
MALFORMED_FEED_RESPONSE = {"body": MALFORMED_XML, "http_status": 200, "content_type": "text/html"}
ATOM_FEED_RESPONSE = {"body": VALID_ATOM, "http_status": 200, "content_type": "application/atom+xml"}


def test_normalize_url_strips_query_and_trailing_slash():
    """URL normalization dedups consistently."""
    assert _normalize_url("https://example.com/a?utm=x") == "https://example.com/a"
    assert _normalize_url("https://example.com/a/") == "https://example.com/a"
    assert _normalize_url("") is None
    assert _normalize_url(None) is None


def test_parse_rss_feed_valid_rss():
    """A valid RSS 2.0 feed parses into article dicts."""
    articles = _parse_rss_feed(VALID_RSS, "Test Feed")
    assert len(articles) == 2
    assert articles[0]["title"] == "Oil prices rise amid Middle East tension"
    assert articles[0]["url"] == "https://example.com/oil-prices-rise"
    assert articles[0]["source"] == "Test Feed"
    assert articles[0]["published_at"] is not None
    assert articles[0]["summary"] == "Crude oil prices increased as tensions escalated."


def test_parse_rss_feed_empty_feed():
    """An empty feed returns no articles without error."""
    articles = _parse_rss_feed(EMPTY_RSS, "Empty Feed")
    assert articles == []


def test_parse_rss_feed_malformed_xml():
    """Malformed XML returns no articles without error."""
    articles = _parse_rss_feed(MALFORMED_XML, "Bad Feed")
    assert articles == []


def test_parse_rss_feed_atom_feed():
    """A valid Atom feed parses into article dicts."""
    articles = _parse_rss_feed(VALID_ATOM, "Atom Feed")
    assert len(articles) == 2
    assert articles[0]["title"] == "Atom article one"
    assert articles[0]["url"] == "https://example.com/atom-one"
    assert articles[0]["published_at"] is not None
    assert articles[1]["title"] == "Atom article two"
    assert articles[1]["url"] == "https://example.com/atom-two"


def test_parse_rss_feed_missing_fields_skipped():
    """Entries missing title or url are skipped gracefully."""
    bad_rss = """<?xml version="1.0"?>
    <rss version="2.0"><channel>
      <item><title>Valid Title</title><link>https://example.com/valid</link></item>
      <item><description>No title or link</description></item>
    </channel></rss>
    """
    articles = _parse_rss_feed(bad_rss, "Test Feed")
    assert len(articles) == 1
    assert articles[0]["url"] == "https://example.com/valid"


@patch("app.services.news_service._fetch_feed", return_value=VALID_FEED_RESPONSE)
def test_ingest_articles_creates_records(mock_fetch, db):
    """Valid articles are ingested and stored."""
    source = NewsSource(
        name="Test Feed", url="https://example.com/rss",
        source_type=SOURCE_TYPE_RSS, enabled=True,
    )
    stats = ingest_articles(db, sources=[source])

    assert stats["ingested"] == 2, stats
    assert stats["errors"] == 0, stats
    assert stats["sources"][0]["parsed"] == 2
    assert stats["sources"][0]["http_status"] == 200
    assert stats["sources"][0]["content_type"] == "application/rss+xml"
    assert stats["sources"][0]["final_status"] == "Success"
    assert stats["status"] == "Success"
    assert db.query(NewsArticle).filter(
        NewsArticle.url == "https://example.com/oil-prices-rise"
    ).first() is not None
    assert db.query(NewsArticle).filter(
        NewsArticle.url == "https://example.com/ptt-investment"
    ).first() is not None


@patch("app.services.news_service._fetch_feed", return_value=VALID_FEED_RESPONSE)
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
    "app.services.news_service._fetch_feed",
    side_effect=HTTPError("https://bad.example.com/rss", 404, "Not Found", {}, None),
)
def test_ingest_articles_handles_http_error(mock_fetch, db):
    """An HTTP error source is logged and does not crash ingestion."""
    source = NewsSource(
        name="Bad Feed", url="https://bad.example.com/rss",
        source_type=SOURCE_TYPE_RSS, enabled=True,
    )
    stats = ingest_articles(db, sources=[source])

    assert stats["errors"] == 1, stats
    assert stats["ingested"] == 0
    assert stats["sources"][0]["error"] is not None
    assert stats["sources"][0]["http_status"] == 404
    assert stats["sources"][0]["final_status"] == "Failed"
    assert stats["status"] == "Failed"


@patch("app.services.news_service._fetch_feed", return_value=MALFORMED_FEED_RESPONSE)
def test_ingest_articles_handles_malformed_xml(mock_fetch, db):
    """A malformed XML source is logged and does not crash ingestion."""
    source = NewsSource(
        name="Bad Feed", url="https://bad.example.com/rss",
        source_type=SOURCE_TYPE_RSS, enabled=True,
    )
    stats = ingest_articles(db, sources=[source])

    assert stats["errors"] == 0, stats  # parse failure is handled, not an exception
    assert stats["ingested"] == 0
    assert stats["sources"][0]["parsed"] == 0
    assert stats["sources"][0]["final_status"] == "No Articles"
    assert stats["status"] == "No Articles"


@patch("app.services.news_service._fetch_feed", return_value=EMPTY_FEED_RESPONSE)
def test_ingest_articles_empty_feed(mock_fetch, db):
    """An empty feed ingests zero articles without error."""
    source = NewsSource(
        name="Empty Feed", url="https://example.com/rss",
        source_type=SOURCE_TYPE_RSS, enabled=True,
    )
    stats = ingest_articles(db, sources=[source])

    assert stats["ingested"] == 0, stats
    assert stats["errors"] == 0, stats
    assert stats["sources"][0]["parsed"] == 0
    assert stats["sources"][0]["final_status"] == "No Articles"
    assert stats["status"] == "No Articles"


@patch("app.services.news_service._fetch_feed", return_value=ATOM_FEED_RESPONSE)
def test_ingest_articles_atom_feed(mock_fetch, db):
    """A valid Atom feed ingests articles."""
    source = NewsSource(
        name="Atom Feed", url="https://example.com/atom",
        source_type=SOURCE_TYPE_RSS, enabled=True,
    )
    stats = ingest_articles(db, sources=[source])

    assert stats["ingested"] == 2, stats
    assert stats["errors"] == 0, stats
    assert db.query(NewsArticle).filter(
        NewsArticle.url == "https://example.com/atom-one"
    ).first() is not None
    assert db.query(NewsArticle).filter(
        NewsArticle.url == "https://example.com/atom-two"
    ).first() is not None


@patch("app.services.news_service._fetch_feed")
def test_ingest_articles_partial_success(mock_fetch, db):
    """When some sources succeed and some fail, overall status is Partial Success."""
    def side_effect(url, timeout=15):
        if "good.example.com" in url:
            return VALID_FEED_RESPONSE
        raise HTTPError(url, 500, "Internal Server Error", {}, None)

    mock_fetch.side_effect = side_effect
    sources = [
        NewsSource(name="Good Feed", url="https://good.example.com/rss", source_type=SOURCE_TYPE_RSS),
        NewsSource(name="Bad Feed", url="https://bad.example.com/rss", source_type=SOURCE_TYPE_RSS),
    ]
    stats = ingest_articles(db, sources=sources)

    assert stats["ingested"] == 2, stats
    assert stats["errors"] == 1, stats
    assert stats["status"] == "Partial Success"
    statuses = {s["name"]: s["final_status"] for s in stats["sources"]}
    assert statuses["Good Feed"] == "Success"
    assert statuses["Bad Feed"] == "Failed"


def test_default_sources_are_current_working_feeds():
    """Regression: default sources must be the verified working RSS feeds.

    The stale configuration (Bangkok Post 404, The Nation returns HTML,
    Reuters 401) must not be present in DEFAULT_SOURCES.
    """
    urls = [s.url for s in DEFAULT_SOURCES]
    names = [s.name for s in DEFAULT_SOURCES]

    stale_urls = {
        "https://www.bangkokpost.com/rss/data.xml",
        "https://www.nationthailand.com/rss/",
        "https://www.reuters.com/business/finance/rss",
    }
    stale_names = {"Bangkok Post", "The Nation Thailand", "Reuters Business"}

    for url in stale_urls:
        assert url not in urls, f"Stale broken source URL still configured: {url}"
    for name in stale_names:
        assert name not in names, f"Stale broken source name still configured: {name}"

    # Verify current working sources are present
    assert "https://feeds.bbci.co.uk/news/business/rss.xml" in urls
    assert "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US" in urls
    assert "https://www.channelnewsasia.com/api/v1/rss-outbound-feed" in urls
    assert "https://www.investing.com/rss/news.rss" in urls
    assert len(DEFAULT_SOURCES) == 4
