import React from 'react';
import type { AuditLogEntry } from '../types';
import { History, UserCheck, Cpu, Clock } from 'lucide-react';

interface AuditLogListProps {
  logs: AuditLogEntry[];
}

export const AuditLogList: React.FC<AuditLogListProps> = ({ logs }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <History className="w-4 h-4 text-teal-400" />
          Clinical Audit Trail & Log History
        </h3>
        <span className="text-xs text-slate-400 font-mono">
          {logs.length} Audit Events Recorded
        </span>
      </div>

      {logs.length === 0 ? (
        <div className="text-center py-8 text-slate-500 text-xs font-mono">
          No audit log entries recorded yet.
        </div>
      ) : (
        <div className="space-y-3">
          {logs.map((log) => {
            const isAI = log.actor.toLowerCase().includes('ai');
            return (
              <div
                key={log.id}
                className="bg-slate-950 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs shadow-sm hover:border-slate-700 transition-colors"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-flex items-center gap-1 font-semibold px-2 py-0.5 rounded text-[11px] ${
                        isAI
                          ? 'bg-teal-950 text-teal-300 border border-teal-800'
                          : 'bg-blue-950 text-blue-300 border border-blue-800'
                      }`}
                    >
                      {isAI ? <Cpu className="w-3 h-3 text-teal-400" /> : <UserCheck className="w-3 h-3 text-blue-400" />}
                      {log.actor}
                    </span>
                    <span className="font-bold text-slate-200">{log.action}</span>
                  </div>
                  <p className="text-slate-300 font-medium pl-1 leading-relaxed">
                    {log.details}
                  </p>
                </div>

                <div className="flex items-center gap-1 text-slate-400 font-mono text-[11px] shrink-0 self-end md:self-auto">
                  <Clock className="w-3 h-3 text-slate-500" />
                  <span>{log.timestamp}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
