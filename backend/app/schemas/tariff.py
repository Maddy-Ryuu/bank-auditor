"""Pydantic schemas for Tariff Rules."""
from typing import Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class TariffRuleBase(BaseModel):
    tier_id: str
    fee_category: str
    fee_name: str
    standard_amount: float
    condition_logic: Dict[str, Any] = {}
    effective_from: date
    effective_to: Optional[date] = None
    source_document_ref: str = "Published Tariff Schedule"


class TariffRuleCreate(TariffRuleBase):
    pass


class TariffRuleResponse(TariffRuleBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
