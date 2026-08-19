import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { PriorityRankedPatient } from '../types';
import { 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  ChevronRight, 
  Search, 
  SlidersHorizontal,
  ArrowUpDown
} from 'lucide-react';

interface PriorityRankingTableProps {
  patients: PriorityRankedPatient[];
}

export const PriorityRankingTable: React.FC<PriorityRankingTableProps> = ({ patients }) => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [tierFilter, setTierFilter] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'priority' | 'score' | 'days'>('priority');

  const filteredPatients = patients
    .filter((p) => {
      const matchesSearch =
        p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.bed_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.patient_id.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesTier = tierFilter === 'ALL' || p.readiness_tier === tierFilter;
      return matchesSearch && matchesTier;
    })
    .sort((a, b) => {
      if (sortBy === 'score') return a.readiness_score - b.readiness_score;
      if (sortBy === 'days') return b.days_admitted - a.days_admitted;
      return a.priority_rank - b.priority_rank;
    });

  const getTierBadge = (tier: string) => {
    switch (tier) {
      case 'High_Risk_Blocked':
        return (
          <span className="inline-flex items-center gap-1.5 bg-rose-950/90 text-rose-300 border border-rose-800 px-2.5 py-1 rounded-md text-[11px] font-bold uppercase tracking-wider animate-pulse">
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
            High Risk — Blocked
          </span>
        );
      case 'Near_Ready':
        return (
          <span className="inline-flex items-center gap-1.5 bg-amber-950/90 text-amber-300 border border-amber-800 px-2.5 py-1 rounded-md text-[11px] font-bold uppercase tracking-wider">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            Near Ready
          </span>
        );
      case 'Ready':
        return (
          <span className="inline-flex items-center gap-1.5 bg-emerald-950/90 text-emerald-300 border border-emerald-800 px-2.5 py-1 rounded-md text-[11px] font-bold uppercase tracking-wider">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            Ready
          </span>
        );
    }
  };

  const getRiskChip = (risk: string) => {
    switch (risk) {
      case 'high':
        return <span className="text-rose-400 font-bold bg-rose-950/50 px-2 py-0.5 rounded border border-rose-800/60">High</span>;
      case 'medium':
        return <span className="text-amber-400 font-bold bg-amber-950/50 px-2 py-0.5 rounded border border-amber-800/60">Medium</span>;
      case 'low':
        return <span className="text-emerald-400 font-bold bg-emerald-950/50 px-2 py-0.5 rounded border border-emerald-800/60">Low</span>;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
      {/* Header Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
          Patient Discharge Priority Queue ({filteredPatients.length})
        </h3>

        <div className="flex flex-wrap items-center gap-2">
          {/* Search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Search patient, bed, ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-xl pl-8 pr-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-teal-500 w-44"
            />
          </div>

          {/* Filter */}
          <div className="flex items-center gap-1 bg-slate-950 border border-slate-700 rounded-xl px-2 py-1">
            <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={tierFilter}
              onChange={(e) => setTierFilter(e.target.value)}
              className="bg-transparent text-slate-200 text-xs font-medium focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Tiers</option>
              <option value="High_Risk_Blocked">High Risk Blocked</option>
              <option value="Near_Ready">Near Ready</option>
              <option value="Ready">Ready</option>
            </select>
          </div>

          {/* Sort */}
          <div className="flex items-center gap-1 bg-slate-950 border border-slate-700 rounded-xl px-2 py-1">
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="bg-transparent text-slate-200 text-xs font-medium focus:outline-none cursor-pointer"
            >
              <option value="priority">Priority Rank</option>
              <option value="score">Lowest Score</option>
              <option value="days">Length of Stay</option>
            </select>
          </div>
        </div>
      </div>

      {/* Patient Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 font-mono uppercase text-[11px]">
              <th className="py-2.5 px-3">Rank</th>
              <th className="py-2.5 px-3">Patient Name</th>
              <th className="py-2.5 px-3">Bed</th>
              <th className="py-2.5 px-3">Readiness Tier</th>
              <th className="py-2.5 px-3 text-center">Score</th>
              <th className="py-2.5 px-3">Readmission Risk</th>
              <th className="py-2.5 px-3">Days Admitted</th>
              <th className="py-2.5 px-3">Attending MD</th>
              <th className="py-2.5 px-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filteredPatients.map((patient) => (
              <tr
                key={patient.patient_id}
                onClick={() => navigate(`/patients/${patient.patient_id}`)}
                className="hover:bg-slate-800/60 transition-colors cursor-pointer group"
              >
                <td className="py-3 px-3 font-mono font-bold text-slate-400">
                  #{patient.priority_rank}
                </td>
                <td className="py-3 px-3 font-bold text-white group-hover:text-teal-300 transition-colors">
                  {patient.name}
                  <span className="block text-[10px] text-slate-500 font-mono font-normal">
                    {patient.patient_id}
                  </span>
                </td>
                <td className="py-3 px-3 font-mono font-semibold text-slate-300">
                  {patient.bed_number}
                </td>
                <td className="py-3 px-3">{getTierBadge(patient.readiness_tier)}</td>
                <td className="py-3 px-3 text-center">
                  <span
                    className={`font-mono font-extrabold text-sm px-2 py-0.5 rounded ${
                      patient.readiness_score >= 85
                        ? 'text-emerald-400 bg-emerald-950/40'
                        : patient.readiness_score >= 60
                        ? 'text-amber-400 bg-amber-950/40'
                        : 'text-rose-400 bg-rose-950/40'
                    }`}
                  >
                    {patient.readiness_score}
                  </span>
                </td>
                <td className="py-3 px-3">{getRiskChip(patient.readmission_risk)}</td>
                <td className="py-3 px-3 font-mono text-slate-300">
                  {patient.days_admitted} days
                </td>
                <td className="py-3 px-3 text-slate-300 font-medium">
                  {patient.attending_md}
                </td>
                <td className="py-3 px-3 text-right">
                  <button className="p-1.5 rounded-lg bg-slate-800 text-slate-400 group-hover:bg-teal-600 group-hover:text-white transition-all">
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
