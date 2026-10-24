"""Tariff Rules API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import get_db
from backend.app.models.tariff import TariffRule
from backend.app.schemas.tariff import TariffRuleResponse, TariffRuleCreate

router = APIRouter(prefix="/tariffs", tags=["Tariffs"])


@router.get("", response_model=List[TariffRuleResponse])
async def list_tariffs(tier_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """List all tariff rules, optionally filtered by account tier."""
    stmt = select(TariffRule)
    if tier_id:
        stmt = stmt.where(TariffRule.tier_id == tier_id)
    stmt = stmt.order_by(TariffRule.fee_category)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=TariffRuleResponse)
async def create_tariff(payload: TariffRuleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new tariff rule."""
    rule = TariffRule(**payload.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule
