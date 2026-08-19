import React from 'react';
import type { PatientFriendlySummary } from '../types';
import { AlertOctagon, Heart, Pill, CalendarCheck2, Sparkles, BookOpen } from 'lucide-react';

interface PatientCaregiverViewProps {
  summary: PatientFriendlySummary;
  patientName: string;
}

export const PatientCaregiverView: React.FC<PatientCaregiverViewProps> = ({ summary, patientName }) => {
  return (
    <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6 max-w-4xl mx-auto font-sans">
      {/* Calm, Accessible Header */}
      <div className="bg-gradient-to-r from-sky-900/60 to-slate-900 border border-sky-800/60 rounded-xl p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-sky-500/20 border border-sky-400/40 flex items-center justify-center shrink-0">
            <Heart className="w-6 h-6 text-sky-300" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white tracking-wide">
              Discharge Instructions & Home Care Plan
            </h2>
            <p className="text-sm text-sky-200 font-medium">
              Prepared specifically for <strong className="text-white">{patientName}</strong> and family caregivers.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 bg-slate-900/90 border border-sky-700/50 px-3 py-1.5 rounded-lg text-xs text-sky-300 font-mono">
          <BookOpen className="w-4 h-4 text-sky-400" />
          <span>Reading Level: <strong>{summary.reading_grade_level}</strong></span>
        </div>
      </div>

      {/* SINGLE MOST SAFETY-CRITICAL SURFACE: RED FLAG WARNING SIGNS */}
      <div className="bg-rose-950/90 border-2 border-rose-600 rounded-2xl p-6 shadow-2xl shadow-rose-950/50 relative overflow-hidden animate-pulse-slow">
        <div className="flex items-center gap-3 pb-3 border-b border-rose-800/80 mb-4">
          <div className="w-10 h-10 rounded-lg bg-rose-600 flex items-center justify-center shadow-lg shadow-rose-900/80 shrink-0">
            <AlertOctagon className="w-6 h-6 text-white stroke-[2.5]" />
          </div>
          <div>
            <h3 className="text-lg font-black text-white uppercase tracking-wider flex items-center gap-2">
              ⚠️ RED FLAG WARNING SIGNS — CALL 911 OR YOUR DOCTOR IMMEDIATELY
            </h3>
            <p className="text-xs text-rose-200 font-medium">
              If you or your caregiver notice ANY of the following symptoms, seek immediate emergency medical care:
            </p>
          </div>
        </div>

        <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {summary.red_flag_warning_signs.map((sign, idx) => (
            <li
              key={idx}
              className="bg-rose-900/60 border border-rose-700/80 rounded-xl p-3.5 flex items-start gap-3 text-white font-bold text-sm leading-snug shadow-md"
            >
              <span className="w-6 h-6 rounded-full bg-rose-600 text-white flex items-center justify-center text-xs font-black shrink-0 mt-0.5">
                !
              </span>
              <span>{sign}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Medication Schedule */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
        <div className="flex items-center gap-2.5 text-emerald-400 font-bold text-base border-b border-slate-800 pb-2">
          <Pill className="w-5 h-5" />
          <span>Home Medication Instructions</span>
        </div>
        <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 text-slate-100 text-sm md:text-base font-medium leading-relaxed">
          {summary.medication_schedule}
        </div>
      </div>

      {/* Next Appointment Notes */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
        <div className="flex items-center gap-2.5 text-teal-400 font-bold text-base border-b border-slate-800 pb-2">
          <CalendarCheck2 className="w-5 h-5" />
          <span>Follow-Up Appointment & Contact Notes</span>
        </div>
        <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 text-slate-100 text-sm md:text-base font-medium leading-relaxed">
          {summary.next_appointment_notes}
        </div>
      </div>

      {/* Reassurance Footer */}
      <div className="text-center pt-2 text-xs text-slate-400 flex items-center justify-center gap-1.5">
        <Sparkles className="w-4 h-4 text-teal-400" />
        <span>Need help after leaving the hospital? Call the 24/7 Nurse Advice Line at (800) 555-0199.</span>
      </div>
    </div>
  );
};
