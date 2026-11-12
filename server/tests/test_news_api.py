"""News API tests via TestClient.

Uses the isolated ``client`` fixture (transaction rolled back per test), so the
development database is never modified. No external news sources are contacted.
"""

from unittest.mock import patch

from app.services.news_sources import NewsSource, SOURCE_TYPE_RSS


EMPTY_FEED_RESPONSE = {
    "body": """<?xml version="1.0" encoding="UTF-8" ?><rss version="2.0"><channel><title>Empty</title></channel></rss>""",
    "http_status": 200,
    "content_type": "application/rss+xml",
}


def test_list_news_empty(client):
    """GET /api/news returns a list (empty or isolated) with 200."""
    response = client.get("/api/news")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_news_pagination_limits(client):
    """GET /api/news enforces a sensible upper limit on page size."""
    response = client.get("/api/news?limit=200")
    assert response.status_code == 422  # limit exceeds the maximum of 100


def test_get_news_article_not_found(client):
    """GET /api/news/{id} returns 404 for a missing article."""
    response = client.get("/api/news/999999")
    assert response.status_code == 404


@patch("app.services.news_service.get_configured_sources")
@patch("app.services.news_service._fetch_feed", return_value=EMPTY_FEED_RESPONSE)
def test_ingest_news_endpoint_returns_stats(mock_fetch, mock_sources, client):
    """POST /api/news/ingest returns ingestion stats without contacting real feeds."""
    mock_sources.return_value = [
        NewsSource(name="Mock Feed", url="https://example.com/mock.xml", source_type=SOURCE_TYPE_RSS, enabled=True)
    ]
    response = client.post("/api/news/ingest")
    assert response.status_code == 200
    data = response.json()
    assert "ingested" in data
    assert "skipped_duplicate" in data
    assert "errors" in data
    assert "status" in data
    assert "sources" in data
    if data["sources"]:
        src = data["sources"][0]
        assert "parsed" in src
        assert "final_status" in src
        assert "http_status" in src


def test_list_news_sources_endpoint(client):
    """GET /api/news/sources returns configured news sources."""
    response = client.get("/api/news/sources")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for src in data:
        assert "name" in src
        assert "url" in src

