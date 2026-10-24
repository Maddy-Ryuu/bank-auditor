import React from 'react';
import { ShieldCheck, Info } from 'lucide-react';

export const MockBankBanner: React.FC = () => {
  return (
    <div className="bg-gradient-to-r from-blue-950/80 via-indigo-950/70 to-slate-900 border-b border-blue-900/40 px-4 py-2.5 text-xs text-blue-200 flex items-center justify-between">
      <div className="flex items-center space-x-2">
        <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
        <span>
          <strong className="text-white font-semibold">Strict Mock Banking Boundary:</strong> All disputes & reversal submissions target the internal <strong>Apex National Mock Gateway</strong>. No live banking credentials or real transfers.
        </span>
      </div>
      <div className="hidden md:flex items-center space-x-2 text-slate-400">
        <Info className="w-3.5 h-3.5 text-blue-400" />
        <span>Ziro Hackathon Production Spec</span>
      </div>
    </div>
  );
};
