import React, { useState } from 'react';
import { CheckCircle2, AlertTriangle, RefreshCw, ArrowRight, ShieldCheck, DollarSign } from 'lucide-react';
import { ReversalRequest, VerificationResult } from '../types';
import { StatusBadge } from '../components/StatusBadge';

interface Props {
  reversals: ReversalRequest[];
  verifications: VerificationResult[];
  onRunVerification: (reversalId: string) => Promise<void>;
}

export const VerificationPage: React.FC<Props> = ({
  reversals,
  verifications,
  onRunVerification,
}) => {
  const [verifyingId, setVerifyingId] = useState<string | null>(null);

  // Eligible reversals for verification (acknowledged or approved)
  const submittedReversals = reversals.filter(
    (r) => r.status === 'ACKNOWLEDGED' || r.status === 'SETTLED' || r.status === 'APPROVED'
  );

  const getVerificationForReversal = (reversalId: string) => {
    return verifications.find((v) => v.reversal_request_id === reversalId);
  };

  const handleVerify = async (reversalId: string) => {
    setVerifyingId(reversalId);
    try {
      await onRunVerification(reversalId);
    } catch (err: any) {
      alert(`Verification error: ${err.message}`);
    } finally {
      setVerifyingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Refund Reconciliation & Verification</h2>
          <p className="text-xs text-slate-400 mt-1">
            Reconciles approved fee disputes against the client's subsequent bank statement to verify that refund credits were deposited.
          </p>
        </div>
      </div>

      {/* Reversals Verification Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/70 border-b border-slate-800 text-slate-400 uppercase font-semibold">
              <tr>
                <th className="px-5 py-3.5">Dispute Reference</th>
                <th className="px-5 py-3.5">Expected Refund</th>
                <th className="px-5 py-3.5">Mock Ticket ID</th>
                <th className="px-5 py-3.5">Reconciliation Status</th>
                <th className="px-5 py-3.5">Verified Credit</th>
                <th className="px-5 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {submittedReversals.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-10 text-center text-slate-500">
                    No submitted fee disputes awaiting subsequent statement verification.
                  </td>
                </tr>
              ) : (
                submittedReversals.map((rev) => {
                  const ver = getVerificationForReversal(rev.id);
                  const isVerifying = verifyingId === rev.id;

                  return (
                    <tr key={rev.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="px-5 py-4">
                        <div className="font-mono font-bold text-slate-100">{rev.reference_number}</div>
                        <div className="text-[11px] text-slate-400 mt-0.5">
                          {rev.finding?.violation_title || 'Fee Dispute'}
                        </div>
                      </td>

                      <td className="px-5 py-4 font-semibold text-white">
                        ${rev.requested_amount.toFixed(2)}
                      </td>

                      <td className="px-5 py-4 font-mono text-purple-300">
                        {rev.mock_ack?.mock_bank_ticket_id || 'Pending Mock Ack'}
                      </td>

                      <td className="px-5 py-4">
                        {ver ? (
                          <div>
                            <StatusBadge status={ver.verification_status} />
                            <p className="text-[10px] text-slate-400 mt-1 max-w-xs truncate" title={ver.notes || ''}>
                              {ver.notes}
                            </p>
                          </div>
                        ) : (
                          <span className="text-slate-500 text-xs italic">Unverified</span>
                        )}
                      </td>

                      <td className="px-5 py-4 font-bold">
                        {ver && ver.is_verified ? (
                          <span className="text-emerald-400 flex items-center space-x-1">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>${ver.verified_amount.toFixed(2)}</span>
                          </span>
                        ) : ver && ver.discrepancy_amount > 0 ? (
                          <span className="text-rose-400 flex items-center space-x-1">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            <span>Shortfall: ${ver.discrepancy_amount.toFixed(2)}</span>
                          </span>
                        ) : (
                          <span className="text-slate-500 font-normal">--</span>
                        )}
                      </td>

                      <td className="px-5 py-4 text-right">
                        <button
                          onClick={() => handleVerify(rev.id)}
                          disabled={isVerifying}
                          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors inline-flex items-center space-x-1.5 shadow-sm"
                        >
                          <RefreshCw className={`w-3.5 h-3.5 ${isVerifying ? 'animate-spin' : ''}`} />
                          <span>{ver ? 'Re-Verify' : 'Verify Against Cycle'}</span>
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
