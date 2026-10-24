"""Reversal service managing reversal drafts, human approvals, and mock submissions."""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.app.models.audit import AuditFinding
from backend.app.models.reversal import ReversalRequest, ApprovalEvent, MockBankAck
from backend.app.models.account import Account
from backend.app.models.statement import Statement
from backend.app.mock_bank.client import mock_bank_client
from backend.app.logging_config import logger


class ReversalService:
    """Handles reversal workflow: draft generation, approval audits, and mock submission."""

    def generate_dispute_memo(self, finding: AuditFinding, account: Account, statement: Statement) -> str:
        """Generates formal, legally-structured fee reversal dispute letter."""
        today_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
        ref_id = f"REV-{datetime.now(timezone.utc).strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"

        memo = (
            f"DISPUTE NOTICE & REQUEST FOR IMMEDIATE FEE REVERSAL\n"
            f"Reference: {ref_id}\n"
            f"Date: {today_str}\n\n"
            f"TO: Operations & Billing Disputes Department\n"
            f"    {account.bank_name}\n\n"
            f"RE: Non-Compliant Fee Dispute for Account {account.account_number}\n"
            f"    Account Holder: {account.holder_name}\n"
            f"    Statement Billing Cycle: {statement.statement_period_start} to {statement.statement_period_end}\n\n"
            f"SUMMARY OF DISPUTE:\n"
            f"Our audit system identified an improper fee assessment totaling ${finding.potential_refund_amount:.2f} "
            f"categorized under '{finding.rule_category}'.\n\n"
            f"VIOLATION FINDING:\n"
            f"• Title: {finding.violation_title}\n"
            f"• Rationale: {finding.violation_reason}\n\n"
            f"AUDIT EVIDENCE SUMMARY:\n"
            f"• Source Statement ID: {statement.source_id}\n"
            f"• Evidence Snapshot: {finding.source_evidence_snapshot or 'Contractual waiver met'}\n"
            f"• Detailed Proof: {finding.evidence_data}\n\n"
            f"REQUESTED ACTION:\n"
            f"Please credit back the sum of ${finding.potential_refund_amount:.2f} to Account {account.account_number} "
            f"on or before the conclusion of the subsequent billing cycle.\n\n"
            f"Submitted via Bank Fee Auditor Compliance Interface\n"
            f"Synthetic Provenance Hash: {statement.raw_statement_hash[:16]}..."
        )
        return memo

    async def draft_reversal(
        self,
        db: AsyncSession,
        finding_id: str,
        prepared_by: str = "Automated Fee Audit Engine"
    ) -> ReversalRequest:
        """Draft a formal reversal request from an existing audit finding."""
        stmt = (
            select(AuditFinding)
            .where(AuditFinding.id == finding_id)
            .options(
                selectinload(AuditFinding.statement).selectinload(Statement.account),
                selectinload(AuditFinding.reversal_request)
            )
        )
        result = await db.execute(stmt)
        finding = result.scalar_one_or_none()
        if not finding:
            raise ValueError(f"Audit finding {finding_id} not found.")

        if finding.reversal_request:
            return finding.reversal_request

        statement = finding.statement
        account = statement.account
        ref_number = f"REV-{datetime.now(timezone.utc).strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"

        rationale = self.generate_dispute_memo(finding, account, statement)

        reversal = ReversalRequest(
            finding_id=finding.id,
            account_id=account.id,
            reference_number=ref_number,
            requested_amount=finding.potential_refund_amount,
            rationale_letter=rationale,
            status="PENDING_APPROVAL",  # Ready for human review
            prepared_by=prepared_by
        )
        db.add(reversal)
        finding.status = "REVERSAL_REQUESTED"

        await db.commit()
        logger.info(f"Drafted reversal request {ref_number} for finding {finding_id}.")

        reload_stmt = (
            select(ReversalRequest)
            .where(ReversalRequest.id == reversal.id)
            .options(
                selectinload(ReversalRequest.finding).selectinload(AuditFinding.transaction),
                selectinload(ReversalRequest.approvals),
                selectinload(ReversalRequest.mock_ack)
            )
        )
        reload_res = await db.execute(reload_stmt)
        return reload_res.scalar_one()

    async def update_draft(
        self,
        db: AsyncSession,
        reversal_id: str,
        requested_amount: Optional[float] = None,
        rationale_letter: Optional[str] = None,
        editor_user: str = "Compliance Officer"
    ) -> ReversalRequest:
        """Update a reversal request draft.
        
        SAFETY RULE: Editing an approved draft immediately invalidates prior approval,
        resetting status back to PENDING_APPROVAL and logging an audit event.
        """
        stmt = (
            select(ReversalRequest)
            .where(ReversalRequest.id == reversal_id)
            .options(
                selectinload(ReversalRequest.approvals),
                selectinload(ReversalRequest.finding)
            )
        )
        result = await db.execute(stmt)
        reversal = result.scalar_one_or_none()
        if not reversal:
            raise ValueError(f"Reversal request {reversal_id} not found.")

        if reversal.status in ("SUBMITTED_TO_MOCK_PORTAL", "ACKNOWLEDGED", "SETTLED"):
            raise ValueError(
                f"Cannot modify reversal {reversal.reference_number}. "
                f"It has already been submitted to the mock bank gateway (status: '{reversal.status}')."
            )

        had_prior_approval = (reversal.status == "APPROVED")

        if requested_amount is not None:
            if requested_amount <= 0:
                raise ValueError("Requested amount must be greater than zero.")
            reversal.requested_amount = requested_amount

        if rationale_letter is not None:
            reversal.rationale_letter = rationale_letter

        # If it was already approved, modifying it MUST invalidate prior approval
        if had_prior_approval:
            reversal.status = "PENDING_APPROVAL"
            if reversal.finding:
                reversal.finding.status = "REVERSAL_REQUESTED"

            invalidation_event = ApprovalEvent(
                reversal_request_id=reversal.id,
                action="APPROVAL_INVALIDATED",
                approved_by_user=editor_user,
                notes="Draft modified after prior approval; approval invalidated. Re-approval required.",
                ip_address="127.0.0.1",
                event_timestamp=datetime.now(timezone.utc)
            )
            reversal.approvals.append(invalidation_event)
            db.add(invalidation_event)
            logger.warning(f"Prior approval invalidated for reversal {reversal.reference_number} due to edits by {editor_user}.")

        await db.commit()

        reload_stmt = (
            select(ReversalRequest)
            .where(ReversalRequest.id == reversal.id)
            .options(
                selectinload(ReversalRequest.finding).selectinload(AuditFinding.transaction),
                selectinload(ReversalRequest.approvals),
                selectinload(ReversalRequest.mock_ack)
            )
        )
        reload_res = await db.execute(reload_stmt)
        return reload_res.scalar_one()

    async def record_approval(
        self,
        db: AsyncSession,
        reversal_id: str,
        action: str,  # "APPROVE", "REJECT", "REQUEST_REVISION"
        approved_by_user: str,
        notes: Optional[str] = None,
        ip_address: Optional[str] = "127.0.0.1"
    ) -> ReversalRequest:
        """Record human approval or rejection before submission to mock portal."""
        stmt = (
            select(ReversalRequest)
            .where(ReversalRequest.id == reversal_id)
            .options(
                selectinload(ReversalRequest.approvals),
                selectinload(ReversalRequest.finding)
            )
        )
        result = await db.execute(stmt)
        reversal = result.scalar_one_or_none()
        if not reversal:
            raise ValueError(f"Reversal request {reversal_id} not found.")

        approval_event = ApprovalEvent(
            reversal_request_id=reversal.id,
            action=action.upper(),
            approved_by_user=approved_by_user,
            notes=notes,
            ip_address=ip_address,
            event_timestamp=datetime.now(timezone.utc)
        )
        reversal.approvals.append(approval_event)
        db.add(approval_event)

        if action.upper() == "APPROVE":
            reversal.status = "APPROVED"
            if reversal.finding:
                reversal.finding.status = "APPROVED"
        elif action.upper() == "REJECT":
            reversal.status = "REJECTED"
            if reversal.finding:
                reversal.finding.status = "DISMISSED"

        await db.commit()
        logger.info(f"Recorded approval action '{action}' on reversal {reversal.reference_number} by {approved_by_user}.")

        reload_stmt = (
            select(ReversalRequest)
            .where(ReversalRequest.id == reversal.id)
            .options(
                selectinload(ReversalRequest.finding).selectinload(AuditFinding.transaction),
                selectinload(ReversalRequest.approvals),
                selectinload(ReversalRequest.mock_ack)
            )
        )
        reload_res = await db.execute(reload_stmt)
        return reload_res.scalar_one()

    async def submit_to_mock_bank(
        self,
        db: AsyncSession,
        reversal_id: str
    ) -> Dict[str, Any]:
        """Submit approved reversal to the mock bank portal."""
        stmt = (
            select(ReversalRequest)
            .where(ReversalRequest.id == reversal_id)
            .options(
                selectinload(ReversalRequest.account),
                selectinload(ReversalRequest.approvals),
                selectinload(ReversalRequest.finding),
                selectinload(ReversalRequest.mock_ack)
            )
        )
        result = await db.execute(stmt)
        reversal = result.scalar_one_or_none()
        if not reversal:
            raise ValueError(f"Reversal request {reversal_id} not found.")

        # Strict safety check: Retries cannot duplicate submissions!
        if reversal.mock_ack is not None or reversal.status in ("SUBMITTED_TO_MOCK_PORTAL", "ACKNOWLEDGED", "SETTLED"):
            raise ValueError(
                f"Cannot submit reversal {reversal.reference_number}: already submitted to mock bank portal "
                f"(status: '{reversal.status}'). Duplicate submissions are strictly prohibited."
            )

        # Strict requirement: Explicit human approval must precede submission!
        if reversal.status != "APPROVED":
            raise ValueError(
                f"Cannot submit reversal {reversal.reference_number}. "
                f"Current status is '{reversal.status}'. Explicit human approval is required prior to submission."
            )

        # Get latest approver name
        last_approval = reversal.approvals[-1] if reversal.approvals else None
        approved_by = last_approval.approved_by_user if last_approval else "Authorized Compliance Officer"

        # Submit safely to Isolated Mock Bank Portal
        ack_data = await mock_bank_client.submit_reversal_request(
            reversal_id=reversal.id,
            reference_number=reversal.reference_number,
            account_number=reversal.account.account_number if reversal.account else "UNKNOWN",
            fee_amount=reversal.requested_amount,
            rationale=reversal.rationale_letter,
            approved_by=approved_by
        )

        mock_ack = MockBankAck(
            reversal_request_id=reversal.id,
            mock_bank_ticket_id=ack_data["ticket_id"],
            status_received=ack_data["status"],
            portal_endpoint_called=mock_bank_client.api_endpoint,
            acknowledgement_payload=ack_data,
            received_at=datetime.now(timezone.utc)
        )
        db.add(mock_ack)

        reversal.status = "ACKNOWLEDGED"
        if reversal.finding:
            reversal.finding.status = "SUBMITTED"

        await db.commit()
        await db.refresh(reversal)
        return ack_data


reversal_service = ReversalService()
