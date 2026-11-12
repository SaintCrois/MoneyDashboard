"""News article API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.news_article import NewsArticle
from app.schemas.news import NewsArticleOut, NewsIngestStats
from app.services.news_service import ingest_articles

router = APIRouter()


@router.get("/news", response_model=List[NewsArticleOut])
def list_news(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    db: Session = Depends(get_db),
):
    """Retrieve news articles with pagination."""
    articles = (
        db.query(NewsArticle)
        .order_by(NewsArticle.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return articles


@router.get("/news/sources")
def list_news_sources():
    """Return the list of configured news sources for UI filtering."""
    from app.services.news_sources import DEFAULT_SOURCES

    return [
        {"name": s.name, "url": s.url, "type": s.source_type, "enabled": s.enabled}
        for s in DEFAULT_SOURCES
    ]


@router.get("/news/{article_id}", response_model=NewsArticleOut)
def get_news_article(article_id: int, db: Session = Depends(get_db)):
    """Retrieve a single news article by ID."""
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="News article not found"
        )
    return article


@router.get("/news/sources")
def list_news_sources():
    """Return the list of configured news sources for UI filtering."""
    from app.services.news_sources import DEFAULT_SOURCES

    return [
        {"name": s.name, "url": s.url, "type": s.source_type, "enabled": s.enabled}
        for s in DEFAULT_SOURCES
    ]


@router.post("/news/ingest", response_model=NewsIngestStats, status_code=status.HTTP_200_OK)
def ingest_news(db: Session = Depends(get_db)):
    """Trigger news ingestion from configured sources."""
    stats = ingest_articles(db)
    return stats

__all__ = ["router"]
