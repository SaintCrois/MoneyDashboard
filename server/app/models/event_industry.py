"""EventIndustry model: connects events with potentially affected industries."""

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from app.database import Base


class EventIndustry(Base):
    __tablename__ = "event_industries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    industry_id: Mapped[int] = mapped_column(
        ForeignKey("industries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    impact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("event_id", "industry_id", name="uq_event_industry"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<EventIndustry(event_id={self.event_id}, industry_id={self.industry_id})>"
