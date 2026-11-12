"""Event model: stores structured events extracted from news."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    event_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source_article_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("news_articles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    classification_method: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    processing_status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="processed"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    source_article = relationship("NewsArticle", lazy="select")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Event(id={self.id}, title={self.title!r})>"
