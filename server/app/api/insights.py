"""Keyword-level insight endpoints for the WhyMove web app.

These answer "which news may relate to this stock, and how could that kind of
event affect the business". They use business-keyword rules only: no AI, and
they never write to or read from the evidence-backed company mappings.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.company import Company
from app.models.news_article import NewsArticle
from app.services.keyword_insight import MATCH_LEVELS, SCENARIOS, rank_news, related_companies

router = APIRouter()

POOL_SIZE = 400
LEVEL_PATTERN = "^(strict|medium|loose)$"


def _article_dict(a: NewsArticle) -> dict:
    return {
        "id": a.id,
        "title": a.title,
        "source": a.source,
        "url": a.url,
        "published_at": a.published_at.isoformat() if a.published_at else None,
        "summary": a.summary,
        "thailand_relevance": a.thailand_relevance,
    }


def _company_dict(c: Company) -> dict:
    return {
        "id": c.id,
        "ticker": c.ticker,
        "name": c.name,
        "industry_name": c.industry.name if c.industry else None,
        "sector": c.sector,
        "description": c.description,
    }


def _pool(db: Session) -> list[dict]:
    rows = (
        db.query(NewsArticle)
        .order_by(NewsArticle.published_at.desc().nullslast(), NewsArticle.id.desc())
        .limit(POOL_SIZE)
        .all()
    )
    return [_article_dict(a) for a in rows]


def _companies(db: Session) -> list[dict]:
    rows = db.query(Company).options(joinedload(Company.industry)).order_by(Company.ticker).all()
    return [_company_dict(c) for c in rows]


def _item(n: int, ranked: dict) -> dict:
    return {
        "n": n,
        "article": ranked["article"],
        "direct": ranked["score"] >= 10,
        "groups": ranked["groups"],
        "reason": ranked["reason"],
    }


@router.get("/insights/levels")
def list_levels():
    """The match strictness levels and what each one requires."""
    return [{"key": k, "description": v} for k, v in MATCH_LEVELS.items()]


@router.get("/insights/companies")
def list_company_insights(
    level: str = Query("medium", pattern=LEVEL_PATTERN),
    db: Session = Depends(get_db),
):
    """Every company with how many recent news items may relate to it."""
    pool = _pool(db)
    out = []
    for company in _companies(db):
        ranked = rank_news(company, pool, limit=POOL_SIZE, level=level)
        out.append(
            {
                "company": company,
                "count": len(ranked),
                "direct_count": sum(1 for r in ranked if r["score"] >= 10),
                "top": ranked[0]["article"] if ranked else None,
            }
        )
    return {"level": level, "pool_size": len(pool), "companies": out}


@router.get("/insights/companies/{ticker}")
def get_company_insight(
    ticker: str,
    level: str = Query("medium", pattern=LEVEL_PATTERN),
    limit: int = Query(12, ge=1, le=40),
    db: Session = Depends(get_db),
):
    """Related news for one company plus the example scenarios those news fall under."""
    company = next((c for c in _companies(db) if c["ticker"].upper() == ticker.upper()), None)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    pool = _pool(db)
    all_ranked = rank_news(company, pool, limit=POOL_SIZE, level=level)
    items = [_item(i, r) for i, r in enumerate(all_ranked[:limit], 1)]
    scenarios = []
    for group in sorted({g for it in items for g in it["groups"]}):
        sc = SCENARIOS[group]
        scenarios.append(
            {
                "group": group,
                "label": sc["label"],
                "kind": sc["kind"],
                "effect": sc["effect"],
                "check": [part.removeprefix("และ") for part in sc["check"].split() if part.removeprefix("และ")],
                "refs": [it["n"] for it in items if group in it["groups"]],
            }
        )
    return {
        "company": company,
        "level": level,
        "pool_size": len(pool),
        "total": len(all_ranked),
        "items": items,
        "scenarios": scenarios,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method": "keyword_rules_v1",
    }


@router.get("/insights/feed")
def get_feed(
    level: str = Query("medium", pattern=LEVEL_PATTERN),
    limit: int = Query(60, ge=1, le=200),
    group: Optional[str] = Query(None, description="Only news that match this business group"),
    db: Session = Depends(get_db),
):
    """Recent news, each with the companies it may relate to."""
    companies = _companies(db)
    out = []
    for article in _pool(db):
        related = related_companies(article["title"], article["summary"], companies, level=level)
        if group and not any(group in r.get("groups", []) for r in related):
            continue
        out.append({"article": article, "companies": related})
        if len(out) >= limit:
            break
    return {"level": level, "items": out}


@router.get("/insights/groups")
def list_groups():
    return [{"key": k, "label": v["label"]} for k, v in SCENARIOS.items()]
