"""Industry request and response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class IndustryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Industry name")
    description: Optional[str] = Field(default=None, description="Industry description")


class IndustryCreate(IndustryBase):
    pass


class IndustryOut(IndustryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


__all__ = ["IndustryBase", "IndustryCreate", "IndustryOut"]
