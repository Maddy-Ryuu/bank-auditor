import React, { useState, useEffect } from 'react';
import { Shield, RefreshCw, Play, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../api/client';

interface Props {
  onRefreshAll: () => void;
}

export const Navbar: React.FC<Props> = ({ onRefreshAll }) => {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [isResetting, setIsResetting] = useState(false);
  const [isRunningAudit, setIsRunningAudit] = useState(false);

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const data = await api.getHealth();
      setIsHealthy(data.status === 'online');
    } catch {
      setIsHealthy(false);
    }
  };

  const handleResetSeed = async () => {
    if (!window.confirm("Reload baseline synthetic data and re-run initial audits?")) return;
    setIsResetting(true);
    try {
      await api.resetDatabaseSeed();
      onRefreshAll();
    } catch (err: any) {
      alert(`Reset failed: ${err.message}`);
    } finally {
      setIsResetting(false);
    }
  };

  const handleRunAuditSuite = async () => {
    setIsRunningAudit(true);
    try {
      const res = await api.runAuditSuite();
      alert(`Audit Suite Complete: Discovered ${res.findings_detected_count} fee findings ($${res.potential_recovery_amount.toFixed(2)} recovery) in ${res.execution_duration_ms}ms.`);
      onRefreshAll();
    } catch (err: any) {
      alert(`Audit run failed: ${err.message}`);
    } finally {
      setIsRunningAudit(false);
    }
  };

  return (
    <header className="bg-slate-900 border-b border-slate-800 px-6 py-3.5 flex items-center justify-between sticky top-0 z-40 backdrop-blur-md bg-opacity-90">
      <div className="flex items-center space-x-3">
        <div className="bg-blue-600/20 border border-blue-500/30 p-2 rounded-lg text-blue-400">
          <Shield className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-lg font-bold text-white tracking-tight">Bank Fee Auditor</h1>
            <span className="bg-blue-900/60 text-blue-300 border border-blue-700/60 text-[10px] font-semibold px-2 py-0.5 rounded">
              v1.0.0
            </span>
          </div>
          <p className="text-xs text-slate-400">Synthetic Statement & Automated Reversal Engine</p>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        {/* API Health Pill */}
        <div className="hidden sm:flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700/80 text-xs">
          {isHealthy === true ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-slate-300">FastAPI Online</span>
            </>
          ) : isHealthy === false ? (
            <>
              <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
              <span className="text-rose-300">API Disconnected</span>
            </>
          ) : (
            <span className="text-slate-400">Connecting...</span>
          )}
        </div>

        {/* Action: Run Audit Suite */}
        <button
          onClick={handleRunAuditSuite}
          disabled={isRunningAudit}
          className="flex items-center space-x-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors shadow-sm"
          title="Run automated audit engine on all initial statements"
        >
          <Play className={`w-3.5 h-3.5 ${isRunningAudit ? 'animate-spin' : ''}`} />
          <span>{isRunningAudit ? 'Auditing...' : 'Run Audit Suite'}</span>
        </button>

        {/* Action: Reset Seed */}
        <button
          onClick={handleResetSeed}
          disabled={isResetting}
          className="flex items-center space-x-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 border border-slate-700 text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors"
          title="Reset synthetic seed accounts and statements"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isResetting ? 'animate-spin' : ''}`} />
          <span className="hidden md:inline">{isResetting ? 'Resetting...' : 'Reset Seed Data'}</span>
        </button>
      </div>
    </header>
  );
};
