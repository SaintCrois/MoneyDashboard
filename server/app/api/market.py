"""Market data API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.schemas.market import MarketAnalysisOut, MarketDataCreate, MarketDataOut
from app.services.market_service import (
    analyze_market,
    create_market_record,
    get_market_data,
    import_market_data_from_csv,
)

router = APIRouter()


def _get_company_or_404(db: Session, company_id: int) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.get("/companies/{company_id}/market-data", response_model=List[MarketDataOut])
def list_company_market_data(company_id: int, db: Session = Depends(get_db)):
    """Retrieve all market data records for a company, ordered by recorded_at."""
    _get_company_or_404(db, company_id)
    records = get_market_data(db, company_id)
    return records


@router.post(
    "/companies/{company_id}/market-data",
    response_model=MarketDataOut,
    status_code=status.HTTP_201_CREATED,
)
def create_company_market_data(
    company_id: int,
    payload: MarketDataCreate,
    db: Session = Depends(get_db),
):
    """Create a market data record. Rejects duplicate (company, recorded_at)."""
    _get_company_or_404(db, company_id)
    data = payload.model_dump()
    record, err = create_market_record(db, company_id, data)
    if err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    return record


@router.get("/companies/{company_id}/market-analysis", response_model=MarketAnalysisOut)
def get_company_market_analysis(company_id: int, db: Session = Depends(get_db)):
    """Return market analysis including records and calculated indicators."""
    company = _get_company_or_404(db, company_id)
    analysis = analyze_market(db, company)
    out_records = [MarketDataOut.model_validate(r) for r in analysis["records"]]
    return MarketAnalysisOut(
        company_id=analysis["company_id"],
        company_ticker=analysis.get("company_ticker"),
        company_name=analysis.get("company_name"),
        records=out_records,
        indicators=analysis["indicators"],
        unavailable_indicators=analysis["unavailable_indicators"],
        data_sources=analysis["data_sources"],
        latest_update=analysis.get("latest_update"),
        notes=analysis.get("notes", []),
    )


@router.post("/companies/{company_id}/market-data/import")
async def import_company_market_data(
    company_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Import market data records from an uploaded CSV file."""
    _get_company_or_404(db, company_id)
    try:
        content = await file.read()
        text = content.decode("utf-8-sig")
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to read uploaded file as UTF-8 CSV")
    stats = import_market_data_from_csv(db, company_id, text, data_source=f"CSV import: {file.filename}")
    return stats
