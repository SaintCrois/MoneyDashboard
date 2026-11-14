"""AI Investment Impact Radar - Streamlit frontend.

All data is retrieved exclusively through the FastAPI backend; Streamlit never
connects to PostgreSQL directly.
"""

import json
import os
from typing import Any, Optional

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
REQUEST_TIMEOUT = 15


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30, show_spinner=False)
def _cached_get(path: str, params_key: tuple):
    """GET with a short cache. Raises on failure so errors are never cached."""
    response = requests.get(
        f"{BACKEND_URL}{path}", params=dict(params_key) or None, timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    return response.json()


def api_get(path: str, params: Optional[dict] = None) -> Optional[dict]:
    # Streamlit reruns the whole script on every interaction; without the cache
    # each rerun repeats every backend call.
    key = tuple(sorted((params or {}).items()))
    try:
        if not st.runtime.exists():  # plain Python (unit tests, scripts): no cache
            return _cached_get.__wrapped__(path, key)
        return _cached_get(path, key)
    except Exception:
        return None


def api_post(path: str, json_body: Optional[dict] = None) -> Optional[dict]:
    try:
        response = requests.post(
            f"{BACKEND_URL}{path}", json=json_body, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        _cached_get.clear()  # a write happened; cached reads may be stale
        return response.json()
    except Exception:
        return None


def get_backend_status() -> bool:
    data = api_get("/health")
    return data is not None and data.get("status") == "ok"


def get_companies(industry_id: Optional[int] = None) -> list[dict]:
    path = "/api/companies"
    if industry_id is not None:
        path += f"?industry_id={industry_id}"
    data = api_get(path)
    return data if isinstance(data, list) else []


def get_company(company_id: int) -> Optional[dict]:
    return api_get(f"/api/companies/{company_id}")


def get_industries() -> list[dict]:
    data = api_get("/api/industries")
    return data if isinstance(data, list) else []


def sync_companies_from_set() -> Optional[dict]:
    return api_post("/api/companies/sync")


def get_articles(
    skip: int = 0,
    limit: int = 50,
    source: Optional[str] = None,
    thailand_relevance: Optional[str] = None,
    language: Optional[str] = None,
) -> list[dict]:
    params: dict = {"skip": skip, "limit": limit}
    if source:
        params["source"] = source
    if thailand_relevance:
        params["thailand_relevance"] = thailand_relevance
    if language:
        params["language"] = language
    data = api_get("/api/news", params=params)
    return data if isinstance(data, list) else []


def get_article(article_id: int) -> Optional[dict]:
    return api_get(f"/api/news/{article_id}")


def ingest_articles() -> Optional[dict]:
    return api_post("/api/news/ingest")


def get_news_sources() -> list[dict]:
    data = api_get("/api/news/sources")
    return data if isinstance(data, list) else []


def filter_articles_by_source(articles: list[dict], source_name: Optional[str]) -> list[dict]:
    """Client-side filter fallback."""
    if not source_name or source_name == "All Sources":
        return articles
    return [a for a in articles if (a.get("source") or "") == source_name]


def get_events(skip: int = 0, limit: int = 50, category: Optional[str] = None) -> list[dict]:
    params: dict = {"skip": skip, "limit": limit}
    if category:
        params["category"] = category
    data = api_get("/api/events", params=params)
    return data if isinstance(data, list) else []


def get_event(event_id: int) -> Optional[dict]:
    return api_get(f"/api/events/{event_id}")


def process_events() -> Optional[dict]:
    return api_post("/api/events/process")


def get_event_categories() -> list[str]:
    data = api_get("/api/events/categories")
    return [c["category"] for c in data] if isinstance(data, list) else []


def get_event_industries(event_id: int) -> list[dict]:
    data = api_get(f"/api/events/{event_id}/industries")
    return data if isinstance(data, list) else []


def get_event_companies(event_id: int) -> list[dict]:
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
    data = api_post("/api/assessments/generate", json_body=payload)
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
        _cached_get.clear()  # new assessment saved; cached reads may be stale
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

def _ingestion_status_badge(source_result: dict) -> str:
    # Preserve explicit final_status when provided by backend.
    fs = source_result.get("final_status")
    if fs:
        return fs
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


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else [parsed]
        except Exception:
            return [value]
    return [value]


def _as_dict(value: Any) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _format_dt(value: Any) -> str:
    if not value:
        return "—"
    if isinstance(value, str):
        return value.replace("T", " ")[:19]
    try:
        return str(value)
    except Exception:
        return "—"


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

    companies = get_companies()
    industries = get_industries()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Companies", len(companies))
    col2.metric("Total Industries", len(industries))
    col3.metric("Backend", status_text)

    # Demo flow is local and never calls the configured AI provider.
    import sys
    from pathlib import Path
    root = str(Path(__file__).resolve().parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)
    from client.demo_analysis import render_demo
    def _load_demo_articles(limit: int = 100) -> list[dict]:
        # The news API returns at most 100 rows per call; read several pages so
        # Thai and global sources are both in the pool the demo ranks.
        pool: list[dict] = []
        for skip in range(0, 400, 100):
            page = get_articles(skip=skip, limit=100)
            pool.extend(page)
            if len(page) < 100:
                break
        return pool

    if render_demo(companies, _load_demo_articles):
        return

    st.subheader("Companies")
    col_sync1, col_sync2 = st.columns([1, 3])
    with col_sync1:
        if st.button("Sync Companies from SET", help="Import/synchronize listed company reference data"):
            with st.spinner("Synchronizing companies..."):
                result = sync_companies_from_set()
            if result is None:
                st.error("Synchronization request failed (backend unavailable or error).")
            else:
                st.session_state["last_company_sync"] = result
                if result.get("errors") and (result.get("imported", 0) + result.get("updated", 0)) == 0 and result.get("retrieved", 0) == 0:
                    st.warning(result.get("message") or "Synchronization completed with issues.")
                else:
                    st.success(result.get("message") or "Synchronization completed.")
    with col_sync2:
        last_sync = st.session_state.get("last_company_sync")
        if last_sync:
            st.caption(f"Last synchronization time: {_format_dt(last_sync.get('last_sync_time'))}")

    last_sync = st.session_state.get("last_company_sync")
    if last_sync:
        st.markdown("**Synchronization results**")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Retrieved", last_sync.get("retrieved", 0))
        c2.metric("Imported", last_sync.get("imported", 0))
        c3.metric("Updated", last_sync.get("updated", 0))
        c4.metric("Duplicates skipped", last_sync.get("duplicates_skipped", 0))
        c5.metric("Errors", len(last_sync.get("errors") or []))
        st.caption(
            f"Source: {last_sync.get('source', 'unknown')} | "
            f"Fallback used: {'Yes' if last_sync.get('used_fallback') else 'No'}"
        )
        errs = last_sync.get("errors") or []
        if errs:
            with st.expander("Synchronization errors / notes"):
                for e in errs:
                    st.write(f"- {e}")

    st.divider()
    if companies:
        st.table(
            [
                {
                    "ID": c.get("id"),
                    "Ticker": c.get("ticker"),
                    "Name": c.get("name"),
                    "Market": c.get("market") or c.get("exchange"),
                    "Industry": c.get("industry_name") or "Unassigned",
                    "Sector": c.get("sector") or "—",
                    "Source": c.get("source") or "—",
                }
                for c in companies
            ]
        )
    else:
        st.info("No companies available. Use 'Sync Companies from SET' or seed/create companies.")


def page_events() -> None:
    st.title("Events")
    st.caption("From Global Events to Investment Insights")

    backend_ok = get_backend_status()
    if not backend_ok:
        st.error("Backend is unavailable. Start the FastAPI backend to view events and articles.")
        return

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
                    f"{result.get('errors', 0)} source errors. Status: {result.get('status')}"
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
            st.rerun()

    # Source status (configured + last known ingestion status)
    st.divider()
    st.subheader("News Source Status")
    configured_sources = get_news_sources()
    if configured_sources:
        src_rows = []
        for s in configured_sources:
            src_rows.append(
                {
                    "Publisher": s.get("publisher") or s.get("name"),
                    "Source name": s.get("name"),
                    "Feed URL": s.get("url") or "—",
                    "HTTP status": s.get("http_status") if s.get("http_status") is not None else "—",
                    "Content type": s.get("content_type") or "—",
                    "Parsed": s.get("parsed_count") if s.get("parsed_count") is not None else "—",
                    "Inserted": s.get("inserted_count") if s.get("inserted_count") is not None else "—",
                    "Duplicates": s.get("duplicate_count") if s.get("duplicate_count") is not None else "—",
                    "Errors": s.get("error_message") or "—",
                    "Last successful ingestion": _format_dt(s.get("last_successful_ingestion_at")),
                    "Final status": s.get("final_status") or ("Unavailable" if not s.get("enabled") else "Not checked"),
                    "Notes": s.get("notes") or "—",
                }
            )
        st.dataframe(pd.DataFrame(src_rows), use_container_width=True)
        st.caption(
            "Status distinguishes Success, No Articles, Failed, Partial Success, Unavailable. "
            "HTTP 200 alone is not reported as success without verified parsed/ingested articles."
        )
    else:
        st.info("No configured news sources returned by backend.")

    # Per-run results
    last_result = st.session_state.get("last_ingest_result")
    if last_result:
        st.subheader("Per-Source Ingestion Results (Current Run)")
        sources_data = last_result.get("sources", [])
        if sources_data:
            table_rows = []
            for s in sources_data:
                table_rows.append(
                    {
                        "Publisher": s.get("publisher") or s.get("name", "—"),
                        "Source name": s.get("name", "—"),
                        "Feed URL": s.get("url", "—"),
                        "HTTP status": s.get("http_status") if s.get("http_status") is not None else "—",
                        "Content type": s.get("content_type") or "—",
                        "Parsed": s.get("parsed", 0),
                        "Inserted": s.get("ingested", 0),
                        "Duplicates skipped": s.get("skipped", 0),
                        "Error": s.get("error") or "—",
                        "Final status": _ingestion_status_badge(s),
                        "Last successful ingestion": _format_dt(s.get("last_successful_ingestion_at")),
                    }
                )
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True)

    st.divider()

    categories = get_event_categories()
    configured_sources = get_news_sources()
    source_names = [s["name"] for s in configured_sources] if configured_sources else []
    all_articles = get_articles(limit=100)
    if not source_names:
        source_names = sorted({a.get("source", "") for a in all_articles if a.get("source")})

    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([2, 1, 1, 1, 1])
    with col_f1:
        search = st.text_input("Search articles or events", placeholder="Keyword search...")
    with col_f2:
        category_options = ["All"] + categories
        selected_category = st.selectbox("Event Category", category_options, index=0)
    with col_f3:
        source_options = ["All Sources"] + source_names
        selected_source = st.selectbox("News Source", source_options, index=0)
    with col_f4:
        rel_options = ["All", "Thailand-focused", "Thailand-related", "International", "Uncertain"]
        selected_relevance = st.selectbox("Thailand relevance", rel_options, index=0)
    with col_f5:
        langs = sorted({(a.get("language") or "unknown") for a in all_articles})
        lang_options = ["All"] + langs
        selected_lang = st.selectbox("Language", lang_options, index=0)

    # Fetch with backend filters where possible
    backend_source = None if selected_source == "All Sources" else selected_source
    backend_rel = None if selected_relevance == "All" else selected_relevance
    backend_lang = None if selected_lang == "All" else selected_lang
    articles = get_articles(limit=100, source=backend_source, thailand_relevance=backend_rel, language=backend_lang)

    st.subheader("Collected News Articles")
    filtered_articles = articles
    if search:
        term = search.lower()
        filtered_articles = [
            a for a in filtered_articles
            if term in (a.get("title") or "").lower()
            or term in (a.get("source") or "").lower()
            or term in (a.get("summary") or "").lower()
            or term in (a.get("relevance_reason") or "").lower()
        ]

    st.caption(
        f"Showing {len(filtered_articles)} of {len(articles)} articles (current query). "
        "Uncertain articles are stored but must not be treated as Thailand-focused."
    )

    if articles:
        if not filtered_articles:
            st.info("No articles match your current filters.")
        else:
            for a in filtered_articles[:25]:
                with st.container():
                    st.markdown(f"**[{a.get('title', 'Untitled')}]({a.get('url', '#')})**")
                    meta = []
                    if a.get("source"):
                        meta.append(f"Source: {a['source']}")
                    if a.get("published_at"):
                        meta.append(f"Published: {str(a['published_at'])[:10]}")
                    if a.get("language"):
                        meta.append(f"Language: {a['language']}")
                    rel = a.get("thailand_relevance") or "Unclassified"
                    meta.append(f"Thailand relevance: {rel}")
                    st.caption(" | ".join(meta))
                    if a.get("relevance_reason"):
                        st.caption(f"Relevance reasoning: {a.get('relevance_reason')}")
                    if a.get("summary"):
                        st.write(str(a["summary"])[:350])
                    st.divider()
    else:
        st.info("No news articles collected yet. Use 'Ingest News' to collect articles.")

    st.divider()

    st.subheader("Detected Events")
    events = get_events(category=None if selected_category == "All" else selected_category)
    if events:
        filtered_events = events
        if search:
            term = search.lower()
            filtered_events = [
                e for e in events
                if term in (e.get("title") or "").lower()
                or term in (e.get("description") or "").lower()
                or term in (e.get("category") or "").lower()
            ]
        if not filtered_events:
            st.info("No events match your search.")
        else:
            import sys
            from pathlib import Path
            root = str(Path(__file__).resolve().parent.parent)
            if root not in sys.path:
                sys.path.insert(0, root)
            from client.demo_analysis import related_companies as _related_companies
            all_companies = get_companies()
            for e in filtered_events[:20]:
                with st.container():
                    st.markdown(f"### {e.get('title', 'Untitled Event')}")
                    meta_cols = st.columns(4)
                    meta_cols[0].caption(f"Category: {e.get('category', 'Uncertain')}")
                    meta_cols[1].caption(f"Method: {e.get('classification_method') or '—'}")
                    conf = e.get("confidence_score")
                    meta_cols[2].caption(f"Confidence: {conf}" if conf is not None else "Confidence: —")
                    meta_cols[3].caption(f"Status: {e.get('processing_status', '—')}")
                    if e.get("description"):
                        st.write(e["description"])
                    if e.get("event_date"):
                        st.caption(f"Event date: {str(e['event_date'])[:10]}")
                    if e.get("source_article_id"):
                        article = get_article(e["source_article_id"])
                        if article:
                            st.caption(
                                f"Source: [{article.get('source', 'Article')}]({article.get('url', '#')}) | "
                                f"Thailand relevance: {article.get('thailand_relevance') or 'Unclassified'}"
                            )

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
                        st.markdown("**Company associations (evidence-backed)**")
                        companies_map = get_event_companies(e["id"])
                        if companies_map:
                            for cm in companies_map:
                                mconf = cm.get("match_confidence") or "—"
                                st.markdown(
                                    f"**{cm.get('company_name', 'Company')} ({cm.get('ticker', '—')})** "
                                    f"— Match confidence: `{mconf}` "
                                    f"(impact: {cm.get('impact_type', 'Uncertain')}, "
                                    f"exposure: {cm.get('exposure_type', '—')}, "
                                    f"relevance: {cm.get('relevance_score') or '—'})"
                                )
                                st.caption(f"Reason: {cm.get('match_reason') or cm.get('explanation') or '—'}")
                                evidence = cm.get("evidence")
                                if evidence:
                                    try:
                                        ev_obj = json.loads(evidence) if isinstance(evidence, str) else evidence
                                        if isinstance(ev_obj, dict):
                                            if ev_obj.get("article_url"):
                                                st.caption(f"Supporting article: {ev_obj.get('article_title') or ''} ({ev_obj.get('article_url')})")
                                            matches = ev_obj.get("matches") or []
                                            if matches:
                                                st.caption("Supporting evidence: " + "; ".join(
                                                    [str(m.get("snippet") or m.get("matched") or m) for m in matches[:3]]
                                                ))
                                    except Exception:
                                        st.caption(f"Supporting evidence: {str(evidence)[:300]}")
                                if mconf == "Low":
                                    st.warning("Low-confidence association: must not be treated as confirmed (shown only if present).")
                        else:
                            st.caption("No sufficiently supported company associations. (Low/uncertain matches remain unassigned.)")
                        # Keyword-level view, kept apart from the evidence-backed list above.
                        confirmed = {cm.get("ticker") for cm in companies_map or []}
                        indirect = [
                            r for r in _related_companies(e.get("title"), e.get("description"), all_companies,
                                                            level=st.session_state.get("match_level", "medium"))
                            if r["ticker"] not in confirmed
                        ]
                        if indirect:
                            st.markdown("**อาจเกี่ยวข้องทางอ้อม (จับจากคำในหมวดธุรกิจ ยังไม่ยืนยัน)**")
                            for r in indirect:
                                st.caption(f"{r['ticker']} · {r['reason']}")
                    st.divider()
    else:
        st.info("No events detected yet. Use 'Process Events' to create events from articles.")


def page_companies() -> None:
    st.title("Companies")
    st.caption("Company financial and market analysis")

    backend_ok = get_backend_status()
    if not backend_ok:
        st.error("Backend is unavailable. Start the FastAPI backend to view company analysis.")
        return

    companies = get_companies()
    if not companies:
        st.info("No companies available. Use Dashboard > Sync Companies from SET or seed/create companies.")
        return

    options = {f"{c['ticker']} - {c['name']}": c for c in companies}
    selected_label = st.selectbox("Select a company", list(options.keys()))
    company = options[selected_label]
    company_id = company["id"]

    st.subheader("Company Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ticker", company.get("ticker", "—"))
    c2.metric("Name", company.get("name", "—"))
    c3.metric("Market", company.get("market") or company.get("exchange") or "—")
    c4.metric("Industry", company.get("industry_name") or "Unassigned")
    if company.get("sector"):
        st.caption(f"Sector: {company.get('sector')}")

    st.divider()

    # Financial analysis
    st.subheader("Financial Analysis")
    fin_analysis = get_company_financial_analysis(company_id)
    if fin_analysis is None:
        st.error("Unable to load financial analysis from backend.")
    else:
        records = fin_analysis.get("records", [])
        calc_metrics = fin_analysis.get("calculated_metrics", [])
        unavailable = fin_analysis.get("unavailable_metrics", [])
        sources = fin_analysis.get("data_sources", [])
        notes = fin_analysis.get("notes", [])

        st.caption("**Source facts (reported):** stored financial records as provided/imported.")
        if records:
            df = pd.DataFrame([
                {
                    "Fiscal Year": r.get("fiscal_year"),
                    "Period": r.get("reporting_period") or r.get("fiscal_year"),
                    "Revenue": r.get("revenue"),
                    "Net Profit": r.get("net_profit"),
                    "Operating Income": r.get("operating_income"),
                    "Total Debt": r.get("total_debt"),
                    "Shareholders' Equity": r.get("shareholders_equity"),
                    "Data Source": r.get("data_source"),
                    "Estimate": r.get("is_estimate"),
                }
                for r in records
            ])
            st.dataframe(df, use_container_width=True)

            chart_df = pd.DataFrame([
                {"Period": (r.get("reporting_period") or str(r.get("fiscal_year"))),
                 "Revenue": r.get("revenue"),
                 "Net Profit": r.get("net_profit")}
                for r in records
            ]).set_index("Period")
            if not chart_df.dropna(how="all").empty:
                st.markdown("**Revenue and Net Income Trends (reported figures)**")
                st.line_chart(chart_df)

            st.caption("**Calculated financial metrics (derived from reported figures):**")
            if calc_metrics:
                calc_rows = []
                for m in calc_metrics:
                    row = {"Period": m.get("reporting_period") or m.get("fiscal_year")}
                    row.update(m.get("calculated", {}))
                    calc_rows.append(row)
                st.dataframe(pd.DataFrame(calc_rows), use_container_width=True)
        else:
            st.info("No financial records available. Add records via API or CSV import.")

        st.caption(f"Financial data sources: {', '.join(sources) if sources else 'none recorded.'}")
        if unavailable:
            st.warning(f"Unavailable metrics (insufficient data): {', '.join(sorted(set(unavailable)))}")
        for n in notes:
            st.info(f"Note: {n}")

    st.divider()

    # Market analysis
    st.subheader("Market Analysis")
    mkt_analysis = get_company_market_analysis(company_id)
    if mkt_analysis is None:
        st.error("Unable to load market analysis from backend.")
    else:
        m_records = mkt_analysis.get("records", [])
        indicators = mkt_analysis.get("indicators", {})
        m_unavail = mkt_analysis.get("unavailable_indicators", [])
        m_sources = mkt_analysis.get("data_sources", [])
        m_notes = mkt_analysis.get("notes", [])
        latest_update = mkt_analysis.get("latest_update")

        st.caption("**Market data (observed/reported records):**")
        if m_records:
            mdf = pd.DataFrame([
                {
                    "Date": str(r.get("recorded_at") or "")[:10],
                    "Open": r.get("open_price"),
                    "High": r.get("high_price"),
                    "Low": r.get("low_price"),
                    "Close": r.get("close_price") or r.get("stock_price"),
                    "Volume": r.get("trading_volume"),
                    "Daily % Change": r.get("daily_change_pct"),
                    "Source": r.get("data_source"),
                    "Delayed": r.get("is_delayed"),
                    "Estimate": r.get("is_estimate"),
                }
                for r in m_records
            ])
            st.dataframe(mdf, use_container_width=True)

            price_df = pd.DataFrame([
                {
                    "Date": str(r.get("recorded_at") or "")[:10],
                    "Price": r.get("close_price") or r.get("stock_price"),
                    "Volume": r.get("trading_volume"),
                }
                for r in m_records
            ]).set_index("Date")
            if not price_df[["Price"]].dropna(how="all").empty:
                st.markdown("**Stock Price History (reported)**")
                st.line_chart(price_df[["Price"]])
            if not price_df[["Volume"]].dropna(how="all").empty:
                st.markdown("**Trading Volume (reported)**")
                st.bar_chart(price_df[["Volume"]])

            st.caption("**Calculated market indicators (derived from records):**")
            ind_rows = []
            for k in ("latest_price", "daily_change_pct", "average_trading_volume", "volatility"):
                if k in indicators:
                    ind_rows.append({"Indicator": k, "Value": indicators[k]})
            if "volume_comparison" in indicators:
                vc = indicators["volume_comparison"]
                ind_rows.append({"Indicator": "volume_ratio", "Value": vc.get("volume_ratio")})
            if ind_rows:
                st.table(ind_rows)
        else:
            st.info("No market data available. Add records via API or CSV import.")

        if latest_update:
            st.caption(f"Latest available data timestamp: {latest_update}")
        st.caption(f"Market data sources: {', '.join(m_sources) if m_sources else 'none recorded.'}")
        if indicators.get("latest_is_delayed"):
            st.warning("Latest market data is marked as delayed.")
        if indicators.get("latest_is_estimate"):
            st.warning("Latest market data is marked as estimate/demonstration (not actual market price).")
        if m_unavail:
            st.warning(f"Unavailable indicators: {', '.join(sorted(set(m_unavail)))}")
        for n in m_notes:
            st.info(f"Note: {n}")


def page_analysis() -> None:
    st.title("Analysis")
    st.caption("AI Investment Impact Assessment")

    backend_ok = get_backend_status()
    if not backend_ok:
        st.error("Backend is unavailable. Start the FastAPI backend to view assessments.")
        return

    companies = get_companies()
    if not companies:
        st.info("No companies available. Seed, sync, or create companies first.")
        return

    options = {f"{c['ticker']} - {c['name']}": c for c in companies}
    selected_label = st.selectbox("Select a company", list(options.keys()))
    company = options[selected_label]
    company_id = company["id"]

    related_events = get_company_events(company_id)
    event_options = {"All mapped events (supported matches only)": None}
    for e in related_events:
        event_options[f"[{e.get('category')}] {e.get('title')} (id={e.get('id')})"] = e.get("id")
    selected_event_label = st.selectbox("Related event", list(event_options.keys()))
    selected_event_id = event_options[selected_event_label]

    st.markdown(
        "**Note:** Assessments use updated company-event relationships and must not rely on "
        "weak or incorrect associations. They combine source facts, calculated metrics, "
        "market indicators, and baseline interpretations. Research support only — not "
        "guaranteed predictions or buy/sell recommendations."
    )

    if st.button("Generate Assessment", type="primary"):
        with st.spinner("Generating assessment..."):
            result = generate_assessments(company_id, selected_event_id)
        if result is None:
            st.error("Assessment generation failed. Check backend availability and inputs.")
        elif len(result) == 0:
            st.warning(
                "No assessments generated. The company may have no sufficiently supported "
                "event mappings. Run event processing/mapping or select a specific event."
            )
        else:
            st.success(f"Generated {len(result)} assessment(s).")

    st.divider()
    st.subheader("Existing Assessments")
    assessments = get_company_assessments(company_id)
    if not assessments:
        st.info("No assessments found for this company yet. Generate one above.")
        return

    for a in assessments:
        with st.container():
            st.markdown(f"### {a.get('event_title') or 'Event'}")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Impact", a.get("impact_type") or "Uncertain")
            m2.metric("Severity", a.get("impact_severity") or "Unknown")
            m3.metric("Risk", a.get("risk_level") or "—")
            conf = a.get("confidence")
            m4.metric("Confidence", f"{conf}" if conf is not None else "—")

            st.caption(
                f"Company: {a.get('company_name') or company.get('name')} ({a.get('company_ticker') or company.get('ticker')}) | "
                f"Category: {a.get('event_category') or '—'} | "
                f"Methodology: {a.get('methodology') or '—'} | "
                f"Assessed: {_format_dt(a.get('assessed_at') or a.get('created_at'))}"
            )

            st.markdown("**Interpretation (explanation):**")
            st.write(a.get("explanation") or "No explanation available.")
            st.markdown("**Financial exposure (interpretation):**")
            st.write(a.get("financial_exposure") or "Not available.")

            fin_m = _as_dict(a.get("relevant_financial_metrics"))
            mkt_m = _as_dict(a.get("relevant_market_indicators"))
            evidence = _as_list(a.get("supporting_evidence"))
            missing = _as_list(a.get("missing_information"))

            col_f, col_m = st.columns(2)
            with col_f:
                st.markdown("**Relevant financial metrics:**")
                st.json(fin_m) if fin_m else st.caption("None available.")
            with col_m:
                st.markdown("**Relevant market indicators:**")
                st.json(mkt_m) if mkt_m else st.caption("None available.")

            st.markdown("**Supporting evidence & source references:**")
            if evidence:
                for ev in evidence:
                    if isinstance(ev, dict):
                        etype = ev.get("type", "evidence")
                        desc = ev.get("description") or ev.get("source") or ev.get("industry") or ""
                        url = ev.get("url")
                        if url:
                            st.markdown(f"- **{etype}**: [{desc or url}]({url})")
                        else:
                            st.write({k: v for k, v in ev.items() if v is not None})
                    else:
                        st.write(ev)
            else:
                st.caption("No supporting evidence recorded.")

            st.markdown("**Missing information & limitations:**")
            if missing:
                for m in missing:
                    st.warning(str(m))
            else:
                st.caption("No major gaps recorded.")
            st.divider()


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
        page = st.radio("Navigation", ["Dashboard", "Events", "Companies", "Analysis"], index=0)
        st.divider()
        backend_ok = get_backend_status()
        status_color = "green" if backend_ok else "red"
        status_text = "Connected" if backend_ok else "Unavailable"
        st.markdown(f"Backend: :{status_color}[{status_text}]")
        st.divider()
        import sys
        from pathlib import Path
        _root = str(Path(__file__).resolve().parent.parent)
        if _root not in sys.path:
            sys.path.insert(0, _root)
        from client.demo_analysis import MATCH_LEVELS
        st.select_slider(
            "ความเข้มของการจับคู่ข่าวกับหุ้น",
            options=list(MATCH_LEVELS),
            value="medium",
            format_func=lambda k: {"strict": "เข้ม", "medium": "กลาง", "loose": "หลวม"}[k],
            key="match_level",
            help="ใช้กับเดโมในหน้า Dashboard และรายการ 'อาจเกี่ยวข้องทางอ้อม' ในหน้า Events",
        )
        st.caption(MATCH_LEVELS[st.session_state.get("match_level", "medium")])
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
