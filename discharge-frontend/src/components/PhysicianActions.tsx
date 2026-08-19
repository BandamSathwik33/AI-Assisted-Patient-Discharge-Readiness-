import React, { useState } from 'react';
import type { ReadinessTier, UserRole } from '../types';
import { apiClient } from '../api/client';
import { 
  FileCheck2, 
  Sliders, 
  AlertTriangle, 
  CheckCircle2, 
  X, 
  ShieldAlert,
  Stethoscope
} from 'lucide-react';

interface PhysicianActionsProps {
  patientId: string;
  patientName: string;
  currentRole: UserRole;
  currentUserName: string;
  onRefresh: () => void;
}

export const PhysicianActions: React.FC<PhysicianActionsProps> = ({
  patientId,
  patientName,
  currentRole,
  currentUserName,
  onRefresh,
}) => {
  const [signingOff, setSigningOff] = useState(false);
  const [signoffError, setSignoffError] = useState<string | null>(null);
  const [signoffSuccess, setSignoffSuccess] = useState<string | null>(null);

  // Override Modal state
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [overrideTier, setOverrideTier] = useState<ReadinessTier>('Near_Ready');
  const [rationale, setRationale] = useState('');
  const [overriding, setOverriding] = useState(false);
  const [overrideError, setOverrideError] = useState<string | null>(null);

  // Render ONLY for Physician or Admin
  if (currentRole !== 'Physician' && currentRole !== 'Admin') {
    return null;
  }

  const handleSignoff = async () => {
    setSigningOff(true);
    setSignoffError(null);
    setSignoffSuccess(null);
    try {
      const res = await apiClient.signoffDischarge(patientId, currentUserName, 'Attending Physician completed final discharge clinical verification.');
      setSignoffSuccess(res.message);
      onRefresh();
    } catch (err: any) {
      console.error('Signoff error caught:', err);
      // Catch 409 error or general error
      if (err.response?.status === 409 || err.message?.includes('409')) {
        setSignoffError(
          err.response?.data?.detail || err.message || '409 Conflict: Cannot sign off discharge while Critical clinical barriers remain unresolved!'
        );
      } else {
        setSignoffError(err.message || 'Failed to complete discharge signoff.');
      }
    } finally {
      setSigningOff(false);
    }
  };

  const handleOverrideSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rationale.trim().length < 10) return;

    setOverriding(true);
    setOverrideError(null);
    try {
      await apiClient.overrideTier(patientId, currentUserName, overrideTier, rationale);
      setShowOverrideModal(false);
      setRationale('');
      onRefresh();
    } catch (err: any) {
      setOverrideError(err.message || 'Failed to override readiness tier.');
    } finally {
      setOverriding(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2 text-teal-300 font-bold text-sm">
          <Stethoscope className="w-4 h-4 text-teal-400" />
          <span>Attending Physician Clinical Controls</span>
        </div>
        <span className="text-xs text-slate-400 font-mono">
          Authorized User: {currentUserName}
        </span>
      </div>

      {/* 409 Error Banner if signoff failed */}
      {signoffError && (
        <div className="bg-rose-950/90 border-2 border-rose-600 text-rose-100 rounded-xl p-4 flex items-start gap-3 shadow-lg animate-shake">
          <ShieldAlert className="w-6 h-6 text-rose-400 shrink-0 mt-0.5" />
          <div className="flex-1 text-xs">
            <h4 className="font-bold text-sm text-rose-200 uppercase tracking-wide mb-1">
              ⛔ Discharge Sign-Off Blocked (409 Conflict)
            </h4>
            <p className="leading-relaxed font-medium">{signoffError}</p>
            <p className="mt-2 text-[11px] text-rose-300 italic">
              Please resolve all Critical clinical barriers before approving discharge, or submit a formal Physician Readiness Override with clinical justification.
            </p>
          </div>
          <button
            onClick={() => setSignoffError(null)}
            className="text-rose-300 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Success Banner */}
      {signoffSuccess && (
        <div className="bg-emerald-950/90 border border-emerald-700 text-emerald-100 rounded-xl p-4 flex items-center gap-3 shadow-lg">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <div className="text-xs font-semibold">{signoffSuccess}</div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={handleSignoff}
          disabled={signingOff}
          className="flex-1 min-w-[200px] flex items-center justify-center gap-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs py-2.5 px-4 rounded-xl shadow-lg shadow-emerald-950/40 transition-all active:scale-95 disabled:opacity-50"
        >
          <FileCheck2 className="w-4 h-4" />
          {signingOff ? 'Processing Sign-Off...' : 'Sign Off on Discharge'}
        </button>

        <button
          onClick={() => setShowOverrideModal(true)}
          className="flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-bold text-xs py-2.5 px-4 rounded-xl shadow-md transition-all active:scale-95"
        >
          <Sliders className="w-4 h-4 text-amber-400" />
          <span>Override Readiness Tier</span>
        </button>
      </div>

      {/* Tier Override Modal */}
      {showOverrideModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-amber-400 font-bold text-base">
                <AlertTriangle className="w-5 h-5" />
                <span>Physician Readiness Tier Override</span>
              </div>
              <button
                onClick={() => setShowOverrideModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Modifying the AI readiness tier for <strong className="text-white">{patientName}</strong> overrides algorithmic decision support. A formal clinical rationale (min. 10 characters) is required for audit logging.
            </p>

            {overrideError && (
              <div className="bg-rose-950 text-rose-300 border border-rose-800 text-xs p-3 rounded-lg">
                {overrideError}
              </div>
            )}

            <form onSubmit={handleOverrideSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                  Select New Target Readiness Tier
                </label>
                <select
                  value={overrideTier}
                  onChange={(e) => setOverrideTier(e.target.value as ReadinessTier)}
                  className="w-full bg-slate-950 border border-slate-700 text-slate-100 rounded-xl p-2.5 text-xs font-semibold focus:ring-2 focus:ring-teal-500"
                >
                  <option value="Ready">Ready (Immediate Discharge)</option>
                  <option value="Near_Ready">Near Ready (Pending Minor Tasks)</option>
                  <option value="High_Risk_Blocked">High Risk — Blocked</option>
                </select>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Clinical Rationale (Required)
                  </label>
                  <span
                    className={`text-[11px] font-mono ${
                      rationale.trim().length >= 10 ? 'text-emerald-400' : 'text-amber-400'
                    }`}
                  >
                    {rationale.trim().length} / 10 min chars
                  </span>
                </div>
                <textarea
                  rows={4}
                  value={rationale}
                  onChange={(e) => setRationale(e.target.value)}
                  placeholder="Enter detailed clinical reasoning for overriding AI readiness tier..."
                  className="w-full bg-slate-950 border border-slate-700 text-slate-100 rounded-xl p-3 text-xs focus:ring-2 focus:ring-teal-500 focus:outline-none placeholder:text-slate-600"
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowOverrideModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={overriding || rationale.trim().length < 10}
                  className={`px-5 py-2 rounded-xl text-xs font-bold transition-all shadow-md ${
                    rationale.trim().length >= 10 && !overriding
                      ? 'bg-amber-600 hover:bg-amber-500 text-white cursor-pointer'
                      : 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
                  }`}
                >
                  {overriding ? 'Submitting Override...' : 'Confirm Tier Override'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
