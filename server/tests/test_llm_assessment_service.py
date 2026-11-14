"""AI integration with mocked provider calls; never uses paid API credentials."""
import json

import httpx
import pytest

from app.services import llm_assessment_service as ai
from app.models.company import Company
from app.models.event import Event
from app.models.news_article import NewsArticle


def result_data(**changes):
    result = dict(impact_type="Mixed", impact_severity="Medium", risk_level="Medium", confidence=0.6,
                  explanation="ต้นทุนอาจเพิ่มขึ้นตามเหตุการณ์ [1] แต่ยังต้องยืนยันข้อมูลบริษัท",
                  financial_exposure="ผลกระทบเป็นสมมติฐาน ไม่ใช่ตัวเลขยืนยัน", evidence_ids=[1],
                  missing_information=["Missing company segment exposure"])
    result.update(changes)
    return result


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-not-a-real-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")


def mock_provider(monkeypatch, result=None, status="completed"):
    calls = []

    def post(url, **kwargs):
        calls.append(kwargs)
        return httpx.Response(200, request=httpx.Request("POST", url), json={
            "status": status, "output": [{"type": "message", "content": [
                {"type": "output_text", "text": json.dumps(result or result_data())}]}]})
    monkeypatch.setattr(ai.httpx, "post", post)
    return calls


def test_disabled_does_not_call_provider(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "false")
    monkeypatch.setattr(ai.httpx, "post", lambda *a, **k: pytest.fail("Provider must not be called"))
    with pytest.raises(ai.AIUnavailableError):
        ai.request_analysis({})


def test_structured_request_and_valid_result(configured, monkeypatch):
    calls = mock_provider(monkeypatch)
    result = ai.request_analysis({"evidence": [{"id": 1}]})
    assert result.impact_type == "Mixed"
    assert calls[0]["json"]["store"] is False
    assert calls[0]["json"]["text"]["format"]["strict"] is True
    assert "test-not-a-real-key" not in json.dumps(calls[0]["json"])


@pytest.mark.parametrize("changes", [{"evidence_ids": [999]}, {"confidence": 1.1}, {"impact_type": "Buy"}])
def test_invalid_analysis_rejected(configured, monkeypatch, changes):
    mock_provider(monkeypatch, result_data(**changes))
    with pytest.raises(ai.AIUnavailableError):
        ai.request_analysis({"evidence": [{"id": 1}]})


def test_incomplete_response_rejected(configured, monkeypatch):
    mock_provider(monkeypatch, status="incomplete")
    with pytest.raises(ai.AIUnavailableError):
        ai.request_analysis({"evidence": [{"id": 1}]})


def test_provider_failure_hides_secrets(configured, monkeypatch):
    def fail(*args, **kwargs):
        raise httpx.ConnectError("secret-provider-body")
    monkeypatch.setattr(ai.httpx, "post", fail)
    with pytest.raises(ai.AIUnavailableError) as error:
        ai.request_analysis({"evidence": [{"id": 1}]})
    assert "secret-provider-body" not in str(error.value)


def test_indirect_event_ai_saved_without_fabricating_mapping(db, client, configured, monkeypatch):
    mock_provider(monkeypatch)
    company = Company(ticker="AILLMTEST", name="Test company", description="Energy user", exchange="SET")
    article = NewsArticle(title="Energy costs increase", source="Test", url="https://example.com/ai-test", summary="Costs increase")
    db.add_all([company, article])
    db.flush()
    event = Event(title=article.title, description="Energy costs increase", category="Energy", source_article_id=article.id)
    db.add(event)
    db.flush()
    response = client.post("/api/assessments/generate", json={"company_id": company.id, "event_id": event.id, "use_ai": True})
    assert response.status_code == 201, response.text
    saved = response.json()[0]
    assert saved["methodology"] == "llm_openai_v1"
    assert saved["impact_type"] == "Mixed"
    assert saved["relevant_financial_metrics"]["available"] is False
    assert saved["input_snapshot"]["model"] == "test-model"
    assert saved["supporting_evidence"][0]["id"] == 1
    assert client.get(f"/api/events/{event.id}/companies").json() == []


def test_disabled_ai_api_does_not_save_baseline(db, client, monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "false")
    company = Company(ticker="AIDISABLED", name="Test disabled AI", exchange="SET")
    event = Event(title="Test event", description="Test", category="Energy")
    db.add_all([company, event])
    db.flush()
    response = client.post("/api/assessments/generate", json={"company_id": company.id, "event_id": event.id, "use_ai": True})
    assert response.status_code == 503
    assert client.get(f"/api/companies/{company.id}/assessments").json() == []
