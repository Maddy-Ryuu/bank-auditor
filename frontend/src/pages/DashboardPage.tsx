import React from 'react';
import { DollarSign, ShieldAlert, CheckCircle2, Clock, ArrowRight, Play, ExternalLink } from 'lucide-react';
import { StatCard } from '../components/StatCard';
import { StatusBadge } from '../components/StatusBadge';
import { AuditFinding, ReversalRequest, Statement, VerificationResult } from '../types';

interface Props {
  findings: AuditFinding[];
  reversals: ReversalRequest[];
  statements: Statement[];
  verifications: VerificationResult[];
  onSelectTab: (tab: any) => void;
  onDraftReversal: (findingId: string) => void;
  onRunAudit: (statementId: string) => void;
}

export const DashboardPage: React.FC<Props> = ({
  findings,
  reversals,
  statements,
  verifications,
  onSelectTab,
  onDraftReversal,
  onRunAudit,
}) => {
  const totalAuditedFees = findings.reduce((acc, f) => acc + f.fee_amount, 0);
  const totalPotentialRecovery = findings.reduce((acc, f) => acc + f.potential_refund_amount, 0);
  const pendingApprovals = reversals.filter(r => r.status === 'PENDING_APPROVAL');
  const verifiedRecovered = verifications
    .filter(v => v.is_verified)
    .reduce((acc, v) => acc + v.verified_amount, 0);

  const initialStatements = statements.filter(s => !s.is_subsequent_statement);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-blue-900/40 via-indigo-900/30 to-slate-900 border border-blue-800/40 p-6 rounded-2xl shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Audit & Recovery Command Center</h2>
          <p className="text-sm text-slate-300 mt-1 max-w-2xl">
            Identifies non-compliant bank service charges against published tariff schedules, orchestrates human-in-the-loop dispute approvals, submits to mock bank gateways, and reconciles refunds.
          </p>
        </div>
        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={() => onSelectTab('findings')}
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs px-4 py-2.5 rounded-xl transition-all shadow-md"
          >
            <span>Review Findings</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Erroneous Fees Audited"
          value={`$${totalAuditedFees.toFixed(2)}`}
          subtitle={`${findings.length} violations detected`}
          icon={DollarSign}
          variant="amber"
        />
        <StatCard
          title="Potential Recovery Target"
          value={`$${totalPotentialRecovery.toFixed(2)}`}
          subtitle="Identified across synthetic accounts"
          icon={ShieldAlert}
          variant="blue"
        />
        <StatCard
          title="Pending Human Approvals"
          value={pendingApprovals.length}
          subtitle="Awaiting compliance sign-off"
          icon={Clock}
          variant="purple"
        />
        <StatCard
          title="Verified Recovered Credits"
          value={`$${verifiedRecovered.toFixed(2)}`}
          subtitle="Reconciled on subsequent statements"
          icon={CheckCircle2}
          variant="emerald"
        />
      </div>

      {/* 2-Column Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Recent Audit Findings */}
        <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div>
              <h3 className="text-base font-bold text-white">Active Audit Findings</h3>
              <p className="text-xs text-slate-400">Non-compliant fees detected across active statement cycles</p>
            </div>
            <button
              onClick={() => onSelectTab('findings')}
              className="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center space-x-1"
            >
              <span>View All</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="mt-4 divide-y divide-slate-800/80">
            {findings.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-sm">
                No active audit findings. Run an audit on a statement to detect fee violations.
              </div>
            ) : (
              findings.slice(0, 5).map((finding) => (
                <div key={finding.id} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-sm text-slate-100">{finding.violation_title}</span>
                      <StatusBadge status={finding.severity} />
                      <StatusBadge status={finding.status} />
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-1">{finding.violation_reason}</p>
                    <div className="text-[11px] text-slate-500 flex items-center space-x-3">
                      <span>Category: <strong className="text-slate-400">{finding.rule_category}</strong></span>
                      <span>•</span>
                      <span>Snapshot: <strong className="text-slate-400">{finding.source_evidence_snapshot || 'N/A'}</strong></span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3 self-end sm:self-center shrink-0">
                    <span className="text-sm font-bold text-amber-400">
                      ${finding.potential_refund_amount.toFixed(2)}
                    </span>
                    {finding.status === 'FLAGGED' ? (
                      <button
                        onClick={() => onDraftReversal(finding.id)}
                        className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors"
                      >
                        Draft Dispute
                      </button>
                    ) : (
                      <button
                        onClick={() => onSelectTab('reversals')}
                        className="text-xs text-slate-400 hover:text-slate-200 border border-slate-700 px-2.5 py-1.5 rounded-lg flex items-center space-x-1"
                      >
                        <span>View Desk</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Statements Ready for Audit */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
          <div className="pb-3 border-b border-slate-800">
            <h3 className="text-base font-bold text-white">Synthetic Statements</h3>
            <p className="text-xs text-slate-400">Statements loaded and ready for audit evaluation</p>
          </div>

          <div className="space-y-3">
            {initialStatements.map((stmt) => (
              <div key={stmt.id} className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200 truncate max-w-[170px]">
                    {stmt.source_filename}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono bg-slate-800 px-1.5 py-0.5 rounded">
                    {stmt.source_id.slice(-8)}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 flex justify-between">
                  <span>Cycle: {stmt.statement_period_start}</span>
                  <span>ADB: <strong className="text-slate-200">${stmt.average_daily_balance.toFixed(2)}</strong></span>
                </div>
                <button
                  onClick={() => onRunAudit(stmt.id)}
                  className="w-full mt-2 flex items-center justify-center space-x-1.5 bg-slate-800 hover:bg-slate-700 text-blue-400 border border-slate-700 hover:border-slate-600 text-xs font-semibold py-1.5 rounded-lg transition-all"
                >
                  <Play className="w-3 h-3" />
                  <span>Audit This Statement</span>
                </button>
              </div>
            ))}
          </div>

          {/* Workflow Guide */}
          <div className="p-3 rounded-lg bg-blue-950/30 border border-blue-900/50 text-xs text-blue-300 space-y-1.5">
            <div className="font-semibold text-white">Production Audit Workflow</div>
            <ol className="list-decimal list-inside space-y-1 text-slate-400 text-[11px]">
              <li>Evaluate statement against published tariff.</li>
              <li>Generate dispute memo with structured evidence.</li>
              <li>Human compliance approval required before submission.</li>
              <li>Submit to isolated Mock Bank Portal.</li>
              <li>Reconcile credit on subsequent statement.</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
};
