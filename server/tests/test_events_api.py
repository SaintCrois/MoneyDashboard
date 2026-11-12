"""Event and mapping API tests via TestClient.

Uses the isolated ``db`` and ``client`` fixtures (transaction rolled back per
test), so the development database is never modified.
"""


def test_event_categories_endpoint(client):
    """GET /api/events/categories returns supported categories."""
    response = client.get("/api/events/categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(c["category"] == "Energy" for c in data)


def test_list_events_empty(client):
    """GET /api/events returns an empty list when no events exist."""
    response = client.get("/api/events")
    assert response.status_code == 200
    assert response.json() == []


def test_process_events_endpoint(client):
    """POST /api/events/process returns processing stats."""
    response = client.post("/api/events/process")
    assert response.status_code == 200
    data = response.json()
    assert "processed" in data
    assert "errors" in data


def test_get_event_not_found(client):
    """GET /api/events/{id} returns 404 for a missing event."""
    response = client.get("/api/events/999999")
    assert response.status_code == 404


def test_get_event_industries_not_found(client):
    """GET /api/events/{id}/industries returns 404 for a missing event."""
    response = client.get("/api/events/999999/industries")
    assert response.status_code == 404


def test_get_event_companies_not_found(client):
    """GET /api/events/{id}/companies returns 404 for a missing event."""
    response = client.get("/api/events/999999/companies")
    assert response.status_code == 404


def test_get_company_events_not_found(client):
    """GET /api/companies/{id}/events returns 404 for a missing company."""
    response = client.get("/api/companies/999999/events")
    assert response.status_code == 404


def test_event_full_flow(db, client):
    """Insert article, process event, then retrieve event and mappings."""
    from app.models.company import Company
    from app.models.industry import Industry
    from app.models.news_article import NewsArticle

    article_url = "https://example.com/api-event-flow-unique"
    event_title = "API Event Flow Unique"
    industry_name = "API Flow Energy Industry"

    # Insert article + industry via the isolated session
    article = NewsArticle(
        title=event_title,
        source="Test Source",
        url=article_url,
        summary="PTT announced a new energy investment.",
        content="PTT announced a new energy investment.",
    )
    db.add(article)
    db.flush()

    industry = Industry(name=industry_name, description="Flow industry")
    db.add(industry)
    db.flush()

    # Process events via API (uses the same isolated session)
    resp = client.post("/api/events/process")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["processed"] >= 1, stats

    # Retrieve the created event
    resp = client.get("/api/events")
    assert resp.status_code == 200
    events = resp.json()
    event = next((e for e in events if e["title"] == event_title), None)
    assert event is not None, events
    event_id = event["id"]
    assert event["source_article_id"] == article.id

    # Event details
    resp = client.get(f"/api/events/{event_id}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["id"] == event_id

    # Industries mapping endpoint
    resp = client.get(f"/api/events/{event_id}/industries")
    assert resp.status_code == 200

    # Companies mapping endpoint
    resp = client.get(f"/api/events/{event_id}/companies")
    assert resp.status_code == 200

    # Company events endpoint
    companies = db.query(Company).all()
    if companies:
        resp = client.get(f"/api/companies/{companies[0].id}/events")
        assert resp.status_code == 200
