"""FinancialData model: stores historical company financial metrics.

Sprint 3 extends the model with additional reported fields, reporting period
metadata, and explicit source tracking. Existing Sprint 1 fields are preserved.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FinancialData(Base):
    __tablename__ = "financial_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    reporting_period: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )
    # Reported figures (preserved as reported; never silently replaced with zero)
    revenue: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    net_profit: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    operating_income: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    total_assets: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    total_liabilities: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    total_debt: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    shareholders_equity: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    operating_cash_flow: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    capital_expenditure: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    eps: Mapped[Optional[float]] = mapped_column(Numeric(20, 4), nullable=True)
    # Calculated ratios (derived from reported figures; stored for convenience)
    operating_margin: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    net_profit_margin: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    debt_to_equity: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    current_ratio: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    free_cash_flow: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    roe: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    revenue_growth: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    # Source and metadata
    data_source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reported_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_estimate: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("company_id", "fiscal_year", name="uq_company_fiscal_year"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<FinancialData(company_id={self.company_id}, "
            f"fiscal_year={self.fiscal_year}, period={self.reporting_period})>"
        )
