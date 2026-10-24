"""Overdraft Fee Audit Rule."""
from collections import defaultdict
from typing import List, Any
from backend.app.rules.base_rule import BaseAuditRule, RuleEvaluationFinding


class OverdraftFeeRule(BaseAuditRule):
    """Audits overdraft and NSF fees against daily frequency caps, thresholds, and tariff pricing."""
    rule_id = "RULE_OVERDRAFT_FEE_LIMITS"
    name = "Overdraft and NSF Fee Compliance Auditor"
    category = "OVERDRAFT"
    description = "Enforces contractual limits on overdraft fees, including daily caps and de minimis transaction thresholds as defined in the account tariff schedule."

    def evaluate(
        self,
        statement: Any,
        account: Any,
        tier: Any,
        tariff_rules: List[Any],
        transactions: List[Any]
    ) -> List[RuleEvaluationFinding]:
        findings: List[RuleEvaluationFinding] = []

        max_daily_cap = tier.max_daily_overdraft_fees if tier else 3
        standard_od_fee = tier.overdraft_fee_amount if tier else 35.0
        de_minimis_threshold = (tier.overdraft_threshold_cents / 100.0) if (tier and tier.overdraft_threshold_cents) else 5.0

        matching_tariff = next((t for t in tariff_rules if t.fee_category == "OVERDRAFT"), None)
        if matching_tariff and matching_tariff.condition_logic:
            cond = matching_tariff.condition_logic
            max_daily_cap = cond.get("max_daily_overdraft_fees", max_daily_cap)
            standard_od_fee = cond.get("overdraft_fee_amount", standard_od_fee)
            de_minimis_threshold = cond.get("de_minimis_threshold", de_minimis_threshold)

        od_keywords = ["overdraft fee", "od fee", "nsf fee", "non-sufficient funds", "courtesy pay fee"]

        # Group transactions by date
        txs_by_date = defaultdict(list)
        for tx in transactions:
            txs_by_date[tx.transaction_date].append(tx)

        for tx_date, day_txs in txs_by_date.items():
            od_fees_this_day: List[Any] = []
            regular_debits_this_day: List[Any] = []

            for tx in day_txs:
                desc_lower = tx.description.lower()
                is_od = (tx.transaction_type == "FEE" and any(kw in desc_lower for kw in od_keywords)) or any(kw in desc_lower for kw in od_keywords)
                if is_od:
                    od_fees_this_day.append(tx)
                elif tx.transaction_type in ("DEBIT", "TRANSFER") and tx.amount > 0:
                    regular_debits_this_day.append(tx)

            # Check 1: Exceeded daily overdraft fee cap
            if len(od_fees_this_day) > max_daily_cap:
                for idx, excess_tx in enumerate(od_fees_this_day[max_daily_cap:], start=max_daily_cap + 1):
                    evidence = {
                        "rule_applied": "OVERDRAFT_DAILY_CAP_EXCEEDED",
                        "transaction_date": str(tx_date),
                        "fee_index_on_date": idx,
                        "max_daily_cap": max_daily_cap,
                        "actual_fees_charged_today": len(od_fees_this_day),
                        "overdraft_fee_charged": float(excess_tx.amount),
                        "expected_fee": 0.0,
                        "excess_amount": float(excess_tx.amount),
                        "transaction_ref": excess_tx.source_transaction_id,
                    }
                    findings.append(
                        RuleEvaluationFinding(
                            rule_category=self.category,
                            fee_amount=float(excess_tx.amount),
                            potential_refund_amount=float(excess_tx.amount),
                            severity="HIGH",
                            violation_title=f"Excessive Daily Overdraft Fee (#{idx} of day)",
                            violation_reason=(
                                f"Account was charged {len(od_fees_this_day)} overdraft fees on {tx_date}, "
                                f"exceeding the contractual tier limit of {max_daily_cap} fees per business day. "
                                f"Fee #{idx} of ${excess_tx.amount:.2f} is non-compliant and subject to full reversal."
                            ),
                            evidence_data=evidence,
                            transaction_id=str(excess_tx.id),
                            rule_id=str(matching_tariff.id) if matching_tariff else None,
                            source_evidence_snapshot=f"Fee #{idx} on {tx_date} exceeded daily limit of {max_daily_cap}"
                        )
                    )

            # Check 2: De minimis threshold violation
            # If an overdraft fee was assessed on an underlying transaction <= de_minimis_threshold ($5.00)
            for od_tx in od_fees_this_day[:max_daily_cap]:
                # If there are small transactions on the same day causing negative balance
                small_debit = next((d for d in regular_debits_this_day if d.amount <= de_minimis_threshold and d.amount > 0), None)
                if small_debit and od_tx.balance_after < 0 and abs(od_tx.balance_after) <= (de_minimis_threshold + od_tx.amount):
                    evidence = {
                        "rule_applied": "OVERDRAFT_DE_MINIMIS_THRESHOLD_VIOLATION",
                        "transaction_date": str(tx_date),
                        "de_minimis_threshold": de_minimis_threshold,
                        "triggering_transaction_amount": float(small_debit.amount),
                        "triggering_transaction_desc": small_debit.description,
                        "fee_charged": float(od_tx.amount),
                        "expected_fee": 0.0,
                        "transaction_ref": od_tx.source_transaction_id
                    }
                    findings.append(
                        RuleEvaluationFinding(
                            rule_category=self.category,
                            fee_amount=float(od_tx.amount),
                            potential_refund_amount=float(od_tx.amount),
                            severity="HIGH",
                            violation_title="Overdraft Fee on De Minimis Transaction",
                            violation_reason=(
                                f"An overdraft fee of ${od_tx.amount:.2f} was assessed on {tx_date} for a micro-transaction "
                                f"('{small_debit.description}' for ${small_debit.amount:.2f}) which is at or below the "
                                f"${de_minimis_threshold:.2f} tariff buffer threshold."
                            ),
                            evidence_data=evidence,
                            transaction_id=str(od_tx.id),
                            rule_id=str(matching_tariff.id) if matching_tariff else None,
                            source_evidence_snapshot=f"Tx amount ${small_debit.amount:.2f} <= threshold ${de_minimis_threshold:.2f}"
                        )
                    )

        return findings
