"""Frontend helper tests for Sprint 1.

Tests the Streamlit helper functions in client/app.py using mocked HTTP calls,
so no running backend is required. Verifies API response handling and
backend-unavailable handling.

The client application module is loaded by file path (rather than ``import app``)
so the import is unambiguous even when the server package is also on sys.path.
"""

import importlib.util
import os

spec = importlib.util.spec_from_file_location(
    "client_app", os.path.join(os.path.dirname(__file__), "..", "app.py")
)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class _Response:
    def __init__(self, payload, status_code=200, raise_error=False):
        self._payload = payload
        self.status_code = status_code
        self.raise_error = raise_error

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.raise_error:
            raise RuntimeError("backend unavailable")


def test_get_backend_status_true(monkeypatch):
    """get_backend_status returns True when /health responds ok."""

    def fake_get(path, timeout=5, params=None):
        return _Response({"status": "ok"})

    monkeypatch.setattr(app.requests, "get", fake_get)
    assert app.get_backend_status() is True


def test_get_backend_status_false_on_error(monkeypatch):
    """get_backend_status returns False when the backend raises."""

    def fake_get(path, timeout=5, params=None):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(app.requests, "get", fake_get)
    assert app.get_backend_status() is False


def test_get_backend_status_false_on_bad_status(monkeypatch):
    """get_backend_status returns False when /health does not return ok."""

    def fake_get(path, timeout=5, params=None):
        return _Response({"status": "error"})

    monkeypatch.setattr(app.requests, "get", fake_get)
    assert app.get_backend_status() is False


def test_get_companies_parses_list(monkeypatch):
    """get_companies returns the list parsed from the backend response."""

    def fake_get(path, timeout=5, params=None):
        return _Response(
            [
                {
                    "id": 1,
                    "ticker": "PTT",
                    "name": "PTT Public Company Limited",
                    "exchange": "SET",
                    "industry_id": 1,
                    "industry_name": "Energy",
                    "description": None,
                    "created_at": "2026-11-12T09:42:12.522002Z",
                }
            ]
        )

    monkeypatch.setattr(app.requests, "get", fake_get)
    companies = app.get_companies()
    assert len(companies) == 1
    assert companies[0]["ticker"] == "PTT"


def test_get_companies_empty_on_backend_failure(monkeypatch):
    """get_companies returns an empty list when the backend is unavailable."""

    def fake_get(path, timeout=5, params=None):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(app.requests, "get", fake_get)
    assert app.get_companies() == []


def test_get_companies_industry_filter_path(monkeypatch):
    """get_companies appends the industry filter query parameter."""
    captured = {}

    def fake_get(path, timeout=5, params=None):
        captured["path"] = path
        return _Response([])

    monkeypatch.setattr(app.requests, "get", fake_get)
    app.get_companies(industry_id=2)
    assert captured["path"] == f"{app.BACKEND_URL}/api/companies?industry_id=2"


def test_get_industries_parses_list(monkeypatch):
    """get_industries returns the list parsed from the backend response."""

    def fake_get(path, timeout=5, params=None):
        return _Response(
            [
                {
                    "id": 1,
                    "name": "Energy",
                    "description": None,
                    "created_at": "2026-11-12T09:42:12.522002Z",
                }
            ]
        )

    monkeypatch.setattr(app.requests, "get", fake_get)
    industries = app.get_industries()
    assert len(industries) == 1
    assert industries[0]["name"] == "Energy"


def test_get_industries_empty_on_backend_failure(monkeypatch):
    """get_industries returns an empty list when the backend is unavailable."""

    def fake_get(path, timeout=5, params=None):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(app.requests, "get", fake_get)
    assert app.get_industries() == []


def test_get_articles_parses_list(monkeypatch):
    """get_articles returns the list parsed from the backend response."""

    def fake_get(path, timeout=5, params=None):
        return _Response(
            [
                {
                    "id": 1,
                    "title": "Test Article",
                    "source": "Test Source",
                    "url": "https://example.com/article",
                    "published_at": "2026-11-12T09:42:12.522002Z",
                    "summary": "A summary.",
                    "content": None,
                    "fetched_at": "2026-11-12T09:42:12.522002Z",
                    "created_at": "2026-11-12T09:42:12.522002Z",
                }
            ]
        )

    monkeypatch.setattr(app.requests, "get", fake_get)
    articles = app.get_articles()
    assert len(articles) == 1
    assert articles[0]["title"] == "Test Article"


def test_get_articles_empty_on_backend_failure(monkeypatch):
    """get_articles returns an empty list when the backend is unavailable."""

    def fake_get(path, timeout=5, params=None):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(app.requests, "get", fake_get)
    assert app.get_articles() == []


def test_get_events_parses_list(monkeypatch):
    """get_events returns the list parsed from the backend response."""

    def fake_get(path, timeout=5, params=None):
        return _Response(
            [
                {
                    "id": 1,
                    "title": "Test Event",
                    "description": "A description.",
                    "category": "Energy",
                    "location": None,
                    "event_date": None,
                    "source_article_id": 1,
                    "classification_method": "rule_based",
                    "confidence_score": 0.7,
                    "processing_status": "processed",
                    "created_at": "2026-11-12T09:42:12.522002Z",
                }
            ]
        )

    monkeypatch.setattr(app.requests, "get", fake_get)
    events = app.get_events()
    assert len(events) == 1
    assert events[0]["category"] == "Energy"


def test_get_events_applies_category_filter(monkeypatch):
    """get_events passes the category filter to the backend."""
    captured = {}

    def fake_get(path, timeout=5, params=None):
        captured["params"] = params
        return _Response([])

    monkeypatch.setattr(app.requests, "get", fake_get)
    app.get_events(category="Energy")
    assert captured["params"] == {"skip": 0, "limit": 50, "category": "Energy"}


def test_get_events_empty_on_backend_failure(monkeypatch):
    """get_events returns an empty list when the backend is unavailable."""

    def fake_get(path, timeout=5, params=None):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(app.requests, "get", fake_get)
    assert app.get_events() == []


def test_get_event_categories_parses_list(monkeypatch):
    """get_event_categories returns category names from the backend."""

    def fake_get(path, timeout=5, params=None):
        return _Response([{"category": "Energy"}, {"category": "Political"}])

    monkeypatch.setattr(app.requests, "get", fake_get)
    categories = app.get_event_categories()
    assert categories == ["Energy", "Political"]


def test_get_event_industries_and_companies_parse(monkeypatch):
    """get_event_industries and get_event_companies parse mapped records."""

    def fake_get(path, timeout=5, params=None):
        if "/industries" in path:
            return _Response(
                [
                    {
                        "id": 1,
                        "event_id": 1,
                        "industry_id": 1,
                        "impact_type": "Uncertain",
                        "relevance_score": 0.55,
                        "explanation": "Related to energy.",
                        "industry_name": "Energy",
                    }
                ]
            )
        if "/companies" in path:
            return _Response(
                [
                    {
                        "id": 1,
                        "event_id": 1,
                        "company_id": 1,
                        "impact_type": "Uncertain",
                        "exposure_type": "Indirect",
                        "relevance_score": 0.9,
                        "explanation": "Related to PTT.",
                        "company_name": "PTT Public Company Limited",
                        "ticker": "PTT",
                    }
                ]
            )
        return _Response({})

    monkeypatch.setattr(app.requests, "get", fake_get)
    industries = app.get_event_industries(1)
    companies = app.get_event_companies(1)
    assert len(industries) == 1
    assert industries[0]["industry_name"] == "Energy"
    assert len(companies) == 1
    assert companies[0]["ticker"] == "PTT"


def test_ingest_and_process_return_none_on_failure(monkeypatch):
    """ingest_articles and process_events return None when the backend fails."""

    def fake_post(path, timeout=5, json=None):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(app.requests, "post", fake_post)
    assert app.ingest_articles() is None
    assert app.process_events() is None


def test_get_news_sources_parses_list(monkeypatch):
    """get_news_sources returns the configured source list."""

    def fake_get(path, timeout=5, params=None):
        if path.endswith("/api/news/sources"):
            return _Response([
                {"name": "BBC Business", "url": "https://feeds.bbci.co.uk/news/business/rss.xml", "type": "rss", "enabled": True},
                {"name": "Yahoo Finance", "url": "https://feeds.finance.yahoo.com/rss/2.0/headline", "type": "rss", "enabled": True},
            ])
        return _Response([])

    monkeypatch.setattr(app.requests, "get", fake_get)
    sources = app.get_news_sources()
    assert len(sources) == 2
    assert sources[0]["name"] == "BBC Business"


def test_get_news_sources_empty_on_failure(monkeypatch):
    """get_news_sources returns empty list on backend failure."""

    def fake_get(path, timeout=5, params=None):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(app.requests, "get", fake_get)
    assert app.get_news_sources() == []


def test_filter_articles_by_source_individual():
    """filter_articles_by_source filters by a specific source name."""
    articles = [
        {"id": 1, "source": "BBC Business", "title": "A"},
        {"id": 2, "source": "Yahoo Finance", "title": "B"},
        {"id": 3, "source": "BBC Business", "title": "C"},
    ]
    filtered = app.filter_articles_by_source(articles, "BBC Business")
    assert len(filtered) == 2
    assert all(a["source"] == "BBC Business" for a in filtered)


def test_filter_articles_by_source_all_sources():
    """filter_articles_by_source returns all articles for 'All Sources'."""
    articles = [
        {"id": 1, "source": "BBC Business", "title": "A"},
        {"id": 2, "source": "Yahoo Finance", "title": "B"},
    ]
    filtered = app.filter_articles_by_source(articles, "All Sources")
    assert len(filtered) == 2


def test_filter_articles_by_source_unknown():
    """filter_articles_by_source returns empty for an unknown source."""
    articles = [
        {"id": 1, "source": "BBC Business", "title": "A"},
        {"id": 2, "source": "Yahoo Finance", "title": "B"},
    ]
    filtered = app.filter_articles_by_source(articles, "NonExistent Source")
    assert len(filtered) == 0


def test_filter_articles_by_source_none_returns_all():
    """filter_articles_by_source returns all articles when source is None."""
    articles = [
        {"id": 1, "source": "BBC Business", "title": "A"},
        {"id": 2, "source": "Yahoo Finance", "title": "B"},
    ]
    filtered = app.filter_articles_by_source(articles, None)
    assert len(filtered) == 2


def test_ingestion_status_badge_logic():
    """_ingestion_status_badge returns correct explicit statuses."""
    assert app._ingestion_status_badge({"final_status": "Success"}) == "Success"
    assert app._ingestion_status_badge({"final_status": "Failed"}) == "Failed"
    assert app._ingestion_status_badge({"final_status": "No Articles"}) == "No Articles"
    assert app._ingestion_status_badge({"error": "HTTPError: 404"}) == "Failed"
    assert app._ingestion_status_badge({"parsed": 0, "ingested": 0, "skipped": 0}) == "No Articles"
    assert app._ingestion_status_badge({"parsed": 5, "ingested": 3, "skipped": 2}) == "Success"
