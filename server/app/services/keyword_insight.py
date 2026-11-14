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
        "effect": "ถ้าราคาซื้อหรือราคาขายพลังงานเปลี่ยน รายได้กับต้นทุนของบริษัทจะโดนไม่เท่ากัน แล้วแต่ว่าบริษัทมีธุรกิจส่วนไหนมากกว่า เลยต้องดูว่าราคาไปทางไหนและเช็กข้อมูลบริษัทก่อนสรุป",
        "check": "ราคาพลังงานล่าสุด สัดส่วนแต่ละธุรกิจ และการป้องกันความเสี่ยงด้านราคา",
    },
    "tourism": {
        "label": "ท่องเที่ยวและการบิน",
        "kind": "uncertain",
        "terms": ("tourism", "tourist", "travel", "airport", "aviation", "flight", "passenger", "ท่องเที่ยว", "สนามบิน", "ผู้โดยสาร", "เที่ยวบิน"),
        "impact": "ทิศทางยังไม่แน่ชัด (ตัวอย่าง)",
        "effect": "ข่าวเรื่องการเดินทางอาจทำให้จำนวนผู้โดยสารและรายได้ค่าบริการเปลี่ยน ถ้าเหตุการณ์ทำให้คนเดินทางมากขึ้นก็เป็นบวก ถ้าน้อยลงก็เป็นลบ",
        "check": "จำนวนผู้โดยสาร ข้อจำกัดการเดินทาง และต้นทุนการดำเนินงาน",
    },
    "petrochemicals": {
        "label": "ปิโตรเคมี",
        "kind": "mixed",
        "terms": ("petrochemical", "chemical", "polyester", "plastic", "feedstock", "pet", "ปิโตรเคมี", "เคมีภัณฑ์", "พลาสติก", "วัตถุดิบ"),
        "impact": "ผลกระทบผสม (ตัวอย่าง)",
        "effect": "ถ้าราคาวัตถุดิบหรือความต้องการสินค้าเปลี่ยน ส่วนต่างระหว่างราคาขายกับต้นทุนอาจแคบลงหรือกว้างขึ้น สุดท้ายขึ้นกับว่าบริษัทขึ้นราคาขายตามต้นทุนได้แค่ไหน",
        "check": "ส่วนต่างราคาสินค้า ต้นทุนวัตถุดิบ และยอดคำสั่งซื้อ",
    },
    "banking": {
        "label": "ธนาคาร",
        "kind": "uncertain",
        "terms": ("bank", "banks", "banking", "loan", "loans", "lending", "household debt", "npl", "credit", "deposit",
                  "central bank", "bank of thailand", "ธนาคาร", "สินเชื่อ", "หนี้ครัวเรือน", "หนี้เสีย", "เงินฝาก"),
        "impact": "ทิศทางยังไม่แน่ชัด (ตัวอย่าง)",
        "effect": "ข่าวเรื่องสินเชื่อ หนี้ หรือนโยบายธนาคารกลาง อาจกระทบรายได้ดอกเบี้ยของธนาคารและโอกาสที่ลูกหนี้จะจ่ายไม่ไหว จะออกมาบวกหรือลบขึ้นกับว่าดอกเบี้ยไปทางไหน และลูกหนี้ยังผ่อนไหวไหม",
        "check": "ส่วนต่างดอกเบี้ย สัดส่วนหนี้เสีย และเงินสำรองหนี้เสีย",
    },
    "telecom": {
        "label": "สื่อสารและดิจิทัล",
        "kind": "uncertain",
        "terms": ("telecom", "mobile", "5g", "broadband", "spectrum", "data centre", "data center", "cloud", "digital economy",
                  "social networks", "online", "โทรคมนาคม", "มือถือ", "คลื่นความถี่", "อินเทอร์เน็ต", "ดิจิทัล"),
        "impact": "ทิศทางยังไม่แน่ชัด (ตัวอย่าง)",
        "effect": "ข่าวเรื่องการใช้งานออนไลน์หรือกฎของหน่วยงานกำกับ อาจกระทบรายได้ค่าบริการและเงินที่ต้องลงทุนในโครงข่าย ต้องดูว่าเหตุการณ์นั้นทำให้คนใช้งานมากขึ้น หรือทำให้ผู้ให้บริการมีต้นทุนเพิ่ม",
        "check": "จำนวนผู้ใช้ รายได้ต่อผู้ใช้ และงบลงทุนโครงข่าย",
    },
    "healthcare": {
        "label": "โรงพยาบาล",
        "kind": "uncertain",
        "terms": ("hospital", "hospitals", "healthcare", "health care", "medical", "patients", "medical tourism", "outbreak",
                  "public health", "โรงพยาบาล", "สาธารณสุข", "ผู้ป่วย", "การแพทย์", "โรคระบาด"),
        "impact": "ทิศทางยังไม่แน่ชัด (ตัวอย่าง)",
        "effect": "ข่าวเรื่องสุขภาพหรือการเดินทางของผู้ป่วยต่างชาติ อาจทำให้คนไปโรงพยาบาลเอกชนมากขึ้นหรือน้อยลง สุดท้ายขึ้นกับว่าโรงพยาบาลมีคนไข้ต่างชาติมากแค่ไหน และต้นทุนบุคลากรเป็นยังไง",
        "check": "จำนวนผู้ป่วย สัดส่วนผู้ป่วยต่างชาติ และต้นทุนบุคลากร",
    },
    "retail": {
        "label": "ค้าปลีก",
        "kind": "uncertain",
        "terms": ("retail", "retailer", "consumer", "consumption", "shoppers", "spending", "minimum wage", "convenience store",
                  "food prices", "ค้าปลีก", "กำลังซื้อ", "ผู้บริโภค", "ค่าแรงขั้นต่ำ", "ร้านสะดวกซื้อ"),
        "impact": "ทิศทางยังไม่แน่ชัด (ตัวอย่าง)",
        "effect": "ข่าวเรื่องกำลังซื้อหรือค่าแรงกระทบร้านค้าปลีกได้ทั้งยอดขายและต้นทุน ถ้ารายได้ของคนซื้อเพิ่มเร็วกว่าต้นทุนที่สูงขึ้นก็ออกมาดี ถ้าไม่ทันก็ออกมาแย่",
        "check": "ยอดขายสาขาเดิม ต้นทุนค่าแรง และกำลังซื้อของผู้บริโภค",
    },
    "economy": {
        "label": "เศรษฐกิจโดยรวม",
        "kind": "uncertain",
        "terms": ("interest rate", "inflation", "exchange rate", "tariff", "ดอกเบี้ย", "เงินเฟ้อ", "ค่าเงิน", "ภาษีนำเข้า"),
        "impact": "ทิศทางยังไม่แน่ชัด (ตัวอย่าง)",
        "effect": "ดอกเบี้ย เงินเฟ้อ ค่าเงิน หรือภาษีนำเข้า อาจกระทบต้นทุนการกู้เงิน กำลังซื้อ หรือรายได้จากต่างประเทศ แต่จากข่าวอย่างเดียวยังบอกไม่ได้ว่าสุดท้ายบริษัทได้หรือเสีย",
        "check": "โครงสร้างหนี้ สกุลเงินของรายได้ และความต้องการของลูกค้า",
    },
}


def contains(text, term):
    if re.fullmatch(r"[a-z0-9 .&-]+", term):
        return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text) is not None
    return term in text


# How strict the keyword link between a news item and a company must be.
MATCH_LEVELS = {
    "strict": "เข้ม: เอาเฉพาะข่าวที่เอ่ยชื่อย่อหุ้นหรือชื่อบริษัทตรง ๆ",
    "medium": "กลาง: เอ่ยชื่อ หรือมีคำเกี่ยวกับธุรกิจของบริษัทตั้งแต่ 2 คำขึ้นไป",
    "loose": "หลวม: เอ่ยชื่อ หรือมีคำที่เกี่ยวข้องแค่ 1 คำก็นับ รวมถึงคำเศรษฐกิจทั่วไปอย่างดอกเบี้ยหรือเงินเฟ้อ",
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
        found = list(dict.fromkeys(term for terms in matches.values() for term in terms))
        reasons = (["เอ่ยชื่อบริษัทหรือชื่อย่อหุ้น"] if direct else []) + (["คำที่เจอในข่าว: " + ", ".join(found)] if found else [])
        ranked.append({"article": dict(article), "score": score, "groups": list(matches), "matches": matches, "reason": " และ".join(reasons)})
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
