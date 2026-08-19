import React, { useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import type { HospitalOverviewResponse } from '../types';
import { BedAvailabilityWidget } from '../components/BedAvailabilityWidget';
import { PriorityRankingTable } from '../components/PriorityRankingTable';
import { Users, CheckCircle, Clock, BarChart3, RefreshCw } from 'lucide-react';

export const OverviewPage: React.FC = () => {
  const [overview, setOverview] = useState<HospitalOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchOverview = async () => {
    try {
      const data = await apiClient.getHospitalOverview();
      setOverview(data);
    } catch (err) {
      console.error('Error fetching hospital overview:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchOverview();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-8">
        <div className="flex items-center gap-3 text-teal-400 font-mono text-sm">
          <RefreshCw className="w-5 h-5 animate-spin" />
          <span>Loading Operational Hospital Intelligence...</span>
        </div>
      </div>
    );
  }

  if (!overview) return null;

  const { summary_stats, bed_availability, priority_ranking } = overview;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 sm:p-6 md:p-8 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
            Hospital Operational Discharge Overview
          </h1>
          <p className="text-xs text-slate-400 font-medium">
            Real-time readiness tracking, capacity planning, and priority queue management
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="self-start md:self-auto flex items-center gap-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-semibold px-3.5 py-2 rounded-xl text-slate-200 transition-all active:scale-95"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-teal-400 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* SUMMARY STATS BAR */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {/* Patients Tracked */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center gap-4 shadow-lg">
          <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 shrink-0">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Active Inpatients Tracked
            </span>
            <span className="text-2xl font-extrabold text-white font-mono">
              {summary_stats.patients_tracked}
            </span>
          </div>
        </div>

        {/* Ready Now */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center gap-4 shadow-lg">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shrink-0">
            <CheckCircle className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Ready for Discharge Now
            </span>
            <span className="text-2xl font-extrabold text-emerald-400 font-mono">
              {summary_stats.ready_now}
            </span>
          </div>
        </div>

        {/* Expected Today */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center gap-4 shadow-lg">
          <div className="w-12 h-12 rounded-xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400 shrink-0">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Expected Today
            </span>
            <span className="text-2xl font-extrabold text-teal-300 font-mono">
              {summary_stats.expected_discharges_today}
            </span>
          </div>
        </div>

        {/* Avg Readiness Score */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center gap-4 shadow-lg">
          <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 shrink-0">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Avg Readiness Index
            </span>
            <span className="text-2xl font-extrabold text-purple-300 font-mono">
              {summary_stats.avg_readiness_score} / 100
            </span>
          </div>
        </div>
      </div>

      {/* Bed Availability Widget */}
      <BedAvailabilityWidget
        totalBeds={bed_availability.total_beds}
        freeNow={bed_availability.free_now}
        expectedSoon={bed_availability.expected_soon}
        expectedTomorrow={bed_availability.expected_tomorrow}
      />

      {/* Priority Ranking Patient Queue */}
      <PriorityRankingTable patients={priority_ranking} />
    </div>
  );
};
