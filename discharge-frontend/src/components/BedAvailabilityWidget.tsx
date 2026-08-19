import React from 'react';
import { BedDouble, CheckCircle2, Clock, CalendarDays } from 'lucide-react';

interface BedAvailabilityProps {
  totalBeds: number;
  freeNow: number;
  expectedSoon: number;
  expectedTomorrow: number;
}

export const BedAvailabilityWidget: React.FC<BedAvailabilityProps> = ({
  totalBeds,
  freeNow,
  expectedSoon,
  expectedTomorrow,
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <BedDouble className="w-4.5 h-4.5 text-teal-400" />
          Hospital Bed Capacity & Discharge Forecast
        </h3>
        <span className="text-xs text-slate-400 font-mono">
          Total Unit Beds: <strong className="text-white">{totalBeds}</strong>
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Free Now */}
        <div className="bg-gradient-to-br from-emerald-950/80 to-slate-950 border border-emerald-800/80 rounded-xl p-4 flex flex-col justify-between shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-emerald-300 uppercase tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Free Now
            </span>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
          </div>
          <div className="mt-3">
            <span className="text-3xl font-extrabold font-mono text-emerald-100">
              {freeNow}
            </span>
            <span className="text-[11px] text-emerald-300/80 block mt-0.5">
              Available immediately
            </span>
          </div>
        </div>

        {/* Expected Soon (Today) */}
        <div className="bg-gradient-to-br from-teal-950/80 to-slate-950 border border-teal-800/80 rounded-xl p-4 flex flex-col justify-between shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-teal-300 uppercase tracking-wider flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-teal-400" />
              Expected Soon
            </span>
            <span className="w-2.5 h-2.5 rounded-full bg-teal-400" />
          </div>
          <div className="mt-3">
            <span className="text-3xl font-extrabold font-mono text-teal-100">
              {expectedSoon}
            </span>
            <span className="text-[11px] text-teal-300/80 block mt-0.5">
              Pending final signoff today
            </span>
          </div>
        </div>

        {/* Expected Tomorrow */}
        <div className="bg-gradient-to-br from-sky-950/80 to-slate-950 border border-sky-800/80 rounded-xl p-4 flex flex-col justify-between shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-sky-300 uppercase tracking-wider flex items-center gap-1.5">
              <CalendarDays className="w-4 h-4 text-sky-400" />
              Expected Tomorrow
            </span>
            <span className="w-2.5 h-2.5 rounded-full bg-sky-400" />
          </div>
          <div className="mt-3">
            <span className="text-3xl font-extrabold font-mono text-sky-100">
              {expectedTomorrow}
            </span>
            <span className="text-[11px] text-sky-300/80 block mt-0.5">
              Scheduled AM discharges
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
