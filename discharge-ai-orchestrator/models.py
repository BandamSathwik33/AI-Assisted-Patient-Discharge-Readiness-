"""
Pydantic V2 models defining the strict team-wide JSON contracts for the
AI Orchestrator service in the AI-Assisted Patient Discharge Readiness system.
"""

from typing import List, Literal, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator


# --- Literal Types strictly matching Section 0.4 team contract ---
BarrierCategory = Literal["Clinical", "Medication", "Caregiver_SDOH", "Administrative"]
BarrierSeverity = Literal["Critical", "Moderate", "Minor"]
AssignedRole = Literal["Physician", "Nurse", "Pharmacist", "Case_Manager"]
SourceField = Literal["clinical_note", "medications", "lab_summary", "caregiver_notes", "insurance_notes"]
ReadinessTier = Literal["Ready", "Near_Ready", "High_Risk_Blocked"]
ReadmissionRisk = Literal["low", "medium", "high"]
RecommendationPriority = Literal["Mandatory", "Recommended"]


# --- Output Sub-Models ---

class ClinicalBarrier(BaseModel):
    """
    Represents an identified discharge barrier traceable to a specific source field.
    'source_field' is the citation wow-factor for the clinical dashboard.
    """
    category: BarrierCategory = Field(
        ...,
        description="Barrier domain: Clinical, Medication, Caregiver_SDOH, or Administrative"
    )
    barrier_description: str = Field(
        ...,
        description="Concise, clinically clear description of the blocking issue"
    )
    severity: BarrierSeverity = Field(
        ...,
        description="Severity level: Critical (-40 pts), Moderate (-15 pts), or Minor (-5 pts)"
    )
    required_action: str = Field(
        ...,
        description="Concrete, actionable step required to clear this barrier"
    )
    assigned_role: AssignedRole = Field(
        ...,
        description="Care team role authorized to resolve this barrier"
    )
    source_field: SourceField = Field(
        ...,
        description="Specific source data field containing the evidence for this barrier"
    )


class FollowUpRecommendation(BaseModel):
    """Post-discharge clinical follow-up appointment or test."""
    timeframe_days: int = Field(
        ...,
        ge=0,
        description="Recommended number of days post-discharge for follow-up"
    )
    specialty: str = Field(
        ...,
        description="Medical specialty or service (e.g. Cardiology, Primary Care, Wound Care)"
    )
    priority: RecommendationPriority = Field(
        ...,
        description="Mandatory (required for safety) or Recommended"
    )
    rationale: str = Field(
        ...,
        description="Clinical explanation for why this follow-up is necessary"
    )


class PatientFriendlySummary(BaseModel):
    """
    Patient and caregiver view written at a 6th-grade reading level.
    Calm, clear, and actionable.
    """
    reading_grade_level: str = Field(
        default="6th Grade",
        description="Reading grade level benchmark (fixed at '6th Grade')"
    )
    medication_schedule: str = Field(
        ...,
        description="Simple, jargon-free instructions on when and how to take medicines"
    )
    red_flag_warning_signs: List[str] = Field(
        ...,
        description="Concrete, urgent symptoms that require contacting a doctor or 911"
    )
    next_appointment_notes: str = Field(
        ...,
        description="Clear summary of upcoming appointments and what to bring"
    )


class DischargeReadinessEvaluation(BaseModel):
    """
    The canonical team contract object produced by the AI Orchestrator
    and validated by the Core Backend API.
    """
    patient_id: str = Field(
        ...,
        description="Unique patient identifier, e.g. P-1001"
    )
    readiness_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Deterministic score 0-100 (100 - 40*Crit - 15*Mod - 5*Min floored at 0)"
    )
    readiness_tier: ReadinessTier = Field(
        ...,
        description="Ready, Near_Ready, or High_Risk_Blocked (forced if any Critical barrier exists)"
    )
    estimated_ready_time: str = Field(
        ...,
        description="'now' | 'within_4h' | 'by_tomorrow_am' | ISO timestamp"
    )
    clinical_barriers: List[ClinicalBarrier] = Field(
        default_factory=list,
        description="List of all barriers identified by category agents"
    )
    follow_up_recommendations: List[FollowUpRecommendation] = Field(
        default_factory=list,
        description="List of post-discharge appointments and follow-up milestones"
    )
    readmission_risk: ReadmissionRisk = Field(
        ...,
        description="Overall readmission risk classification: low, medium, or high"
    )
    readmission_risk_reason: str = Field(
        ...,
        description="One-line clinical rationale for the assigned readmission risk"
    )
    patient_friendly_summary: PatientFriendlySummary = Field(
        ...,
        description="Patient & caregiver facing discharge instructions"
    )


# --- Input Request Models ---

class ConditionItem(BaseModel):
    name: str
    icd10_hint: Optional[str] = None


class MedicationItem(BaseModel):
    name: str
    dose: Optional[str] = None
    frequency: Optional[str] = None
    access_flag: Optional[str] = None


class StructuredClinicalData(BaseModel):
    conditions: List[Union[ConditionItem, Dict[str, Any], str]] = Field(default_factory=list)
    medications: List[Union[MedicationItem, Dict[str, Any], str]] = Field(default_factory=list)
    vitals_summary: Optional[str] = ""
    labs_pending: List[str] = Field(default_factory=list)
    deidentified_text: Optional[str] = None


class RawContext(BaseModel):
    admission_notes: Optional[str] = ""
    medication_list: Optional[str] = ""
    lab_summary: Optional[str] = ""
    caregiver_notes: Optional[str] = ""
    insurance_notes: Optional[str] = ""
    days_admitted: Optional[int] = 0


class EvaluateRequest(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier")
    structured_clinical_data: StructuredClinicalData = Field(
        default_factory=StructuredClinicalData,
        description="Extracted entities from NLP Service"
    )
    raw_context: RawContext = Field(
        default_factory=RawContext,
        description="Raw EHR text notes for grounding"
    )


# --- Internal Sub-Agent Tool Call Models ---

class SubAgentBarrierItem(BaseModel):
    barrier_description: str = Field(..., description="Specific description of the barrier")
    severity: BarrierSeverity = Field(..., description="Critical, Moderate, or Minor")
    required_action: str = Field(..., description="Action needed to clear this barrier")
    assigned_role: AssignedRole = Field(..., description="Care team role that can clear this")
    source_field_hint: Optional[str] = Field(
        None,
        description="Optional hint for source field (e.g. lab_summary vs clinical_note)"
    )


class ReportBarriersPayload(BaseModel):
    """Payload schema for category agent forced tool use."""
    barriers: List[SubAgentBarrierItem] = Field(
        default_factory=list,
        description="List of barriers identified in this specific category"
    )


class SynthesisPayload(BaseModel):
    """Payload schema for Synthesis Agent forced tool use."""
    follow_up_recommendations: List[FollowUpRecommendation] = Field(
        default_factory=list,
        description="Follow-up recommendations (Mandatory for critical clinical barriers)"
    )
    readmission_risk: ReadmissionRisk = Field(
        ...,
        description="Overall readmission risk: low, medium, or high"
    )
    readmission_risk_reason: str = Field(
        ...,
        description="One-sentence rationale weighing stay duration, barrier severity, and SDOH"
    )
    patient_friendly_summary: PatientFriendlySummary = Field(
        ...,
        description="6th grade patient and caregiver instructions"
    )
