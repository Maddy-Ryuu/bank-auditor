"""Wire Transfer Fee Audit Rule."""
from typing import List, Any
from backend.app.rules.base_rule import BaseAuditRule, RuleEvaluationFinding


class WireTransferFeeRule(BaseAuditRule):
    """Audits wire transfer fees against published tier allowances and tariffs."""
    rule_id = "RULE_WIRE_TRANSFER_FEE"
    name = "Wire Transfer Fee Schedule Auditor"
    category = "WIRE_TRANSFER"
    description = "Detects erroneous domestic and international incoming/outgoing wire transfer charges."

    def evaluate(
        self,
        statement: Any,
        account: Any,
        tier: Any,
        tariff_rules: List[Any],
        transactions: List[Any]
    ) -> List[RuleEvaluationFinding]:
        findings: List[RuleEvaluationFinding] = []

        expected_incoming_domestic = tier.wire_incoming_domestic_fee if tier else 0.0
        expected_outgoing_domestic = tier.wire_outgoing_domestic_fee if tier else 25.0

        matching_tariff = next((t for t in tariff_rules if t.fee_category == "WIRE_TRANSFER"), None)
        if matching_tariff and matching_tariff.condition_logic:
            cond = matching_tariff.condition_logic
            expected_incoming_domestic = cond.get("wire_incoming_domestic_fee", expected_incoming_domestic)
            expected_outgoing_domestic = cond.get("wire_outgoing_domestic_fee", expected_outgoing_domestic)

        incoming_wire_keywords = ["incoming wire fee", "wire transfer in fee", "wire credit fee"]
        outgoing_wire_keywords = ["outgoing domestic wire fee", "domestic wire transfer fee", "wire out fee"]

        for tx in transactions:
            desc_lower = tx.description.lower()

            # Incoming wire fee audit
            if any(kw in desc_lower for kw in incoming_wire_keywords):
                if expected_incoming_domestic == 0.0 and tx.amount > 0:
                    evidence = {
                        "rule_applied": "FREE_INCOMING_WIRE_BENEFIT_VIOLATION",
                        "tier_name": tier.name if tier else "Standard",
                        "allowed_fee": 0.0,
                        "charged_fee": float(tx.amount),
                        "overcharge": float(tx.amount),
                        "transaction_ref": tx.source_transaction_id,
                        "transaction_date": str(tx.transaction_date)
                    }
                    findings.append(
                        RuleEvaluationFinding(
                            rule_category=self.category,
                            fee_amount=float(tx.amount),
                            potential_refund_amount=float(tx.amount),
                            severity="HIGH",
                            violation_title="Billed for Complimentary Incoming Wire Transfer",
                            violation_reason=(
                                f"Account tier '{tier.name if tier else 'Premier'}' includes complimentary incoming domestic wires. "
                                f"Fee of ${tx.amount:.2f} was incorrectly levied."
                            ),
                            evidence_data=evidence,
                            transaction_id=str(tx.id),
                            rule_id=str(matching_tariff.id) if matching_tariff else None,
                            source_evidence_snapshot=f"Tier {tier.name if tier else ''} wire_incoming_domestic_fee = $0.00"
                        )
                    )

            # Outgoing wire overcharge audit
            elif any(kw in desc_lower for kw in outgoing_wire_keywords):
                if tx.amount > expected_outgoing_domestic:
                    excess = float(tx.amount - expected_outgoing_domestic)
                    evidence = {
                        "rule_applied": "OUTGOING_WIRE_OVERCHARGE",
                        "published_tariff": float(expected_outgoing_domestic),
                        "fee_charged": float(tx.amount),
                        "excess_billed": excess,
                        "transaction_ref": tx.source_transaction_id,
                        "transaction_date": str(tx.transaction_date)
                    }
                    findings.append(
                        RuleEvaluationFinding(
                            rule_category=self.category,
                            fee_amount=float(tx.amount),
                            potential_refund_amount=excess,
                            severity="MEDIUM",
                            violation_title="Outgoing Wire Fee Exceeds Published Tariff",
                            violation_reason=(
                                f"Standard tariff for outgoing domestic wire is ${expected_outgoing_domestic:.2f}, "
                                f"but ${tx.amount:.2f} was deducted (${excess:.2f} overcharge)."
                            ),
                            evidence_data=evidence,
                            transaction_id=str(tx.id),
                            rule_id=str(matching_tariff.id) if matching_tariff else None,
                            source_evidence_snapshot=f"Tariff=${expected_outgoing_domestic:.2f} vs Charged=${tx.amount:.2f}"
                        )
                    )

        return findings
