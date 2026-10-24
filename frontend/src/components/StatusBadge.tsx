import React from 'react';

interface Props {
  status: string;
}

export const StatusBadge: React.FC<Props> = ({ status }) => {
  const normalized = status.toUpperCase();

  let styles = "bg-slate-800 text-slate-300 border-slate-700";

  switch (normalized) {
    case 'FLAGGED':
      styles = "bg-amber-950/60 text-amber-300 border-amber-800/80";
      break;
    case 'PENDING_APPROVAL':
      styles = "bg-blue-950/60 text-blue-300 border-blue-800/80";
      break;
    case 'APPROVED':
      styles = "bg-emerald-950/60 text-emerald-300 border-emerald-700/80";
      break;
    case 'REJECTED':
    case 'DISMISSED':
      styles = "bg-rose-950/60 text-rose-300 border-rose-800/80";
      break;
    case 'SUBMITTED':
    case 'SUBMITTED_TO_MOCK_PORTAL':
    case 'ACKNOWLEDGED':
      styles = "bg-purple-950/60 text-purple-300 border-purple-800/80";
      break;
    case 'SETTLED':
    case 'REVERSED':
    case 'MATCHED_EXACT':
      styles = "bg-teal-950/60 text-teal-300 border-teal-700/80";
      break;
    case 'PARTIAL_REFUND':
      styles = "bg-orange-950/60 text-orange-300 border-orange-800/80";
      break;
    case 'AMBIGUOUS_UNRESOLVED':
      styles = "bg-yellow-950/70 text-yellow-300 border-yellow-700/80";
      break;
    case 'APPROVAL_INVALIDATED':
      styles = "bg-orange-950/80 text-orange-200 border-orange-700";
      break;
    case 'NOT_FOUND_IN_SUBSEQUENT':
      styles = "bg-red-950/60 text-red-300 border-red-800/80";
      break;
    case 'HIGH':
      styles = "bg-rose-950/80 text-rose-200 border-rose-700";
      break;
    case 'MEDIUM':
      styles = "bg-amber-950/70 text-amber-200 border-amber-700";
      break;
    case 'LOW':
      styles = "bg-slate-800 text-slate-300 border-slate-700";
      break;
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${styles}`}>
      {normalized.replace(/_/g, ' ')}
    </span>
  );
};
