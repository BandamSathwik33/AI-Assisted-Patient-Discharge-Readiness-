from typing import List, Optional
from pydantic import BaseModel, Field


class ConditionItem(BaseModel):
    name: str = Field(..., description="Canonical clinical condition or diagnosis name")
    icd10_hint: str = Field(..., description="Plausible ICD-10 diagnostic code")


class MedicationItem(BaseModel):
    name: str = Field(..., description="Medication or active substance name")
    dose: Optional[str] = Field(None, description="Extracted strength or dose, null if missing in source text")
    frequency: Optional[str] = Field(None, description="Extracted route or frequency, null if missing in source text")
    access_flag: Optional[str] = Field(None, description="Access barrier, prior authorization, or interaction note")


class ExtractEntitiesRequest(BaseModel):
    raw_note_text: str = Field(..., description="Clinical admission or progress note free text")
    medication_list_text: Optional[str] = Field(None, description="Raw medication list string")
    lab_summary_text: Optional[str] = Field(None, description="Raw laboratory findings and status string")


class ExtractEntitiesResponse(BaseModel):
    conditions: List[ConditionItem] = Field(default_factory=list, description="Extracted conditions with ICD-10 hints")
    medications: List[MedicationItem] = Field(default_factory=list, description="Extracted medications with dosage, frequency, access flags")
    vitals_summary: str = Field(..., description="Normalized or extracted vitals indicators")
    labs_pending: List[str] = Field(default_factory=list, description="Pending or unresulted diagnostic lab tests")
    deidentified_text: str = Field(..., description="Safe de-identified clinical note with PHI tokens replaced")


class SyntheticPatient(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier, e.g. P-1001")
    name: str = Field(..., description="Full patient name")
    age: int = Field(..., ge=0, le=120, description="Patient age in years")
    admission_date: str = Field(..., description="ISO 8601 admission date, e.g. 2026-08-14")
    days_admitted: int = Field(..., ge=0, description="Number of days currently admitted (1-9)")
    attending_md: str = Field(..., description="Assigned attending physician name")
    bed_number: str = Field(..., description="Assigned floor and bed number, e.g. 3-304")
    admission_notes: str = Field(..., description="Clinical admission and progress note free text")
    medication_list: str = Field(..., description="Free text medication list")
    lab_summary: str = Field(..., description="Free text laboratory findings and pending status")
    caregiver_notes: str = Field(..., description="Free text social history and caregiver availability")
    insurance_notes: str = Field(..., description="Free text insurance, prior authorization, and equipment coverage")
    scenario_type: str = Field(..., description="Internal archetype scenario label")
