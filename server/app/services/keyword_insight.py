"""Keyword-level link between news and listed companies. No AI, no database.

Shared by the FastAPI insights endpoints and the Streamlit demo. Scenario text
is illustrative product copy, not a verified financial conclusion.
"""
import re

# Product scenarios, not verified financial conclusions or company disclosures.
SCENARIOS = {
    "energy": {
        "label": "พลังงาน",
        "kind": "mixed",
        "terms": ("oil", "crude", "gas", "energy", "fuel", "petroleum", "น้ำมัน", "พลังงาน", "ก๊าซ"),
        "impact": "ผลกระทบผสม (ตัวอย่าง)",
        "effect": "หากต้นทุนหรือราคาขายพลังงานเปลี่ยน อาจกระทบรายได้และต้นทุนต่างกันตามสัดส่วนธุรกิจ ต้องตรวจสอบทิศทางราคาและข้อมูลบริษัทก่อนสรุป",
        "check": "ราคาพลังงานจริง สัดส่วนธุรกิจ และการป้องกันความเสี่ยง",
    },
    "tourism": {
        "label": "ท่องเที่ยวและการบิน",
        "kind": "uncertain",
        "terms": ("tourism", "tourist", "travel", "airport", "aviation", "flight", "passenger", "ท่องเที่ยว", "สนามบิน", "ผู้โดยสาร", "เที่ยวบิน"),
        "impact": "ทิศทางยังไม่แน่ชัด (ตัวอย่าง)",
        "effect": "ข่าวด้านการเดินทางอาจส่งผลต่อจำนวนผู้โดยสารและรายได้บริการ แต่ผลบวกหรือลบขึ้นอยู่กับว่าเหตุการณ์เพิ่มหรือลดการเดินทาง",
        "check": "จำนวนผู้โดยสาร ข้อจำกัดการเดินทาง และต้นทุนดำเนินงาน",
    },
    "petrochemicals": {
        "label": "ปิโตรเคมี",
        "kind": "mixed",
        "terms": ("petrochemical", "chemical", "polyester", "plastic", "feedstock", "pet", "ปิโตรเคมี", "เคมีภัณฑ์", "พลาสติก", "วัตถุดิบ"),
        "impact": "ผลกระทบผสม (ตัวอย่าง)",
        "effect": "การเปลี่ยนแปลงของวัตถุดิบและความต้องการสินค้าอาจกระทบส่วนต่างกำไร ผลสุทธิขึ้นอยู่กับราคาขายและความสามารถส่งผ่านต้นทุน",
        "check": "ส่วนต่างราคาผลิตภัณฑ์ ต้นทุนวัตถุดิบ และคำสั่งซื้อ",
    },
    "banking": {
        "label": "ธนาคาร",
        "kind": "uncertain",
        "terms": ("bank", "banks", "banking", "loan", "loans", "lending", "household debt", "npl", "credit", "deposit",
                  "central bank", "bank of thailand", "ธนาคาร", "สินเชื่อ", "หนี้ครัวเรือน", "หนี้เสีย", "เงินฝาก"),
        "impact": "ทิศทางยังไม่แน่ชัด (ตัวอย่าง)",
        "effect": "ข่าวด้านสินเชื่อ หนี้ และนโยบายธนาคารกลางอาจกระทบรายได้ดอกเบี้ยและคุณภาพสินเชื่อของธนาคาร ผลบวกหรือลบขึ้นอยู่กับทิศทางดอกเบี้ยและความสามารถชำระหนี้ของลูกหนี้",
        "check": "ส่วนต่างอัตราดอกเบี้ย สัดส่วนหนี้เสีย และการตั้งสำรอง",
    },
    "telecom": {
        "label": "สื่อสารและดิจิทัล",
        "kind": "uncertain",
        "terms": ("telecom", "mobile", "5g", "broadband", "spectrum", "data centre", "data center", "cloud", "digital economy",
                  "social networks", "online", "โทรคมนาคม", "มือถือ", "คลื่นความถี่", "อินเทอร์เน็ต", "ดิจิทัล"),
        "impact": "ทิศทางยังไม่แน่ชัด (ตัวอย่าง)",
        "effect": "ข่าวด้านการใช้งานดิจิทัลและกฎกำกับดูแลอาจกระทบรายได้ค่าบริการและเงินลงทุนโครงข่าย ต้องดูว่าเหตุการณ์เพิ่มการใช้งานหรือเพิ่มต้นทุนให้ผู้ให้บริการ",
        "check": "จำนวนผู้ใช้ รายได้ต่อผู้ใช้ และงบลงทุนโครงข่าย",
    },
    "healthcare": {
        "label": "โรงพยาบาล",
        "kind": "uncertain",
        "terms": ("hospital", "hospitals", "healthcare", "health care", "medical", "patients", "medical tourism", "outbreak",
                  "public health", "โรงพยาบาล", "สาธารณสุข", "ผู้ป่วย", "การแพทย์", "โรคระบาด"),
        "impact": "ทิศทางยังไม่แน่ชัด (ตัวอย่าง)",
        "effect": "ข่าวด้านสุขภาพและการเดินทางของผู้ป่วยต่างชาติอาจกระทบจำนวนผู้ใช้บริการโรงพยาบาลเอกชน ผลสุทธิขึ้นอยู่กับสัดส่วนผู้ป่วยต่างชาติและต้นทุนบุคลากร",
        "check": "จำนวนผู้ป่วย สัดส่วนผู้ป่วยต่างชาติ และต้นทุนบุคลากร",
    },
    "retail": {
        "label": "ค้าปลีก",
        "kind": "uncertain",
        "terms": ("retail", "retailer", "consumer", "consumption", "shoppers", "spending", "minimum wage", "convenience store",
                  "food prices", "ค้าปลีก", "กำลังซื้อ", "ผู้บริโภค", "ค่าแรงขั้นต่ำ", "ร้านสะดวกซื้อ"),
        "impact": "ทิศทางยังไม่แน่ชัด (ตัวอย่าง)",
        "effect": "ข่าวด้านกำลังซื้อและค่าแรงอาจกระทบทั้งยอดขายและต้นทุนของธุรกิจค้าปลีก ผลสุทธิขึ้นอยู่กับว่ารายได้ผู้บริโภคเพิ่มมากกว่าต้นทุนที่สูงขึ้นหรือไม่",
        "check": "ยอดขายสาขาเดิม ต้นทุนค่าแรง และกำลังซื้อของผู้บริโภค",
    },
    "economy": {
        "label": "เศรษฐกิจมหภาค",
        "kind": "uncertain",
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


# How strict the keyword link between a news item and a company must be.
MATCH_LEVELS = {
    "strict": "เข้ม: ข่าวต้องเอ่ยชื่อย่อหุ้นหรือชื่อบริษัท",
    "medium": "กลาง: เอ่ยชื่อ หรือมีคำในหมวดธุรกิจของบริษัทอย่างน้อย 2 คำ",
    "loose": "หลวม: เอ่ยชื่อ หรือมีคำที่เกี่ยวข้องอย่างน้อย 1 คำ (รวมคำเศรษฐกิจทั่วไป)",
}


def passes_level(direct, matches, level):
    if direct:
        return True
    if level == "strict":
        return False
    if level == "medium":
        return sum(len(terms) for group, terms in matches.items() if group != "economy") >= 2
    return bool(matches)


def rank_news(company, articles, limit=8, level="loose"):
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
    if ticker in ("scb", "kbank") or any(x in profile for x in ("bank", "financ", "ธนาคาร")):
        groups.add("banking")
    if ticker == "advanc" or any(x in profile for x in ("communication", "telecom", "สื่อสาร")):
        groups.add("telecom")
    if ticker == "bdms" or any(x in profile for x in ("health", "medical", "โรงพยาบาล")):
        groups.add("healthcare")
    if ticker == "cpall" or any(x in profile for x in ("commerce", "consumer", "retail", "ค้าปลีก")):
        groups.add("retail")
    groups.add("economy")
    ranked, seen = [], set()
    for article in articles:
        title = article.get("title") or ""
        identity = re.sub(r"\W+", "", title.casefold()) or str(article.get("id"))
        if identity in seen:
            continue
        text = (title + " " + (article.get("summary") or "")).casefold()
        # Tickers must appear in capitals in the original text, so "Gulf of Thailand"
        # or "the Gulf" is not read as the company GULF.
        raw = title + " " + (article.get("summary") or "")
        direct = bool(ticker and re.search(r"(?<![A-Za-z0-9])" + re.escape(ticker.upper()) + r"(?![A-Za-z0-9])", raw))
        name = (company.get("name") or "").casefold().strip()
        direct = direct or bool(len(name) > 5 and name in text)
        matches = {group: [term for term in SCENARIOS[group]["terms"] if contains(text, term)]
                   for group in sorted(groups)}
        matches = {group: terms for group, terms in matches.items() if terms}
        if not passes_level(direct, matches, level):
            continue
        seen.add(identity)
        score = (10 if direct else 0) + sum(min(len(terms), 3) for terms in matches.values())
        reasons = (["พบชื่อบริษัทหรือ ticker"] if direct else []) + ["คำที่เกี่ยวข้อง: " + ", ".join(terms) for terms in matches.values()]
        ranked.append({"article": dict(article), "score": score, "groups": list(matches), "reason": " · ".join(reasons)})
    return sorted(ranked, key=lambda item: item["score"], reverse=True)[:limit]


def related_companies(title, summary, companies, level="medium"):
    """Companies whose business keywords appear in one news item.

    Keyword-level and unconfirmed: this is separate from the evidence-backed
    company associations stored by the backend. ``level`` is one of MATCH_LEVELS.
    """
    out = []
    for company in companies:
        hit = rank_news(company, [{"id": 0, "title": title or "", "summary": summary or ""}], limit=1, level=level)
        if not hit:
            continue
        item = hit[0]
        out.append({
            "ticker": company.get("ticker"),
            "name": company.get("name"),
            "reason": item["reason"],
            "direct": item["score"] >= 10,
            "groups": item["groups"],
        })
    return out
