"""Company request and response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CompanyBase(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=50, description="Stock ticker symbol")
    name: str = Field(..., min_length=1, max_length=255, description="Company name")
    exchange: str = Field(default="SET", max_length=100, description="Stock exchange")
    market: Optional[str] = Field(default=None, max_length=100, description="Market/listing board")
    sector: Optional[str] = Field(default=None, max_length=255, description="Sector if available")
    industry_id: Optional[int] = Field(default=None, description="Related industry ID")
    description: Optional[str] = Field(default=None, description="Company description")
    source: Optional[str] = Field(default=None, max_length=255, description="Data source")


class CompanyCreate(CompanyBase):
    pass


class CompanyOut(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    industry_name: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    created_at: datetime


class CompanySyncResult(BaseModel):
    retrieved: int = 0
    imported: int = 0
    updated: int = 0
    duplicates_skipped: int = 0
    errors: list[str] = Field(default_factory=list)
    source: str = "unknown"
    used_fallback: bool = False
    last_sync_time: Optional[datetime] = None
    message: Optional[str] = None


__all__ = ["CompanyBase", "CompanyCreate", "CompanyOut", "CompanySyncResult"]

