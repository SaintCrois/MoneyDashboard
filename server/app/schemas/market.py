"""Market data request and response schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class MarketDataBase(BaseModel):
    recorded_at: datetime = Field(..., description="Trading date/timestamp")
    stock_price: Optional[float] = Field(default=None, description="Last/close stock price")
    open_price: Optional[float] = Field(default=None, description="Opening price")
    high_price: Optional[float] = Field(default=None, description="Highest price")
    low_price: Optional[float] = Field(default=None, description="Lowest price")
    close_price: Optional[float] = Field(default=None, description="Closing price")
    trading_volume: Optional[int] = Field(default=None, ge=0, description="Trading volume")
    daily_change_pct: Optional[float] = Field(default=None, description="Daily % price change")
    foreign_net_value: Optional[float] = Field(default=None, description="Foreign investor net value")
    institutional_net_value: Optional[float] = Field(default=None, description="Institutional investor net value")
    data_source: Optional[str] = Field(default=None, max_length=255, description="Data source name")
    is_delayed: bool = Field(default=False, description="True if data is delayed")
    is_estimate: bool = Field(default=False, description="True if data is estimated/demonstration")


class MarketDataCreate(MarketDataBase):
    pass


class MarketDataOut(MarketDataBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    created_at: datetime


class MarketAnalysisOut(BaseModel):
    company_id: int
    company_ticker: Optional[str] = None
    company_name: Optional[str] = None
    records: list[MarketDataOut]
    indicators: dict[str, Any]
    unavailable_indicators: list[str]
    data_sources: list[str]
    latest_update: Optional[datetime] = None
    notes: list[str]


__all__ = ["MarketDataBase", "MarketDataCreate", "MarketDataOut", "MarketAnalysisOut"]
