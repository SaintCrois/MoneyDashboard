"""Thailand relevance classification service.

Classifies news articles based on title, summary, and available content.
This is a deterministic, explainable baseline (no external LLM required).

Classes:
- Thailand-focused
- Thailand-related
- International
- Uncertain

Rules:
- Consider explicit references to Thailand, Thai companies, Thai government
  agencies, Thai industries, and Thai economic developments.
- Do NOT classify as Thailand-related merely because it comes from a Thai
  publisher.
- Uncertain articles remain stored; callers must not auto-treat them as
  Thailand-focused.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional

THAILAND_FOCUSED = "Thailand-focused"
THAILAND_RELATED = "Thailand-related"
INTERNATIONAL = "International"
UNCERTAIN = "Uncertain"

_THAILAND_TERMS = [
    "thailand",
    "thai",
    "bangkok",
    "set index",
    "stock exchange of thailand",
    "bank of thailand",
    "bot",
    "baht",
    "ministry of",
    "cabinet",
    "thai government",
    "thailand board of investment",
    "boi",
    "nesdc",
    "excise department",
    "revenue department",
]

_THAI_COMPANY_HINTS = [
    "ptt", "pttep", "aot", "airports of thailand", "scb", "kasikorn", "kbank",
    "cp all", "cp group", "true corporation", "ais", "advanc", "bdms",
    "bangkok dusit", "gulf energy", "banpu", "scc", "siam cement",
]

_THAI_SECTOR_HINTS = [
    "thai economy", "thailand economy", "thai tourism", "tourism in thailand",
    "eastern economic corridor", "eec", "thai exports", "thailand exports",
    "thai energy", "thailand energy", "thai manufacturing", "thailand manufacturing",
]

_GLOBAL_STRONG_TERMS = [
    "united states", "u.s.", "usa", "uk", "united kingdom", "europe", "eu ",
    "china", "japan", "india", "russia", "ukraine", "middle east", "gaza",
    "israel", "iran", "global", "worldwide", "nvidia", "fed", "ecb",
]


@dataclass
class RelevanceResult:
    classification: str
    reason: str


def _normalize(text: Optional[str]) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip().lower()


def _contains_any(text: str, terms: Iterable[str]) -> list[str]:
    found = []
    for t in terms:
        # word-ish boundary for short tokens to reduce accidental matches
        if len(t) <= 4 and t.isalpha():
            if re.search(rf"\b{re.escape(t)}\b", text):
                found.append(t)
        else:
            if t in text:
                found.append(t)
    return found


def classify_thailand_relevance(
    title: Optional[str],
    summary: Optional[str],
    content: Optional[str] = None,
) -> RelevanceResult:
    """Classify article relevance to Thailand with an explicit reason."""
    text = _normalize(" ".join([title or "", summary or "", content or ""]))
    if not text:
        return RelevanceResult(
            classification=UNCERTAIN,
            reason="Insufficient text (title/summary/content missing) to determine Thailand relevance.",
        )

    th_terms = _contains_any(text, _THAILAND_TERMS)
    co_terms = _contains_any(text, _THAI_COMPANY_HINTS)
    sec_terms = _contains_any(text, _THAI_SECTOR_HINTS)
    global_terms = _contains_any(text, _GLOBAL_STRONG_TERMS)

    has_thailand = bool(th_terms)
    has_thai_entity = bool(co_terms or sec_terms)

    # Explicit Thailand/company/sector references dominate.
    if has_thailand and has_thai_entity:
        refs = ", ".join(sorted(set(th_terms + co_terms + sec_terms))[:6])
        # If only generic "thai" adjective/entity signals appear alongside strong
        # global context (and no explicit country/city/place terms), treat as
        # Thailand-related rather than purely domestic-focused.
        place_terms = {"thailand", "bangkok", "baht", "stock exchange of thailand"}
        if global_terms and not (set(th_terms) & place_terms):
            g = ", ".join(sorted(set(global_terms))[:4])
            return RelevanceResult(
                classification=THAILAND_RELATED,
                reason=(
                    f"References Thai company/sector/economic indicators ({refs}) in an "
                    f"international context ({g}); related to Thailand but not purely domestic-focused."
                ),
            )
        return RelevanceResult(
            classification=THAILAND_FOCUSED,
            reason=f"Explicit Thailand and Thai company/sector/economic references found: {refs}.",
        )

    if has_thailand and ("thailand" in th_terms or "bangkok" in th_terms or "baht" in th_terms):
        refs = ", ".join(sorted(set(th_terms))[:6])
        if global_terms:
            g = ", ".join(sorted(set(global_terms))[:4])
            return RelevanceResult(
                classification=THAILAND_RELATED,
                reason=(
                    f"Mentions Thailand explicitly ({refs}) alongside international context ({g}); "
                    "likely related to Thailand rather than purely domestic focus."
                ),
            )
        return RelevanceResult(
            classification=THAILAND_FOCUSED,
            reason=f"Explicit Thailand reference found in article text: {refs}.",
        )

    if has_thai_entity:
        refs = ", ".join(sorted(set(co_terms + sec_terms))[:6])
        return RelevanceResult(
            classification=THAILAND_RELATED,
            reason=f"References Thai company/sector/economic development indicators: {refs}.",
        )

    if global_terms and not has_thailand and not has_thai_entity:
        g = ", ".join(sorted(set(global_terms))[:6])
        return RelevanceResult(
            classification=INTERNATIONAL,
            reason=f"No explicit Thailand/Thai entity references found; international terms present ({g}).",
        )

    return RelevanceResult(
        classification=UNCERTAIN,
        reason=(
            "No clear explicit Thailand or Thai company/sector references detected, "
            "and insufficient signals to classify confidently as international."
        ),
    )


__all__ = [
    "RelevanceResult",
    "classify_thailand_relevance",
    "THAILAND_FOCUSED",
    "THAILAND_RELATED",
    "INTERNATIONAL",
    "UNCERTAIN",
]
