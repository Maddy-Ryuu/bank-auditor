"""Verification service reconciling mock bank refunds on subsequent statements."""
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.app.models.reversal import ReversalRequest, MockBankAck
from backend.app.models.statement import Statement, Transaction
from backend.app.models.verification import VerificationResult
from backend.app.logging_config import logger


class VerificationService:
    """Verifies that approved fee reversals actually appeared as credits on subsequent statements."""

    async def verify_reversal(
        self,
        db: AsyncSession,
        reversal_id: str,
        subsequent_statement_id: Optional[str] = None
    ) -> VerificationResult:
        """Verify reversal against a subsequent statement."""
        stmt = (
            select(ReversalRequest)
            .where(ReversalRequest.id == reversal_id)
            .options(
                selectinload(ReversalRequest.account),
                selectinload(ReversalRequest.mock_ack),
                selectinload(ReversalRequest.finding)
            )
        )
        result = await db.execute(stmt)
        reversal = result.scalar_one_or_none()
        if not reversal:
            raise ValueError(f"Reversal request {reversal_id} not found.")

        # If subsequent_statement_id is not passed, find the subsequent statement for this account
        if not subsequent_statement_id:
            sub_stmt = (
                select(Statement)
                .where(
                    Statement.account_id == reversal.account_id,
                    Statement.is_subsequent_statement.is_(True)
                )
                .order_by(Statement.statement_period_start.desc())
            )
            sub_res = await db.execute(sub_stmt)
            subsequent = sub_res.scalars().first()
        else:
            sub_stmt = select(Statement).where(Statement.id == subsequent_statement_id)
            sub_res = await db.execute(sub_stmt)
            subsequent = sub_res.scalar_one_or_none()

        if not subsequent:
            raise ValueError(f"No subsequent statement found for account {reversal.account_id}.")

        # Load subsequent statement transactions
        tx_stmt = select(Transaction).where(Transaction.statement_id == subsequent.id)
        tx_res = await db.execute(tx_stmt)
        transactions = list(tx_res.scalars().all())

        expected_amount = reversal.requested_amount
        ticket_id = reversal.mock_ack.mock_bank_ticket_id if reversal.mock_ack else None
        ref_num = reversal.reference_number

        # Keywords strictly identifying bank fee reversal adjustments
        FEE_REVERSAL_KEYWORDS = [
            "FEE REFUND",
            "FEE REVERSAL",
            "COURTESY REFUND",
            "COURTESY CREDIT",
            "FEE ADJUSTMENT",
            "FEE ADJ",
            "DISPUTE CREDIT",
            "BANK CHARGE REVERSAL",
            "OVERDRAFT REVERSAL",
            "MAINTENANCE FEE REVERSAL",
            "WIRE FEE REVERSAL",
        ]

        # Keywords identifying explicitly unrelated commercial/payroll transactions
        UNRELATED_KEYWORDS = [
            "PAYROLL",
            "SALARY",
            "WAGES",
            "DIRECT DEPOSIT",
            "CHECK DEPOSIT",
            "MOBILE DEPOSIT",
            "ATM DEPOSIT",
            "CASH DEPOSIT",
            "TRANSFER FROM",
            "ZELLE",
            "VENMO",
            "MERCHANT REFUND",
            "PURCHASE RETURN",
            "STORE RETURN",
            "AMAZON",
            "TARGET",
            "WALMART",
            "WHOLE FOODS",
            "TAX REFUND",
            "INVESTMENT",
            "DIVIDEND",
        ]

        matched_tx: Optional[Transaction] = None
        ambiguous_candidates: List[Transaction] = []

        for tx in transactions:
            if tx.amount <= 0:
                continue

            desc_upper = tx.description.upper()
            is_credit_type = tx.transaction_type in ("REFUND", "CREDIT")

            # Check if explicitly unrelated
            is_unrelated = any(kw in desc_upper for kw in UNRELATED_KEYWORDS)
            if is_unrelated:
                # Strictly skip unrelated commercial or payroll credits
                continue

            # Provenance match: ticket ID or dispute reference number in transaction
            has_ticket_match = ticket_id and (ticket_id.upper() in desc_upper)
            has_ref_match = ref_num and (ref_num.upper() in desc_upper)
            has_fee_keyword = any(kw in desc_upper for kw in FEE_REVERSAL_KEYWORDS)

            amount_matches = abs(tx.amount - expected_amount) < 0.01

            if has_ticket_match or has_ref_match or has_fee_keyword:
                if amount_matches:
                    matched_tx = tx
                    break  # Definite exact match with verifiable fee reversal provenance
                elif tx.amount < expected_amount and (has_ticket_match or has_ref_match or has_fee_keyword):
                    # Potential partial refund candidate
                    matched_tx = tx

            elif amount_matches and is_credit_type:
                # Credit matches the exact dollar amount but lacks verifiable bank fee reversal provenance!
                # Per safety policy: ambiguous credits must remain unresolved.
                ambiguous_candidates.append(tx)

        if matched_tx and abs(matched_tx.amount - expected_amount) < 0.01:
            status = "MATCHED_EXACT"
            verified_amount = matched_tx.amount
            discrepancy = 0.0
            notes = (
                f"Successfully reconciled exact fee refund of ${verified_amount:.2f} on subsequent statement "
                f"(Tx Ref: {matched_tx.source_transaction_id}, Description: '{matched_tx.description}')."
            )
            is_verified = True
            reversal.status = "SETTLED"
            if reversal.finding:
                reversal.finding.status = "REVERSED"

        elif matched_tx and matched_tx.amount > 0 and matched_tx.amount < expected_amount:
            status = "PARTIAL_REFUND"
            verified_amount = matched_tx.amount
            discrepancy = expected_amount - verified_amount
            notes = (
                f"Partial refund detected: ${verified_amount:.2f} credited vs ${expected_amount:.2f} expected "
                f"(Shortfall: ${discrepancy:.2f}). Dispute remains pending full resolution."
            )
            is_verified = False
            # Reversal status remains ACKNOWLEDGED (not settled)

        elif ambiguous_candidates:
            # Ambiguous credit found without fee reversal provenance
            candidate = ambiguous_candidates[0]
            status = "AMBIGUOUS_UNRESOLVED"
            verified_amount = 0.0
            discrepancy = expected_amount
            notes = (
                f"Candidate credit of ${candidate.amount:.2f} found ('{candidate.description}') but lacks "
                f"verifiable fee reversal provenance or dispute reference. Remained unresolved per safety policy."
            )
            is_verified = False
            # Reversal status remains ACKNOWLEDGED (not credited)

        else:
            status = "NOT_FOUND_IN_SUBSEQUENT"
            verified_amount = 0.0
            discrepancy = expected_amount
            notes = (
                f"No matching fee refund credit of ${expected_amount:.2f} was detected in subsequent statement "
                f"cycle ({subsequent.statement_period_start} to {subsequent.statement_period_end}). Reversal remains pending."
            )
            is_verified = False
            # Reversal status remains ACKNOWLEDGED (never credited)

        verification_record = VerificationResult(
            reversal_request_id=reversal.id,
            subsequent_statement_id=subsequent.id,
            refund_transaction_id=matched_tx.id if matched_tx else None,
            is_verified=is_verified,
            verified_amount=verified_amount,
            expected_amount=expected_amount,
            discrepancy_amount=discrepancy,
            verification_status=status,
            notes=notes,
            verified_at=datetime.now(timezone.utc)
        )
        db.add(verification_record)

        await db.commit()
        await db.refresh(verification_record)
        logger.info(
            f"Verification complete for reversal {reversal.reference_number}: "
            f"Status={status}, Verified=${verified_amount:.2f}"
        )
        return verification_record


verification_service = VerificationService()
