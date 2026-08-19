import axios from 'axios';
import type { 
  AuthResponse, 
  User, 
  Patient, 
  PatientDetailResponse, 
  DischargeReadinessEvaluation, 
  Task, 
  AuditLogEntry, 
  HospitalOverviewResponse,
  ReadinessTier,
  UserRole
} from '../types';
import { 
  DEMO_USERS, 
  INITIAL_PATIENTS, 
  INITIAL_EVALUATIONS, 
  INITIAL_AUDIT_LOGS 
} from '../mock/mockData';

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const AUTH_BASE_URL = import.meta.env.VITE_AUTH_BASE_URL || 'http://localhost:8003';

// Axios instance for live backend fallback
const axiosClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

axiosClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('discharge_auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// In-memory stateful store for mock mode
let mockPatients: Patient[] = [...INITIAL_PATIENTS];
let mockEvaluations: Record<string, DischargeReadinessEvaluation> = JSON.parse(JSON.stringify(INITIAL_EVALUATIONS));
let mockAuditLogs: AuditLogEntry[] = [...INITIAL_AUDIT_LOGS];

// Helper delay to simulate realistic network latency
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const apiClient = {
  // Auth endpoints
  async login(username: string, password?: string): Promise<AuthResponse> {
    if (USE_MOCK) {
      await delay(400);
      const demoUser = DEMO_USERS[username] || {
        user_id: `usr_custom_${Date.now()}`,
        username: username,
        full_name: `${username.charAt(0).toUpperCase() + username.slice(1)} (Custom)`,
        role: 'Physician' as UserRole,
      };

      const authResp: AuthResponse = {
        access_token: `mock_jwt_token_${demoUser.user_id}_${Date.now()}`,
        token_type: 'Bearer',
        role: demoUser.role,
        user_id: demoUser.user_id,
        full_name: demoUser.full_name,
      };

      localStorage.setItem('discharge_auth_token', authResp.access_token);
      localStorage.setItem('discharge_user', JSON.stringify(demoUser));
      return authResp;
    } else {
      const response = await axios.post(`${AUTH_BASE_URL}/auth/login`, { username, password });
      localStorage.setItem('discharge_auth_token', response.data.access_token);
      return response.data;
    }
  },

  async getCurrentUser(): Promise<User | null> {
    if (USE_MOCK) {
      await delay(150);
      const stored = localStorage.getItem('discharge_user');
      return stored ? JSON.parse(stored) : null;
    } else {
      const response = await axios.get(`${AUTH_BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('discharge_auth_token')}` },
      });
      return response.data;
    }
  },

  // GET /patients
  async getPatients(): Promise<Array<Patient & { latest_evaluation: DischargeReadinessEvaluation | null }>> {
    if (USE_MOCK) {
      await delay(350);
      return mockPatients.map((p) => ({
        ...p,
        latest_evaluation: mockEvaluations[p.patient_id] || null,
      }));
    } else {
      const res = await axiosClient.get('/patients');
      return res.data;
    }
  },

  // GET /patients/{id}
  async getPatientDetail(id: string): Promise<PatientDetailResponse> {
    if (USE_MOCK) {
      await delay(300);
      const profile = mockPatients.find((p) => p.patient_id === id);
      if (!profile) {
        throw new Error(`Patient ${id} not found`);
      }
      const evalData = mockEvaluations[id] || null;

      // Extract tasks from evaluation clinical barriers
      const tasks: Task[] = (evalData?.clinical_barriers || []).map((b, idx) => ({
        task_id: b.id || `task_${id}_${idx}`,
        patient_id: id,
        category: b.category,
        role: b.assigned_role,
        description: b.required_action,
        is_resolved: !!b.is_resolved,
        barrier_description: b.barrier_description,
        severity: b.severity,
        source_field: b.source_field,
      }));

      return {
        profile,
        latest_evaluation: evalData,
        tasks,
      };
    } else {
      const res = await axiosClient.get(`/patients/${id}`);
      return res.data;
    }
  },

  // POST /evaluate/{id} (Simulates 5-15s AI calculation)
  async runEvaluation(id: string): Promise<DischargeReadinessEvaluation> {
    if (USE_MOCK) {
      // 6 second realistic async AI computation
      await delay(6000);
      const currentEval = mockEvaluations[id];
      if (!currentEval) {
        throw new Error(`No evaluation found for ${id}`);
      }

      // Check how many critical barriers remain resolved
      const unresolvedCritical = currentEval.clinical_barriers.filter(b => b.severity === 'Critical' && !b.is_resolved).length;
      const totalUnresolved = currentEval.clinical_barriers.filter(b => !b.is_resolved).length;

      let newScore = Math.min(100, Math.max(10, 100 - (unresolvedCritical * 30) - (totalUnresolved * 10)));
      let newTier: ReadinessTier = 'Ready';
      if (newScore < 60 || unresolvedCritical > 0) {
        newTier = 'High_Risk_Blocked';
      } else if (newScore < 85 || totalUnresolved > 0) {
        newTier = 'Near_Ready';
      }

      const updatedEval: DischargeReadinessEvaluation = {
        ...currentEval,
        readiness_score: newScore,
        readiness_tier: newTier,
        estimated_ready_time: newTier === 'Ready' ? 'now' : newTier === 'Near_Ready' ? 'within_4h' : 'by_tomorrow_am',
      };

      mockEvaluations[id] = updatedEval;

      mockAuditLogs.unshift({
        id: `log_${Date.now()}`,
        timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
        actor: 'AI Clinical Engine (v2.4)',
        action: 'Re-Evaluation Executed',
        details: `Re-calculated readiness score to ${newScore}/100 (${newTier}). ${unresolvedCritical} critical barriers remaining.`,
        patient_id: id,
      });

      return updatedEval;
    } else {
      const res = await axiosClient.post(`/evaluate/${id}`);
      return res.data;
    }
  },

  // GET /patients/{id}/tasks
  async getTasks(patientId: string): Promise<Task[]> {
    if (USE_MOCK) {
      await delay(200);
      const evalData = mockEvaluations[patientId];
      if (!evalData) return [];
      return evalData.clinical_barriers.map((b, idx) => ({
        task_id: b.id || `task_${patientId}_${idx}`,
        patient_id: patientId,
        category: b.category,
        role: b.assigned_role,
        description: b.required_action,
        is_resolved: !!b.is_resolved,
        barrier_description: b.barrier_description,
        severity: b.severity,
        source_field: b.source_field,
      }));
    } else {
      const res = await axiosClient.get(`/patients/${patientId}/tasks`);
      return res.data;
    }
  },

  // PATCH /tasks/{task_id}/resolve
  async resolveTask(taskId: string, resolvedBy: string, patientId: string): Promise<Task> {
    if (USE_MOCK) {
      await delay(400);
      const evalData = mockEvaluations[patientId];
      if (evalData) {
        const barrier = evalData.clinical_barriers.find((b) => b.id === taskId);
        if (barrier) {
          barrier.is_resolved = true;
        }

        // Recalculate score after barrier resolution
        const unresolvedCritical = evalData.clinical_barriers.filter(b => b.severity === 'Critical' && !b.is_resolved).length;
        const totalUnresolved = evalData.clinical_barriers.filter(b => !b.is_resolved).length;
        
        if (unresolvedCritical === 0 && evalData.readiness_tier === 'High_Risk_Blocked') {
          evalData.readiness_tier = totalUnresolved === 0 ? 'Ready' : 'Near_Ready';
          evalData.readiness_score = Math.max(evalData.readiness_score, totalUnresolved === 0 ? 90 : 75);
          evalData.estimated_ready_time = totalUnresolved === 0 ? 'now' : 'within_4h';
        }
      }

      mockAuditLogs.unshift({
        id: `log_${Date.now()}`,
        timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
        actor: resolvedBy,
        action: 'Clinical Barrier Resolved',
        details: `Task ID ${taskId} marked as resolved by ${resolvedBy}.`,
        patient_id: patientId,
      });

      return {
        task_id: taskId,
        patient_id: patientId,
        category: 'Clinical',
        role: 'Physician',
        description: 'Task resolved successfully',
        is_resolved: true,
        resolved_by: resolvedBy,
      };
    } else {
      const res = await axiosClient.patch(`/tasks/${taskId}/resolve`, { resolved_by: resolvedBy });
      return res.data;
    }
  },

  // POST /patients/{id}/signoff (409 Conflict if Critical barrier unresolved!)
  async signoffDischarge(patientId: string, physicianId: string, rationale?: string): Promise<{ success: boolean; message: string }> {
    if (USE_MOCK) {
      await delay(500);
      const evalData = mockEvaluations[patientId];
      
      // Check for unresolved critical barriers
      const unresolvedCriticalBarriers = evalData?.clinical_barriers.filter(
        (b) => b.severity === 'Critical' && !b.is_resolved
      ) || [];

      if (unresolvedCriticalBarriers.length > 0) {
        const barrierNames = unresolvedCriticalBarriers.map(b => `[${b.category}] ${b.barrier_description}`).join('; ');
        const error: any = new Error(`409 Conflict: Discharge signoff blocked! Patient has ${unresolvedCriticalBarriers.length} unresolved CRITICAL clinical barrier(s): ${barrierNames}`);
        error.response = {
          status: 409,
          data: {
            detail: `Discharge sign-off rejected. ${unresolvedCriticalBarriers.length} Critical barrier(s) remain unresolved.`,
            critical_barriers: unresolvedCriticalBarriers,
          },
        };
        throw error;
      }

      // If clear, update tier
      if (evalData) {
        evalData.readiness_tier = 'Ready';
        evalData.readiness_score = 100;
        evalData.estimated_ready_time = 'now';
      }

      mockAuditLogs.unshift({
        id: `log_${Date.now()}`,
        timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
        actor: physicianId,
        action: 'Physician Discharge Signoff Approved',
        details: rationale || 'Attending physician signed off on patient discharge.',
        patient_id: patientId,
      });

      return { success: true, message: 'Discharge signoff approved successfully.' };
    } else {
      const res = await axiosClient.post(`/patients/${patientId}/signoff`, { physician_id: physicianId, rationale });
      return res.data;
    }
  },

  // POST /patients/{id}/override
  async overrideTier(patientId: string, physicianId: string, newTier: ReadinessTier, rationale: string): Promise<DischargeReadinessEvaluation> {
    if (USE_MOCK) {
      await delay(450);
      if (!rationale || rationale.trim().length < 10) {
        throw new Error('Rationale is required and must be at least 10 characters.');
      }

      const evalData = mockEvaluations[patientId];
      if (!evalData) {
        throw new Error(`Patient evaluation ${patientId} not found`);
      }

      evalData.readiness_tier = newTier;
      evalData.readiness_score = newTier === 'Ready' ? 95 : newTier === 'Near_Ready' ? 75 : 40;

      mockAuditLogs.unshift({
        id: `log_${Date.now()}`,
        timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
        actor: physicianId,
        action: `Physician Readiness Tier Override (${newTier})`,
        details: `Rationale: ${rationale}`,
        patient_id: patientId,
      });

      return evalData;
    } else {
      const res = await axiosClient.post(`/patients/${patientId}/override`, { physician_id: physicianId, new_tier: newTier, rationale });
      return res.data;
    }
  },

  // GET /audit-log/{id}
  async getAuditLogs(patientId: string): Promise<AuditLogEntry[]> {
    if (USE_MOCK) {
      await delay(200);
      return mockAuditLogs.filter((log) => log.patient_id === patientId);
    } else {
      const res = await axiosClient.get(`/audit-log/${patientId}`);
      return res.data;
    }
  },

  // GET /hospital-overview
  async getHospitalOverview(): Promise<HospitalOverviewResponse> {
    if (USE_MOCK) {
      await delay(400);

      const readyCount = mockPatients.filter(
        (p) => mockEvaluations[p.patient_id]?.readiness_tier === 'Ready'
      ).length;

      const expectedDischarges = mockPatients.filter(
        (p) => mockEvaluations[p.patient_id]?.estimated_ready_time === 'now' ||
               mockEvaluations[p.patient_id]?.estimated_ready_time === 'within_4h'
      ).length;

      const scores = mockPatients.map((p) => mockEvaluations[p.patient_id]?.readiness_score || 0);
      const avgScore = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);

      // Rank patients by priority: High_Risk_Blocked & lowest readiness score first
      const priorityRanking = mockPatients
        .map((p) => {
          const ev = mockEvaluations[p.patient_id];
          return {
            patient_id: p.patient_id,
            name: p.name,
            readiness_score: ev?.readiness_score || 0,
            readmission_risk: ev?.readmission_risk || 'medium',
            days_admitted: p.days_admitted,
            priority_rank: 0,
            bed_number: p.bed_number,
            readiness_tier: ev?.readiness_tier || 'Near_Ready',
            attending_md: p.attending_md,
          };
        })
        .sort((a, b) => a.readiness_score - b.readiness_score)
        .map((item, index) => ({
          ...item,
          priority_rank: index + 1,
        }));

      return {
        bed_availability: {
          total_beds: 120,
          free_now: 14,
          expected_soon: readyCount + 3,
          expected_tomorrow: 18,
        },
        summary_stats: {
          patients_tracked: mockPatients.length,
          ready_now: readyCount,
          expected_discharges_today: expectedDischarges,
          avg_readiness_score: avgScore,
        },
        priority_ranking: priorityRanking,
      };
    } else {
      const res = await axiosClient.get('/hospital-overview');
      return res.data;
    }
  },
};
