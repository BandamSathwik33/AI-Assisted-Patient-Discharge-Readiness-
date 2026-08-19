import pytest
from src.extractor import (
    extract_conditions,
    extract_medications,
    extract_vitals_summary,
    extract_pending_labs,
    deidentify_clinical_text,
    extract_all_entities,
    parse_single_medication,
)
from src.schemas import ExtractEntitiesResponse


def test_extract_conditions_matching():
    note = "Patient admitted for severe sepsis secondary to acute pyelonephritis with underlying congestive heart failure and type 2 diabetes mellitus."
    conditions = extract_conditions(note)
    condition_names = [c.name for c in conditions]
    icd10_codes = [c.icd10_hint for c in conditions]

    assert "Sepsis" in condition_names
    assert "A41.9" in icd10_codes
    assert "Congestive Heart Failure Exacerbation" in condition_names
    assert "I50.9" in icd10_codes
    assert "Type 2 Diabetes Mellitus" in condition_names
    assert "E11.9" in icd10_codes


def test_extract_conditions_post_op_and_pneumonia():
    note = "72yo male status post right total hip arthroplasty, also noted to have mild community-acquired pneumonia."
    conditions = extract_conditions(note)
    condition_names = [c.name for c in conditions]

    assert "Post-operative Total Hip Arthroplasty" in condition_names
    assert "Pneumonia" in condition_names


def test_extract_medications_complete():
    med_text = "Metformin 500mg oral BID; Lisinopril 10mg oral daily; Atorvastatin 40mg nightly"
    meds = extract_medications(med_text)

    assert len(meds) == 3
    assert meds[0].dose == "500mg"
    assert meds[0].frequency == "BID"
    assert meds[1].dose == "10mg"
    assert meds[1].frequency == "daily"
    assert meds[2].dose == "40mg"
    assert meds[2].frequency == "nightly"


def test_extract_medications_missing_dose_returns_null():
    """
    CRITICAL REQUIREMENT: A missing dose or frequency MUST return None/null rather than guessing.
    Downstream safety agents rely on this null as a clinical barrier signal.
    """
    med_text = "Lisinopril oral daily; Furosemide; Metoprolol succinate 25mg"
    meds = extract_medications(med_text)

    assert len(meds) == 3
    # Lisinopril has frequency but no dose
    assert meds[0].name.startswith("Lisinopril")
    assert meds[0].dose is None
    assert meds[0].frequency == "daily"

    # Furosemide has neither dose nor frequency
    assert meds[1].name.startswith("Furosemide")
    assert meds[1].dose is None
    assert meds[1].frequency is None

    # Metoprolol has dose but no frequency
    assert meds[2].dose == "25mg"
    assert meds[2].frequency is None


def test_extract_medications_access_flag_and_prior_auth():
    med_text = "Insulin glargine 24 units subcutaneous nightly (pending prior authorization); Warfarin 5mg daily (flagged drug-drug interaction with Fluconazole)"
    meds = extract_medications(med_text)

    assert len(meds) == 2
    assert meds[0].dose == "24 units"
    assert meds[0].frequency == "nightly"
    assert meds[0].access_flag == "pending_prior_authorization"

    assert meds[1].dose == "5mg"
    assert meds[1].frequency == "daily"
    assert meds[1].access_flag == "drug_interaction_flag"


def test_extract_vitals_summary():
    note = "Patient is afebrile. Vitals: BP 122/76 mmHg, HR 70 bpm, Temp 98.4 F, SpO2 98% on room air. Hemodynamically stable."
    vitals = extract_vitals_summary(note)

    assert "BP 122/76" in vitals
    assert "HR 70" in vitals
    assert "SpO2 98%" in vitals
    assert "Temp 98.4" in vitals


def test_extract_pending_labs_detection():
    lab_text = "CBC: WBC 10.4, Hgb 12.1. Blood culture pending, drawn 2 days ago, no result yet. Urinalysis: E. coli >100k."
    pending = extract_pending_labs(lab_text)

    assert len(pending) >= 1
    assert any("blood culture pending" in p.lower() for p in pending)


def test_extract_pending_labs_empty_when_all_resulted():
    lab_text = "BMP: Na 140, K 4.0, Cr 0.9. CBC WNL. All labs resulted."
    pending = extract_pending_labs(lab_text)

    assert len(pending) == 0


def test_deidentify_clinical_text():
    note = "Mr. Johnson was admitted by Dr. Sarah Smith on 2026-08-15. MRN: 98765432. Phone 555-123-4567. Bed 4-401."
    deidentified = deidentify_clinical_text(note)

    assert "Johnson" not in deidentified
    assert "[PATIENT]" in deidentified
    assert "Dr. Sarah Smith" not in deidentified
    assert "[PROVIDER]" in deidentified
    assert "98765432" not in deidentified
    assert "[REDACTED]" in deidentified
    assert "555-123-4567" not in deidentified
    assert "[PHONE]" in deidentified
    assert "2026-08-15" not in deidentified
    assert "[DATE]" in deidentified


def test_extract_all_entities_full_payload():
    note = "68yo female with congestive heart failure exacerbation. Vitals: BP 120/78, HR 72, SpO2 98% RA. Afebrile."
    meds_text = "Furosemide 40mg daily; Lisinopril 10mg daily"
    labs_text = "BNP 210. Urine culture pending."

    res: ExtractEntitiesResponse = extract_all_entities(note, meds_text, labs_text)

    assert len(res.conditions) >= 1
    assert res.conditions[0].name == "Congestive Heart Failure Exacerbation"
    assert len(res.medications) == 2
    assert len(res.labs_pending) >= 1
    assert "BP 120/78" in res.vitals_summary
    assert res.deidentified_text is not None
