import json
import os
import pytest
from src.generator import generate_synthetic_patients, save_synthetic_patients_to_json, SYNTHETIC_PATIENT_RECORDS
from src.schemas import SyntheticPatient


def test_generator_returns_at_least_12_patients():
    patients = generate_synthetic_patients()
    assert len(patients) >= 12
    assert len(patients) == len(SYNTHETIC_PATIENT_RECORDS)


def test_all_patient_records_valid_schema():
    patients = generate_synthetic_patients()
    for p in patients:
        assert isinstance(p, SyntheticPatient)
        assert p.patient_id.startswith("P-")
        assert len(p.name) > 2
        assert 0 < p.age < 120
        assert 1 <= p.days_admitted <= 9
        assert p.attending_md.startswith("Dr.")
        assert len(p.bed_number) > 0
        assert len(p.admission_notes) > 20
        assert len(p.medication_list) > 10
        assert len(p.lab_summary) > 5
        assert len(p.caregiver_notes) > 5
        assert len(p.insurance_notes) > 5
        assert len(p.scenario_type) > 3


def test_archetype_coverage():
    scenarios = [p["scenario_type"].lower() for p in SYNTHETIC_PATIENT_RECORDS]

    # Archetype 1: CHF Stable Ready
    assert any("chf" in s and "ready" in s for s in scenarios)

    # Archetype 2: Post-op Hip PT clearance
    assert any("hip" in s and "pt" in s for s in scenarios)

    # Archetype 3: Pneumonia Oxygen
    assert any("pneumonia" in s and "oxygen" in s for s in scenarios)

    # Archetype 4: Diabetes Insulin Prior Auth
    assert any("diabetes" in s and "prior auth" in s for s in scenarios)

    # Archetype 5: Sepsis Blood Culture
    assert any("sepsis" in s and "blood culture" in s for s in scenarios)

    # Archetype 6: Elderly Living Alone Caregiver
    assert any("elderly" in s and "caregiver" in s for s in scenarios)

    # Archetype 7: Polypharmacy Drug Interaction
    assert any("polypharmacy" in s or "drug-drug interaction" in s for s in scenarios)

    # Archetype 8: Appendectomy Ready
    assert any("appendectomy" in s and "ready" in s for s in scenarios)

    # Archetype 9: High Readmission Risk
    assert any("readmission risk" in s for s in scenarios)

    # Archetype 10: Administrative logistics
    assert any("administrative" in s or "wheelchair" in s for s in scenarios)


def test_days_admitted_spread():
    days = [p["days_admitted"] for p in SYNTHETIC_PATIENT_RECORDS]
    assert min(days) <= 2
    assert max(days) >= 7
    # Ensure variety of values
    assert len(set(days)) >= 5


def test_save_synthetic_patients_to_json(tmp_path):
    out_file = str(tmp_path / "test_synthetic.json")
    saved_path = save_synthetic_patients_to_json(out_file)

    assert os.path.exists(saved_path)
    with open(saved_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) >= 12
    assert data[0]["patient_id"] == "P-1001"
