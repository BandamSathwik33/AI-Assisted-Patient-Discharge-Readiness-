from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Category(str, Enum):
    CLINICAL = "Clinical"
    MEDICATION = "Medication"
    CAREGIVER_SDOH = "Caregiver_SDOH"
    ADMINISTRATIVE = "Administrative"


class Severity(str, Enum):
    CRITICAL = "Critical"
    MODERATE = "Moderate"
    MINOR = "Minor"


class AssignedRole(str, Enum):
    PHYSICIAN = "Physician"
    NURSE = "Nurse"
    PHARMACIST = "Pharmacist"
    CASE_MANAGER = "Case_Manager"


class SourceField(str, Enum):
    CLINICAL_NOTE = "clinical_note"
    MEDICATIONS = "medications"
    LAB_SUMMARY = "lab_summary"
    CAREGIVER_NOTES = "caregiver_notes"
    INSURANCE_NOTES = "insurance_notes"


class ReadinessTier(str, Enum):
    READY = "Ready"
    NEAR_READY = "Near_Ready"
    HIGH_RISK_BLOCKED = "High_Risk_Blocked"
    NOT_EVALUATED = "Not_Evaluated"  # backend-internal only; never returned by the AI


class ReadmissionRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FollowUpPriority(str, Enum):
    MANDATORY = "Mandatory"
    RECOMMENDED = "Recommended"


class ClinicalBarrier(BaseModel):
    category: Category
    barrier_description: str
    severity: Severity
    required_action: str
    assigned_role: AssignedRole
    source_field: SourceField


class FollowUpRecommendation(BaseModel):
    timeframe_days: int
    specialty: str
    priority: FollowUpPriority
    rationale: str


class PatientFriendlySummary(BaseModel):
    reading_grade_level: str = "6th Grade"
    medication_schedule: str
    red_flag_warning_signs: List[str] = Field(default_factory=list)
    next_appointment_notes: str


class DischargeReadinessEvaluation(BaseModel):
    """The team-wide contract (Section 0.4). Field names are fixed -- do not rename."""

    patient_id: str
    readiness_score: int = Field(ge=0, le=100)
    readiness_tier: ReadinessTier
    estimated_ready_time: str  # "now" | "within_4h" | "by_tomorrow_am" | ISO timestamp
    clinical_barriers: List[ClinicalBarrier] = Field(default_factory=list)
    follow_up_recommendations: List[FollowUpRecommendation] = Field(default_factory=list)
    readmission_risk: ReadmissionRisk
    readmission_risk_reason: str
    patient_friendly_summary: PatientFriendlySummary


class PatientCreate(BaseModel):
    patient_id: str
    name: str
    age: int
    admission_date: str
    attending_md: str
    bed_number: str
    days_admitted: int
    admission_notes: str
    medication_list: str
    lab_summary: str
    caregiver_notes: str
    insurance_notes: str


class TaskResolveRequest(BaseModel):
    resolved_by: str


class SignoffRequest(BaseModel):
    physician_id: str
    rationale: Optional[str] = None


class OverrideRequest(BaseModel):
    physician_id: str
    new_tier: ReadinessTier
    rationale: str = Field(min_length=10)
