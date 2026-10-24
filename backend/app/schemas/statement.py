"""Pydantic schemas for Statements and Transactions."""
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class TransactionBase(BaseModel):
    transaction_date: date
    posting_date: date
    description: str
    transaction_type: str
    amount: float
    balance_after: float
    raw_category: str = "GENERAL"
    source_transaction_id: str


class TransactionResponse(TransactionBase):
    id: str
    statement_id: str

    model_config = ConfigDict(from_attributes=True)


class StatementBase(BaseModel):
    account_id: str
    statement_period_start: date
    statement_period_end: date
    opening_balance: float = 0.0
    closing_balance: float = 0.0
    average_daily_balance: float = 0.0
    total_qualifying_direct_deposits: float = 0.0
    is_subsequent_statement: bool = False
    source_id: str
    source_filename: str
    raw_statement_hash: str


class StatementResponse(StatementBase):
    id: str
    verified_against_statement_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StatementDetailResponse(StatementResponse):
    transactions: List[TransactionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class SyntheticStatementUpload(BaseModel):
    account_id: str
    statement_period_start: date
    statement_period_end: date
    opening_balance: float
    closing_balance: float
    average_daily_balance: float
    total_qualifying_direct_deposits: float
    is_subsequent_statement: bool = False
    source_id: str
    source_filename: str
    transactions: List[TransactionBase] = []
