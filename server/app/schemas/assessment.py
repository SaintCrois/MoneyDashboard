"""Impact assessment request and response schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class AssessmentGenerateRequest(BaseModel):
    use_ai: bool = Field(default=False, description="Explicitly call the configured AI provider for one event")
    company_id: int = Field(..., description="Company to assess")
    event_id: Optional[int] = Field(default=None, description="Specific event to assess; if omitted, assess most relevant events")


class ImpactAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    company_id: int
    impact_type: str
    impact_severity: Optional[str] = None
    risk_level: str
    confidence: Optional[float] = None
    explanation: Optional[str] = None
    financial_exposure: Optional[str] = None
    relevant_financial_metrics: Optional[Any] = None
    relevant_market_indicators: Optional[Any] = None
    supporting_evidence: Optional[Any] = None
    missing_information: Optional[Any] = None
    methodology: Optional[str] = None
    input_snapshot: Optional[Any] = None
    assessed_at: Optional[datetime] = None
    created_at: datetime
    # Enriched fields (optional, populated by API)
    company_name: Optional[str] = None
    company_ticker: Optional[str] = None
    event_title: Optional[str] = None
    event_category: Optional[str] = None


__all__ = ["AssessmentGenerateRequest", "ImpactAssessmentOut"]
