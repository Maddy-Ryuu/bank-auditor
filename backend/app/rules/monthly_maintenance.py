"""Monthly Maintenance Fee Audit Rule."""
from typing import List, Any
from backend.app.rules.base_rule import BaseAuditRule, RuleEvaluationFinding


class MonthlyMaintenanceFeeRule(BaseAuditRule):
    """Audits monthly account maintenance fees against published waiver criteria."""
    rule_id = "RULE_MONTHLY_MAINTENANCE_FEE"
    name = "Monthly Maintenance Fee Waiver Auditor"
    category = "MONTHLY_MAINTENANCE"
    description = "Verifies if monthly maintenance fee was erroneously assessed when balance or direct deposit waiver criteria were satisfied."

    def evaluate(
        self,
        statement: Any,
        account: Any,
        tier: Any,
        tariff_rules: List[Any],
        transactions: List[Any]
    ) -> List[RuleEvaluationFinding]:
        findings: List[RuleEvaluationFinding] = []

        # Find matching tariff rule if present
        matching_tariff = next(
            (t for t in tariff_rules if t.fee_category == "MONTHLY_MAINTENANCE"),
            None
        )
        min_balance_threshold = tier.min_balance_waiver if tier else 1500.0
        min_deposit_threshold = tier.min_direct_deposit_waiver if tier else 500.0

        if matching_tariff and matching_tariff.condition_logic:
            cond = matching_tariff.condition_logic
            min_balance_threshold = cond.get("min_balance_waiver", min_balance_threshold)
            min_deposit_threshold = cond.get("min_direct_deposit_waiver", min_deposit_threshold)

        # Look for monthly maintenance fee transactions
        fee_keywords = [
            "monthly service fee",
            "monthly maintenance",
            "service charge - checking",
            "monthly account fee",
            "maintenance charge"
        ]

        for tx in transactions:
            desc_lower = tx.description.lower()
            if tx.transaction_type == "FEE" or any(kw in desc_lower for kw in fee_keywords):
                if any(kw in desc_lower for kw in fee_keywords):
                    # Check waiver conditions
                    avg_balance = float(statement.average_daily_balance or 0.0)
                    direct_deposits = float(statement.total_qualifying_direct_deposits or 0.0)

                    balance_waived = avg_balance >= min_balance_threshold
                    deposit_waived = (min_deposit_threshold > 0) and (direct_deposits >= min_deposit_threshold)

                    if balance_waived or deposit_waived:
                        waiver_reason = []
                        if balance_waived:
                            waiver_reason.append(
                                f"Average daily balance was ${avg_balance:,.2f}, exceeding the ${min_balance_threshold:,.2f} waiver requirement."
                            )
                        if deposit_waived:
                            waiver_reason.append(
                                f"Qualifying direct deposits totaled ${direct_deposits:,.2f}, satisfying the ${min_deposit_threshold:,.2f} threshold."
                            )

                        violation_reason = (
                            f"Account satisfied tariff waiver criteria: {' '.join(waiver_reason)} "
                            f"The fee of ${tx.amount:.2f} was incorrectly levied."
                        )

                        evidence = {
                            "rule_applied": self.rule_id,
                            "tier_name": tier.name if tier else "Standard",
                            "fee_charged": float(tx.amount),
                            "expected_fee": 0.0,
                            "discrepancy": float(tx.amount),
                            "average_daily_balance": avg_balance,
                            "min_balance_waiver_threshold": min_balance_threshold,
                            "total_qualifying_direct_deposits": direct_deposits,
                            "min_direct_deposit_waiver_threshold": min_deposit_threshold,
                            "balance_waiver_qualified": balance_waived,
                            "deposit_waiver_qualified": deposit_waived,
                            "transaction_date": str(tx.transaction_date),
                            "transaction_ref": tx.source_transaction_id
                        }

                        findings.append(
                            RuleEvaluationFinding(
                                rule_category=self.category,
                                fee_amount=float(tx.amount),
                                potential_refund_amount=float(tx.amount),
                                severity="HIGH",
                                violation_title="Incorrect Monthly Maintenance Fee Assessment",
                                violation_reason=violation_reason,
                                evidence_data=evidence,
                                transaction_id=str(tx.id),
                                rule_id=str(matching_tariff.id) if matching_tariff else None,
                                source_evidence_snapshot=f"Statement ADB=${avg_balance:.2f} vs Waiver=${min_balance_threshold:.2f}"
                            )
                        )

        return findings
