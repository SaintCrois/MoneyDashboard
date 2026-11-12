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

    def fake_get(path, timeout=5):
        return _Response({"status": "ok"})

    monkeypatch.setattr(app.requests, "get", fake_get)
    assert app.get_backend_status() is True


def test_get_backend_status_false_on_error(monkeypatch):
    """get_backend_status returns False when the backend raises."""

    def fake_get(path, timeout=5):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(app.requests, "get", fake_get)
    assert app.get_backend_status() is False


def test_get_backend_status_false_on_bad_status(monkeypatch):
    """get_backend_status returns False when /health does not return ok."""

    def fake_get(path, timeout=5):
        return _Response({"status": "error"})

    monkeypatch.setattr(app.requests, "get", fake_get)
    assert app.get_backend_status() is False


def test_get_companies_parses_list(monkeypatch):
    """get_companies returns the list parsed from the backend response."""

    def fake_get(path, timeout=5):
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

    def fake_get(path, timeout=5):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(app.requests, "get", fake_get)
    assert app.get_companies() == []


def test_get_companies_industry_filter_path(monkeypatch):
    """get_companies appends the industry filter query parameter."""
    captured = {}

    def fake_get(path, timeout=5):
        captured["path"] = path
        return _Response([])

    monkeypatch.setattr(app.requests, "get", fake_get)
    app.get_companies(industry_id=2)
    assert captured["path"] == f"{app.BACKEND_URL}/api/companies?industry_id=2"


def test_get_industries_parses_list(monkeypatch):
    """get_industries returns the list parsed from the backend response."""

    def fake_get(path, timeout=5):
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

    def fake_get(path, timeout=5):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(app.requests, "get", fake_get)
    assert app.get_industries() == []
