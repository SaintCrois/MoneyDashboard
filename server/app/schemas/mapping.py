"""Event-to-industry and event-to-company mapping schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EventIndustryBase(BaseModel):
    event_id: int = Field(..., description="Related event ID")
    industry_id: int = Field(..., description="Related industry ID")
    impact_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Positive, Negative, Mixed, or Uncertain",
    )
    relevance_score: Optional[float] = Field(
        default=None, description="Relevance or confidence score"
    )
    explanation: Optional[str] = Field(default=None, description="Mapping explanation")


class EventIndustryOut(EventIndustryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class EventCompanyBase(BaseModel):
    event_id: int = Field(..., description="Related event ID")
    company_id: int = Field(..., description="Related company ID")
    impact_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Positive, Negative, Mixed, or Uncertain",
    )
    exposure_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Direct or Indirect",
    )
    relevance_score: Optional[float] = Field(
        default=None, description="Relevance or confidence score"
    )
    explanation: Optional[str] = Field(default=None, description="Mapping explanation")
    match_confidence: Optional[str] = Field(default=None, description="High, Medium, or Low")
    match_reason: Optional[str] = Field(default=None, description="Why the company was matched")
    evidence: Optional[str] = Field(default=None, description="Supporting evidence text/reference")
    created_at: Optional[datetime] = Field(default=None, description="Mapping creation time")


class EventCompanyOut(EventCompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class EventIndustryDetail(EventIndustryOut):
    industry_name: Optional[str] = None


class EventCompanyDetail(EventCompanyOut):
    company_name: Optional[str] = None
    ticker: Optional[str] = None


__all__ = [
    "EventIndustryBase",
    "EventIndustryOut",
    "EventIndustryDetail",
    "EventCompanyBase",
    "EventCompanyOut",
    "EventCompanyDetail",
]

