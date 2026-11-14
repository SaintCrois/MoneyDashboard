"""Verify reads reuse session data, expire, and invalidate after a mutation."""
from streamlit.testing.v1 import AppTest


SCRIPT = '''
from unittest.mock import patch
import client.app as app
import streamlit as st

class Response:
    def raise_for_status(self):
        pass
    def json(self):
        return [{"id": 1}]

st.session_state.setdefault("network_reads", 0)
def get(*args, **kwargs):
    st.session_state["network_reads"] += 1
    return Response()

with patch.object(app.requests, "get", get), patch.object(app.requests, "post", return_value=Response()):
    st.button("Local interaction", key="local")
    if st.button("Refresh data", key="refresh"):
        app.clear_api_read_cache()
    if st.button("Mutation", key="mutate"):
        app.api_post("/api/events/process")
    app.api_get("/api/companies")
    app.api_get("/api/companies")
'''


def test_reads_cached_across_reruns_refresh_and_mutation_invalidate():
    app = AppTest.from_string(SCRIPT, default_timeout=15).run()
    assert not app.exception
    assert app.session_state["network_reads"] == 1
    app.button(key="local").click().run()
    assert not app.exception
    assert app.session_state["network_reads"] == 1
    app.button(key="refresh").click().run()
    assert app.session_state["network_reads"] == 2
    app.button(key="mutate").click().run()
    assert app.session_state["network_reads"] == 3
    for key, (_, value) in list(app.session_state["api_read_cache"].items()):
        app.session_state["api_read_cache"][key] = (0, value)
    app.button(key="local").click().run()
    assert not app.exception
    assert app.session_state["network_reads"] == 4
