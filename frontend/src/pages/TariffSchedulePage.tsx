import React, { useState } from 'react';
import { BookOpen, ShieldCheck, Check, DollarSign, Calendar } from 'lucide-react';
import { AccountTier, TariffRule } from '../types';

interface Props {
  tiers: AccountTier[];
  tariffs: TariffRule[];
}

export const TariffSchedulePage: React.FC<Props> = ({ tiers, tariffs }) => {
  const [selectedTierId, setSelectedTierId] = useState<string>(tiers[0]?.id || '');

  const activeTier = tiers.find((t) => t.id === selectedTierId) || tiers[0];
  const activeTariffs = tariffs.filter((tr) => tr.tier_id === activeTier?.id);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Published Tariff Schedules & Fee Rules</h2>
          <p className="text-xs text-slate-400 mt-1">
            Contractual fee schedules, waiver thresholds, and statutory daily caps against which audits are performed.
          </p>
        </div>

        {/* Tier Selector */}
        <div className="flex items-center space-x-2">
          {tiers.map((t) => (
            <button
              key={t.id}
              onClick={() => setSelectedTierId(t.id)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTier?.id === t.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {t.name}
            </button>
          ))}
        </div>
      </div>

      {activeTier && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Tier Overview Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <div>
              <span className="text-xs font-mono text-blue-400 font-bold">{activeTier.code}</span>
              <h3 className="text-lg font-bold text-white mt-1">{activeTier.name}</h3>
              <p className="text-xs text-slate-400 mt-1">{activeTier.description}</p>
            </div>

            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800/80 space-y-3 text-xs">
              <div className="flex justify-between items-center pb-2 border-b border-slate-800/80">
                <span className="text-slate-400">Monthly Service Charge:</span>
                <span className="font-bold text-white">${activeTier.monthly_maintenance_fee.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-slate-800/80">
                <span className="text-slate-400">Min ADB Balance Waiver:</span>
                <span className="font-bold text-emerald-400">${activeTier.min_balance_waiver.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-slate-800/80">
                <span className="text-slate-400">Min Direct Deposit Waiver:</span>
                <span className="font-bold text-emerald-400">${activeTier.min_direct_deposit_waiver.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-slate-800/80">
                <span className="text-slate-400">Overdraft Fee / Item:</span>
                <span className="font-bold text-amber-400">${activeTier.overdraft_fee_amount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-slate-800/80">
                <span className="text-slate-400">Daily Max Overdraft Cap:</span>
                <span className="font-bold text-white">{activeTier.max_daily_overdraft_fees} fees/day</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-slate-800/80">
                <span className="text-slate-400">Overdraft De Minimis Buffer:</span>
                <span className="font-bold text-white">${(activeTier.overdraft_threshold_cents / 100).toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Incoming Domestic Wire:</span>
                <span className="font-bold text-white">
                  {activeTier.wire_incoming_domestic_fee === 0 ? 'FREE ($0.00)' : `$${activeTier.wire_incoming_domestic_fee.toFixed(2)}`}
                </span>
              </div>
            </div>
          </div>

          {/* Published Rules for this Tier */}
          <div className="lg:col-span-2 space-y-4">
            <h3 className="text-base font-bold text-white">Audit Rule Specs for {activeTier.name}</h3>

            <div className="space-y-3">
              {activeTariffs.length === 0 ? (
                <div className="p-8 text-center bg-slate-900 border border-slate-800 rounded-xl text-slate-500 text-xs">
                  No specific JSON rules registered for this tier. Tier baseline standards apply.
                </div>
              ) : (
                activeTariffs.map((tr) => (
                  <div
                    key={tr.id}
                    className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2 text-xs shadow-md"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <BookOpen className="w-4 h-4 text-blue-400" />
                        <span className="font-bold text-white">{tr.fee_name}</span>
                      </div>
                      <span className="font-mono text-xs text-amber-400 font-bold">
                        ${tr.standard_amount.toFixed(2)}
                      </span>
                    </div>

                    <div className="text-[11px] text-slate-400 flex items-center space-x-3">
                      <span>Category: <strong className="text-slate-300">{tr.fee_category}</strong></span>
                      <span>•</span>
                      <span>Effective: {tr.effective_from}</span>
                      <span>•</span>
                      <span className="italic">{tr.source_document_ref}</span>
                    </div>

                    <div className="mt-2 p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-[11px] font-mono text-slate-300">
                      Condition Logic: {JSON.stringify(tr.condition_logic)}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
