"""Local demonstration of the analysis journey. Never calls an AI provider."""
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import streamlit as st

NOTICE = "Demo — เป็นเพียงการสาธิต ยังไม่มีการใช้ AI จริง และไม่มีการส่งข่าวไปยังผู้ให้บริการ AI"

# Product scenarios, not verified financial conclusions or company disclosures.
SCENARIOS = {
    "energy": {
        "terms": ("oil", "crude", "gas", "energy", "fuel", "petroleum", "น้ำมัน", "พลังงาน", "ก๊าซ"),
        "impact": "ผลกระทบผสม (ตัวอย่าง)",
        "effect": "หากต้นทุนหรือราคาขายพลังงานเปลี่ยน อาจกระทบรายได้และต้นทุนต่างกันตามสัดส่วนธุรกิจ ต้องตรวจสอบทิศทางราคาและข้อมูลบริษัทก่อนสรุป",
        "check": "ราคาพลังงานจริง สัดส่วนธุรกิจ และการป้องกันความเสี่ยง",
    },
    "tourism": {
        "terms": ("tourism", "tourist", "travel", "airport", "aviation", "flight", "passenger", "ท่องเที่ยว", "สนามบิน", "ผู้โดยสาร", "เที่ยวบิน"),
        "impact": "ทิศทางยังไม่แน่ชัด (ตัวอย่าง)",
        "effect": "ข่าวด้านการเดินทางอาจส่งผลต่อจำนวนผู้โดยสารและรายได้บริการ แต่ผลบวกหรือลบขึ้นอยู่กับว่าเหตุการณ์เพิ่มหรือลดการเดินทาง",
        "check": "จำนวนผู้โดยสาร ข้อจำกัดการเดินทาง และต้นทุนดำเนินงาน",
    },
    "petrochemicals": {
        "terms": ("petrochemical", "chemical", "polyester", "plastic", "feedstock", "pet", "ปิโตรเคมี", "เคมีภัณฑ์", "พลาสติก", "วัตถุดิบ"),
        "impact": "ผลกระทบผสม (ตัวอย่าง)",
        "effect": "การเปลี่ยนแปลงของวัตถุดิบและความต้องการสินค้าอาจกระทบส่วนต่างกำไร ผลสุทธิขึ้นอยู่กับราคาขายและความสามารถส่งผ่านต้นทุน",
        "check": "ส่วนต่างราคาผลิตภัณฑ์ ต้นทุนวัตถุดิบ และคำสั่งซื้อ",
    },
    "economy": {
        "terms": ("interest rate", "inflation", "exchange rate", "tariff", "ดอกเบี้ย", "เงินเฟ้อ", "ค่าเงิน", "ภาษีนำเข้า"),
        "impact": "ทิศทางยังไม่แน่ชัด (ตัวอย่าง)",
        "effect": "ปัจจัยเศรษฐกิจอาจส่งผลต่อต้นทุนเงินทุน กำลังซื้อ หรือรายได้ต่างประเทศ แต่ยังระบุผลสุทธิของบริษัทไม่ได้",
        "check": "โครงสร้างหนี้ สกุลเงินรายได้ และความต้องการของลูกค้า",
    },
}


def contains(text, term):
    if re.fullmatch(r"[a-z0-9 .&-]+", term):
        return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text) is not None
    return term in text


def rank_news(company, articles, limit=8):
    """Deterministic shortlist; no language model, sentiment inference or random scores."""
    ticker = (company.get("ticker") or "").lower()
    profile = " ".join(str(company.get(k) or "") for k in ("industry_name", "sector", "description")).lower()
    groups = set()
    if ticker in ("ptt", "pttep") or any(x in profile for x in ("energy", "พลังงาน")):
        groups.add("energy")
    if ticker == "aot" or any(x in profile for x in ("tourism", "airport", "ท่องเที่ยว")):
        groups.add("tourism")
    if ticker == "ivl" or any(x in profile for x in ("petrochemical", "ปิโตรเคมี")):
        groups.update(("petrochemicals", "energy"))
    groups.add("economy")
    ranked, seen = [], set()
    for article in articles:
        title = article.get("title") or ""
        identity = re.sub(r"\W+", "", title.casefold()) or str(article.get("id"))
        if identity in seen:
            continue
        text = (title + " " + (article.get("summary") or "")).casefold()
        direct = bool(ticker and contains(text, ticker))
        name = (company.get("name") or "").casefold().strip()
        direct = direct or bool(len(name) > 5 and name in text)
        matches = {group: [term for term in SCENARIOS[group]["terms"] if contains(text, term)]
                   for group in sorted(groups)}
        matches = {group: terms for group, terms in matches.items() if terms}
        if not direct and not matches:
            continue
        seen.add(identity)
        score = (10 if direct else 0) + sum(min(len(terms), 3) for terms in matches.values())
        reasons = (["พบชื่อบริษัทหรือ ticker"] if direct else []) + ["คำที่เกี่ยวข้อง: " + ", ".join(terms) for terms in matches.values()]
        ranked.append({"article": dict(article), "score": score, "groups": list(matches), "reason": " · ".join(reasons)})
    return sorted(ranked, key=lambda item: item["score"], reverse=True)[:limit]


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
        items = rank_news(lookup[company_id], articles)
        if not items:
            st.info("ไม่พบข่าวที่เกี่ยวข้องจากคำสำคัญในชุดที่โหลด ลองเลือกบริษัทอื่นหรือเพิ่มข่าว ระบบจะไม่สร้างผลกระทบขึ้นมาเอง")
            return False
        st.session_state["demo_analysis"] = {"stage": "processing", "company": dict(lookup[company_id]),
                                               "items": items, "loaded_count": len(articles),
                                               "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        with st.status("กำลังประมวลผลด้วย AI (Demo — ยังไม่มีการใช้ AI จริง)", expanded=True) as status:
            show_news(items)
            progress = st.progress(0, text="กำลังคัดข่าวที่อาจเกี่ยวข้อง")
            for percent, label in [(30, "จัดกลุ่มคำสำคัญในข่าว"), (65, "จำลองการเชื่อมโยงกับธุรกิจ"), (100, "เตรียมหน้าสรุปตัวอย่าง")]:
                time.sleep(0.7)
                progress.progress(percent, text=label)
            status.update(label="ประมวลผลเดโมเสร็จแล้ว", state="complete")
        st.session_state["demo_analysis"]["stage"] = "summary"
        st.rerun()
    return False
