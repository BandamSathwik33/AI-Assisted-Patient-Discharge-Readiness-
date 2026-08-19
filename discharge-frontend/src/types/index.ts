export type UserRole = 'Physician' | 'Nurse' | 'Pharmacist' | 'Case_Manager' | 'Admin';

export type ReadinessTier = 'Ready' | 'Near_Ready' | 'High_Risk_Blocked';

export type EstimatedReadyTime = 'now' | 'within_4h' | 'by_tomorrow_am' | string;

export type BarrierCategory = 'Clinical' | 'Medication' | 'Caregiver_SDOH' | 'Administrative';

export type Severity = 'Critical' | 'Moderate' | 'Minor';

export type SourceField = 'clinical_note' | 'medications' | 'lab_summary' | 'caregiver_notes' | 'insurance_notes';

export interface ClinicalBarrier {
  id?: string;
  category: BarrierCategory;
  barrier_description: string;
  severity: Severity;
  required_action: string;
  assigned_role: UserRole;
  source_field: SourceField;
  is_resolved?: boolean;
}

export interface FollowUpRecommendation {
  timeframe_days: number;
  specialty: string;
  priority: 'Mandatory' | 'Recommended';
  rationale: string;
}

export interface PatientFriendlySummary {
  reading_grade_level: string; // e.g. "6th Grade"
  medication_schedule: string;
  red_flag_warning_signs: string[];
  next_appointment_notes: string;
}

export interface DischargeReadinessEvaluation {
  patient_id: string;
  readiness_score: number; // 0-100
  readiness_tier: ReadinessTier;
  estimated_ready_time: EstimatedReadyTime;
  clinical_barriers: ClinicalBarrier[];
  follow_up_recommendations: FollowUpRecommendation[];
  readmission_risk: 'low' | 'medium' | 'high';
  readmission_risk_reason: string;
  patient_friendly_summary: PatientFriendlySummary;
}

export interface Patient {
  patient_id: string;
  name: string;
  age: number;
  admission_date: string;
  attending_md: string;
  bed_number: string;
  days_admitted: number;
  gender?: string;
  primary_diagnosis?: string;
}

export interface Task {
  task_id: string;
  patient_id: string;
  category: BarrierCategory;
  role: UserRole;
  description: string;
  is_resolved: boolean;
  resolved_by?: string;
  barrier_description?: string;
  severity?: Severity;
  source_field?: SourceField;
}

export interface PatientDetailResponse {
  profile: Patient;
  latest_evaluation: DischargeReadinessEvaluation | null;
  tasks: Task[];
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  details: string;
  patient_id: string;
}

export interface PriorityRankedPatient {
  patient_id: string;
  name: string;
  readiness_score: number;
  readmission_risk: 'low' | 'medium' | 'high';
  days_admitted: number;
  priority_rank: number;
  bed_number: string;
  readiness_tier: ReadinessTier;
  attending_md: string;
}

export interface HospitalOverviewResponse {
  bed_availability: {
    total_beds: number;
    free_now: number;
    expected_soon: number;
    expected_tomorrow: number;
  };
  summary_stats: {
    patients_tracked: number;
    ready_now: number;
    expected_discharges_today: number;
    avg_readiness_score: number;
  };
  priority_ranking: PriorityRankedPatient[];
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  role: UserRole;
  user_id: string;
  full_name: string;
}

export interface User {
  user_id: string;
  username: string;
  full_name: string;
  role: UserRole;
  token?: string;
}
