import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar, TabType } from './components/Sidebar';
import { MockBankBanner } from './components/MockBankBanner';
import { DashboardPage } from './pages/DashboardPage';
import { StatementsPage } from './pages/StatementsPage';
import { AuditFindingsPage } from './pages/AuditFindingsPage';
import { ReversalDeskPage } from './pages/ReversalDeskPage';
import { VerificationPage } from './pages/VerificationPage';
import { TariffSchedulePage } from './pages/TariffSchedulePage';
import { MockBankPortalPage } from './pages/MockBankPortalPage';
import { api } from './api/client';
import {
  Account,
  AccountTier,
  Statement,
  AuditFinding,
  ReversalRequest,
  VerificationResult,
  TariffRule,
  MockBankStatus,
} from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<TabType>('dashboard');
  const [loading, setLoading] = useState(true);

  // Core data states
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [tiers, setTiers] = useState<AccountTier[]>([]);
  const [statements, setStatements] = useState<Statement[]>([]);
  const [findings, setFindings] = useState<AuditFinding[]>([]);
  const [reversals, setReversals] = useState<ReversalRequest[]>([]);
  const [verifications, setVerifications] = useState<VerificationResult[]>([]);
  const [tariffs, setTariffs] = useState<TariffRule[]>([]);
  const [mockStatus, setMockStatus] = useState<MockBankStatus | null>(null);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    try {
      const [accs, trs, stmts, fnds, revs, vers, tfs, ms] = await Promise.all([
        api.getAccounts().catch(() => []),
        api.getTiers().catch(() => []),
        api.getStatements().catch(() => []),
        api.getFindings().catch(() => []),
        api.getReversals().catch(() => []),
        api.getVerifications().catch(() => []),
        api.getTariffs().catch(() => []),
        api.getMockBankStatus().catch(() => null),
      ]);

      setAccounts(accs);
      setTiers(trs);
      setStatements(stmts);
      setFindings(fnds);
      setReversals(revs);
      setVerifications(vers);
      setTariffs(tfs);
      setMockStatus(ms);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAudit = async (statementId: string) => {
    try {
      const summary = await api.runAudit(statementId);
      alert(`Audit Complete: Discovered ${summary.findings_count} violations ($${summary.total_potential_refund.toFixed(2)} recovery target).`);
      await loadAllData();
      setCurrentTab('findings');
    } catch (err: any) {
      alert(`Audit error: ${err.message}`);
    }
  };

  const handleDraftReversal = async (findingId: string) => {
    try {
      await api.draftReversal(findingId);
      await loadAllData();
      setCurrentTab('reversals');
    } catch (err: any) {
      alert(`Dispute drafting failed: ${err.message}`);
    }
  };

  const handleTakeApprovalAction = async (
    reversalId: string,
    action: 'APPROVE' | 'REJECT',
    user: string,
    notes?: string
  ) => {
    await api.takeApprovalAction(reversalId, action, user, notes);
    await loadAllData();
  };

  const handleUpdateDraft = async (
    reversalId: string,
    amount?: number,
    rationale?: string
  ) => {
    await api.updateReversalDraft(reversalId, amount, rationale);
    await loadAllData();
  };

  const handleSubmitToMockBank = async (reversalId: string) => {
    await api.submitToMockBank(reversalId);
    await loadAllData();
  };

  const handleRunVerification = async (reversalId: string) => {
    await api.runVerification(reversalId);
    await loadAllData();
  };

  const counts = {
    findingsCount: findings.filter((f) => f.status === 'FLAGGED').length,
    pendingApprovalsCount: reversals.filter((r) => r.status === 'PENDING_APPROVAL').length,
    verifiedCount: verifications.filter((v) => v.is_verified).length,
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <MockBankBanner />
      <Navbar onRefreshAll={loadAllData} />

      <div className="flex flex-1">
        <Sidebar
          currentTab={currentTab}
          onSelectTab={setCurrentTab}
          counts={counts}
        />

        <main className="flex-1 p-6 md:p-8 max-w-7xl mx-auto w-full overflow-x-hidden">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-24 space-y-4">
              <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-sm text-slate-400">Loading audit records & mock gateway state...</p>
            </div>
          ) : (
            <>
              {currentTab === 'dashboard' && (
                <DashboardPage
                  findings={findings}
                  reversals={reversals}
                  statements={statements}
                  verifications={verifications}
                  onSelectTab={setCurrentTab}
                  onDraftReversal={handleDraftReversal}
                  onRunAudit={handleRunAudit}
                />
              )}

              {currentTab === 'statements' && (
                <StatementsPage
                  statements={statements}
                  accounts={accounts}
                  onRunAudit={handleRunAudit}
                  onFetchDetails={api.getStatementDetails}
                />
              )}

              {currentTab === 'findings' && (
                <AuditFindingsPage
                  findings={findings}
                  onDraftReversal={handleDraftReversal}
                  onSelectTab={setCurrentTab}
                />
              )}

              {currentTab === 'reversals' && (
                <ReversalDeskPage
                  reversals={reversals}
                  onTakeAction={handleTakeApprovalAction}
                  onSubmitToMockBank={handleSubmitToMockBank}
                  onUpdateDraft={handleUpdateDraft}
                />
              )}

              {currentTab === 'verification' && (
                <VerificationPage
                  reversals={reversals}
                  verifications={verifications}
                  onRunVerification={handleRunVerification}
                />
              )}

              {currentTab === 'tariffs' && (
                <TariffSchedulePage
                  tiers={tiers}
                  tariffs={tariffs}
                />
              )}

              {currentTab === 'mock-bank' && (
                <MockBankPortalPage
                  mockStatus={mockStatus}
                  onRefresh={loadAllData}
                />
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
