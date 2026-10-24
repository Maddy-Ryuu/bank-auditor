import {
  Account,
  AccountTier,
  Statement,
  AuditFinding,
  ReversalRequest,
  VerificationResult,
  TariffRule,
  MockBankStatus
} from '../types';

// Retrieve API base URL from Vite environment variable with fallback to relative '/api'
const rawApiBase = import.meta.env.VITE_API_BASE_URL || '';
const API_BASE = rawApiBase ? `${rawApiBase.replace(/\/+$/, '')}/api` : '/api';

export const api = {
  // Health
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  // Accounts & Tiers
  async getAccounts(): Promise<Account[]> {
    const res = await fetch(`${API_BASE}/v1/accounts`);
    if (!res.ok) throw new Error('Failed to fetch accounts');
    return res.json();
  },

  async getTiers(): Promise<AccountTier[]> {
    const res = await fetch(`${API_BASE}/v1/accounts/tiers`);
    if (!res.ok) throw new Error('Failed to fetch tiers');
    return res.json();
  },

  // Statements
  async getStatements(isSubsequent?: boolean): Promise<Statement[]> {
    const url = isSubsequent !== undefined 
      ? `${API_BASE}/v1/statements?is_subsequent=${isSubsequent}`
      : `${API_BASE}/v1/statements`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch statements');
    return res.json();
  },

  async getStatementDetails(statementId: string): Promise<Statement> {
    const res = await fetch(`${API_BASE}/v1/statements/${statementId}`);
    if (!res.ok) throw new Error('Failed to fetch statement details');
    return res.json();
  },

  // Audits
  async runAudit(statementId: string) {
    const res = await fetch(`${API_BASE}/v1/audits/run/${statementId}`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed to execute audit');
    return res.json();
  },

  async getFindings(status?: string, category?: string): Promise<AuditFinding[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (category) params.append('category', category);
    const query = params.toString() ? `?${params.toString()}` : '';

    const res = await fetch(`${API_BASE}/v1/audits/findings${query}`);
    if (!res.ok) throw new Error('Failed to fetch audit findings');
    return res.json();
  },

  // Reversals
  async getReversals(status?: string): Promise<ReversalRequest[]> {
    const query = status ? `?status=${status}` : '';
    const res = await fetch(`${API_BASE}/v1/reversals${query}`);
    if (!res.ok) throw new Error('Failed to fetch reversal requests');
    return res.json();
  },

  async draftReversal(findingId: string): Promise<ReversalRequest> {
    const res = await fetch(`${API_BASE}/v1/reversals/draft/${findingId}`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to draft reversal');
    }
    return res.json();
  },

  async updateReversalDraft(
    reversalId: string,
    requestedAmount?: number,
    rationaleLetter?: string,
    editorUser?: string
  ): Promise<ReversalRequest> {
    const res = await fetch(`${API_BASE}/v1/reversals/${reversalId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        requested_amount: requestedAmount,
        rationale_letter: rationaleLetter,
        editor_user: editorUser || 'Compliance Officer'
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to update draft');
    }
    return res.json();
  },

  async takeApprovalAction(
    reversalId: string,
    action: 'APPROVE' | 'REJECT' | 'REQUEST_REVISION',
    approvedByUser: string,
    notes?: string
  ): Promise<ReversalRequest> {
    const res = await fetch(`${API_BASE}/v1/reversals/${reversalId}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action,
        approved_by_user: approvedByUser,
        notes: notes || 'Reviewed compliance evidence.'
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to record approval');
    }
    return res.json();
  },

  async submitToMockBank(reversalId: string) {
    const res = await fetch(`${API_BASE}/v1/reversals/${reversalId}/submit-mock-bank`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to submit reversal to mock portal');
    }
    return res.json();
  },

  // Verifications
  async getVerifications(): Promise<VerificationResult[]> {
    const res = await fetch(`${API_BASE}/v1/verifications`);
    if (!res.ok) throw new Error('Failed to fetch verifications');
    return res.json();
  },

  async runVerification(reversalId: string, subsequentStatementId?: string): Promise<VerificationResult> {
    const res = await fetch(`${API_BASE}/v1/verifications/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reversal_id: reversalId,
        subsequent_statement_id: subsequentStatementId
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to execute verification');
    }
    return res.json();
  },

  // Tariffs
  async getTariffs(tierId?: string): Promise<TariffRule[]> {
    const query = tierId ? `?tier_id=${tierId}` : '';
    const res = await fetch(`${API_BASE}/v1/tariffs${query}`);
    if (!res.ok) throw new Error('Failed to fetch tariffs');
    return res.json();
  },

  // Mock Bank Gateway
  async getMockBankStatus(): Promise<MockBankStatus> {
    const res = await fetch(`${API_BASE}/v1/mock-bank/status`);
    if (!res.ok) throw new Error('Failed to fetch mock bank status');
    return res.json();
  },

  async getMockBankTickets(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/v1/mock-bank/tickets`);
    if (!res.ok) throw new Error('Failed to fetch mock bank tickets');
    return res.json();
  },

  // Reset / Run test suite
  async resetDatabaseSeed() {
    const res = await fetch(`${API_BASE}/v1/seed/reset`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to reset seed');
    return res.json();
  },

  async runAuditSuite() {
    const res = await fetch(`${API_BASE}/v1/seed/run-audit-suite`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to execute audit suite');
    return res.json();
  }
};
