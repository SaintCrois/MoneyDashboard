"""MarketData model: stores historical market information."""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MarketData(Base):
    __tablename__ = "market_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    stock_price: Mapped[Optional[float]] = mapped_column(Numeric(20, 4), nullable=True)
    trading_volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    foreign_net_value: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    institutional_net_value: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MarketData(company_id={self.company_id}, recorded_at={self.recorded_at})>"
