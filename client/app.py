"""AI Investment Impact Radar - Streamlit frontend.

Sprint 1 + Sprint 2: application shell plus a working Events page. All data is
retrieved exclusively through the FastAPI backend; Streamlit never connects to
PostgreSQL directly.
"""

import os
import time
from typing import Any, Optional

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
REQUEST_TIMEOUT = 10
READ_TIMEOUT = 3


def _read_cache():
    """Keep short-lived reads per browser session; plain helper tests stay stateless."""
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    if get_script_run_ctx(suppress_warning=True) is None:
        return None
    return st.session_state.setdefault("api_read_cache", {})


def clear_api_read_cache() -> None:
    cache = _read_cache()
    if cache is not None:
        cache.clear()


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def api_get(path: str, params: Optional[dict] = None) -> Optional[dict]:
    """Make a GET request to the backend, returning None on failure."""
    cache = _read_cache()
    key = (BACKEND_URL, path, tuple(sorted((params or {}).items())))
    now = time.monotonic()
    if cache is not None and key in cache:
        expires, payload = cache[key]
        if now < expires:
            return payload
    try:
        response = requests.get(
            f"{BACKEND_URL}{path}", params=params, timeout=READ_TIMEOUT
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        payload = None
    if cache is not None:
        ttl = 2 if payload is None else (5 if path == "/health" else 30)
        cache[key] = (time.monotonic() + ttl, payload)
    return payload


def api_post(path: str, json: Optional[dict] = None) -> Optional[dict]:
    """Make a POST request to the backend, returning None on failure."""
    clear_api_read_cache()
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


def get_news_sources() -> list[dict]:
    """Retrieve the list of configured news sources."""
    data = api_get("/api/news/sources")
    return data if isinstance(data, list) else []


def filter_articles_by_source(
    articles: list[dict], source_name: Optional[str]
) -> list[dict]:
    """Filter articles by source name. 'All Sources' or None returns all."""
    if not source_name or source_name == "All Sources":
        return articles
    return [a for a in articles if (a.get("source") or "") == source_name]


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


def get_company_events(company_id: int) -> list[dict]:
    data = api_get(f"/api/companies/{company_id}/events")
    return data if isinstance(data, list) else []


# --- Sprint 3 helpers ---

def get_company_financials(company_id: int) -> list[dict]:
    data = api_get(f"/api/companies/{company_id}/financials")
    return data if isinstance(data, list) else []


def get_company_financial_analysis(company_id: int) -> Optional[dict]:
    return api_get(f"/api/companies/{company_id}/financial-analysis")


def get_company_market_data(company_id: int) -> list[dict]:
    data = api_get(f"/api/companies/{company_id}/market-data")
    return data if isinstance(data, list) else []


def get_company_market_analysis(company_id: int) -> Optional[dict]:
    return api_get(f"/api/companies/{company_id}/market-analysis")


def get_company_assessments(company_id: int) -> list[dict]:
    data = api_get(f"/api/companies/{company_id}/assessments")
    return data if isinstance(data, list) else []


def get_event_assessments(event_id: int) -> list[dict]:
    data = api_get(f"/api/events/{event_id}/assessments")
    return data if isinstance(data, list) else []


def get_assessments() -> list[dict]:
    data = api_get("/api/assessments")
    return data if isinstance(data, list) else []


def generate_assessments(company_id: int, event_id: Optional[int] = None) -> Optional[list]:
    payload: dict[str, Any] = {"company_id": company_id}
    if event_id is not None:
        payload["event_id"] = event_id
    data = api_post("/api/assessments/generate", json=payload)
    return data if isinstance(data, list) else None


def generate_ai_assessment(company_id: int, event_id: int) -> Optional[list]:
    """AI gets a longer timeout than ordinary reads; never silently use baseline."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/assessments/generate",
            json={"company_id": company_id, "event_id": event_id, "use_ai": True}, timeout=75,
        )
        if not response.ok:
            st.error(response.json().get("detail", "AI analysis failed."))
            return None
        return response.json()
    except (requests.RequestException, ValueError):
        st.error("AI request could not be confirmed. Refresh saved assessments before retrying.")
        return None


def dashboard_ai_impacts(companies: list[dict]) -> None:
    st.subheader("AI · ผลกระทบรายบริษัท")
    settings = api_get("/api/analysis/status") or {}
    ready = settings.get("ready", False)
    st.caption(f"AI: {settings.get('model') or 'Not configured'} · เรียกวิเคราะห์เฉพาะเมื่อกดปุ่ม ผลลัพธ์เป็นการตีความ ไม่ใช่ข้อเท็จจริงยืนยัน")
    if not ready:
        st.info("เปิด AI_ENABLED และตั้ง OPENAI_API_KEY / OPENAI_MODEL ใน .env ของ backend แล้ว restart เพื่อเปิดใช้งาน AI")
    events = get_events(limit=100)
    if not companies or not events:
        st.info("ต้องมีบริษัทและเหตุการณ์ก่อน ไปหน้า Events เพื่อดึงข่าวและประมวลผลเหตุการณ์")
        return
    event_by_id = {event['id']: event for event in events}
    event_id = st.selectbox("ข่าว/เหตุการณ์ที่ต้องการวิเคราะห์", list(event_by_id),
                            format_func=lambda value: f"#{value} · {event_by_id[value]['title']}")
    company_by_id = {company['id']: company for company in companies}
    defaults = [c['id'] for c in companies if c['ticker'] in ('PTT', 'PTTEP', 'AOT', 'IVL')][:4]
    selected = st.multiselect("บริษัทที่ต้องการเปรียบเทียบ (สูงสุด 4 บริษัท)", list(company_by_id),
                              default=defaults, max_selections=4,
                              format_func=lambda value: company_by_id[value]['ticker'])
    st.caption("วิเคราะห์ได้แม้ข่าวไม่กล่าวถึง ticker โดยตรง ความเกี่ยวข้องทางอ้อมเป็นสมมติฐานของ AI และไม่เปลี่ยน mapping ที่ยืนยันจากข่าว")
    if st.button("วิเคราะห์ผลกระทบด้วย AI", disabled=not ready or not selected, type="primary"):
        for company_id in selected:
            with st.spinner(f"กำลังวิเคราะห์ {company_by_id[company_id]['ticker']}…"):
                result = generate_ai_assessment(company_id, event_id)
            if result:
                st.success(f"บันทึกผล {company_by_id[company_id]['ticker']} แล้ว")
    for company_id in selected:
        company = company_by_id[company_id]
        # API returns newest first. Keep each event's assessment separate.
        saved = next((a for a in get_company_assessments(company_id)
                      if a.get('event_id') == event_id and a.get('methodology') == 'llm_openai_v1'), None)
        with st.container(border=True):
            st.markdown(f"### {company['ticker']} · {company['name']}")
            if not saved:
                st.caption("ยังไม่มีผล AI สำหรับเหตุการณ์นี้")
                continue
            cols = st.columns(3)
            cols[0].metric("Impact", saved.get('impact_type', 'Uncertain'))
            cols[1].metric("Severity", saved.get('impact_severity', 'Unknown'))
            confidence = saved.get('confidence')
            cols[2].metric("Model confidence", f"{confidence:.0%}" if confidence is not None else '—')
            st.caption(f"{saved.get('methodology')} · {_format_dt(saved.get('assessed_at'))} · ความมั่นใจเป็นการประเมินของโมเดล ไม่ใช่โอกาสได้ผลตอบแทน")
            st.write(saved.get('explanation'))
            with st.expander("หลักฐาน ข้อมูลที่ขาด และรายละเอียด"):
                st.write(saved.get('financial_exposure'))
                st.json(saved.get('supporting_evidence') or [])
                st.json(saved.get('missing_information') or [])
    st.divider()


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _format_dt(value: Any) -> str:
    """Format timestamps for assessment views, including missing values."""
    return str(value).replace("T", " ")[:19] if value else "—"


def _ingestion_status_badge(source_result: dict) -> str:
    """Return explicit ingestion status: Success, No Articles, Failed, Partial Success."""
    if source_result.get("final_status"):
        return source_result["final_status"]
    if source_result.get("error"):
        return "Failed"
    parsed = source_result.get("parsed", 0)
    ingested = source_result.get("ingested", 0)
    skipped = source_result.get("skipped", 0)
    if parsed == 0:
        return "No Articles"
    if ingested > 0 or skipped > 0:
        return "Success"
    return "No Articles"


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
    st.markdown(f"Backend connection: :{status_color}[{status_text}]")

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
    # Demo flow is local and never calls the configured AI provider.
    import sys
    from pathlib import Path
    root = str(Path(__file__).resolve().parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)
    from client.demo_analysis import render_demo
    if render_demo(companies, get_articles):
        return

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
                st.session_state["last_ingest_result"] = result
                st.success(
                    f"Ingestion complete: {result.get('ingested', 0)} new, "
                    f"{result.get('skipped_duplicate', 0)} duplicates skipped, "
                    f"{result.get('errors', 0)} source errors."
                )
            else:
                st.session_state["last_ingest_result"] = None
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
            clear_api_read_cache()
            st.rerun()

    # ---- Per-source ingestion results & health summary ----
    last_result = st.session_state.get("last_ingest_result")
    if last_result:
        st.divider()
        st.subheader("Per-Source Ingestion Results")
        sources_data = last_result.get("sources", [])
        if sources_data:
            table_rows = []
            for s in sources_data:
                table_rows.append(
                    {
                        "Source name": s.get("name", "—"),
                        "Feed URL": s.get("url", "—"),
                        "HTTP status": s.get("http_status") if s.get("http_status") is not None else "—",
                        "Content type": s.get("content_type") or "—",
                        "Articles parsed": s.get("parsed", 0),
                        "Articles inserted": s.get("ingested", 0),
                        "Duplicates skipped": s.get("skipped", 0),
                        "Error": s.get("error") or "—",
                        "Final status": _ingestion_status_badge(s),
                    }
                )
            st.table(table_rows)

            # Health summary
            total_sources = len(sources_data)
            reached = sum(
                1 for s in sources_data
                if s.get("http_status") is not None and s.get("error") is None
            )
            failed = sum(1 for s in sources_data if s.get("error") is not None)
            total_parsed = sum(s.get("parsed", 0) for s in sources_data)
            total_inserted = sum(s.get("ingested", 0) for s in sources_data)
            total_skipped = sum(s.get("skipped", 0) for s in sources_data)

            st.subheader("Source Health Summary (Current Run)")
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric("Total sources", total_sources)
            c2.metric("Reached", reached)
            c3.metric("Failed", failed)
            c4.metric("Parsed", total_parsed)
            c5.metric("Inserted", total_inserted)
            c6.metric("Duplicates skipped", total_skipped)
            st.caption(
                "Historical database article counts are shown separately in the Articles section below."
            )

    st.divider()

    # ---- Filters ----
    categories = get_event_categories()
    configured_sources = get_news_sources()
    source_names = [s["name"] for s in configured_sources] if configured_sources else []

    # Fallback: if configured sources not available, derive from articles
    all_articles = get_articles()
    if not source_names:
        source_names = sorted({a.get("source", "") for a in all_articles if a.get("source")})

    col_filter1, col_filter2, col_filter3 = st.columns([2, 1, 1])
    with col_filter1:
        search = st.text_input(
            "Search articles or events",
            placeholder="Keyword search...",
        )
    with col_filter2:
        category_options = ["All"] + categories
        selected_category = st.selectbox("Category", category_options, index=0)
    with col_filter3:
        source_options = ["All Sources"] + source_names
        selected_source = st.selectbox("News Source", source_options, index=0)

    # ---- News Articles ----
    st.subheader("Collected News Articles")
    articles = all_articles  # use already-fetched articles (no extra RSS request)
    filtered_articles = filter_articles_by_source(articles, selected_source)

    if search:
        term = search.lower()
        filtered_articles = [
            a
            for a in filtered_articles
            if term in (a.get("title") or "").lower()
            or term in (a.get("source") or "").lower()
            or term in (a.get("summary") or "").lower()
        ]

    st.caption(
        f"Showing {len(filtered_articles)} of {len(articles)} articles "
        f"(historical database count: {len(articles)})."
    )

    if articles:
        if not filtered_articles:
            st.info("No articles match your current filters (source/search).")
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
                                    f"relevance: {im.get('relevance_score') or '—'})\n"
                                    f"  {im.get('explanation', '')}"
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
                                    f"relevance: {cm.get('relevance_score') or '—'})\n"
                                    f"  {cm.get('explanation', '')}"
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
            ["Dashboard", "Events", "Companies"],
            index=0,
        )
        st.divider()
        backend_ok = get_backend_status()
        status_color = "green" if backend_ok else "red"
        status_text = "Connected" if backend_ok else "Unavailable"
        st.markdown(f"Backend: :{status_color}[{status_text}]")
        if st.button("Refresh Backend Status"):
            clear_api_read_cache()
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
