"""EventCompany model: connects events with potentially affected companies."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EventCompany(Base):
    __tablename__ = "event_companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    impact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    exposure_type: Mapped[str] = mapped_column(String(50), nullable=False)
    relevance_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Traceable matching metadata (additive).
    match_confidence: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # High | Medium | Low
    match_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("event_id", "company_id", name="uq_event_company"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<EventCompany(event_id={self.event_id}, company_id={self.company_id})>"

