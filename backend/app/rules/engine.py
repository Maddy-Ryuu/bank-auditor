"""Audit Rules Engine orchestrator."""
from typing import List, Any
from backend.app.rules.base_rule import BaseAuditRule, RuleEvaluationFinding
from backend.app.rules.monthly_maintenance import MonthlyMaintenanceFeeRule
from backend.app.rules.overdraft_fee import OverdraftFeeRule
from backend.app.rules.paper_statement_fee import PaperStatementFeeRule
from backend.app.rules.wire_transfer_fee import WireTransferFeeRule
from backend.app.rules.foreign_transaction import ForeignTransactionFeeRule
from backend.app.logging_config import logger


class AuditRulesEngine:
    """Orchestrates execution of all active fee audit rules."""

    def __init__(self):
        self.rules: List[BaseAuditRule] = [
            MonthlyMaintenanceFeeRule(),
            OverdraftFeeRule(),
            PaperStatementFeeRule(),
            WireTransferFeeRule(),
            ForeignTransactionFeeRule(),
        ]

    def register_rule(self, rule: BaseAuditRule) -> None:
        """Register a new custom audit rule."""
        self.rules.append(rule)
        logger.info(f"Registered custom audit rule: {rule.name} ({rule.rule_id})")

    def run_audit(
        self,
        statement: Any,
        account: Any,
        tier: Any,
        tariff_rules: List[Any],
        transactions: List[Any]
    ) -> List[RuleEvaluationFinding]:
        """Execute all active rules against the provided statement data."""
        all_findings: List[RuleEvaluationFinding] = []

        logger.info(
            f"Running audit engine on statement {getattr(statement, 'id', 'unknown')} "
            f"for account {getattr(account, 'account_number', 'unknown')} "
            f"with {len(transactions)} transactions across {len(self.rules)} rules."
        )

        for rule in self.rules:
            try:
                findings = rule.evaluate(statement, account, tier, tariff_rules, transactions)
                if findings:
                    logger.warning(
                        f"Rule '{rule.name}' flagged {len(findings)} potential fee violations "
                        f"(total amount: ${sum(f.potential_refund_amount for f in findings):.2f})."
                    )
                all_findings.extend(findings)
            except Exception as exc:
                logger.error(f"Error evaluating rule '{rule.name}': {exc}", exc_info=True)

        return all_findings


audit_engine = AuditRulesEngine()
