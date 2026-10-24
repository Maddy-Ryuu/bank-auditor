import React, { useState } from 'react';
import {
  FileCheck2,
  CheckCircle,
  XCircle,
  Send,
  Building2,
  Clock,
  UserCheck,
  FileText,
  AlertCircle
} from 'lucide-react';
import { ReversalRequest } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { Modal } from '../components/Modal';

interface Props {
  reversals: ReversalRequest[];
  onTakeAction: (reversalId: string, action: 'APPROVE' | 'REJECT', user: string, notes?: string) => Promise<void>;
  onSubmitToMockBank: (reversalId: string) => Promise<void>;
  onUpdateDraft?: (reversalId: string, amount?: number, rationale?: string) => Promise<void>;
}

export const ReversalDeskPage: React.FC<Props> = ({
  reversals,
  onTakeAction,
  onSubmitToMockBank,
  onUpdateDraft,
}) => {
  const [selectedReversal, setSelectedReversal] = useState<ReversalRequest | null>(null);
  const [reviewMode, setReviewMode] = useState<boolean>(false);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editedRationale, setEditedRationale] = useState<string>('');
  const [approverName, setApproverName] = useState<string>('Senior Compliance Officer');
  const [approvalNotes, setApprovalNotes] = useState<string>('Evidence validated against published tariff.');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSaveDraft = async () => {
    if (!selectedReversal || !onUpdateDraft) return;
    try {
      await onUpdateDraft(selectedReversal.id, undefined, editedRationale);
      setIsEditing(false);
      setSelectedReversal(null);
      alert('Draft saved. Note: if draft was previously approved, prior approval is invalidated per safety rules.');
    } catch (err: any) {
      alert(`Save error: ${err.message}`);
    }
  };

  const handleApprove = async (revId: string) => {
    try {
      await onTakeAction(revId, 'APPROVE', approverName, approvalNotes);
      setReviewMode(false);
      setSelectedReversal(null);
    } catch (err: any) {
      alert(`Approval error: ${err.message}`);
    }
  };

  const handleReject = async (revId: string) => {
    try {
      await onTakeAction(revId, 'REJECT', approverName, approvalNotes);
      setReviewMode(false);
      setSelectedReversal(null);
    } catch (err: any) {
      alert(`Rejection error: ${err.message}`);
    }
  };

  const handleSubmitMock = async (revId: string) => {
    setIsSubmitting(true);
    try {
      await onSubmitToMockBank(revId);
      alert('Mock submission successful! Dispute acknowledged by Apex National Mock Gateway.');
      setSelectedReversal(null);
    } catch (err: any) {
      alert(`Submission error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Reversal Dispute Desk & Approvals</h2>
          <p className="text-xs text-slate-400 mt-1">
            Human-in-the-loop review station: Formal dispute letters must receive authorized sign-off prior to mock gateway submission.
          </p>
        </div>
      </div>

      {/* Reversals List */}
      <div className="grid grid-cols-1 gap-4">
        {reversals.length === 0 ? (
          <div className="p-12 text-center bg-slate-900 border border-slate-800 rounded-xl text-slate-400">
            No reversal requests drafted yet. Go to Audit Findings and select "Draft Dispute".
          </div>
        ) : (
          reversals.map((rev) => {
            const isApproved = rev.status === 'APPROVED';
            const isPending = rev.status === 'PENDING_APPROVAL';
            const isAcknowledged = rev.status === 'ACKNOWLEDGED' || rev.status === 'SETTLED';

            return (
              <div
                key={rev.id}
                className="p-5 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl shadow-lg space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center space-x-3">
                    <div className="p-2.5 rounded-lg bg-blue-950/60 border border-blue-800/80 text-blue-400">
                      <FileCheck2 className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-mono font-bold text-white text-sm">{rev.reference_number}</span>
                        <StatusBadge status={rev.status} />
                      </div>
                      <div className="text-xs text-slate-400 mt-0.5">
                        Amount Claimed: <strong className="text-emerald-400">${rev.requested_amount.toFixed(2)}</strong> • Prepared by: {rev.prepared_by}
                      </div>
                    </div>
                  </div>

                  {rev.mock_ack && (
                    <div className="px-3 py-1 bg-purple-950/50 border border-purple-800/70 rounded-lg text-purple-300 text-xs font-mono flex items-center space-x-1.5 self-start sm:self-auto">
                      <Building2 className="w-3.5 h-3.5" />
                      <span>Ticket: {rev.mock_ack.mock_bank_ticket_id}</span>
                    </div>
                  )}
                </div>

                {/* Dispute Letter Preview Box */}
                <div className="bg-slate-950/60 p-3.5 rounded-lg border border-slate-800/80 text-xs text-slate-300 font-mono whitespace-pre-wrap max-h-32 overflow-y-auto">
                  {rev.rationale_letter}
                </div>

                {/* Actions & Audit Trail Footer */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-slate-800 text-xs">
                  <div className="text-slate-400 flex items-center space-x-2">
                    <UserCheck className="w-3.5 h-3.5 text-blue-400" />
                    <span>
                      {rev.approvals.length > 0 ? (
                        <>Signed off by: <strong className="text-slate-200">{rev.approvals[rev.approvals.length - 1].approved_by_user}</strong></>
                      ) : (
                        <span className="text-amber-400">Awaiting Human Approval</span>
                      )}
                    </span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => {
                        setSelectedReversal(rev);
                        setReviewMode(false);
                      }}
                      className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-3 py-1.5 rounded-lg transition-colors font-semibold"
                    >
                      View Full Dispute
                    </button>

                    {isPending && (
                      <button
                        onClick={() => {
                          setSelectedReversal(rev);
                          setReviewMode(true);
                        }}
                        className="bg-blue-600 hover:bg-blue-500 text-white font-semibold px-3 py-1.5 rounded-lg transition-colors shadow-sm"
                      >
                        Review & Approve
                      </button>
                    )}

                    {isApproved && (
                      <button
                        onClick={() => handleSubmitMock(rev.id)}
                        disabled={isSubmitting}
                        className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold px-3 py-1.5 rounded-lg transition-colors shadow-sm flex items-center space-x-1.5"
                      >
                        <Send className="w-3.5 h-3.5" />
                        <span>Submit to Mock Portal</span>
                      </button>
                    )}

                    {isAcknowledged && (
                      <span className="text-emerald-400 font-semibold flex items-center space-x-1">
                        <CheckCircle className="w-4 h-4" />
                        <span>Mock Submission Acknowledged</span>
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Review & Approve Modal */}
      <Modal
        isOpen={selectedReversal !== null}
        onClose={() => {
          setSelectedReversal(null);
          setReviewMode(false);
        }}
        title={`Dispute Memo: ${selectedReversal?.reference_number}`}
        maxWidth="3xl"
      >
        {selectedReversal && (
          <div className="space-y-4 text-xs">
            {/* Memo Letter Header & Edit Toggle */}
            <div className="flex items-center justify-between text-xs pb-1">
              <span className="font-semibold text-slate-300">Formal Reversal Dispute Memo:</span>
              {selectedReversal.status !== 'ACKNOWLEDGED' && selectedReversal.status !== 'SETTLED' && (
                <button
                  onClick={() => {
                    if (!isEditing) {
                      setEditedRationale(selectedReversal.rationale_letter);
                    }
                    setIsEditing(!isEditing);
                  }}
                  className="text-blue-400 hover:text-blue-300 font-semibold"
                >
                  {isEditing ? 'Cancel Edit' : 'Edit Dispute Letter'}
                </button>
              )}
            </div>

            {isEditing ? (
              <div className="space-y-2">
                <div className="p-2 bg-amber-950/60 border border-amber-800 text-amber-300 text-[11px] rounded-lg">
                  ⚠️ <strong>Safety Warning:</strong> Editing this draft will invalidate any existing approval and reset the status to <strong>PENDING_APPROVAL</strong>.
                </div>
                <textarea
                  value={editedRationale}
                  onChange={(e) => setEditedRationale(e.target.value)}
                  className="w-full h-64 bg-slate-950 border border-slate-700 rounded-xl p-3 font-mono text-[11px] text-slate-200 focus:outline-none focus:border-blue-500"
                />
                <button
                  onClick={handleSaveDraft}
                  className="bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs px-4 py-2 rounded-lg"
                >
                  Save Changes (Invalidates Prior Approval)
                </button>
              </div>
            ) : (
              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 font-mono text-slate-300 text-[11px] whitespace-pre-wrap leading-relaxed max-h-72 overflow-y-auto">
                {selectedReversal.rationale_letter}
              </div>
            )}

            {/* Approval Form (if in review mode or pending) */}
            {selectedReversal.status === 'PENDING_APPROVAL' && (
              <div className="p-4 bg-slate-950 rounded-xl border border-blue-900/60 space-y-3">
                <h4 className="font-bold text-white text-xs flex items-center space-x-1.5">
                  <UserCheck className="w-4 h-4 text-blue-400" />
                  <span>Compliance Officer Review & Sign-Off</span>
                </h4>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-400 text-[11px] mb-1">Auditor / Officer Name:</label>
                    <input
                      type="text"
                      value={approverName}
                      onChange={(e) => setApproverName(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 text-[11px] mb-1">Approval Notes / Evidence Verification:</label>
                    <input
                      type="text"
                      value={approvalNotes}
                      onChange={(e) => setApprovalNotes(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>

                <div className="flex justify-end space-x-3 pt-2">
                  <button
                    onClick={() => handleReject(selectedReversal.id)}
                    className="flex items-center space-x-1.5 bg-rose-950/80 hover:bg-rose-900 text-rose-300 border border-rose-800 text-xs font-semibold px-4 py-2 rounded-lg transition-colors"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Reject Dispute</span>
                  </button>
                  <button
                    onClick={() => handleApprove(selectedReversal.id)}
                    className="flex items-center space-x-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors shadow-sm"
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>Approve for Mock Submission</span>
                  </button>
                </div>
              </div>
            )}

            {/* If already approved, show mock submission trigger */}
            {selectedReversal.status === 'APPROVED' && (
              <div className="p-4 bg-emerald-950/40 border border-emerald-800/70 rounded-xl space-y-3">
                <div className="text-emerald-300 font-semibold flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4" />
                  <span>Dispute Approved! Ready for Mock Gateway Submission.</span>
                </div>
                <p className="text-slate-400 text-[11px]">
                  Authorized by: {selectedReversal.approvals[selectedReversal.approvals.length - 1]?.approved_by_user}
                </p>
                <button
                  onClick={() => handleSubmitMock(selectedReversal.id)}
                  disabled={isSubmitting}
                  className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold text-xs py-2 rounded-lg transition-colors flex items-center justify-center space-x-2"
                >
                  <Send className="w-4 h-4" />
                  <span>{isSubmitting ? 'Submitting to Mock Gateway...' : 'Submit to Apex National Mock Portal'}</span>
                </button>
              </div>
            )}

            {/* If acknowledged, show ticket payload */}
            {selectedReversal.mock_ack && (
              <div className="p-4 bg-slate-950 rounded-xl border border-purple-900/60 space-y-2">
                <div className="text-purple-300 font-semibold flex items-center space-x-2">
                  <Building2 className="w-4 h-4 text-purple-400" />
                  <span>Mock Bank Portal Acknowledgement Record</span>
                </div>
                <div className="font-mono text-[11px] text-slate-300">
                  Ticket ID: <strong className="text-purple-300">{selectedReversal.mock_ack.mock_bank_ticket_id}</strong>
                </div>
                <pre className="p-3 bg-slate-900 rounded-lg text-slate-300 font-mono text-[10px] overflow-x-auto">
                  {JSON.stringify(selectedReversal.mock_ack.acknowledgement_payload, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};
