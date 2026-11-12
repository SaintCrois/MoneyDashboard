"""Event-to-industry and event-to-company impact mapping service.

Company mapping rules (critical):
- Associate a company only when there is sufficient evidence.
- Use: exact registered company name, recognized company name variations,
  ticker symbols with contextual validation, verified aliases, explicit
  references in the article, strong contextual evidence.
- Do NOT associate based on: industry-only mentions, common words in company
  names, foreign organizations with similar names, or unrelated acronym/ticker
  strings.
- Confidence:
  - High: explicit company name or verified alias in relevant context.
  - Medium: strong contextual evidence with identifiable company exposure.
  - Low: ambiguous/weak association.
- Automatically create mappings only for sufficiently supported matches
  (High/Medium). Low-confidence matches remain unassigned (not stored).
- Every mapping stores match confidence, reason, and supporting evidence.

Industry mapping remains keyword-evidence based and labeled Uncertain when
impact direction cannot be determined from the article alone.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.event import Event
from app.models.event_company import EventCompany
from app.models.event_industry import EventIndustry
from app.models.industry import Industry
from app.models.news_article import NewsArticle

logger = logging.getLogger(__name__)

VALID_IMPACT_DIRECTIONS = ["Positive", "Negative", "Mixed", "Uncertain"]
DEFAULT_IMPACT_DIRECTION = "Uncertain"

CONF_HIGH = "High"
CONF_MEDIUM = "Medium"
CONF_LOW = "Low"

_GENERIC_NAME_TOKENS = {
    "public", "company", "limited", "plc", "pcl", "ltd", "inc", "corp",
    "corporation", "group", "holdings", "holding", "the", "and", "of",
}


@dataclass
class CompanyMatch:
    company: Company
    confidence: str
    score: float
    reason: str
    evidence: list[dict]
    exposure_type: str = "Direct"


def _normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    text = text.replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()


def _tokenize(text: Optional[str]) -> list[str]:
    if not text:
        return []
    return re.findall(r"[a-z0-9]+", text.lower())


def _strip_corp_suffixes(name: str) -> str:
    s = _normalize_text(name)
    patterns = [
        r"\bpublic company limited\b",
        r"\bpublic co\.?,?\s*ltd\.?\b",
        r"\bcompany limited\b",
        r"\bco\.?,?\s*ltd\.?\b",
        r"\blimited\b",
        r"\bpcl\.?\b",
        r"\bplc\.?\b",
        r"\binc\.?\b",
        r"\bcorp\.?\b",
    ]
    out = s
    for p in patterns:
        out = re.sub(p, "", out, flags=re.IGNORECASE)
    out = re.sub(r"[,\.\-]+", " ", out)
    return re.sub(r"\s+", " ", out).strip()


def _company_aliases(company: Company) -> list[str]:
    """Return recognized name aliases/variations for matching."""
    aliases: set[str] = set()
    name = _normalize_text(company.name)
    if name:
        aliases.add(name)
        stripped = _strip_corp_suffixes(name)
        if stripped and stripped.lower() != name.lower():
            aliases.add(stripped)
        tokens = [t for t in _tokenize(stripped) if t not in _GENERIC_NAME_TOKENS]
        if len(tokens) >= 2:
            aliases.add(" ".join(tokens))

    cleaned = []
    for a in aliases:
        a_n = _normalize_text(a)
        if len(a_n) < 3:
            continue
        toks = [t for t in _tokenize(a_n) if t not in _GENERIC_NAME_TOKENS]
        if not toks:
            continue
        cleaned.append(a_n)

    seen = set()
    out = []
    for a in cleaned:
        k = a.lower()
        if k not in seen:
            seen.add(k)
            out.append(a)
    return out


def _find_name_evidence(text: str, alias: str) -> Optional[dict]:
    alias_norm = _normalize_text(alias)
    if not alias_norm:
        return None
    pattern = r"(?<![A-Za-z0-9])" + re.escape(alias_norm) + r"(?![A-Za-z0-9])"
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return None
    start = max(0, m.start() - 40)
    end = min(len(text), m.end() + 40)
    snippet = _normalize_text(text[start:end])
    return {"type": "name_alias", "matched": alias_norm, "snippet": snippet, "start": m.start(), "end": m.end()}


def _find_ticker_evidence(text: str, ticker: str) -> Optional[dict]:
    t = _normalize_text(ticker).upper()
    if not t or len(t) < 2:
        return None
    pattern = r"(?<![A-Za-z0-9])" + re.escape(t) + r"(?![A-Za-z0-9])"
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return None

    snippet_start = max(0, m.start() - 40)
    snippet_end = min(len(text), m.end() + 40)
    snippet = _normalize_text(text[snippet_start:snippet_end])

    window_start = max(0, m.start() - 60)
    window_end = min(len(text), m.end() + 60)
    window = text[window_start:window_end].lower()
    context_terms = [
        "shares", "stock", "listed", "set", "exchange", "earnings", "profit",
        "revenue", "company", "plc", "pcl", "public company", "investment",
        "announces", "announced", "ceo", "results", "dividend", "baht",
        "thailand", "thai", "firm", "operator",
    ]
    has_context = any(term in window for term in context_terms)
    return {
        "type": "ticker",
        "matched": t,
        "snippet": snippet,
        "has_context": has_context,
        "start": m.start(),
        "end": m.end(),
    }


def evaluate_company_match(company: Company, text: str) -> CompanyMatch:
    """Evaluate whether and how strongly a company matches article/event text.

    Returns High/Medium/Low. Low means do not auto-create mapping.
    """
    text_norm = _normalize_text(text)
    evidences: list[dict] = []
    reasons: list[str] = []

    name_hits = []
    for alias in _company_aliases(company):
        ev = _find_name_evidence(text_norm, alias)
        if ev:
            name_hits.append(ev)

    seen_alias = set()
    uniq_name_hits = []
    for ev in name_hits:
        k = ev["matched"].lower()
        if k not in seen_alias:
            seen_alias.add(k)
            uniq_name_hits.append(ev)

    ticker_ev = _find_ticker_evidence(text_norm, company.ticker or "")

    if uniq_name_hits:
        safe_hits = []
        downgraded = False
        for ev in uniq_name_hits:
            matched = ev.get("matched", "")
            is_short_ticker_alias = (
                matched.upper() == (company.ticker or "").upper() and len(matched) <= 5
            )
            if is_short_ticker_alias:
                snippet = (ev.get("snippet") or "").lower()
                # Detect continuation into a different organization name, e.g.
                # "PTT Global Chemical Europe ..." (foreign org) vs Thai PTT.
                # Use the text immediately following the match.
                tail = text_norm[ev.get("end", 0): ev.get("end", 0) + 40]
                continuation_words = re.findall(r"[A-Za-z]+", tail)
                continuation = " ".join(w.lower() for w in continuation_words[:3])
                foreign_org_markers = {
                    "global", "chemical", "europe", "international", "overseas",
                    "uk", "london", "singapore", "japan", "china", "america",
                }
                looks_foreign_variant = any(
                    marker in continuation.split() or marker in snippet
                    for marker in ["europe", "united kingdom", "uk civil"]
                ) or (
                    continuation_words[:1] and continuation_words[0].lower() in {"global", "international"}
                )
                thai_context = any(t in snippet for t in ["thailand", "thai", "set", "bangkok", "baht"])
                business_context = any(
                    term in snippet
                    for term in [
                        "shares", "stock", "listed", "set", "exchange", "earnings", "profit",
                        "revenue", "company", "pcl", "plc", "announces", "announced",
                        "investment", "ceo", "results", "dividend",
                    ]
                )

                if looks_foreign_variant and not thai_context:
                    downgraded = True
                    continue
                if matched == _normalize_text(company.name):
                    safe_hits.append(ev)
                elif business_context or thai_context:
                    safe_hits.append(ev)
                else:
                    downgraded = True
                    continue
            else:
                safe_hits.append(ev)

        if safe_hits:
            evidences.extend({k: v for k, v in e.items() if k not in ("start", "end")} for e in safe_hits)
            reasons.append(
                "Explicit company name/alias reference found: "
                + ", ".join(e["matched"] for e in safe_hits[:3])
                + "."
            )
            return CompanyMatch(
                company=company,
                confidence=CONF_HIGH,
                score=0.9,
                reason=" ".join(reasons),
                evidence=[{k: v for k, v in e.items() if k not in ("start", "end")} for e in safe_hits],
                exposure_type="Direct",
            )
        if downgraded:
            reasons.append(
                "Possible name/alias mention found but context is ambiguous or may refer to a different organization; "
                "insufficient evidence for a confirmed company association."
            )
            return CompanyMatch(
                company=company,
                confidence=CONF_LOW,
                score=0.25,
                reason=" ".join(reasons),
                evidence=[{k: v for k, v in e.items() if k not in ("start", "end")} for e in uniq_name_hits],
                exposure_type="Indirect",
            )

    if ticker_ev:
        ev_clean = {k: v for k, v in ticker_ev.items() if k not in ("start", "end")}
        evidences.append(ev_clean)
        if ticker_ev.get("has_context"):
            reasons.append(
                f"Ticker '{company.ticker}' found with supporting business/company context."
            )
            return CompanyMatch(
                company=company,
                confidence=CONF_MEDIUM,
                score=0.6,
                reason=" ".join(reasons),
                evidence=evidences,
                exposure_type="Direct",
            )
        reasons.append(
            f"Ticker '{company.ticker}' appears without sufficient contextual validation; ambiguous or weak association."
        )
        return CompanyMatch(
            company=company,
            confidence=CONF_LOW,
            score=0.2,
            reason=" ".join(reasons),
            evidence=evidences,
            exposure_type="Indirect",
        )

    reasons.append("No explicit company name, verified alias, or contextually validated ticker reference found.")
    return CompanyMatch(
        company=company,
        confidence=CONF_LOW,
        score=0.0,
        reason=" ".join(reasons),
        evidence=[],
        exposure_type="Indirect",
    )


def _evidence_text(article: Optional[NewsArticle], event: Event) -> str:
    parts = [event.title or "", event.description or ""]
    if article:
        parts.extend([article.title or "", article.summary or ""])
        if article.content:
            parts.append(article.content[:2000])
    return _normalize_text(" \n ".join([p for p in parts if p]))


class ImpactMappingService:
    """Maps events to industries and companies based on evidence."""

    def map_event(self, db: Session, event: Event) -> dict:
        """Create industry and company mappings for a single event."""
        result = {"event_id": event.id, "industries": [], "companies": []}

        article = None
        if event.source_article_id:
            article = db.query(NewsArticle).filter(NewsArticle.id == event.source_article_id).first()
        text = _evidence_text(article, event)

        tokens = _tokenize(text)
        industries = db.query(Industry).all()
        for industry in industries:
            ind_tokens = [t for t in _tokenize(industry.name) if t not in _GENERIC_NAME_TOKENS and len(t) > 2]
            if industry.description:
                ind_tokens += [t for t in _tokenize(industry.description) if t not in _GENERIC_NAME_TOKENS and len(t) > 2]
            ind_tokens = list(dict.fromkeys(ind_tokens))
            if not ind_tokens:
                continue
            score = sum(1 for kw in ind_tokens if kw in tokens)
            if score == 0:
                continue
            existing = (
                db.query(EventIndustry)
                .filter(EventIndustry.event_id == event.id, EventIndustry.industry_id == industry.id)
                .first()
            )
            if existing:
                continue
            mapping = EventIndustry(
                event_id=event.id,
                industry_id=industry.id,
                impact_type=DEFAULT_IMPACT_DIRECTION,
                relevance_score=round(min(0.99, 0.4 + 0.15 * score), 2),
                explanation=(
                    f"Event/article text mentions terms related to the '{industry.name}' "
                    f"industry (keyword evidence count {score}). Impact direction is "
                    "not determined from the article alone."
                ),
            )
            db.add(mapping)
            db.flush()
            result["industries"].append(
                {
                    "id": mapping.id,
                    "industry_id": industry.id,
                    "industry_name": industry.name,
                    "impact_type": mapping.impact_type,
                    "relevance_score": mapping.relevance_score,
                    "explanation": mapping.explanation,
                }
            )

        companies = db.query(Company).all()
        for company in companies:
            existing = (
                db.query(EventCompany)
                .filter(EventCompany.event_id == event.id, EventCompany.company_id == company.id)
                .first()
            )
            if existing:
                continue

            match = evaluate_company_match(company, text)
            if match.confidence not in (CONF_HIGH, CONF_MEDIUM):
                continue

            evidence_payload = {
                "article_id": article.id if article else None,
                "article_url": article.url if article else None,
                "article_title": article.title if article else None,
                "matches": match.evidence,
            }
            explanation = (
                f"{match.reason} Impact direction is not determined from the "
                "article alone and is labeled Uncertain unless other evidence applies."
            )
            mapping = EventCompany(
                event_id=event.id,
                company_id=company.id,
                impact_type=DEFAULT_IMPACT_DIRECTION,
                exposure_type=match.exposure_type or "Direct",
                relevance_score=round(match.score, 2),
                explanation=explanation,
                match_confidence=match.confidence,
                match_reason=match.reason,
                evidence=json.dumps(evidence_payload, ensure_ascii=False),
                created_at=datetime.now(timezone.utc),
            )
            db.add(mapping)
            db.flush()
            result["companies"].append(
                {
                    "id": mapping.id,
                    "company_id": company.id,
                    "company_name": company.name,
                    "ticker": company.ticker,
                    "impact_type": mapping.impact_type,
                    "exposure_type": mapping.exposure_type,
                    "relevance_score": mapping.relevance_score,
                    "explanation": mapping.explanation,
                    "match_confidence": mapping.match_confidence,
                    "match_reason": mapping.match_reason,
                }
            )

        db.commit()
        return result

    def map_all_unmapped_events(self, db: Session) -> dict:
        stats = {"events_mapped": 0, "industry_mappings": 0, "company_mappings": 0}
        events = db.query(Event).all()
        for event in events:
            has_industry = db.query(EventIndustry).filter(EventIndustry.event_id == event.id).first()
            has_company = db.query(EventCompany).filter(EventCompany.event_id == event.id).first()
            if has_industry and has_company:
                continue
            result = self.map_event(db, event)
            stats["events_mapped"] += 1
            stats["industry_mappings"] += len(result["industries"])
            stats["company_mappings"] += len(result["companies"])
        return stats


__all__ = [
    "ImpactMappingService",
    "map_event",
    "evaluate_company_match",
    "CompanyMatch",
    "VALID_IMPACT_DIRECTIONS",
    "DEFAULT_IMPACT_DIRECTION",
    "CONF_HIGH",
    "CONF_MEDIUM",
    "CONF_LOW",
]


def map_event(db: Session, event: Event) -> dict:
    return ImpactMappingService().map_event(db, event)


def map_all_unmapped_events(db: Session) -> dict:
    return ImpactMappingService().map_all_unmapped_events(db)
