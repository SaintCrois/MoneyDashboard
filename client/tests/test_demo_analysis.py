"""Checks demo matching and the complete submit -> summary -> back journey."""
import importlib.util
from pathlib import Path

from streamlit.testing.v1 import AppTest

spec = importlib.util.spec_from_file_location("demo_analysis", Path(__file__).parents[1] / "demo_analysis.py")
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)

COMPANY = {"id": 1, "ticker": "PTT", "name": "Test PTT", "industry_name": "Energy"}


def test_ranking_indirect_direct_duplicates_and_unrelated():
    articles = [
        {"id": 1, "title": "Oil supply disruption", "summary": None},
        {"id": 2, "title": "Oil supply disruption", "summary": "Duplicate"},
        {"id": 3, "title": "PTT announces results"},
        {"id": 4, "title": "Sports match today"},
        {"id": 5, "title": "PTTEP update"},
    ]
    result = demo.rank_news(COMPANY, articles)
    assert [item["article"]["id"] for item in result] == [3, 1]
    assert result[1]["groups"] == ["energy"]
    assert demo.rank_news(COMPANY, []) == []


def test_different_companies_get_different_news():
    articles = [{"id": 1, "title": "Oil supply"}, {"id": 2, "title": "Airport passenger travel"}]
    aot = dict(COMPANY, ticker="AOT", industry_name="Tourism")
    assert demo.rank_news(aot, articles)[0]["article"]["id"] == 2
    assert len(demo.rank_news(aot, articles)) == 1


SCRIPT = '''
from unittest.mock import patch
from client.demo_analysis import render_demo
import streamlit as st
company = {"id": 1, "ticker": "PTT", "name": "Test PTT", "industry_name": "Energy"}
def news(**kwargs):
    return [] if st.session_state.get("empty_news") else [{"id": 1, "title": "Oil supply disruption", "url": "https://example.com/news"}]
with patch("client.demo_analysis.time.sleep"), \\
     patch("requests.post", side_effect=AssertionError("No external API allowed")), \\
     patch("httpx.post", side_effect=AssertionError("No AI calls allowed")):
    render_demo([company], news)
'''


def test_demo_process_summary_and_back_without_ai_calls():
    app = AppTest.from_string(SCRIPT, default_timeout=15).run()
    assert not app.exception
    assert any("ยังไม่มีการใช้ AI จริง" in item.value for item in app.info)
    app.button(key="demo_process").click().run()
    assert not app.exception
    assert app.session_state["demo_analysis"]["stage"] == "summary"
    assert any("สรุปผลกระทบตัวอย่าง" in item.value for item in app.subheader)
    assert any("Oil supply disruption" in item.value for item in app.markdown)
    app.button(key="demo_back").click().run()
    assert not app.exception
    assert len(app.selectbox) == 1


def test_no_news_does_not_fabricate_results():
    app = AppTest.from_string(SCRIPT, default_timeout=15).run()
    app.session_state["empty_news"] = True
    app.button(key="demo_process").click().run()
    assert not app.exception
    assert any("ยังไม่มีข่าว" in item.value for item in app.warning)
    assert not any("สรุปผลกระทบตัวอย่าง" in item.value for item in app.subheader)
