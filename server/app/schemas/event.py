"""Event request and response schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, description="Event title")
    description: str = Field(..., description="Event description")
    category: str = Field(..., min_length=1, max_length=50, description="Event category")
    location: Optional[str] = Field(default=None, max_length=255, description="Event location")
    event_date: Optional[datetime] = Field(default=None, description="Date of the event")


class EventCreate(EventBase):
    source_article_id: Optional[int] = Field(
        default=None, description="Related source article ID"
    )
    classification_method: Optional[str] = Field(
        default=None, description="Method used to classify the event"
    )
    confidence_score: Optional[float] = Field(
        default=None, description="Classification confidence score"
    )
    processing_status: str = Field(default="processed", max_length=50)


class EventOut(EventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_article_id: Optional[int] = None
    classification_method: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_status: str
    created_at: datetime


class EventProcessStats(BaseModel):
    processed: int
    skipped: int
    errors: int
    events: list[dict]


class CategoryOut(BaseModel):
    category: str


__all__ = [
    "EventBase",
    "EventCreate",
    "EventOut",
    "EventProcessStats",
    "CategoryOut",
]
