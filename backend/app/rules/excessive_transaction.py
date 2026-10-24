"""Excessive Transaction Fee Audit Rule."""
from typing import List, Any
from backend.app.rules.base_rule import BaseAuditRule, RuleEvaluationFinding


class ExcessiveTransactionFeeRule(BaseAuditRule):
    """Audits excessive withdrawal/activity fees on savings or checking accounts."""
    rule_id = "RULE_EXCESSIVE_TRANSACTION_FEE"
    name = "Excessive Withdrawal Fee Auditor"
    category = "EXCESSIVE_TRANSACTION"
    description = "Audits excessive withdrawal fees against statutory Regulation D thresholds and monthly cycle counts."

    def evaluate(
        self,
        statement: Any,
        account: Any,
        tier: Any,
        tariff_rules: List[Any],
        transactions: List[Any]
    ) -> List[RuleEvaluationFinding]:
        findings: List[RuleEvaluationFinding] = []

        allowed_withdrawals = 6
        fee_per_excess = 15.0

        matching_tariff = next((t for t in tariff_rules if t.fee_category == "EXCESSIVE_TRANSACTION"), None)
        if matching_tariff and matching_tariff.condition_logic:
            allowed_withdrawals = matching_tariff.condition_logic.get("allowed_monthly_count", allowed_withdrawals)
            fee_per_excess = matching_tariff.condition_logic.get("fee_per_excess", fee_per_excess)

        excess_keywords = ["excessive withdrawal fee", "excessive transaction fee", "activity limit fee"]

        # Count actual debit transactions that qualify
        qualifying_withdrawals = [
            tx for tx in transactions
            if tx.transaction_type in ("DEBIT", "TRANSFER") and tx.amount > 0 and not any(k in tx.description.lower() for k in excess_keywords)
        ]

        excess_fee_txs = [
            tx for tx in transactions
            if any(k in tx.description.lower() for k in excess_keywords)
        ]

        if excess_fee_txs and len(qualifying_withdrawals) <= allowed_withdrawals:
            for fee_tx in excess_fee_txs:
                evidence = {
                    "rule_applied": self.rule_id,
                    "actual_withdrawals_in_cycle": len(qualifying_withdrawals),
                    "allowed_withdrawals_limit": allowed_withdrawals,
                    "fee_charged": float(fee_tx.amount),
                    "expected_fee": 0.0,
                    "transaction_ref": fee_tx.source_transaction_id,
                    "transaction_date": str(fee_tx.transaction_date)
                }
                findings.append(
                    RuleEvaluationFinding(
                        rule_category=self.category,
                        fee_amount=float(fee_tx.amount),
                        potential_refund_amount=float(fee_tx.amount),
                        severity="HIGH",
                        violation_title="Unjustified Excessive Withdrawal Fee",
                        violation_reason=(
                            f"Account incurred only {len(qualifying_withdrawals)} debit transactions during the cycle, "
                            f"which is within the allowed limit of {allowed_withdrawals}. The ${fee_tx.amount:.2f} excessive "
                            f"activity fee was improperly charged."
                        ),
                        evidence_data=evidence,
                        transaction_id=str(fee_tx.id),
                        rule_id=str(matching_tariff.id) if matching_tariff else None,
                        source_evidence_snapshot=f"Withdrawals={len(qualifying_withdrawals)} <= Allowed={allowed_withdrawals}"
                    )
                )

        return findings
