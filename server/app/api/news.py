"""News article API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
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
    source: Optional[str] = Query(None, description="Filter by source name"),
    thailand_relevance: Optional[str] = Query(None, description="Filter by Thailand relevance"),
    language: Optional[str] = Query(None, description="Filter by language"),
    db: Session = Depends(get_db),
):
    """Retrieve news articles with pagination and optional filters."""
    query = db.query(NewsArticle)
    if source:
        query = query.filter(NewsArticle.source == source)
    if thailand_relevance:
        query = query.filter(NewsArticle.thailand_relevance == thailand_relevance)
    if language:
        query = query.filter(NewsArticle.language == language)
    articles = query.order_by(NewsArticle.created_at.desc()).offset(skip).limit(limit).all()
    return articles


@router.get("/news/sources")
def list_news_sources(db: Session = Depends(get_db)):
    """Return configured news sources with latest ingestion status."""
    from app.services.news_sources import get_configured_sources

    sources = get_configured_sources()
    status_rows = {}
    try:
        rows = db.execute(
            text(
                "SELECT source_name, http_status, content_type, parsed_count, inserted_count, "
                "duplicate_count, error_message, final_status, last_successful_ingestion_at, last_checked_at "
                "FROM news_source_status"
            )
        ).mappings().all()
        for r in rows:
            status_rows[r["source_name"]] = dict(r)
    except Exception:
        status_rows = {}

    out = []
    for s in sources:
        st = status_rows.get(s.name, {})
        out.append(
            {
                "name": s.name,
                "publisher": getattr(s, "publisher", s.name),
                "url": s.url,
                "type": s.source_type,
                "enabled": getattr(s, "enabled", True),
                "language": getattr(s, "language", "en"),
                "notes": getattr(s, "notes", None),
                "http_status": st.get("http_status"),
                "content_type": st.get("content_type"),
                "parsed_count": st.get("parsed_count"),
                "inserted_count": st.get("inserted_count"),
                "duplicate_count": st.get("duplicate_count"),
                "error_message": st.get("error_message"),
                "final_status": st.get("final_status"),
                "last_successful_ingestion_at": st.get("last_successful_ingestion_at"),
                "last_checked_at": st.get("last_checked_at"),
            }
        )
    return out


@router.get("/news/{article_id}", response_model=NewsArticleOut)
def get_news_article(article_id: int, db: Session = Depends(get_db)):
    """Retrieve a single news article by ID."""
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="News article not found"
        )
    return article


@router.post("/news/ingest", response_model=NewsIngestStats, status_code=status.HTTP_200_OK)
def ingest_news(db: Session = Depends(get_db)):
    """Trigger news ingestion from configured sources."""
    stats = ingest_articles(db)
    return stats


__all__ = ["router"]

