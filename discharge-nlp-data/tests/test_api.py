import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_synthetic_patients_endpoint():
    response = client.get("/synthetic-patients")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 12
    # Verify first patient structure
    first = data[0]
    assert "patient_id" in first
    assert "name" in first
    assert "admission_notes" in first
    assert "medication_list" in first
    assert "lab_summary" in first
    assert "caregiver_notes" in first
    assert "insurance_notes" in first
    assert "days_admitted" in first


def test_extract_entities_endpoint_chf_scenario():
    payload = {
        "raw_note_text": "68yo female admitted for congestive heart failure exacerbation. Afebrile, vitals: BP 122/76, HR 70, SpO2 98% RA.",
        "medication_list_text": "Furosemide 40mg oral daily; Lisinopril 10mg daily",
        "lab_summary_text": "BMP normal. BNP 210. All labs resulted.",
    }
    response = client.post("/extract-entities", json=payload)
    assert response.status_code == 200
    res = response.json()

    assert "conditions" in res
    assert any(c["name"] == "Congestive Heart Failure Exacerbation" for c in res["conditions"])
    assert any(c["icd10_hint"] == "I50.9" for c in res["conditions"])

    assert "medications" in res
    assert len(res["medications"]) == 2
    assert res["medications"][0]["dose"] == "40mg"
    assert res["medications"][0]["frequency"] == "daily"

    assert "vitals_summary" in res
    assert "BP 122/76" in res["vitals_summary"]

    assert "labs_pending" in res
    assert len(res["labs_pending"]) == 0

    assert "deidentified_text" in res


def test_extract_entities_endpoint_sepsis_pending_lab():
    payload = {
        "raw_note_text": "65yo female admitted for severe sepsis secondary to UTI. Patient is afebrile.",
        "medication_list_text": "Cefpodoxime 200mg oral BID",
        "lab_summary_text": "CBC: WBC 10.4. Blood culture pending, drawn 2 days ago, no result yet.",
    }
    response = client.post("/extract-entities", json=payload)
    assert response.status_code == 200
    res = response.json()

    assert any(c["name"] == "Sepsis" for c in res["conditions"])
    assert len(res["labs_pending"]) >= 1
    assert any("blood culture pending" in lab.lower() for lab in res["labs_pending"])


def test_extract_entities_missing_dosage_returns_null():
    payload = {
        "raw_note_text": "Patient with type 2 diabetes mellitus.",
        "medication_list_text": "Metformin oral BID; Insulin glargine",
        "lab_summary_text": "A1c 11.4%. No pending labs.",
    }
    response = client.post("/extract-entities", json=payload)
    assert response.status_code == 200
    res = response.json()

    meds = res["medications"]
    assert len(meds) == 2
    # Metformin has frequency BID but no dose
    assert meds[0]["dose"] is None
    assert meds[0]["frequency"] == "BID"

    # Insulin glargine has neither
    assert meds[1]["dose"] is None
    assert meds[1]["frequency"] is None
