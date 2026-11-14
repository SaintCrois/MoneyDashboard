"""Dashboard renders stored AI results and invokes AI only on an explicit click."""
from streamlit.testing.v1 import AppTest


SCRIPT = '''
from unittest.mock import patch
import client.app as app

companies = [{"id": 1, "ticker": "PTT", "name": "Test PTT"}]
saved = [{"event_id": 2, "methodology": "llm_openai_v1", "impact_type": "Mixed",
          "impact_severity": "Medium", "confidence": 0.6, "explanation": "AI interpretation",
          "assessed_at": "2026-11-14T00:00:00Z", "supporting_evidence": [], "missing_information": []}]
with patch.object(app, "api_get", return_value={"ready": True, "model": "mock-model"}), \\
     patch.object(app, "get_events", return_value=[{"id": 2, "title": "Oil event"}]), \\
     patch.object(app, "get_company_assessments", return_value=saved), \\
     patch.object(app, "generate_ai_assessment", return_value=saved) as generate:
    app.dashboard_ai_impacts(companies)
    app.st.session_state["provider_calls"] = generate.call_count
'''


def test_dashboard_saved_result_and_explicit_generation():
    app = AppTest.from_string(SCRIPT).run()
    assert not app.exception
    assert app.session_state["provider_calls"] == 0
    assert any(metric.value == "Mixed" for metric in app.metric)
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state["provider_calls"] == 1
