"""ImpactAssessment model: stores AI-generated company impact assessments.

Sprint 3 extends the model with structured assessment fields: severity,
methodology, financial/market evidence summaries, supporting references,
and missing-information tracking. Existing Sprint 1 fields are preserved.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ImpactAssessment(Base):
    __tablename__ = "impact_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Classification
    impact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    impact_severity: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, server_default="Unknown"
    )
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    # Explanations and evidence (stored as JSON text for portability)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    financial_exposure: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    relevant_financial_metrics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    relevant_market_indicators: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supporting_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    missing_information: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Methodology and reproducibility
    methodology: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    input_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Timestamps
    assessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ImpactAssessment(id={self.id}, company_id={self.company_id})>"
