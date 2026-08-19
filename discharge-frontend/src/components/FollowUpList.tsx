import React from 'react';
import type { FollowUpRecommendation } from '../types';
import { Calendar, ShieldAlert, CheckCircle, Clock } from 'lucide-react';

interface FollowUpListProps {
  recommendations: FollowUpRecommendation[];
}

export const FollowUpList: React.FC<FollowUpListProps> = ({ recommendations }) => {
  // Sorted by timeframe_days
  const sorted = [...recommendations].sort((a, b) => a.timeframe_days - b.timeframe_days);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <Calendar className="w-4 h-4 text-teal-400" />
          Outpatient Follow-Up Care Plan
        </h3>
        <span className="text-xs text-slate-400 font-mono">
          {sorted.length} Scheduled Interventions
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {sorted.map((rec, idx) => {
          const isMandatory = rec.priority === 'Mandatory';
          return (
            <div
              key={idx}
              className={`rounded-xl border p-4 transition-all shadow-md relative overflow-hidden ${
                isMandatory
                  ? 'bg-slate-900 border-teal-500/80 shadow-teal-950/20'
                  : 'bg-slate-900/80 border-slate-800'
              }`}
            >
              {/* Mandatory Indicator Line */}
              {isMandatory && (
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-teal-500 to-emerald-400" />
              )}

              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="bg-slate-800 text-teal-300 font-mono text-xs font-bold px-2.5 py-1 rounded-md border border-slate-700 flex items-center gap-1">
                    <Clock className="w-3 h-3 text-teal-400" />
                    Within {rec.timeframe_days} Day{rec.timeframe_days > 1 ? 's' : ''}
                  </span>
                  <span className="text-sm font-bold text-white">{rec.specialty}</span>
                </div>

                {isMandatory ? (
                  <span className="inline-flex items-center gap-1 bg-rose-950 text-rose-300 border border-rose-800 text-[11px] font-bold uppercase px-2 py-0.5 rounded">
                    <ShieldAlert className="w-3 h-3 text-rose-400" />
                    Mandatory
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 bg-slate-800 text-slate-300 border border-slate-700 text-[11px] font-semibold uppercase px-2 py-0.5 rounded">
                    <CheckCircle className="w-3 h-3 text-slate-400" />
                    Recommended
                  </span>
                )}
              </div>

              <p className="text-xs text-slate-300 font-medium leading-relaxed mt-2 bg-slate-950/50 p-2.5 rounded-lg border border-slate-800/80">
                <strong className="text-slate-400 text-[10px] uppercase block mb-0.5">Clinical Rationale:</strong>
                {rec.rationale}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
