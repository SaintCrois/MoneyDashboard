"""AI Investment Impact Radar - Streamlit frontend.

Sprint 1: basic application shell. Data is retrieved exclusively through the
FastAPI backend; Streamlit never connects to PostgreSQL directly.
"""

import os
from typing import Optional

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
REQUEST_TIMEOUT = 5


def api_get(path: str) -> Optional[dict]:
    """Make a GET request to the backend, returning None on failure."""
    try:
        response = requests.get(f"{BACKEND_URL}{path}", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def get_backend_status() -> bool:
    """Return True when the backend /health endpoint responds successfully."""
    data = api_get("/health")
    return data is not None and data.get("status") == "ok"


def get_companies(industry_id: Optional[int] = None) -> list[dict]:
    """Retrieve companies from the backend."""
    path = "/api/companies"
    if industry_id is not None:
        path += f"?industry_id={industry_id}"
    data = api_get(path)
    return data if isinstance(data, list) else []


def get_industries() -> list[dict]:
    """Retrieve industries from the backend."""
    data = api_get("/api/industries")
    return data if isinstance(data, list) else []


def page_dashboard() -> None:
    st.title("AI Investment Impact Radar")
    st.caption("From Global Events to Investment Insights")

    st.divider()
    st.subheader("Dashboard")

    backend_ok = get_backend_status()
    status_color = "green" if backend_ok else "red"
    status_text = "Connected" if backend_ok else "Unavailable"
    st.markdown(
        f"Backend connection: :{status_color}[{status_text}]"
    )

    companies = []
    load_error = None
    try:
        companies = get_companies()
    except Exception as exc:  # pragma: no cover - defensive UI handling
        load_error = str(exc)

    total_companies = len(companies)
    industries = get_industries()
    total_industries = len(industries)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Companies", total_companies)
    col2.metric("Total Industries", total_industries)
    col3.metric("Backend", status_text)

    if load_error:
        st.error(f"Unable to load company data from backend: {load_error}")

    st.subheader("Companies")
    if companies:
        st.table(
            [
                {
                    "ID": c.get("id"),
                    "Ticker": c.get("ticker"),
                    "Name": c.get("name"),
                    "Exchange": c.get("exchange"),
                    "Industry": c.get("industry_name") or "Unassigned",
                }
                for c in companies
            ]
        )
    else:
        st.info("No companies available. Verify the backend is running.")


def page_events() -> None:
    st.title("Events")
    st.caption("From Global Events to Investment Insights")
    st.info("Placeholder: Event management will be implemented in Sprint 2.")
    st.write("This page will display detected events and their categories.")


def page_companies() -> None:
    st.title("Companies")
    st.caption("From Global Events to Investment Insights")
    st.info("Placeholder: detailed company views will be expanded in later sprints.")

    companies = get_companies()
    if companies:
        st.subheader("Listed Companies")
        st.table(
            [
                {
                    "ID": c.get("id"),
                    "Ticker": c.get("ticker"),
                    "Name": c.get("name"),
                    "Exchange": c.get("exchange"),
                    "Industry": c.get("industry_name") or "Unassigned",
                }
                for c in companies
            ]
        )
    else:
        st.warning("Unable to load companies from the backend.")


def page_analysis() -> None:
    st.title("Analysis")
    st.caption("From Global Events to Investment Insights")
    st.info("Placeholder: AI impact analysis will be implemented in Sprint 3.")
    st.write("This page will display investment impact assessments.")


def main() -> None:
    st.set_page_config(
        page_title="AI Investment Impact Radar",
        page_icon=":chart_with_upwards_trend:",
        layout="wide",
    )

    with st.sidebar:
        st.header("AI Investment Impact Radar")
        st.caption("From Global Events to Investment Insights")
        st.divider()
        page = st.radio(
            "Navigation",
            ["Dashboard", "Events", "Companies", "Analysis"],
            index=0,
        )
        st.divider()
        if st.button("Refresh Backend Status"):
            st.rerun()

    if page == "Dashboard":
        page_dashboard()
    elif page == "Events":
        page_events()
    elif page == "Companies":
        page_companies()
    elif page == "Analysis":
        page_analysis()


if __name__ == "__main__":
    main()
