import React, { useState } from 'react';
import { AlertOctagon, Eye, FileText, CheckCircle, ShieldAlert, ArrowRight } from 'lucide-react';
import { AuditFinding } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { Modal } from '../components/Modal';

interface Props {
  findings: AuditFinding[];
  onDraftReversal: (findingId: string) => void;
  onSelectTab: (tab: any) => void;
}

export const AuditFindingsPage: React.FC<Props> = ({
  findings,
  onDraftReversal,
  onSelectTab,
}) => {
  const [selectedFinding, setSelectedFinding] = useState<AuditFinding | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('ALL');
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');

  const categories = ['ALL', ...Array.from(new Set(findings.map((f) => f.rule_category)))];

  const filtered = findings.filter((f) => {
    if (filterCategory !== 'ALL' && f.rule_category !== filterCategory) return false;
    if (filterSeverity !== 'ALL' && f.severity !== filterSeverity) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Audit Findings & Evidence</h2>
          <p className="text-xs text-slate-400 mt-1">
            Contractual and statutory fee violations identified by the rules engine with immutable proof.
          </p>
        </div>

        {/* Filter dropdowns */}
        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="text-slate-400">Category:</span>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-blue-500"
            >
              {categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-1.5">
            <span className="text-slate-400">Severity:</span>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">ALL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </div>
        </div>
      </div>

      {/* Findings Grid */}
      <div className="grid grid-cols-1 gap-4">
        {filtered.length === 0 ? (
          <div className="p-12 text-center bg-slate-900 border border-slate-800 rounded-xl text-slate-400">
            No audit findings match your current filters.
          </div>
        ) : (
          filtered.map((finding) => (
            <div
              key={finding.id}
              className="p-5 bg-slate-900 border border-slate-800 hover:border-slate-700/80 rounded-xl transition-all shadow-md space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center space-x-2.5">
                  <div className="p-2 rounded-lg bg-rose-950/60 border border-rose-800/80 text-rose-400">
                    <AlertOctagon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">{finding.violation_title}</h3>
                    <div className="text-xs text-slate-400 flex items-center space-x-2 mt-0.5">
                      <span>Category: <strong className="text-slate-300">{finding.rule_category}</strong></span>
                      <span>•</span>
                      <span>Detected: {new Date(finding.detected_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2 self-start sm:self-auto">
                  <StatusBadge status={finding.severity} />
                  <StatusBadge status={finding.status} />
                </div>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-3 rounded-lg border border-slate-800/80">
                {finding.violation_reason}
              </p>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-slate-800/80">
                <div className="flex items-center space-x-4 text-xs">
                  <div>
                    <span className="text-slate-500">Fee Charged:</span>{' '}
                    <strong className="text-rose-400 font-semibold">${finding.fee_amount.toFixed(2)}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500">Refund Target:</span>{' '}
                    <strong className="text-emerald-400 font-bold">${finding.potential_refund_amount.toFixed(2)}</strong>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setSelectedFinding(finding)}
                    className="flex items-center space-x-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>View Evidence</span>
                  </button>

                  {finding.status === 'FLAGGED' ? (
                    <button
                      onClick={() => onDraftReversal(finding.id)}
                      className="flex items-center space-x-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors shadow-sm"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>Draft Dispute</span>
                    </button>
                  ) : (
                    <button
                      onClick={() => onSelectTab('reversals')}
                      className="flex items-center space-x-1.5 text-xs text-blue-400 hover:text-blue-300 border border-blue-900/60 bg-blue-950/30 px-3 py-1.5 rounded-lg transition-colors"
                    >
                      <span>In Reversal Desk</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Evidence Modal */}
      <Modal
        isOpen={selectedFinding !== null}
        onClose={() => setSelectedFinding(null)}
        title="Audit Evidence & Mathematical Proof"
        maxWidth="2xl"
      >
        {selectedFinding && (
          <div className="space-y-4 text-xs">
            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
              <div className="font-semibold text-white text-sm">{selectedFinding.violation_title}</div>
              <p className="text-slate-300">{selectedFinding.violation_reason}</p>
            </div>

            <div>
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                Structured Evidence Snapshot
              </h4>
              <pre className="p-4 bg-slate-950 border border-slate-800 rounded-xl text-slate-300 font-mono text-[11px] overflow-x-auto leading-relaxed">
                {JSON.stringify(selectedFinding.evidence_data, null, 2)}
              </pre>
            </div>

            <div className="p-3 bg-blue-950/30 border border-blue-900/50 rounded-xl text-blue-300 text-[11px] flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-blue-400 shrink-0" />
              <span>
                This audit evidence is timestamped ({new Date(selectedFinding.detected_at).toISOString()}) and signed by rule <strong>{selectedFinding.rule_category}</strong>.
              </span>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
