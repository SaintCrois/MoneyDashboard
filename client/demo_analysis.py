"""Local demonstration of the analysis journey. Never calls an AI provider."""
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import streamlit as st

NOTICE = "Demo — เป็นเพียงการสาธิต ยังไม่มีการใช้ AI จริง และไม่มีการส่งข่าวไปยังผู้ให้บริการ AI"

# The matching rules live in the backend so the web app and this demo share one
# copy. Loaded by path: "app" would otherwise resolve to client/app.py here.
import importlib.util as _ilu
from pathlib import Path as _Path

_spec = _ilu.spec_from_file_location(
    "whymove_keyword_insight",
    _Path(__file__).resolve().parent.parent / "server" / "app" / "services" / "keyword_insight.py",
)
_ki = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_ki)
SCENARIOS = _ki.SCENARIOS
MATCH_LEVELS = _ki.MATCH_LEVELS
contains = _ki.contains
passes_level = _ki.passes_level
rank_news = _ki.rank_news
related_companies = _ki.related_companies


def show_news(items):
    for index, item in enumerate(items, 1):
        article = item["article"]
        st.write(f"{index}. {article.get('title') or 'Untitled'}")
        st.caption(f"{article.get('source') or 'Unknown source'} · {article.get('published_at') or 'ไม่ทราบวันที่'}")
        st.caption(item["reason"])
        url = article.get("url") or ""
        if urlparse(url).scheme in ("http", "https") and urlparse(url).netloc:
            st.link_button(f"อ่านข่าวต้นทาง #{index}", url)


def render_demo(companies, load_articles):
    st.subheader("วิเคราะห์ผลกระทบต่อบริษัท · Demo")
    st.info(NOTICE)
    state = st.session_state.get("demo_analysis")
    if state and state["stage"] == "summary":
        company, items = state["company"], state["items"]
        st.subheader(f"สรุปผลกระทบตัวอย่าง · {company['ticker']}")
        st.caption(f"{company['name']} · {state['created_at']} · วิธี: จับคำสำคัญ + ข้อความสถานการณ์ที่เตรียมไว้")
        st.metric("ข่าวที่อาจเกี่ยวข้องในรอบนี้", len(items))
        st.caption(f"คัดจากข่าวล่าสุดที่โหลด {state['loaded_count']} รายการ แสดงสูงสุด 8 ข่าว ไม่ใช่จำนวนข่าวทั้งหมดในระบบ")
        st.warning("ข้อความต่อไปนี้เป็นสถานการณ์ตัวอย่างจากหมวดคำที่พบ ไม่ใช่การอ่านและทำความเข้าใจข่าวด้วย AI และไม่ยืนยันว่าบริษัทได้รับผลกระทบจริง")
        groups = sorted({group for item in items for group in item["groups"]})
        if not groups:
            st.write("พบการกล่าวถึงบริษัท แต่ยังไม่มีข้อมูลเพียงพอระบุทิศทางผลกระทบ")
        for group in groups:
            scenario = SCENARIOS[group]
            with st.container(border=True):
                st.markdown(f"**{scenario['impact']}**")
                st.write(scenario["effect"])
                refs = [str(index) for index, item in enumerate(items, 1) if group in item["groups"]]
                st.caption("เกิดจากคำสำคัญในข่าวหมายเลข " + ", ".join(refs))
                st.write("สิ่งที่ควรตรวจสอบ: " + scenario["check"])
        st.caption("ไม่มีการคำนวณราคาหุ้น ผลตอบแทน หรือคะแนนความมั่นใจของ AI ในเดโมนี้")
        with st.expander("ข่าวที่ใช้ประกอบการสาธิต", expanded=True):
            show_news(items)
        if st.button("← กลับไปเลือกบริษัท", key="demo_back"):
            del st.session_state["demo_analysis"]
            st.rerun()
        return True

    if not companies:
        st.info("ยังไม่มีบริษัท กรุณาเชื่อมต่อ backend และ seed หรือ sync บริษัทก่อน")
        return False
    lookup = {c["id"]: c for c in companies}
    company_id = st.selectbox("เลือกบริษัท", list(lookup), key="demo_company",
                              format_func=lambda value: f"{lookup[value]['ticker']} · {lookup[value]['name']}")
    st.caption("ระบบจะคัดข่าวด้วยชื่อบริษัทและคำสำคัญของธุรกิจ โดยไม่ใช้ API key")
    if st.button("ประมวลผล (Demo)", key="demo_process", type="primary"):
        articles = load_articles(limit=100)
        if not articles:
            st.warning("ยังไม่มีข่าวหรือโหลดข่าวไม่สำเร็จ ไปหน้า Events เพื่อดึงข่าวก่อน แล้วลองอีกครั้ง")
            return False
        items = rank_news(lookup[company_id], articles, level=st.session_state.get("match_level", "loose"))
        if not items:
            st.info("ไม่พบข่าวที่เกี่ยวข้องจากคำสำคัญในชุดที่โหลด ลองเลือกบริษัทอื่นหรือเพิ่มข่าว ระบบจะไม่สร้างผลกระทบขึ้นมาเอง")
            return False
        st.session_state["demo_analysis"] = {"stage": "processing", "company": dict(lookup[company_id]),
                                               "items": items, "loaded_count": len(articles),
                                               "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        with st.status("กำลังคัดข่าวที่เกี่ยวข้อง (Demo — ยังไม่มีการใช้ AI จริง)", expanded=True) as status:
            show_news(items)
            progress = st.progress(0, text="กำลังคัดข่าวที่อาจเกี่ยวข้อง")
            for percent, label in [(30, "จัดกลุ่มคำสำคัญในข่าว"), (65, "จำลองการเชื่อมโยงกับธุรกิจ"), (100, "เตรียมหน้าสรุปตัวอย่าง")]:
                time.sleep(0.3)
                progress.progress(percent, text=label)
            status.update(label="ประมวลผลเดโมเสร็จแล้ว", state="complete")
        st.session_state["demo_analysis"]["stage"] = "summary"
        st.rerun()
    return False
