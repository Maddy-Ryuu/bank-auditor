"""Statements and Transactions API endpoints."""
import hashlib
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.app.database import get_db
from backend.app.models.statement import Statement, Transaction
from backend.app.schemas.statement import (
    StatementResponse,
    StatementDetailResponse,
    SyntheticStatementUpload,
)

router = APIRouter(prefix="/statements", tags=["Statements"])


@router.get("", response_model=List[StatementResponse])
async def list_statements(
    account_id: Optional[str] = None,
    is_subsequent: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """List statements with optional filters."""
    stmt = select(Statement)
    if account_id:
        stmt = stmt.where(Statement.account_id == account_id)
    if is_subsequent is not None:
        stmt = stmt.where(Statement.is_subsequent_statement == is_subsequent)
    stmt = stmt.order_by(Statement.statement_period_start.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{statement_id}", response_model=StatementDetailResponse)
async def get_statement(statement_id: str, db: AsyncSession = Depends(get_db)):
    """Get statement details including line-item transactions."""
    stmt = (
        select(Statement)
        .where(Statement.id == statement_id)
        .options(selectinload(Statement.transactions))
    )
    result = await db.execute(stmt)
    statement = result.scalar_one_or_none()
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")
    return statement


@router.post("/upload-synthetic", response_model=StatementDetailResponse)
async def upload_synthetic_statement(
    payload: SyntheticStatementUpload,
    db: AsyncSession = Depends(get_db)
):
    """Upload or register a new synthetic statement for auditing."""
    raw_hash = hashlib.sha256(f"{payload.source_id}-{payload.source_filename}".encode("utf-8")).hexdigest()

    statement = Statement(
        account_id=payload.account_id,
        statement_period_start=payload.statement_period_start,
        statement_period_end=payload.statement_period_end,
        opening_balance=payload.opening_balance,
        closing_balance=payload.closing_balance,
        average_daily_balance=payload.average_daily_balance,
        total_qualifying_direct_deposits=payload.total_qualifying_direct_deposits,
        is_subsequent_statement=payload.is_subsequent_statement,
        source_id=payload.source_id,
        source_filename=payload.source_filename,
        raw_statement_hash=raw_hash
    )
    db.add(statement)
    await db.flush()

    for tx_in in payload.transactions:
        tx = Transaction(
            statement_id=statement.id,
            transaction_date=tx_in.transaction_date,
            posting_date=tx_in.posting_date,
            description=tx_in.description,
            transaction_type=tx_in.transaction_type,
            amount=tx_in.amount,
            balance_after=tx_in.balance_after,
            raw_category=tx_in.raw_category,
            source_transaction_id=tx_in.source_transaction_id
        )
        db.add(tx)

    await db.commit()
    await db.refresh(statement)

    # Reload with transactions
    reload_stmt = select(Statement).where(Statement.id == statement.id).options(selectinload(Statement.transactions))
    res = await db.execute(reload_stmt)
    return res.scalar_one()
