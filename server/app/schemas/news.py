"""News article request and response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class NewsArticleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, description="Article title")
    source: str = Field(..., min_length=1, max_length=255, description="News source name")
    url: str = Field(..., description="Original article URL")
    published_at: Optional[datetime] = Field(
        default=None, description="Publication timestamp"
    )
    summary: Optional[str] = Field(default=None, description="Article summary")
    content: Optional[str] = Field(default=None, description="Article content")


class NewsArticleCreate(NewsArticleBase):
    pass


class NewsArticleOut(NewsArticleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fetched_at: Optional[datetime] = None
    created_at: datetime


class NewsIngestStats(BaseModel):
    ingested: int
    skipped_duplicate: int
    errors: int
    sources: list[dict]


__all__ = ["NewsArticleBase", "NewsArticleCreate", "NewsArticleOut", "NewsIngestStats"]
