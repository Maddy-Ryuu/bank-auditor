"""Mock Bank Portal simulation and inspectability endpoints."""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.app.database import get_db
from backend.app.config import settings
from backend.app.models.reversal import MockBankAck, ReversalRequest
from backend.app.schemas.mock_bank import MockBankPortalStatusResponse

router = APIRouter(prefix="/mock-bank", tags=["Mock Bank Portal"])


@router.get("/status", response_model=MockBankPortalStatusResponse)
async def get_mock_bank_status(db: AsyncSession = Depends(get_db)):
    """Status and metrics of the isolated synthetic mock bank portal."""
    acks_count_res = await db.execute(select(func.count(MockBankAck.id)))
    acks_count = acks_count_res.scalar_one() or 0

    queued_count_res = await db.execute(
        select(func.count(ReversalRequest.id)).where(ReversalRequest.status == "APPROVED")
    )
    queued_count = queued_count_res.scalar_one() or 0

    return MockBankPortalStatusResponse(
        gateway_name=settings.MOCK_BANK_PORTAL_NAME,
        status="OPERATIONAL",
        endpoint="mock://internal-gateway.apexnational.com/api/v1/disputes/reversal",
        is_simulation=True,
        mock_settlement_cycle="SUBSEQUENT_STATEMENT_BILLING_CYCLE",
        total_reversals_processed=acks_count,
        pending_reversals_queued=queued_count
    )


@router.get("/tickets")
async def list_mock_tickets(db: AsyncSession = Depends(get_db)):
    """List all acknowledged mock bank dispute tickets."""
    stmt = select(MockBankAck).order_by(MockBankAck.received_at.desc())
    res = await db.execute(stmt)
    acks = list(res.scalars().all())
    return [
        {
            "id": a.id,
            "reversal_request_id": a.reversal_request_id,
            "mock_bank_ticket_id": a.mock_bank_ticket_id,
            "status_received": a.status_received,
            "portal_endpoint_called": a.portal_endpoint_called,
            "acknowledgement_payload": a.acknowledgement_payload,
            "received_at": a.received_at
        }
        for a in acks
    ]
