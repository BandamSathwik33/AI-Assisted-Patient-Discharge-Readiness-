import React from 'react';
import { RadialBarChart, RadialBar, ResponsiveContainer, PolarAngleAxis } from 'recharts';
import type { ReadinessTier } from '../types';
import { ShieldAlert, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

interface ReadinessGaugeProps {
  score: number;
  tier: ReadinessTier;
  readmissionRisk: 'low' | 'medium' | 'high';
  readmissionRiskReason: string;
  estimatedReadyTime: string;
}

export const ReadinessGauge: React.FC<ReadinessGaugeProps> = ({
  score,
  tier,
  readmissionRisk,
  readmissionRiskReason,
  estimatedReadyTime,
}) => {
  // Color configuration based on tier/score
  let chartColor = '#10b981'; // Green Ready
  if (tier === 'High_Risk_Blocked' || score < 60) {
    chartColor = '#e11d48'; // Rose Red Blocked
  } else if (tier === 'Near_Ready' || score < 85) {
    chartColor = '#f59e0b'; // Amber Near Ready
  }

  const chartData = [
    {
      name: 'Readiness',
      value: score,
      fill: chartColor,
    },
  ];

  const getTierBadge = () => {
    switch (tier) {
      case 'High_Risk_Blocked':
        return (
          <div className="inline-flex items-center gap-1.5 bg-rose-950/80 text-rose-300 border border-rose-800/80 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider shadow-sm animate-pulse">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            <span>High Risk — Blocked</span>
          </div>
        );
      case 'Near_Ready':
        return (
          <div className="inline-flex items-center gap-1.5 bg-amber-950/80 text-amber-300 border border-amber-800/80 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider shadow-sm">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span>Near Ready</span>
          </div>
        );
      case 'Ready':
        return (
          <div className="inline-flex items-center gap-1.5 bg-emerald-950/80 text-emerald-300 border border-emerald-800/80 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider shadow-sm">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            <span>Ready for Discharge</span>
          </div>
        );
    }
  };

  const getRiskChip = () => {
    switch (readmissionRisk) {
      case 'high':
        return (
          <span className="bg-rose-900/50 text-rose-300 border border-rose-700/60 text-[11px] font-semibold px-2.5 py-0.5 rounded-md">
            High Readmission Risk
          </span>
        );
      case 'medium':
        return (
          <span className="bg-amber-900/50 text-amber-300 border border-amber-700/60 text-[11px] font-semibold px-2.5 py-0.5 rounded-md">
            Moderate Readmission Risk
          </span>
        );
      case 'low':
        return (
          <span className="bg-emerald-900/50 text-emerald-300 border border-emerald-700/60 text-[11px] font-semibold px-2.5 py-0.5 rounded-md">
            Low Readmission Risk
          </span>
        );
    }
  };

  const formatEstimatedTime = (timeStr: string) => {
    if (timeStr === 'now') return 'Immediate Discharge Ready';
    if (timeStr === 'within_4h') return 'Expected within 4 Hours';
    if (timeStr === 'by_tomorrow_am') return 'Expected Tomorrow Morning';
    return timeStr;
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col items-center relative overflow-hidden">
      {/* Top Header */}
      <div className="w-full flex items-center justify-between pb-3 border-b border-slate-800">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          AI Readiness Index
        </span>
        {getTierBadge()}
      </div>

      {/* Gauge Chart */}
      <div className="relative w-48 h-48 my-2 flex items-center justify-center">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="50%"
            innerRadius="75%"
            outerRadius="100%"
            barSize={14}
            data={chartData}
            startAngle={225}
            endAngle={-45}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
            <RadialBar
              background={{ fill: '#1e293b' }}
              dataKey="value"
              cornerRadius={10}
            />
          </RadialBarChart>
        </ResponsiveContainer>

        {/* Center Score Display */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-4xl font-extrabold tracking-tight text-white font-mono">
            {score}
          </span>
          <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-widest mt-0.5">
            / 100 Score
          </span>
        </div>
      </div>

      {/* Estimated Time & Risk Reason */}
      <div className="w-full space-y-2.5 text-center mt-1">
        <div className="flex items-center justify-center gap-1.5 text-xs text-slate-300 font-medium">
          <Clock className="w-3.5 h-3.5 text-teal-400" />
          <span>Timeline: {formatEstimatedTime(estimatedReadyTime)}</span>
        </div>

        <div className="pt-2 border-t border-slate-800/80 flex flex-col items-center gap-1.5">
          <div className="flex items-center justify-center gap-2">
            {getRiskChip()}
          </div>
          <p className="text-xs text-slate-400 max-w-sm italic leading-relaxed px-2">
            "{readmissionRiskReason}"
          </p>
        </div>
      </div>
    </div>
  );
};
