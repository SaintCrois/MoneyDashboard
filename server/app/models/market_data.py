"""MarketData model: stores historical market information.

Sprint 3 extends the model with OHLC fields, daily change, data source, and
timestamps. Existing Sprint 1 fields are preserved. A unique constraint
prevents duplicate records for the same company and trading date/timestamp.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MarketData(Base):
    __tablename__ = "market_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    # OHLC and volume (reported market values)
    open_price: Mapped[Optional[float]] = mapped_column(Numeric(20, 4), nullable=True)
    high_price: Mapped[Optional[float]] = mapped_column(Numeric(20, 4), nullable=True)
    low_price: Mapped[Optional[float]] = mapped_column(Numeric(20, 4), nullable=True)
    close_price: Mapped[Optional[float]] = mapped_column(Numeric(20, 4), nullable=True)
    stock_price: Mapped[Optional[float]] = mapped_column(Numeric(20, 4), nullable=True)
    trading_volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    # Derived / market indicators
    daily_change_pct: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    # Existing Sprint 1 investor flow fields
    foreign_net_value: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    institutional_net_value: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    # Source and metadata
    data_source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_delayed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_estimate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("company_id", "recorded_at", name="uq_company_recorded_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MarketData(company_id={self.company_id}, recorded_at={self.recorded_at})>"
