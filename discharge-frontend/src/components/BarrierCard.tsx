import React, { useState } from 'react';
import type { ClinicalBarrier, UserRole } from '../types';
import { 
  ShieldAlert, 
  AlertCircle, 
  CheckCircle2, 
  FileText, 
  Pill, 
  FlaskConical, 
  HeartHandshake, 
  FileCheck2,
  Lock,
  UserCheck
} from 'lucide-react';

interface BarrierCardProps {
  barrier: ClinicalBarrier;
  patientId: string;
  currentUserRole: UserRole;
  currentUserName?: string;
  onResolve: (barrierId: string) => Promise<void>;
}

export const BarrierCard: React.FC<BarrierCardProps> = ({
  barrier,
  currentUserRole,
  onResolve,
}) => {
  const [resolving, setResolving] = useState(false);
  const [resolved, setResolved] = useState(!!barrier.is_resolved);

  const canResolve = currentUserRole === barrier.assigned_role || currentUserRole === 'Admin';

  const handleResolveClick = async () => {
    if (!canResolve || resolved || resolving) return;
    setResolving(true);
    try {
      if (barrier.id) {
        await onResolve(barrier.id);
        setResolved(true);
      }
    } catch (err) {
      console.error('Failed to resolve barrier:', err);
    } finally {
      setResolving(false);
    }
  };

  // Source Field Citation Icon & Label
  const getSourceCitation = (sourceField: string) => {
    let icon = <FileText className="w-3.5 h-3.5" />;
    let bgStyle = 'bg-cyan-950/80 text-cyan-300 border-cyan-700/60';

    switch (sourceField) {
      case 'lab_summary':
        icon = <FlaskConical className="w-3.5 h-3.5 text-purple-400" />;
        bgStyle = 'bg-purple-950/90 text-purple-200 border-purple-700/80 shadow-purple-900/30';
        break;
      case 'medications':
        icon = <Pill className="w-3.5 h-3.5 text-emerald-400" />;
        bgStyle = 'bg-emerald-950/90 text-emerald-200 border-emerald-700/80 shadow-emerald-900/30';
        break;
      case 'caregiver_notes':
        icon = <HeartHandshake className="w-3.5 h-3.5 text-amber-400" />;
        bgStyle = 'bg-amber-950/90 text-amber-200 border-amber-700/80 shadow-amber-900/30';
        break;
      case 'insurance_notes':
        icon = <FileCheck2 className="w-3.5 h-3.5 text-blue-400" />;
        bgStyle = 'bg-blue-950/90 text-blue-200 border-blue-700/80 shadow-blue-900/30';
        break;
      case 'clinical_note':
      default:
        icon = <FileText className="w-3.5 h-3.5 text-teal-400" />;
        bgStyle = 'bg-teal-950/90 text-teal-200 border-teal-700/80 shadow-teal-900/30';
        break;
    }

    return (
      <div 
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md border text-xs font-mono font-semibold tracking-wide shadow-sm ${bgStyle}`}
        title={`Source Record Citation: Extracted directly from ${sourceField}`}
      >
        {icon}
        <span>— from {sourceField}</span>
      </div>
    );
  };

  // Severity Badge
  const getSeverityBadge = () => {
    switch (barrier.severity) {
      case 'Critical':
        return (
          <span className="inline-flex items-center gap-1 bg-rose-950/90 text-rose-300 border border-rose-700 px-2.5 py-0.5 rounded-md text-[11px] font-bold uppercase tracking-wider animate-pulse">
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
            Critical Barrier
          </span>
        );
      case 'Moderate':
        return (
          <span className="inline-flex items-center gap-1 bg-amber-950/90 text-amber-300 border border-amber-700 px-2.5 py-0.5 rounded-md text-[11px] font-bold uppercase tracking-wider">
            <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
            Moderate Barrier
          </span>
        );
      case 'Minor':
        return (
          <span className="inline-flex items-center gap-1 bg-slate-800 text-slate-300 border border-slate-700 px-2.5 py-0.5 rounded-md text-[11px] font-semibold uppercase tracking-wider">
            Minor Barrier
          </span>
        );
    }
  };

  // Role Badge
  const getRoleTag = (role: UserRole) => {
    return (
      <span className="inline-flex items-center gap-1 bg-slate-800/90 text-slate-200 border border-slate-700 px-2.5 py-0.5 rounded-md text-xs font-medium">
        <UserCheck className="w-3.5 h-3.5 text-teal-400" />
        {role.replace('_', ' ')}
      </span>
    );
  };

  return (
    <div
      className={`rounded-xl border p-4 transition-all duration-200 shadow-md ${
        resolved
          ? 'bg-slate-900/50 border-slate-800/80 opacity-75'
          : barrier.severity === 'Critical'
          ? 'bg-slate-900 border-rose-600/80 ring-1 ring-rose-500/20 shadow-rose-950/20'
          : barrier.severity === 'Moderate'
          ? 'bg-slate-900 border-amber-600/60'
          : 'bg-slate-900 border-slate-800'
      }`}
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex flex-wrap items-center gap-2">
          {getSeverityBadge()}
          {getRoleTag(barrier.assigned_role)}
          {resolved && (
            <span className="inline-flex items-center gap-1 bg-emerald-950 text-emerald-300 border border-emerald-800 px-2.5 py-0.5 rounded-md text-[11px] font-bold uppercase">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              Resolved
            </span>
          )}
        </div>

        {/* UNMISTAKABLE CITATION LABEL */}
        <div className="self-start md:self-auto">
          {getSourceCitation(barrier.source_field)}
        </div>
      </div>

      {/* Barrier Description & Required Action */}
      <div className="my-3 space-y-2">
        <div>
          <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block mb-0.5">
            Clinical Barrier
          </span>
          <p className="text-sm text-slate-100 font-medium leading-relaxed">
            {barrier.barrier_description}
          </p>
        </div>

        <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3">
          <span className="text-[11px] uppercase tracking-wider text-teal-400 font-semibold block mb-1">
            Required Intervention
          </span>
          <p className="text-xs text-slate-300 font-medium">
            {barrier.required_action}
          </p>
        </div>
      </div>

      {/* Action Footer with Role-Gated Resolve Button & Tooltip */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
        <span className="text-[11px] text-slate-400">
          Assigned to: <strong className="text-slate-200">{barrier.assigned_role.replace('_', ' ')}</strong>
        </span>

        {resolved ? (
          <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1">
            <CheckCircle2 className="w-4 h-4" /> Action Verified
          </span>
        ) : (
          <div className="relative group">
            <button
              onClick={handleResolveClick}
              disabled={!canResolve || resolving}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                canResolve
                  ? 'bg-teal-600 hover:bg-teal-500 text-white shadow-md shadow-teal-900/40 cursor-pointer active:scale-95'
                  : 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed opacity-70'
              }`}
            >
              {!canResolve && <Lock className="w-3.5 h-3.5 text-slate-400" />}
              {resolving ? 'Resolving...' : 'Resolve Barrier'}
            </button>

            {/* Explanatory Tooltip when disabled */}
            {!canResolve && (
              <div className="absolute right-0 bottom-full mb-2 hidden group-hover:block w-64 bg-slate-950 text-slate-200 border border-slate-700 text-xs rounded-lg p-2.5 shadow-2xl z-20 pointer-events-none">
                <p className="font-semibold text-rose-400 mb-0.5">Role Permission Restricted</p>
                <p className="text-[11px] text-slate-300">
                  Resolving this barrier requires the <strong className="text-teal-300">{barrier.assigned_role.replace('_', ' ')}</strong> role or Admin privileges. Your current role is <strong className="text-amber-300">{currentUserRole.replace('_', ' ')}</strong>.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
