"""News API tests via TestClient.

Uses the isolated ``client`` fixture (transaction rolled back per test), so the
development database is never modified. No external news sources are contacted.
"""


def test_list_news_empty(client):
    """GET /api/news returns an empty list when no articles exist."""
    response = client.get("/api/news")
    assert response.status_code == 200
    assert response.json() == []


def test_list_news_pagination_limits(client):
    """GET /api/news enforces a sensible upper limit on page size."""
    response = client.get("/api/news?limit=200")
    assert response.status_code == 422  # limit exceeds the maximum of 100


def test_get_news_article_not_found(client):
    """GET /api/news/{id} returns 404 for a missing article."""
    response = client.get("/api/news/999999")
    assert response.status_code == 404


def test_ingest_news_endpoint_returns_stats(client):
    """POST /api/news/ingest returns ingestion stats (sources may be unavailable)."""
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
