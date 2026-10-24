"""Paper Statement Fee Audit Rule."""
from typing import List, Any
from backend.app.rules.base_rule import BaseAuditRule, RuleEvaluationFinding


class PaperStatementFeeRule(BaseAuditRule):
    """Audits paper statement charges against electronic statement enrollment status."""
    rule_id = "RULE_PAPER_STATEMENT_FEE"
    name = "Paper Statement Fee Enrollment Auditor"
    category = "PAPER_STATEMENT"
    description = "Checks whether paper statement fees were levied against accounts actively enrolled in paperless / electronic delivery."

    def evaluate(
        self,
        statement: Any,
        account: Any,
        tier: Any,
        tariff_rules: List[Any],
        transactions: List[Any]
    ) -> List[RuleEvaluationFinding]:
        findings: List[RuleEvaluationFinding] = []

        is_electronic = bool(getattr(account, "electronic_statements_enrolled", False))
        matching_tariff = next((t for t in tariff_rules if t.fee_category == "PAPER_STATEMENT"), None)

        paper_keywords = ["paper statement fee", "paper delivery fee", "printed statement charge", "paper fee"]

        for tx in transactions:
            desc_lower = tx.description.lower()
            if any(kw in desc_lower for kw in paper_keywords):
                if is_electronic:
                    evidence = {
                        "rule_applied": self.rule_id,
                        "account_electronic_enrolled": True,
                        "fee_charged": float(tx.amount),
                        "expected_fee": 0.0,
                        "transaction_ref": tx.source_transaction_id,
                        "transaction_date": str(tx.transaction_date)
                    }
                    findings.append(
                        RuleEvaluationFinding(
                            rule_category=self.category,
                            fee_amount=float(tx.amount),
                            potential_refund_amount=float(tx.amount),
                            severity="MEDIUM",
                            violation_title="Paper Statement Fee on Paperless Enrolled Account",
                            violation_reason=(
                                f"Account {account.account_number} is actively enrolled in paperless e-statements. "
                                f"A paper delivery fee of ${tx.amount:.2f} was billed on {tx.transaction_date} in violation "
                                f"of the enrollment agreement."
                            ),
                            evidence_data=evidence,
                            transaction_id=str(tx.id),
                            rule_id=str(matching_tariff.id) if matching_tariff else None,
                            source_evidence_snapshot="Account electronic_statements_enrolled = True"
                        )
                    )

        return findings
