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


class NewsIngestSourceResult(BaseModel):
    name: str
    url: str
    type: Optional[str] = None
    http_status: Optional[int] = None
    content_type: Optional[str] = None
    parsed: int = 0
    ingested: int = 0
    skipped: int = 0
    error: Optional[str] = None
    final_status: str


class NewsIngestStats(BaseModel):
    ingested: int
    skipped_duplicate: int
    errors: int
    status: str
    sources: list[NewsIngestSourceResult]


__all__ = [
    "NewsArticleBase",
    "NewsArticleCreate",
    "NewsArticleOut",
    "NewsIngestSourceResult",
    "NewsIngestStats",
]
