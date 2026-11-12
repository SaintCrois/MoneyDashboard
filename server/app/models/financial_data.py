"""FinancialData model: stores historical company financial metrics."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FinancialData(Base):
    __tablename__ = "financial_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    revenue: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    net_profit: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    operating_margin: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    net_profit_margin: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    debt_to_equity: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    current_ratio: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    free_cash_flow: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    roe: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("company_id", "fiscal_year", name="uq_company_fiscal_year"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<FinancialData(company_id={self.company_id}, fiscal_year={self.fiscal_year})>"
