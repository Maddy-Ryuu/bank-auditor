"""Pydantic schemas for Accounts and Tiers."""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AccountTierBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    monthly_maintenance_fee: float
    min_balance_waiver: float
    min_direct_deposit_waiver: float
    overdraft_fee_amount: float
    max_daily_overdraft_fees: int
    overdraft_threshold_cents: int
    wire_incoming_domestic_fee: float
    wire_outgoing_domestic_fee: float
    wire_outgoing_international_fee: float
    paper_statement_fee: float
    foreign_transaction_fee_rate: float


class AccountTierResponse(AccountTierBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccountBase(BaseModel):
    account_number: str
    holder_name: str
    bank_name: str = "Apex National Bank"
    routing_number: str = "021000021"
    currency: str = "USD"
    current_balance: float = 0.0
    tier_id: str
    electronic_statements_enrolled: bool = True
    source_id: str = "SYNTH-MANUAL-01"
    source_url: Optional[str] = None


class AccountCreate(AccountBase):
    pass


class AccountResponse(AccountBase):
    id: str
    tier: Optional[AccountTierResponse] = None
    retrieval_timestamp: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
