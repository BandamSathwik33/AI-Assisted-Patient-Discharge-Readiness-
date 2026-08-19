import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../api/client';
import type { PatientDetailResponse, AuditLogEntry } from '../types';
import { SafetyBanner } from '../components/SafetyBanner';
import { ReadinessGauge } from '../components/ReadinessGauge';
import { BarrierCard } from '../components/BarrierCard';
import { FollowUpList } from '../components/FollowUpList';
import { PatientCaregiverView } from '../components/PatientCaregiverView';
import { PhysicianActions } from '../components/PhysicianActions';
import { AuditLogList } from '../components/AuditLogList';
import { 
  ArrowLeft, 
  Sparkles, 
  RotateCw, 
  ShieldCheck, 
  Calendar, 
  Bed, 
  Clock, 
  Stethoscope, 
  FileText,
  HeartPulse,
  History,
  Layers
} from 'lucide-react';

export const PatientDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();

  const [detail, setDetail] = useState<PatientDetailResponse | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [activeTab, setActiveTab] = useState<'barriers' | 'followup' | 'patient_view' | 'audit'>('barriers');

  const fetchPatientDetail = async () => {
    if (!id) return;
    try {
      const data = await apiClient.getPatientDetail(id);
      setDetail(data);
      const logs = await apiClient.getAuditLogs(id);
      setAuditLogs(logs);
    } catch (err) {
      console.error('Error loading patient detail:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatientDetail();
  }, [id]);

  const handleRunEvaluation = async () => {
    if (!id || evaluating) return;
    setEvaluating(true);
    try {
      await apiClient.runEvaluation(id);
      await fetchPatientDetail();
    } catch (err) {
      console.error('Error running evaluation:', err);
    } finally {
      setEvaluating(false);
    }
  };

  const handleResolveBarrier = async (barrierId: string) => {
    if (!id || !user) return;
    await apiClient.resolveTask(barrierId, user.full_name, id);
    await fetchPatientDetail();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-8">
        <div className="flex items-center gap-3 text-teal-400 font-mono text-sm">
          <RotateCw className="w-5 h-5 animate-spin" />
          <span>Fetching Clinical Evaluation & Barriers...</span>
        </div>
      </div>
    );
  }

  if (!detail || !detail.profile) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-8 text-center space-y-4">
        <h2 className="text-xl font-bold text-rose-400">Patient Record Not Found</h2>
        <Link to="/overview" className="text-xs text-teal-400 hover:underline">
          Return to Hospital Overview
        </Link>
      </div>
    );
  }

  const { profile, latest_evaluation } = detail;
  const currentRole = user?.role || 'Physician';
  const currentUserName = user?.full_name || 'Dr. Arthur Smith';

  // Group barriers by category
  const groupedBarriers: Record<string, NonNullable<typeof latest_evaluation>['clinical_barriers']> = {
    Clinical: [],
    Medication: [],
    Caregiver_SDOH: [],
    Administrative: [],
  };

  if (latest_evaluation?.clinical_barriers) {
    latest_evaluation.clinical_barriers.forEach((barrier) => {
      if (!groupedBarriers[barrier.category]) {
        groupedBarriers[barrier.category] = [];
      }
      groupedBarriers[barrier.category].push(barrier);
    });
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pb-12">
      {/* Dynamic Clinical Decision Support Safety Banner */}
      <SafetyBanner isPatientView={activeTab === 'patient_view'} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-6">
        {/* Navigation Back Link & Patient Demographics Header */}
        <div className="space-y-4">
          <Link
            to="/overview"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-teal-400 font-medium transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Hospital Queue</span>
          </Link>

          {/* Patient Header Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-xl flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                  {profile.name}
                </h1>
                <span className="bg-slate-800 text-teal-300 font-mono text-xs px-2.5 py-1 rounded-md border border-slate-700 font-bold">
                  {profile.patient_id}
                </span>
                {profile.primary_diagnosis && (
                  <span className="bg-sky-950 text-sky-200 border border-sky-800 text-xs px-2.5 py-1 rounded-md font-semibold">
                    {profile.primary_diagnosis}
                  </span>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-slate-400 font-medium pt-1">
                <span className="flex items-center gap-1.5">
                  <Bed className="w-4 h-4 text-teal-400" /> Bed: <strong className="text-slate-200 font-mono">{profile.bed_number}</strong>
                </span>
                <span className="flex items-center gap-1.5">
                  <Stethoscope className="w-4 h-4 text-teal-400" /> Attending: <strong className="text-slate-200">{profile.attending_md}</strong>
                </span>
                <span className="flex items-center gap-1.5">
                  <Calendar className="w-4 h-4 text-teal-400" /> Admitted: <strong className="text-slate-200 font-mono">{profile.admission_date}</strong>
                </span>
                <span className="flex items-center gap-1.5">
                  <Clock className="w-4 h-4 text-teal-400" /> Length of Stay: <strong className="text-slate-200 font-mono">{profile.days_admitted} Days</strong>
                </span>
              </div>
            </div>

            {/* Run New AI Evaluation Button (Simulates 5-15s AI Run) */}
            <div className="shrink-0 flex flex-col items-end gap-1.5">
              <button
                onClick={handleRunEvaluation}
                disabled={evaluating}
                className="w-full sm:w-auto flex items-center justify-center gap-2 bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 text-white font-bold text-xs py-3 px-5 rounded-xl shadow-lg shadow-teal-950/50 transition-all active:scale-95 disabled:opacity-60"
              >
                <Sparkles className={`w-4 h-4 text-amber-300 ${evaluating ? 'animate-spin' : ''}`} />
                <span>{evaluating ? 'Analyzing Medical Record (AI Evaluating...)' : 'Run New AI Evaluation'}</span>
              </button>
              {evaluating && (
                <p className="text-[11px] text-teal-300 font-mono animate-pulse">
                  Extracting labs, notes & pharmacy records (non-blocking)...
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-slate-800 flex items-center gap-2 overflow-x-auto">
          <button
            onClick={() => setActiveTab('barriers')}
            className={`flex items-center gap-2 px-4 py-3 text-xs font-bold border-b-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'barriers'
                ? 'border-teal-500 text-teal-400 bg-slate-900/60 rounded-t-xl'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Readiness & Clinical Barriers</span>
          </button>

          <button
            onClick={() => setActiveTab('followup')}
            className={`flex items-center gap-2 px-4 py-3 text-xs font-bold border-b-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'followup'
                ? 'border-teal-500 text-teal-400 bg-slate-900/60 rounded-t-xl'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Follow-Up Recommendations</span>
          </button>

          <button
            onClick={() => setActiveTab('patient_view')}
            className={`flex items-center gap-2 px-4 py-3 text-xs font-bold border-b-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'patient_view'
                ? 'border-sky-400 text-sky-300 bg-sky-950/40 rounded-t-xl'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <HeartPulse className="w-4 h-4 text-sky-400" />
            <span>Patient & Caregiver Summary</span>
          </button>

          <button
            onClick={() => setActiveTab('audit')}
            className={`flex items-center gap-2 px-4 py-3 text-xs font-bold border-b-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'audit'
                ? 'border-teal-500 text-teal-400 bg-slate-900/60 rounded-t-xl'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <History className="w-4 h-4" />
            <span>Audit Trail</span>
          </button>
        </div>

        {/* TAB 1: READINESS & CLINICAL BARRIERS */}
        {activeTab === 'barriers' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Radial Gauge Widget */}
              <div className="lg:col-span-1">
                {latest_evaluation ? (
                  <ReadinessGauge
                    score={latest_evaluation.readiness_score}
                    tier={latest_evaluation.readiness_tier}
                    readmissionRisk={latest_evaluation.readmission_risk}
                    readmissionRiskReason={latest_evaluation.readmission_risk_reason}
                    estimatedReadyTime={latest_evaluation.estimated_ready_time}
                  />
                ) : (
                  <div className="bg-slate-900 p-6 rounded-2xl text-center text-slate-500 text-xs">
                    No evaluation data available.
                  </div>
                )}
              </div>

              {/* Physician Controls & Role Actions */}
              <div className="lg:col-span-2 space-y-4">
                <PhysicianActions
                  patientId={profile.patient_id}
                  patientName={profile.name}
                  currentRole={currentRole}
                  currentUserName={currentUserName}
                  onRefresh={fetchPatientDetail}
                />

                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center justify-between text-xs">
                  <span className="text-slate-400">
                    Active Demo Role: <strong className="text-teal-300 font-mono">{currentRole.replace('_', ' ')}</strong>
                  </span>
                  <span className="text-slate-500 italic text-[11px]">
                    Use the role selector in the top bar to switch perspectives (Physician, Nurse, Pharmacist, Case Manager).
                  </span>
                </div>
              </div>
            </div>

            {/* CLINICAL BARRIERS GROUPED BY CATEGORY */}
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-teal-400" />
                  Identified Clinical Barriers & Interventions
                </h3>
                <span className="text-xs text-slate-400 font-mono">
                  {latest_evaluation?.clinical_barriers?.length || 0} Total Barriers Found
                </span>
              </div>

              {Object.entries(groupedBarriers).map(([category, barriers]) => {
                if (!barriers || barriers.length === 0) return null;
                return (
                  <div key={category} className="space-y-3">
                    <div className="flex items-center gap-2 border-b border-slate-800 pb-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-teal-400" />
                      <h4 className="text-xs font-bold uppercase tracking-wider text-teal-300">
                        {category.replace('_', ' / ')} Category
                      </h4>
                      <span className="text-[11px] text-slate-500 font-mono">
                        ({barriers.length} barrier{barriers.length > 1 ? 's' : ''})
                      </span>
                    </div>

                    <div className="grid grid-cols-1 gap-3">
                      {barriers.map((barrier, idx) => (
                        <BarrierCard
                          key={barrier.id || idx}
                          barrier={barrier}
                          patientId={profile.patient_id}
                          currentUserRole={currentRole}
                          currentUserName={currentUserName}
                          onResolve={handleResolveBarrier}
                        />
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 2: FOLLOW-UP RECOMMENDATIONS */}
        {activeTab === 'followup' && (
          <div>
            {latest_evaluation?.follow_up_recommendations ? (
              <FollowUpList recommendations={latest_evaluation.follow_up_recommendations} />
            ) : (
              <div className="bg-slate-900 p-8 rounded-2xl text-center text-slate-500 text-xs">
                No follow-up recommendations specified.
              </div>
            )}
          </div>
        )}

        {/* TAB 3: PATIENT & CAREGIVER VIEW */}
        {activeTab === 'patient_view' && (
          <div>
            {latest_evaluation?.patient_friendly_summary ? (
              <PatientCaregiverView
                summary={latest_evaluation.patient_friendly_summary}
                patientName={profile.name}
              />
            ) : (
              <div className="bg-slate-900 p-8 rounded-2xl text-center text-slate-500 text-xs">
                No patient summary available.
              </div>
            )}
          </div>
        )}

        {/* TAB 4: AUDIT TRAIL */}
        {activeTab === 'audit' && (
          <div>
            <AuditLogList logs={auditLogs} />
          </div>
        )}
      </main>
    </div>
  );
};
