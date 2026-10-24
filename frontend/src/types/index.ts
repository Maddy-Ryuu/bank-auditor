export interface AccountTier {
  id: string;
  name: string;
  code: string;
  description?: string;
  monthly_maintenance_fee: number;
  min_balance_waiver: number;
  min_direct_deposit_waiver: number;
  overdraft_fee_amount: number;
  max_daily_overdraft_fees: number;
  overdraft_threshold_cents: number;
  wire_incoming_domestic_fee: number;
  wire_outgoing_domestic_fee: number;
  wire_outgoing_international_fee: number;
  paper_statement_fee: number;
  foreign_transaction_fee_rate: number;
}

export interface Account {
  id: string;
  account_number: string;
  holder_name: string;
  bank_name: string;
  routing_number: string;
  currency: string;
  current_balance: number;
  tier_id: string;
  tier?: AccountTier;
  electronic_statements_enrolled: boolean;
  source_id: string;
  source_url?: string;
  retrieval_timestamp: string;
}

export interface Transaction {
  id: string;
  statement_id: string;
  transaction_date: string;
  posting_date: string;
  description: string;
  transaction_type: string;
  amount: number;
  balance_after: number;
  raw_category: string;
  source_transaction_id: string;
}

export interface Statement {
  id: string;
  account_id: string;
  statement_period_start: string;
  statement_period_end: string;
  opening_balance: number;
  closing_balance: number;
  average_daily_balance: number;
  total_qualifying_direct_deposits: number;
  is_subsequent_statement: boolean;
  verified_against_statement_id?: string;
  source_id: string;
  source_filename: string;
  raw_statement_hash: string;
  transactions?: Transaction[];
}

export interface AuditFinding {
  id: string;
  statement_id: string;
  transaction_id?: string;
  rule_id?: string;
  rule_category: string;
  fee_amount: number;
  potential_refund_amount: number;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'FLAGGED' | 'REVERSAL_REQUESTED' | 'APPROVED' | 'SUBMITTED' | 'REVERSED' | 'DISMISSED';
  violation_title: string;
  violation_reason: string;
  evidence_data: Record<string, any>;
  source_evidence_snapshot?: string;
  detected_at: string;
  transaction?: Transaction;
}

export interface ApprovalEvent {
  id: string;
  reversal_request_id: string;
  action: 'APPROVE' | 'REJECT' | 'REQUEST_REVISION';
  approved_by_user: string;
  notes?: string;
  ip_address?: string;
  event_timestamp: string;
}

export interface MockBankAck {
  id: string;
  reversal_request_id: string;
  mock_bank_ticket_id: string;
  status_received: string;
  portal_endpoint_called: string;
  acknowledgement_payload: Record<string, any>;
  received_at: string;
}

export interface ReversalRequest {
  id: string;
  finding_id: string;
  account_id: string;
  reference_number: string;
  requested_amount: number;
  rationale_letter: string;
  status: 'DRAFTED' | 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'SUBMITTED_TO_MOCK_PORTAL' | 'ACKNOWLEDGED' | 'SETTLED';
  prepared_by: string;
  created_at: string;
  updated_at: string;
  finding?: AuditFinding;
  approvals: ApprovalEvent[];
  mock_ack?: MockBankAck;
}

export interface VerificationResult {
  id: string;
  reversal_request_id: string;
  subsequent_statement_id: string;
  refund_transaction_id?: string;
  is_verified: boolean;
  verified_amount: number;
  expected_amount: number;
  discrepancy_amount: number;
  verification_status: 'MATCHED_EXACT' | 'PARTIAL_REFUND' | 'NOT_FOUND_IN_SUBSEQUENT' | 'PENDING_STATEMENT';
  notes?: string;
  verified_at: string;
}

export interface TariffRule {
  id: string;
  tier_id: string;
  fee_category: string;
  fee_name: string;
  standard_amount: number;
  condition_logic: Record<string, any>;
  effective_from: string;
  effective_to?: string;
  source_document_ref: string;
}

export interface MockBankStatus {
  gateway_name: string;
  status: string;
  endpoint: string;
  is_simulation: boolean;
  mock_settlement_cycle: string;
  total_reversals_processed: number;
  pending_reversals_queued: number;
}
