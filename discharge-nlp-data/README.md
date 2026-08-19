# Clinical NLP Extraction & Synthetic Data Layer (`discharge-nlp-data`)

**Service Owner**: Person 4  
**Port**: `8002`  
**Framework**: Python 3.11+ / FastAPI / Pydantic v2  

---

## 1. Overview & Clinical Value

The **Clinical NLP Extraction & Synthetic Data Layer** provides two critical foundational capabilities for the *AI-Assisted Patient Discharge Readiness & Follow-Up Planner*:

1. **Deterministic Clinical Entity Extraction (`POST /extract-entities`)**: Converts unstructured free-text clinical notes, medication lists, and laboratory summaries into structured, validated JSON tokens **before** reaching the AI reasoning layer. This grounds downstream LLM agents in verified facts and eliminates hallucinations (e.g., preventing the AI from inventing a missing dosage or overlooking a pending blood culture).
2. **Comprehensive Synthetic Patient Dataset (`GET /synthetic-patients` & `data/synthetic_patients.json`)**: Generates 14 clinically authentic, de-identified patient encounter records covering a diverse spectrum of discharge readiness tiers, barrier categories, and lengths of stay.

---

## 2. Architecture & Design Principles

```
Unstructured Clinical Text
  ├── Admission Notes ──────────► [Condition Extractor & ICD-10 Matcher] ──► conditions: [{name, icd10_hint}]
  ├── Admission Notes ──────────► [Vitals & Stability Parser]             ──► vitals_summary: "BP 122/76, SpO2 98%"
  ├── Medication Free-Text ─────► [Regex Dosage & Frequency Parser]       ──► medications: [{name, dose, freq, access_flag}]
  ├── Lab Summary Text ─────────► [Pending Investigations Scanner]        ──► labs_pending: ["Blood culture pending..."]
  └── Raw Clinical Note ────────► [Safe Harbor De-identifier]             ──► deidentified_text: "[PATIENT] admitted..."
```

### Key Engineering Safeguards
- **Deterministic Null Safety**: If a medication dosage or frequency cannot be parsed from the raw text, the extractor explicitly outputs `null`/`None` instead of guessing. A missing dosage is itself a critical clinical barrier signal for the downstream Medication Reconciliation Agent.
- **Access & Interaction Flagging**: Automatically identifies prior authorization requirements, drug-drug interaction warnings, and formulary restrictions.
- **De-Identification**: Cleanses Protected Health Information (names, dates, MRNs, phone numbers, room numbers) according to HIPAA Safe Harbor guidelines.

---

## 3. Environment & Configuration

Create `.env` based on `.env.example`:

```env
PORT=8002
CORS_ALLOWED_ORIGIN=http://localhost:5173
```

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PORT` | `8002` | HTTP port for the FastAPI server |
| `CORS_ALLOWED_ORIGIN` | `http://localhost:5173` | Allowed CORS origin (React frontend) |

---

## 4. Quickstart Guide

### Step 1: Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### Step 2: Regenerate Synthetic Patients Dataset
```bash
python src/generator.py
```
This generates and saves `data/synthetic_patients.json` with 14 clinical archetype patients.

### Step 3: Run the Service
```bash
# Using uvicorn directly:
uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload

# Or via Python module:
python -m src.main
```

### Step 4: Run Tests
```bash
pytest
```

---

## 5. API Reference

### `GET /health`
Verifies service liveness.
- **Response `200 OK`**:
```json
{
  "status": "ok"
}
```

---

### `GET /synthetic-patients`
Returns the array of 14 synthetic patient records for seeding and operations testing.
- **Response `200 OK`**: Array of `SyntheticPatient` objects:
```json
[
  {
    "patient_id": "P-1001",
    "name": "Eleanor Vance",
    "age": 68,
    "admission_date": "2026-08-15",
    "days_admitted": 4,
    "attending_md": "Dr. Sarah Smith",
    "bed_number": "4-401",
    "admission_notes": "68yo female admitted for acute decompensated congestive heart failure...",
    "medication_list": "Furosemide 40mg oral daily; Lisinopril 10mg oral daily...",
    "lab_summary": "BMP: Na 138, K 4.2, BUN 18, Cr 1.0. BNP 210. All labs resulted.",
    "caregiver_notes": "Patient lives with supportive spouse who is present for discharge teaching.",
    "insurance_notes": "Medicare Part B active. Prescriptions verified.",
    "scenario_type": "CHF Exacerbation - Clinically Stable - Ready"
  }
]
```

---

### `POST /extract-entities`
Extracts structured clinical tokens from raw text fields.
- **Request Body**:
```json
{
  "raw_note_text": "65yo female admitted for severe sepsis secondary to complicated UTI. Patient is afebrile with stable vitals: BP 118/72, HR 76, SpO2 97% on room air.",
  "medication_list_text": "Cefpodoxime 200mg oral BID; Acetaminophen 650mg oral q6h PRN",
  "lab_summary_text": "CBC: WBC 10.4. Blood culture pending, drawn 2 days ago, no result yet."
}
```

- **Response `200 OK`**:
```json
{
  "conditions": [
    {
      "name": "Sepsis",
      "icd10_hint": "A41.9"
    },
    {
      "name": "Urinary Tract Infection",
      "icd10_hint": "N39.0"
    }
  ],
  "medications": [
    {
      "name": "Cefpodoxime",
      "dose": "200mg",
      "frequency": "BID",
      "access_flag": null
    },
    {
      "name": "Acetaminophen",
      "dose": "650mg",
      "frequency": "q6h",
      "access_flag": null
    }
  ],
  "vitals_summary": "BP 118/72 mmHg, HR 76 bpm, SpO2 97% (Afebrile)",
  "labs_pending": [
    "Blood culture pending, drawn 2 days ago, no result yet"
  ],
  "deidentified_text": "65yo female admitted for severe sepsis secondary to complicated UTI. Patient is afebrile with stable vitals: BP 118/72, HR 76, SpO2 97% on room air."
}
```

---

## 6. Synthetic Patient Archetypes Summary

The synthetic dataset (`data/synthetic_patients.json`) spans 14 diverse clinical scenarios:

| Patient ID | Name | Days Admitted | Archetype / Clinical Scenario | Expected Tier / Barrier Category |
| :--- | :--- | :---: | :--- | :--- |
| `P-1001` | Eleanor Vance | 4 | CHF Exacerbation, diuresed, fully stable | **Ready** (No barriers) |
| `P-1002` | Arthur Pendelton | 2 | Post-op Hip Replacement, awaiting final PT stairs clearance | **Near_Ready** (Clinical: Moderate) |
| `P-1003` | Marcus Holloway | 5 | Pneumonia, requires home O2, equipment delivery unconfirmed | **High_Risk_Blocked** (Clinical: Critical) |
| `P-1004` | Brenda Morales | 3 | Diabetes, new basal-bolus insulin pending prior authorization | **Near_Ready / High_Risk** (Med/Admin: Critical/Mod) |
| `P-1005` | Walter Kowalski | 4 | Severe Sepsis, repeat blood cultures pending final readout | **High_Risk_Blocked** (Clinical: Critical - Hard blocker) |
| `P-1006` | Agnes Sterling | 6 | Elderly fall patient living alone, zero caregiver support | **High_Risk_Blocked** (Caregiver_SDOH: Critical) |
| `P-1007` | Raymond Hayes | 3 | Polypharmacy on 6+ meds with Warfarin + Fluconazole interaction | **High_Risk_Blocked** (Medication: Critical) |
| `P-1008` | Lucas Davies | 1 | Laparoscopic Appendectomy recovery, ambulating, eating | **Ready** (Minor follow-up) |
| `P-1009` | Geraldine Ross | 7 | Severe COPD & CKD, 4th admission in 90 days (High Readmission) | **Near_Ready** (High Readmission Risk) |
| `P-1010` | Patricia Zimmerman | 5 | Resolved Cellulitis, clinically cleared, awaiting DME wheelchair | **Near_Ready** (Administrative Logistics) |
| `P-1011` | Clifford Barnes | 3 | COPD Exacerbation, improper inhaler technique, RT demo required | **Near_Ready** (Medication Education) |
| `P-1012` | Dominic Thorne | 2 | Hypertensive Urgency, BP normalized on oral regimen, 48h PCP follow-up | **Near_Ready** (Clinical Follow-up) |
| `P-1013` | Victor Delgado | 3 | Acute DVT, DOAC rivaroxaban starter pack education | **Near_Ready** (Medication Education) |
| `P-1014` | Helen Montgomery | 4 | Acute Kidney Injury resolved with IV fluids, Cr 0.9 | **Ready** (No barriers) |

---

## 7. Handoff to Teammates

- **For Person 2 (Core Backend API)**:
  - Load `data/synthetic_patients.json` into `discharge-backend-core/data/synthetic_patients.json` for your database seed script (`seed.py`).
  - Call `http://localhost:8002/extract-entities` during your `/evaluate/{patient_id}` flow.
- **For Person 3 (AI Orchestrator)**:
  - The output shape of `/extract-entities` directly matches the `structured_clinical_data` input parameter expected by `/orchestrate/evaluate`.
