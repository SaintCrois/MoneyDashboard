"""AI Investment Impact Radar - Streamlit frontend.

Sprint 1 + Sprint 2: application shell plus a working Events page. All data is
retrieved exclusively through the FastAPI backend; Streamlit never connects to
PostgreSQL directly.
"""

import os
from typing import Optional

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
REQUEST_TIMEOUT = 10


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def api_get(path: str, params: Optional[dict] = None) -> Optional[dict]:
    """Make a GET request to the backend, returning None on failure."""
    try:
        response = requests.get(
            f"{BACKEND_URL}{path}", params=params, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def api_post(path: str, json: Optional[dict] = None) -> Optional[dict]:
    """Make a POST request to the backend, returning None on failure."""
    try:
        response = requests.post(
            f"{BACKEND_URL}{path}", json=json, timeout=REQUEST_TIMEOUT
        )
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


def get_articles(
    skip: int = 0, limit: int = 50
) -> list[dict]:
    """Retrieve news articles from the backend."""
    data = api_get("/api/news", params={"skip": skip, "limit": limit})
    return data if isinstance(data, list) else []


def get_article(article_id: int) -> Optional[dict]:
    """Retrieve a single news article by ID."""
    return api_get(f"/api/news/{article_id}")


def ingest_articles() -> Optional[dict]:
    """Trigger news ingestion from configured sources."""
    return api_post("/api/news/ingest")


def get_events(
    skip: int = 0, limit: int = 50, category: Optional[str] = None
) -> list[dict]:
    """Retrieve events from the backend, optionally filtered by category."""
    params: dict = {"skip": skip, "limit": limit}
    if category:
        params["category"] = category
    data = api_get("/api/events", params=params)
    return data if isinstance(data, list) else []


def get_event(event_id: int) -> Optional[dict]:
    """Retrieve a single event by ID."""
    return api_get(f"/api/events/{event_id}")


def process_events() -> Optional[dict]:
    """Trigger processing of unprocessed articles into events."""
    return api_post("/api/events/process")


def get_event_categories() -> list[str]:
    """Retrieve the list of supported event categories."""
    data = api_get("/api/events/categories")
    return [c["category"] for c in data] if isinstance(data, list) else []


def get_event_industries(event_id: int) -> list[dict]:
    """Retrieve industries potentially affected by an event."""
    data = api_get(f"/api/events/{event_id}/industries")
    return data if isinstance(data, list) else []


def get_event_companies(event_id: int) -> list[dict]:
    """Retrieve companies potentially affected by an event."""
    data = api_get(f"/api/events/{event_id}/companies")
    return data if isinstance(data, list) else []


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

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

    backend_ok = get_backend_status()
    if not backend_ok:
        st.error(
            "Backend is unavailable. Start the FastAPI backend to view events and articles."
        )
        return

    # ---- Controls ----
    st.subheader("News & Event Intelligence")
    col_ingest, col_process, col_refresh = st.columns([1, 1, 1])
    with col_ingest:
        if st.button("Ingest News", help="Collect articles from configured sources"):
            with st.spinner("Ingesting news..."):
                result = ingest_articles()
            if result:
                st.success(
                    f"Ingestion complete: {result.get('ingested', 0)} new, "
                    f"{result.get('skipped_duplicate', 0)} duplicates skipped, "
                    f"{result.get('errors', 0)} source errors."
                )
            else:
                st.error("News ingestion failed.")
    with col_process:
        if st.button("Process Events", help="Convert articles into structured events"):
            with st.spinner("Processing events..."):
                result = process_events()
            if result:
                st.success(
                    f"Processing complete: {result.get('processed', 0)} events created, "
                    f"{result.get('errors', 0)} errors."
                )
            else:
                st.error("Event processing failed.")
    with col_refresh:
        if st.button("Refresh", help="Reload articles and events"):
            st.rerun()

    st.divider()

    # ---- Filters ----
    categories = get_event_categories()
    col_filter1, col_filter2 = st.columns([2, 1])
    with col_filter1:
        search = st.text_input(
            "Search articles or events",
            placeholder="Keyword search...",
        )
    with col_filter2:
        category_options = ["All"] + categories
        selected_category = st.selectbox("Category", category_options, index=0)

    # ---- News Articles ----
    st.subheader("Collected News Articles")
    articles = get_articles()
    if articles:
        filtered_articles = articles
        if search:
            term = search.lower()
            filtered_articles = [
                a
                for a in articles
                if term in (a.get("title") or "").lower()
                or term in (a.get("source") or "").lower()
                or term in (a.get("summary") or "").lower()
            ]
        if not filtered_articles:
            st.info("No articles match your search.")
        else:
            for a in filtered_articles[:20]:
                with st.container():
                    st.markdown(
                        f"**[{a.get('title', 'Untitled')}]({a.get('url', '#')})**"
                    )
                    meta = []
                    if a.get("source"):
                        meta.append(f"Source: {a['source']}")
                    if a.get("published_at"):
                        meta.append(f"Published: {a['published_at'][:10]}")
                    st.caption(" | ".join(meta))
                    if a.get("summary"):
                        st.write(a["summary"][:300])
                    st.divider()
    else:
        st.info("No news articles collected yet. Use 'Ingest News' to collect articles.")

    st.divider()

    # ---- Events ----
    st.subheader("Detected Events")
    events = get_events(
        category=None if selected_category == "All" else selected_category
    )
    if events:
        filtered_events = events
        if search:
            term = search.lower()
            filtered_events = [
                e
                for e in events
                if term in (e.get("title") or "").lower()
                or term in (e.get("description") or "").lower()
                or term in (e.get("category") or "").lower()
            ]
        if not filtered_events:
            st.info("No events match your search.")
        else:
            for e in filtered_events[:20]:
                with st.container():
                    st.markdown(f"### {e.get('title', 'Untitled Event')}")
                    meta_cols = st.columns(4)
                    meta_cols[0].caption(f"Category: {e.get('category', 'Uncertain')}")
                    meta_cols[1].caption(
                        f"Method: {e.get('classification_method') or '—'}"
                    )
                    conf = e.get("confidence_score")
                    meta_cols[2].caption(
                        f"Confidence: {conf}" if conf is not None else "Confidence: —"
                    )
                    meta_cols[3].caption(
                        f"Status: {e.get('processing_status', '—')}"
                    )
                    if e.get("description"):
                        st.write(e["description"])
                    if e.get("event_date"):
                        st.caption(f"Event date: {e['event_date'][:10]}")
                    if e.get("source_article_id"):
                        article = get_article(e["source_article_id"])
                        if article:
                            st.caption(
                                f"Source: [{article.get('source', 'Article')}]({article.get('url', '#')})"
                            )

                    # Mappings
                    ind_col, comp_col = st.columns(2)
                    with ind_col:
                        st.markdown("**Potentially affected industries**")
                        industries_map = get_event_industries(e["id"])
                        if industries_map:
                            for im in industries_map:
                                st.write(
                                    f"- {im.get('industry_name', 'Industry')} "
                                    f"(impact: {im.get('impact_type', 'Uncertain')}, "
                                    f"relevance: {im.get('relevance_score') or '—'})"
                                    f"\n  {im.get('explanation', '')}"
                                )
                        else:
                            st.caption("None mapped yet.")
                    with comp_col:
                        st.markdown("**Potentially affected companies**")
                        companies_map = get_event_companies(e["id"])
                        if companies_map:
                            for cm in companies_map:
                                st.write(
                                    f"- {cm.get('company_name', 'Company')} "
                                    f"({cm.get('ticker', '—')}) "
                                    f"(impact: {cm.get('impact_type', 'Uncertain')}, "
                                    f"exposure: {cm.get('exposure_type', '—')}, "
                                    f"relevance: {cm.get('relevance_score') or '—'})"
                                    f"\n  {cm.get('explanation', '')}"
                                )
                        else:
                            st.caption("None mapped yet.")
                    st.divider()
    else:
        st.info("No events detected yet. Use 'Process Events' to create events from articles.")


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
        backend_ok = get_backend_status()
        status_color = "green" if backend_ok else "red"
        status_text = "Connected" if backend_ok else "Unavailable"
        st.markdown(f"Backend: :{status_color}[{status_text}]")
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
