import React from 'react';
import {
  LayoutDashboard,
  FileSpreadsheet,
  AlertOctagon,
  FileCheck2,
  CheckCircle2,
  BookOpen,
  Building2
} from 'lucide-react';

export type TabType = 
  | 'dashboard' 
  | 'statements' 
  | 'findings' 
  | 'reversals' 
  | 'verification' 
  | 'tariffs' 
  | 'mock-bank';

interface Props {
  currentTab: TabType;
  onSelectTab: (tab: TabType) => void;
  counts: {
    findingsCount: number;
    pendingApprovalsCount: number;
    verifiedCount: number;
  };
}

export const Sidebar: React.FC<Props> = ({ currentTab, onSelectTab, counts }) => {
  const navItems = [
    { id: 'dashboard', label: 'Executive Dashboard', icon: LayoutDashboard },
    { id: 'statements', label: 'Statements & Ledgers', icon: FileSpreadsheet },
    { 
      id: 'findings', 
      label: 'Audit Findings', 
      icon: AlertOctagon, 
      badge: counts.findingsCount > 0 ? counts.findingsCount : undefined,
      badgeColor: 'bg-rose-950 text-rose-300 border-rose-800'
    },
    { 
      id: 'reversals', 
      label: 'Reversal Desk', 
      icon: FileCheck2,
      badge: counts.pendingApprovalsCount > 0 ? counts.pendingApprovalsCount : undefined,
      badgeColor: 'bg-amber-950 text-amber-300 border-amber-800'
    },
    { 
      id: 'verification', 
      label: 'Refund Verification', 
      icon: CheckCircle2,
      badge: counts.verifiedCount > 0 ? counts.verifiedCount : undefined,
      badgeColor: 'bg-emerald-950 text-emerald-300 border-emerald-800'
    },
    { id: 'tariffs', label: 'Tariff Schedules', icon: BookOpen },
    { id: 'mock-bank', label: 'Mock Bank Portal', icon: Building2 },
  ];

  return (
    <aside className="w-64 bg-slate-900/60 border-r border-slate-800 p-4 flex flex-col justify-between shrink-0 min-h-[calc(100vh-65px)]">
      <div>
        <div className="text-[11px] font-bold text-slate-400 tracking-wider uppercase px-3 mb-3">
          Compliance & Auditing
        </div>
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id as TabType)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30 font-semibold shadow-sm'
                    : 'text-slate-300 hover:bg-slate-800/80 hover:text-white border border-transparent'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge !== undefined && (
                  <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${item.badgeColor}`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl mt-6">
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
          <span>Audit Gateway: Active</span>
        </div>
        <p className="text-[11px] text-slate-400 mt-1">
          Apex National Bank API simulation is bound to localhost.
        </p>
      </div>
    </aside>
  );
};
