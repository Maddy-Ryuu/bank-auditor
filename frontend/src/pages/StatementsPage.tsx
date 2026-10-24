import React, { useState } from 'react';
import { FileText, Play, ChevronRight, Hash, ArrowDownRight, ArrowUpRight, ShieldCheck } from 'lucide-react';
import { Statement, Account } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { Modal } from '../components/Modal';

interface Props {
  statements: Statement[];
  accounts: Account[];
  onRunAudit: (statementId: string) => void;
  onFetchDetails: (statementId: string) => Promise<Statement>;
}

export const StatementsPage: React.FC<Props> = ({
  statements,
  accounts,
  onRunAudit,
  onFetchDetails,
}) => {
  const [selectedStatement, setSelectedStatement] = useState<Statement | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [filterType, setFilterType] = useState<'all' | 'initial' | 'subsequent'>('all');

  const filteredStatements = statements.filter((s) => {
    if (filterType === 'initial') return !s.is_subsequent_statement;
    if (filterType === 'subsequent') return s.is_subsequent_statement;
    return true;
  });

  const getAccountInfo = (accountId: string) => {
    return accounts.find((a) => a.id === accountId);
  };

  const handleOpenDetails = async (stmt: Statement) => {
    setLoadingDetails(true);
    try {
      const detailed = await onFetchDetails(stmt.id);
      setSelectedStatement(detailed);
    } catch (err: any) {
      alert(`Could not load statement transactions: ${err.message}`);
    } finally {
      setLoadingDetails(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Synthetic Statements & Ledgers</h2>
          <p className="text-xs text-slate-400 mt-1">
            Browse synthetic banking periods, immutable cryptographic hashes, and line-item transaction ledgers.
          </p>
        </div>

        {/* Filter buttons */}
        <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 p-1 rounded-xl text-xs font-semibold">
          <button
            onClick={() => setFilterType('all')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              filterType === 'all' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            All Statements ({statements.length})
          </button>
          <button
            onClick={() => setFilterType('initial')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              filterType === 'initial' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Audit Statements ({statements.filter(s => !s.is_subsequent_statement).length})
          </button>
          <button
            onClick={() => setFilterType('subsequent')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              filterType === 'subsequent' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Subsequent Verification ({statements.filter(s => s.is_subsequent_statement).length})
          </button>
        </div>
      </div>

      {/* Statements Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/70 border-b border-slate-800 text-slate-400 uppercase font-semibold">
              <tr>
                <th className="px-5 py-3.5">Account & File</th>
                <th className="px-5 py-3.5">Statement Cycle</th>
                <th className="px-5 py-3.5">Closing Balance</th>
                <th className="px-5 py-3.5">Avg Daily Balance (ADB)</th>
                <th className="px-5 py-3.5">Type & Provenance</th>
                <th className="px-5 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {filteredStatements.map((stmt) => {
                const acc = getAccountInfo(stmt.account_id);
                return (
                  <tr key={stmt.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-5 py-4">
                      <div className="font-semibold text-slate-100 flex items-center space-x-2">
                        <FileText className="w-4 h-4 text-blue-400" />
                        <span>{stmt.source_filename}</span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5 font-mono">
                        {acc ? `${acc.holder_name} (${acc.account_number})` : stmt.account_id}
                      </div>
                    </td>
                    <td className="px-5 py-4 text-slate-300 font-mono">
                      {stmt.statement_period_start} → {stmt.statement_period_end}
                    </td>
                    <td className="px-5 py-4 font-semibold text-white">
                      ${stmt.closing_balance.toFixed(2)}
                    </td>
                    <td className="px-5 py-4 text-blue-300 font-semibold">
                      ${stmt.average_daily_balance.toFixed(2)}
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center space-x-2">
                        <StatusBadge status={stmt.is_subsequent_statement ? 'SUBSEQUENT' : 'INITIAL_AUDIT'} />
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono mt-1 flex items-center space-x-1">
                        <Hash className="w-3 h-3 text-slate-600" />
                        <span title={stmt.raw_statement_hash}>{stmt.raw_statement_hash.slice(0, 14)}...</span>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-right space-x-2">
                      <button
                        onClick={() => handleOpenDetails(stmt)}
                        className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs px-3 py-1.5 rounded-lg transition-colors inline-flex items-center space-x-1"
                      >
                        <span>View Ledger</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                      {!stmt.is_subsequent_statement && (
                        <button
                          onClick={() => onRunAudit(stmt.id)}
                          className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors inline-flex items-center space-x-1"
                        >
                          <Play className="w-3 h-3" />
                          <span>Audit</span>
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Statement Ledger Modal */}
      <Modal
        isOpen={selectedStatement !== null}
        onClose={() => setSelectedStatement(null)}
        title={`Ledger: ${selectedStatement?.source_filename || 'Statement Detail'}`}
        maxWidth="3xl"
      >
        {selectedStatement && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950 p-3.5 rounded-xl border border-slate-800 text-xs">
              <div>
                <span className="text-slate-400">Opening Balance:</span>
                <div className="font-semibold text-white mt-0.5">${selectedStatement.opening_balance.toFixed(2)}</div>
              </div>
              <div>
                <span className="text-slate-400">Closing Balance:</span>
                <div className="font-semibold text-white mt-0.5">${selectedStatement.closing_balance.toFixed(2)}</div>
              </div>
              <div>
                <span className="text-slate-400">Average Daily Bal:</span>
                <div className="font-semibold text-blue-400 mt-0.5">${selectedStatement.average_daily_balance.toFixed(2)}</div>
              </div>
              <div>
                <span className="text-slate-400">Total Direct Dep:</span>
                <div className="font-semibold text-emerald-400 mt-0.5">${selectedStatement.total_qualifying_direct_deposits.toFixed(2)}</div>
              </div>
            </div>

            <div className="overflow-x-auto border border-slate-800 rounded-xl">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase font-semibold">
                  <tr>
                    <th className="px-4 py-2.5">Date</th>
                    <th className="px-4 py-2.5">Description</th>
                    <th className="px-4 py-2.5">Type</th>
                    <th className="px-4 py-2.5 text-right">Amount</th>
                    <th className="px-4 py-2.5 text-right">Balance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {selectedStatement.transactions?.map((tx) => {
                    const isFee = tx.transaction_type === 'FEE';
                    const isCredit = tx.transaction_type === 'CREDIT' || tx.transaction_type === 'REFUND';
                    return (
                      <tr key={tx.id} className={isFee ? 'bg-amber-950/20' : ''}>
                        <td className="px-4 py-2.5 font-mono text-slate-300">{tx.transaction_date}</td>
                        <td className="px-4 py-2.5">
                          <div className="font-medium text-slate-200">{tx.description}</div>
                          <div className="text-[10px] text-slate-500 font-mono">{tx.source_transaction_id}</div>
                        </td>
                        <td className="px-4 py-2.5">
                          <StatusBadge status={tx.transaction_type} />
                        </td>
                        <td className={`px-4 py-2.5 text-right font-semibold ${
                          isCredit ? 'text-emerald-400' : isFee ? 'text-amber-400' : 'text-slate-300'
                        }`}>
                          {isCredit ? '+' : '-'}${tx.amount.toFixed(2)}
                        </td>
                        <td className="px-4 py-2.5 text-right font-mono text-slate-400">
                          ${tx.balance_after.toFixed(2)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="flex justify-between items-center text-xs text-slate-500 pt-2 border-t border-slate-800 font-mono">
              <span className="flex items-center space-x-1">
                <ShieldCheck className="w-4 h-4 text-emerald-500" />
                <span>SHA-256 Provenance Verified: {selectedStatement.raw_statement_hash}</span>
              </span>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
