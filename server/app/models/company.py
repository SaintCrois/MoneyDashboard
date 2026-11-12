"""Company model: stores publicly listed companies."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    exchange: Mapped[str] = mapped_column(String(100), nullable=False, server_default="SET")
    industry_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("industries.id", ondelete="SET NULL"), nullable=True, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    industry = relationship("Industry", back_populates="companies", lazy="select")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Company(id={self.id}, ticker={self.ticker!r})>"
