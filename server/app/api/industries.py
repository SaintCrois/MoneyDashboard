"""Industry API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.industry import Industry
from app.schemas.industry import IndustryCreate, IndustryOut

router = APIRouter()


@router.get("/industries", response_model=list[IndustryOut])
def list_industries(db: Session = Depends(get_db)):
    """Retrieve all industries."""
    industries = db.query(Industry).order_by(Industry.id).all()
    return [
        IndustryOut(
            id=i.id,
            name=i.name,
            description=i.description,
            created_at=i.created_at,
        )
        for i in industries
    ]


@router.post("/industries", response_model=IndustryOut, status_code=status.HTTP_201_CREATED)
def create_industry(industry_in: IndustryCreate, db: Session = Depends(get_db)):
    """Create an industry. Prevents duplicate industry names."""
    existing = db.query(Industry).filter(Industry.name == industry_in.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Industry with name '{industry_in.name}' already exists",
        )
    industry = Industry(name=industry_in.name, description=industry_in.description)
    db.add(industry)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Industry with name '{industry_in.name}' already exists",
        )
    db.refresh(industry)
    return IndustryOut(
        id=industry.id,
        name=industry.name,
        description=industry.description,
        created_at=industry.created_at,
    )
