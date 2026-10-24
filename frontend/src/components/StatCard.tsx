import React from 'react';
import { LucideIcon } from 'lucide-react';

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  variant?: 'blue' | 'emerald' | 'amber' | 'purple' | 'slate';
}

export const StatCard: React.FC<Props> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'blue'
}) => {
  const colorMap = {
    blue: 'border-blue-800/40 bg-gradient-to-br from-slate-900 to-blue-950/40 text-blue-400',
    emerald: 'border-emerald-800/40 bg-gradient-to-br from-slate-900 to-emerald-950/40 text-emerald-400',
    amber: 'border-amber-800/40 bg-gradient-to-br from-slate-900 to-amber-950/40 text-amber-400',
    purple: 'border-purple-800/40 bg-gradient-to-br from-slate-900 to-purple-950/40 text-purple-400',
    slate: 'border-slate-800 bg-slate-900 text-slate-400',
  };

  return (
    <div className={`p-5 rounded-xl border backdrop-blur-sm transition-all hover:border-slate-700 shadow-lg ${colorMap[variant]}`}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-400">{title}</span>
        <div className="p-2.5 rounded-lg bg-slate-800/70 text-slate-200">
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <div className="mt-4">
        <div className="text-2xl font-bold tracking-tight text-white">{value}</div>
        {subtitle && (
          <p className="mt-1 text-xs text-slate-400 truncate">{subtitle}</p>
        )}
      </div>
    </div>
  );
};
