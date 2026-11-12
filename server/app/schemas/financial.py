"""Financial data request and response schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class FinancialDataBase(BaseModel):
    fiscal_year: int = Field(..., ge=1900, le=2100, description="Fiscal year")
    reporting_period: Optional[str] = Field(default=None, max_length=50, description="e.g. FY2024, Q1-2024")
    # Reported figures
    revenue: Optional[float] = Field(default=None, description="Reported revenue")
    net_profit: Optional[float] = Field(default=None, description="Reported net profit/income")
    operating_income: Optional[float] = Field(default=None, description="Reported operating income")
    total_assets: Optional[float] = Field(default=None, description="Reported total assets")
    total_liabilities: Optional[float] = Field(default=None, description="Reported total liabilities")
    total_debt: Optional[float] = Field(default=None, description="Reported total debt")
    shareholders_equity: Optional[float] = Field(default=None, description="Reported shareholders' equity")
    operating_cash_flow: Optional[float] = Field(default=None, description="Reported operating cash flow")
    capital_expenditure: Optional[float] = Field(default=None, description="Reported capital expenditure")
    eps: Optional[float] = Field(default=None, description="Reported earnings per share")
    # Existing Sprint 1 fields (can be provided or calculated)
    operating_margin: Optional[float] = Field(default=None, description="Operating margin")
    net_profit_margin: Optional[float] = Field(default=None, description="Net profit margin")
    debt_to_equity: Optional[float] = Field(default=None, description="Debt-to-equity ratio")
    current_ratio: Optional[float] = Field(default=None, description="Current ratio")
    free_cash_flow: Optional[float] = Field(default=None, description="Free cash flow")
    roe: Optional[float] = Field(default=None, description="Return on equity")
    revenue_growth: Optional[float] = Field(default=None, description="Revenue growth %")
    # Metadata
    data_source: Optional[str] = Field(default=None, max_length=255, description="Data source name")
    reported_at: Optional[datetime] = Field(default=None, description="When the data was reported")
    is_estimate: bool = Field(default=False, description="True if data is estimated, not reported")


class FinancialDataCreate(FinancialDataBase):
    pass


class FinancialDataOut(FinancialDataBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    created_at: datetime


class FinancialAnalysisOut(BaseModel):
    company_id: int
    company_ticker: Optional[str] = None
    company_name: Optional[str] = None
    records: list[FinancialDataOut]
    calculated_metrics: list[dict[str, Any]]
    unavailable_metrics: list[str]
    data_sources: list[str]
    latest_period: Optional[str] = None
    notes: list[str]


__all__ = ["FinancialDataBase", "FinancialDataCreate", "FinancialDataOut", "FinancialAnalysisOut"]
