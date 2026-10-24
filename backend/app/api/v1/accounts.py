"""Account and Tier API endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.app.database import get_db
from backend.app.models.account import Account, AccountTier
from backend.app.schemas.account import AccountResponse, AccountTierResponse

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get("", response_model=List[AccountResponse])
async def list_accounts(db: AsyncSession = Depends(get_db)):
    """List all accounts with their assigned tiers."""
    stmt = select(Account).options(selectinload(Account.tier)).order_by(Account.holder_name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/tiers", response_model=List[AccountTierResponse])
async def list_tiers(db: AsyncSession = Depends(get_db)):
    """List all account tiers and fee schedules."""
    stmt = select(AccountTier).order_by(AccountTier.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: str, db: AsyncSession = Depends(get_db)):
    """Get single account by ID."""
    stmt = select(Account).where(Account.id == account_id).options(selectinload(Account.tier))
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account
