"""Initial schema migration.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-03-01 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. account_tiers
    op.create_table(
        'account_tiers',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False, unique=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('monthly_maintenance_fee', sa.Float(), nullable=False, server_default='12.0'),
        sa.Column('min_balance_waiver', sa.Float(), nullable=False, server_default='1500.0'),
        sa.Column('min_direct_deposit_waiver', sa.Float(), nullable=False, server_default='500.0'),
        sa.Column('overdraft_fee_amount', sa.Float(), nullable=False, server_default='35.0'),
        sa.Column('max_daily_overdraft_fees', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('overdraft_threshold_cents', sa.Integer(), nullable=False, server_default='500'),
        sa.Column('wire_incoming_domestic_fee', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('wire_outgoing_domestic_fee', sa.Float(), nullable=False, server_default='25.0'),
        sa.Column('wire_outgoing_international_fee', sa.Float(), nullable=False, server_default='45.0'),
        sa.Column('paper_statement_fee', sa.Float(), nullable=False, server_default='3.0'),
        sa.Column('foreign_transaction_fee_rate', sa.Float(), nullable=False, server_default='0.03'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 2. accounts
    op.create_table(
        'accounts',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('account_number', sa.String(length=50), nullable=False, unique=True),
        sa.Column('holder_name', sa.String(length=150), nullable=False),
        sa.Column('bank_name', sa.String(length=100), nullable=False),
        sa.Column('routing_number', sa.String(length=20), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('current_balance', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('tier_id', sa.String(length=36), sa.ForeignKey('account_tiers.id'), nullable=False),
        sa.Column('electronic_statements_enrolled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('source_id', sa.String(length=100), nullable=False),
        sa.Column('source_url', sa.String(length=255), nullable=True),
        sa.Column('retrieval_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 3. tariff_rules
    op.create_table(
        'tariff_rules',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('tier_id', sa.String(length=36), sa.ForeignKey('account_tiers.id'), nullable=False),
        sa.Column('fee_category', sa.String(length=50), nullable=False),
        sa.Column('fee_name', sa.String(length=100), nullable=False),
        sa.Column('standard_amount', sa.Float(), nullable=False),
        sa.Column('condition_logic', sa.JSON(), nullable=False),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_to', sa.Date(), nullable=True),
        sa.Column('source_document_ref', sa.String(length=200), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 4. statements
    op.create_table(
        'statements',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('account_id', sa.String(length=36), sa.ForeignKey('accounts.id'), nullable=False),
        sa.Column('statement_period_start', sa.Date(), nullable=False),
        sa.Column('statement_period_end', sa.Date(), nullable=False),
        sa.Column('opening_balance', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('closing_balance', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('average_daily_balance', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_qualifying_direct_deposits', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_subsequent_statement', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('verified_against_statement_id', sa.String(length=36), nullable=True),
        sa.Column('source_id', sa.String(length=100), nullable=False),
        sa.Column('source_filename', sa.String(length=150), nullable=False),
        sa.Column('raw_statement_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 5. transactions
    op.create_table(
        'transactions',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('statement_id', sa.String(length=36), sa.ForeignKey('statements.id'), nullable=False),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('posting_date', sa.Date(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('transaction_type', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('balance_after', sa.Float(), nullable=False),
        sa.Column('raw_category', sa.String(length=50), nullable=False),
        sa.Column('source_transaction_id', sa.String(length=100), nullable=False),
    )

    # 6. audit_findings
    op.create_table(
        'audit_findings',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('statement_id', sa.String(length=36), sa.ForeignKey('statements.id'), nullable=False),
        sa.Column('transaction_id', sa.String(length=36), sa.ForeignKey('transactions.id'), nullable=True),
        sa.Column('rule_id', sa.String(length=36), sa.ForeignKey('tariff_rules.id'), nullable=True),
        sa.Column('rule_category', sa.String(length=50), nullable=False),
        sa.Column('fee_amount', sa.Float(), nullable=False),
        sa.Column('potential_refund_amount', sa.Float(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='HIGH'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='FLAGGED'),
        sa.Column('violation_title', sa.String(length=200), nullable=False),
        sa.Column('violation_reason', sa.String(length=1000), nullable=False),
        sa.Column('evidence_data', sa.JSON(), nullable=False),
        sa.Column('source_evidence_snapshot', sa.String(length=500), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 7. reversal_requests
    op.create_table(
        'reversal_requests',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('finding_id', sa.String(length=36), sa.ForeignKey('audit_findings.id'), nullable=False, unique=True),
        sa.Column('account_id', sa.String(length=36), sa.ForeignKey('accounts.id'), nullable=False),
        sa.Column('reference_number', sa.String(length=50), nullable=False, unique=True),
        sa.Column('requested_amount', sa.Float(), nullable=False),
        sa.Column('rationale_letter', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False, server_default='DRAFTED'),
        sa.Column('prepared_by', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 8. approval_events
    op.create_table(
        'approval_events',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('reversal_request_id', sa.String(length=36), sa.ForeignKey('reversal_requests.id'), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('approved_by_user', sa.String(length=100), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('event_timestamp', sa.DateTime(timezone=True), nullable=False),
    )

    # 9. mock_bank_acks
    op.create_table(
        'mock_bank_acks',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('reversal_request_id', sa.String(length=36), sa.ForeignKey('reversal_requests.id'), nullable=False, unique=True),
        sa.Column('mock_bank_ticket_id', sa.String(length=64), nullable=False),
        sa.Column('status_received', sa.String(length=50), nullable=False),
        sa.Column('portal_endpoint_called', sa.String(length=200), nullable=False),
        sa.Column('acknowledgement_payload', sa.JSON(), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 10. verification_results
    op.create_table(
        'verification_results',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('reversal_request_id', sa.String(length=36), sa.ForeignKey('reversal_requests.id'), nullable=False),
        sa.Column('subsequent_statement_id', sa.String(length=36), sa.ForeignKey('statements.id'), nullable=False),
        sa.Column('refund_transaction_id', sa.String(length=36), sa.ForeignKey('transactions.id'), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('verified_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('expected_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('discrepancy_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('verification_status', sa.String(length=40), nullable=False, server_default='PENDING_STATEMENT'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 11. test_runs
    op.create_table(
        'test_runs',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('test_suite_name', sa.String(length=100), nullable=False),
        sa.Column('run_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('findings_detected_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_fee_amount_audited', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('potential_recovery_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('execution_duration_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('test_runs')
    op.drop_table('verification_results')
    op.drop_table('mock_bank_acks')
    op.drop_table('approval_events')
    op.drop_table('reversal_requests')
    op.drop_table('audit_findings')
    op.drop_table('transactions')
    op.drop_table('statements')
    op.drop_table('tariff_rules')
    op.drop_table('accounts')
    op.drop_table('account_tiers')
