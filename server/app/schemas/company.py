"""Company request and response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CompanyBase(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=50, description="Stock ticker symbol")
    name: str = Field(..., min_length=1, max_length=255, description="Company name")
    exchange: str = Field(default="SET", max_length=100, description="Stock exchange")
    industry_id: Optional[int] = Field(default=None, description="Related industry ID")
    description: Optional[str] = Field(default=None, description="Company description")


class CompanyCreate(CompanyBase):
    pass


class CompanyOut(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    industry_name: Optional[str] = None
    created_at: datetime


__all__ = ["CompanyBase", "CompanyCreate", "CompanyOut"]
