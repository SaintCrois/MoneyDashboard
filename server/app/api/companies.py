"""Company API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.models.industry import Industry
from app.schemas.company import CompanyCreate, CompanyOut

router = APIRouter()


def _company_to_out(company: Company, db: Session) -> CompanyOut:
    industry_name = None
    if company.industry_id:
        industry = db.query(Industry).filter(Industry.id == company.industry_id).first()
        if industry:
            industry_name = industry.name
    return CompanyOut(
        id=company.id,
        ticker=company.ticker,
        name=company.name,
        exchange=company.exchange,
        industry_id=company.industry_id,
        industry_name=industry_name,
        description=company.description,
        created_at=company.created_at,
    )


@router.get("/companies", response_model=list[CompanyOut])
def list_companies(
    industry_id: Optional[int] = Query(None, description="Filter companies by industry ID"),
    db: Session = Depends(get_db),
):
    """Retrieve companies, optionally filtered by industry."""
    query = db.query(Company)
    if industry_id is not None:
        query = query.filter(Company.industry_id == industry_id)
    companies = query.order_by(Company.id).all()
    return [_company_to_out(c, db) for c in companies]


@router.get("/companies/{company_id}", response_model=CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db)):
    """Retrieve a single company by ID."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return _company_to_out(company, db)


@router.post("/companies", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(company_in: CompanyCreate, db: Session = Depends(get_db)):
    """Create a company. Rejects duplicate tickers."""
    existing = db.query(Company).filter(Company.ticker == company_in.ticker).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Company with ticker '{company_in.ticker}' already exists",
        )
    company = Company(
        ticker=company_in.ticker,
        name=company_in.name,
        exchange=company_in.exchange,
        industry_id=company_in.industry_id,
        description=company_in.description,
    )
    db.add(company)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Company with ticker '{company_in.ticker}' already exists",
        )
    db.refresh(company)
    return _company_to_out(company, db)
