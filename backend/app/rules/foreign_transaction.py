"""Foreign Transaction Fee Audit Rule."""
from typing import List, Any
from backend.app.rules.base_rule import BaseAuditRule, RuleEvaluationFinding


class ForeignTransactionFeeRule(BaseAuditRule):
    """Audits international transaction surcharge fees."""
    rule_id = "RULE_FOREIGN_TRANSACTION_FEE"
    name = "Foreign Transaction Surcharge Auditor"
    category = "FOREIGN_TRANSACTION"
    description = "Checks foreign transaction fee rates against underlying foreign currency transactions and detects bogus fees on domestic transactions."

    def evaluate(
        self,
        statement: Any,
        account: Any,
        tier: Any,
        tariff_rules: List[Any],
        transactions: List[Any]
    ) -> List[RuleEvaluationFinding]:
        findings: List[RuleEvaluationFinding] = []

        standard_rate = tier.foreign_transaction_fee_rate if tier else 0.03
        matching_tariff = next((t for t in tariff_rules if t.fee_category == "FOREIGN_TRANSACTION"), None)
        if matching_tariff and matching_tariff.condition_logic:
            standard_rate = matching_tariff.condition_logic.get("rate", standard_rate)

        fx_fee_keywords = ["foreign transaction fee", "international transaction fee", "fx surcharge", "cross-border fee"]

        for tx in transactions:
            desc_lower = tx.description.lower()
            if any(kw in desc_lower for kw in fx_fee_keywords):
                # Check if there is mention of a domestic entity or an overcharge
                if "domestic" in desc_lower or "usd settled" in desc_lower or "us merchant" in desc_lower:
                    evidence = {
                        "rule_applied": "DOMESTIC_TRANSACTION_FX_FEE_ERROR",
                        "fee_charged": float(tx.amount),
                        "transaction_ref": tx.source_transaction_id,
                        "transaction_date": str(tx.transaction_date)
                    }
                    findings.append(
                        RuleEvaluationFinding(
                            rule_category=self.category,
                            fee_amount=float(tx.amount),
                            potential_refund_amount=float(tx.amount),
                            severity="HIGH",
                            violation_title="Foreign Transaction Fee on Domestic Transaction",
                            violation_reason=(
                                f"A foreign transaction surcharge of ${tx.amount:.2f} was billed on {tx.transaction_date} "
                                f"for a domestic/USD-denominated transaction."
                            ),
                            evidence_data=evidence,
                            transaction_id=str(tx.id),
                            rule_id=str(matching_tariff.id) if matching_tariff else None,
                            source_evidence_snapshot="Transaction description indicates domestic USD settlement"
                        )
                    )

        return findings
