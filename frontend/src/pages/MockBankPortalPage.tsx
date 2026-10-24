import React, { useState, useEffect } from 'react';
import { Building2, ShieldCheck, CheckCircle, Clock, Server, Terminal, RefreshCw } from 'lucide-react';
import { MockBankStatus } from '../types';
import { api } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';

interface Props {
  mockStatus: MockBankStatus | null;
  onRefresh: () => void;
}

export const MockBankPortalPage: React.FC<Props> = ({ mockStatus, onRefresh }) => {
  const [tickets, setTickets] = useState<any[]>([]);
  const [loadingTickets, setLoadingTickets] = useState(false);

  useEffect(() => {
    loadTickets();
  }, []);

  const loadTickets = async () => {
    setLoadingTickets(true);
    try {
      const data = await api.getMockBankTickets();
      setTickets(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingTickets(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Apex National Mock Gateway Console</h2>
          <p className="text-xs text-slate-400 mt-1">
            Simulated banking dispute receiver: inspects incoming electronic reversals, tickets, digital signatures, and automated settlement cycles.
          </p>
        </div>

        <button
          onClick={() => {
            onRefresh();
            loadTickets();
          }}
          className="flex items-center space-x-1.5 bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Console</span>
        </button>
      </div>

      {/* Gateway Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
          <div className="text-slate-400 flex items-center space-x-1.5">
            <Server className="w-4 h-4 text-emerald-400" />
            <span>Gateway Mode</span>
          </div>
          <div className="text-lg font-bold text-white flex items-center space-x-2">
            <span>ISOLATED SIMULATION</span>
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
          </div>
          <p className="text-slate-500 text-[11px]">Strict localhost boundary; zero live bank routing.</p>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
          <div className="text-slate-400 flex items-center space-x-1.5">
            <Clock className="w-4 h-4 text-blue-400" />
            <span>Settlement Cycle Protocol</span>
          </div>
          <div className="text-base font-bold text-blue-300 font-mono">
            {mockStatus?.mock_settlement_cycle || 'NEXT_STATEMENT_CYCLE'}
          </div>
          <p className="text-slate-500 text-[11px]">Credits post to subsequent monthly statements.</p>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
          <div className="text-slate-400 flex items-center space-x-1.5">
            <CheckCircle className="w-4 h-4 text-purple-400" />
            <span>Processed Disputed Tickets</span>
          </div>
          <div className="text-2xl font-bold text-white">
            {tickets.length}
          </div>
          <p className="text-slate-500 text-[11px]">Acknowledged mock dispute tickets.</p>
        </div>
      </div>

      {/* Received Tickets Ledger */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-bold text-white">Mock Bank Inbound Submission Log</h3>
          </div>
          <span className="text-xs text-slate-500 font-mono">Endpoint: mock://apexnational.internal/disputes</span>
        </div>

        <div className="space-y-3">
          {tickets.length === 0 ? (
            <div className="py-8 text-center text-slate-500 text-xs">
              No tickets received by mock gateway yet. Go to Reversal Desk and submit an approved reversal!
            </div>
          ) : (
            tickets.map((t) => (
              <div key={t.id} className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2 text-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono font-bold text-purple-400 text-sm">{t.mock_bank_ticket_id}</span>
                    <StatusBadge status={t.status_received} />
                  </div>
                  <span className="text-slate-500 text-[11px] font-mono">
                    {new Date(t.received_at).toLocaleString()}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] text-slate-300 pt-1">
                  <div>
                    <span className="text-slate-500">Credited Amount:</span>{' '}
                    <strong className="text-emerald-400">${t.acknowledgement_payload?.credited_amount?.toFixed(2)}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500">Resolution:</span>{' '}
                    <strong className="text-slate-200">{t.acknowledgement_payload?.resolution_status}</strong>
                  </div>
                </div>

                <div className="text-[11px] text-slate-400 italic bg-slate-900/60 p-2 rounded border border-slate-800/80">
                  "{t.acknowledgement_payload?.bank_notes}"
                </div>

                <div className="text-[10px] text-slate-500 font-mono truncate">
                  Digital Signature: {t.acknowledgement_payload?.digital_signature}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
