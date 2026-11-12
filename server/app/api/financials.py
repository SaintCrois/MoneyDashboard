"""Financial data API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.models.financial_data import FinancialData
from app.schemas.financial import FinancialAnalysisOut, FinancialDataCreate, FinancialDataOut
from app.services.financial_service import (
    analyze_financials,
    create_financial_record,
    get_financials,
    import_financials_from_csv,
)

router = APIRouter()


def _get_company_or_404(db: Session, company_id: int) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.get("/companies/{company_id}/financials", response_model=List[FinancialDataOut])
def list_company_financials(company_id: int, db: Session = Depends(get_db)):
    """Retrieve all financial records for a company, ordered by fiscal year."""
    _get_company_or_404(db, company_id)
    records = get_financials(db, company_id)
    return records


@router.post(
    "/companies/{company_id}/financials",
    response_model=FinancialDataOut,
    status_code=status.HTTP_201_CREATED,
)
def create_company_financial(
    company_id: int,
    payload: FinancialDataCreate,
    db: Session = Depends(get_db),
):
    """Create a financial record for a company. Rejects duplicate (company, fiscal_year)."""
    _get_company_or_404(db, company_id)
    data = payload.model_dump()
    record, err = create_financial_record(db, company_id, data)
    if err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    return record


@router.get("/companies/{company_id}/financial-analysis", response_model=FinancialAnalysisOut)
def get_company_financial_analysis(company_id: int, db: Session = Depends(get_db)):
    """Return financial analysis including reported records and calculated metrics."""
    company = _get_company_or_404(db, company_id)
    analysis = analyze_financials(db, company)
    # Serialize records via schema-compatible dicts
    out_records = [FinancialDataOut.model_validate(r) for r in analysis["records"]]
    return FinancialAnalysisOut(
        company_id=analysis["company_id"],
        company_ticker=analysis.get("company_ticker"),
        company_name=analysis.get("company_name"),
        records=out_records,
        calculated_metrics=analysis["calculated_metrics"],
        unavailable_metrics=analysis["unavailable_metrics"],
        data_sources=analysis["data_sources"],
        latest_period=analysis.get("latest_period"),
        notes=analysis.get("notes", []),
    )


@router.post("/companies/{company_id}/financials/import")
async def import_company_financials(
    company_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Import financial records from an uploaded CSV file."""
    _get_company_or_404(db, company_id)
    try:
        content = await file.read()
        text = content.decode("utf-8-sig")
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to read uploaded file as UTF-8 CSV")
    stats = import_financials_from_csv(db, company_id, text, data_source=f"CSV import: {file.filename}")
    return stats
