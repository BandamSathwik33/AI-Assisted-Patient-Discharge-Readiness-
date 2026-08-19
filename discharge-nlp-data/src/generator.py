"""
Synthetic Patient Generator.
Produces realistic, de-identified synthetic hospital encounter data for 14 diverse clinical archetypes spanning all discharge readiness tiers, barrier categories, and lengths of stay.
"""

import json
import os
import sys
from typing import List

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.schemas import SyntheticPatient

SYNTHETIC_PATIENT_RECORDS: List[dict] = [
    {
        "patient_id": "P-1001",
        "name": "Eleanor Vance",
        "age": 68,
        "admission_date": "2026-08-15",
        "days_admitted": 4,
        "attending_md": "Dr. Sarah Smith",
        "bed_number": "4-401",
        "admission_notes": "68yo female admitted for acute decompensated congestive heart failure exacerbation with bilateral lower extremity edema and dyspnea on exertion. Following IV diuresis with furosemide, patient is now euvolemic, afebrile, and eupneic on room air with stable vitals (BP 122/76 mmHg, HR 70 bpm, SpO2 98% on room air). Ambulated 300 feet without desaturation. Discharge home approved.",
        "medication_list": "Furosemide 40mg oral daily; Lisinopril 10mg oral daily; Metoprolol succinate 25mg oral daily; Potassium chloride 20mEq oral daily",
        "lab_summary": "BMP: Na 138, K 4.2, BUN 18, Cr 1.0. BNP decreased from 1240 on admission to 210 today. All labs resulted and within normal limits.",
        "caregiver_notes": "Patient lives with supportive spouse who is present for discharge teaching. Home environment assessed as safe with no stairs.",
        "insurance_notes": "Medicare Part B active. All discharge prescriptions verified and covered at patient's local retail pharmacy.",
        "scenario_type": "CHF Exacerbation - Clinically Stable - Ready",
    },
    {
        "patient_id": "P-1002",
        "name": "Arthur Pendelton",
        "age": 72,
        "admission_date": "2026-08-17",
        "days_admitted": 2,
        "attending_md": "Dr. Robert Chen",
        "bed_number": "3-308",
        "admission_notes": "72yo male status post elective right total hip arthroplasty (THA) for severe osteoarthritis. Incision clean, dry, and intact with no erythema or drainage. Pain well controlled on oral analgesics. Vitals stable: BP 128/80 mmHg, HR 74 bpm, SpO2 97% on room air. Awaiting final physical therapy evaluation and stair clearance this afternoon prior to safe discharge.",
        "medication_list": "Apixaban 2.5mg oral BID; Acetaminophen 1000mg oral q8h PRN pain; Tramadol 50mg oral q6h PRN breakthrough pain; Docusate sodium 100mg oral daily",
        "lab_summary": "Post-op CBC: Hgb 11.2 (stable), WBC 7.8, Platelets 220. BMP normal. No pending labs.",
        "caregiver_notes": "Patient's adult daughter available to assist with meal prep and transportation for the first week post-discharge.",
        "insurance_notes": "Commercial insurance authorization approved for outpatient physical therapy visits.",
        "scenario_type": "Post-Op Hip Replacement - Pending PT Clearance",
    },
    {
        "patient_id": "P-1003",
        "name": "Marcus Holloway",
        "age": 76,
        "admission_date": "2026-08-14",
        "days_admitted": 5,
        "attending_md": "Dr. Sarah Smith",
        "bed_number": "4-412",
        "admission_notes": "76yo male admitted with community-acquired pneumonia requiring 2L nasal cannula oxygen. Completed 5-day IV antibiotic course. Patient is afebrile with resolving cough, but desaturates to 88% on room air during ambulation, requiring 2L home O2. Vitals: BP 134/82 mmHg, HR 78 bpm, Temp 98.4 F, SpO2 94% on 2L nasal cannula. Home oxygen equipment delivery to residence is still unconfirmed.",
        "medication_list": "Amoxicillin-clavulanate 875-125mg oral BID x 5 days; Albuterol HFA 2 puffs inhaled q4h PRN wheezing; Prednisone 20mg oral daily taper",
        "lab_summary": "WBC normalized to 8.2. Procalcitonin down to 0.08. Sputum culture final: normal respiratory flora. No pending labs.",
        "caregiver_notes": "Spouse at home able to assist with daily activities, but expressed concern regarding oxygen tank setup.",
        "insurance_notes": "Prior authorization submitted for home oxygen concentrator and portable tanks; delivery confirmation pending DME vendor dispatch.",
        "scenario_type": "Pneumonia - Unconfirmed Home Oxygen Delivery",
    },
    {
        "patient_id": "P-1004",
        "name": "Brenda Morales",
        "age": 54,
        "admission_date": "2026-08-16",
        "days_admitted": 3,
        "attending_md": "Dr. James Wilson",
        "bed_number": "2-205",
        "admission_notes": "54yo female admitted with severe hyperglycemia (blood glucose 480 mg/dL) and newly diagnosed Type 2 Diabetes Mellitus with mild dehydration. Patient rehydrated and transitioned to a basal-bolus subcutaneous insulin regimen. Blood sugars currently stabilized between 130-170 mg/dL. Vitals: BP 130/84 mmHg, HR 82 bpm, SpO2 99% on room air. Discharge contingent on insulin supply.",
        "medication_list": "Insulin glargine 24 units subcutaneous nightly (pending prior authorization); Insulin lispro 4 units subcutaneous TID with meals; Metformin 1000mg oral BID",
        "lab_summary": "A1c 11.4%. BMP: Glucose 142, K 4.1, Cr 0.9. Anion gap closed (8). All labs resulted.",
        "caregiver_notes": "Patient lives independently, receptive to diabetes self-management and glucometer training.",
        "insurance_notes": "Insurance carrier requires urgent prior authorization for brand insulin glargine pen; approval status pending review by payer.",
        "scenario_type": "Diabetes - Insulin Prior Authorization Pending",
    },
    {
        "patient_id": "P-1005",
        "name": "Walter Kowalski",
        "age": 65,
        "admission_date": "2026-08-15",
        "days_admitted": 4,
        "attending_md": "Dr. Sarah Smith",
        "bed_number": "4-408",
        "admission_notes": "65yo female admitted for severe sepsis secondary to complicated urinary tract infection. Received aggressive IV fluid resuscitation and IV piperacillin-tazobactam. Currently afebrile for 24 hours with normalizing hemodynamics (BP 118/72 mmHg, HR 76 bpm, Temp 98.6 F, SpO2 97% room air). However, repeat blood cultures drawn 48 hours ago remain pending final microbiology readout.",
        "medication_list": "Cefpodoxime 200mg oral BID; Phenazopyridine 100mg oral TID PRN dysuria x 2 days; Acetaminophen 650mg oral q6h PRN",
        "lab_summary": "CBC: WBC 10.4 (down from 19.8). Urinalysis: E. coli >100k CFU/mL sensitive to cephalosporins. Blood culture pending, drawn 2 days ago, no result yet.",
        "caregiver_notes": "Son lives nearby and will assist with post-discharge follow-up appointments.",
        "insurance_notes": "Medicaid managed care active, transportation voucher requested.",
        "scenario_type": "Sepsis - Pending Blood Cultures",
    },
    {
        "patient_id": "P-1006",
        "name": "Agnes Sterling",
        "age": 84,
        "admission_date": "2026-08-13",
        "days_admitted": 6,
        "attending_md": "Dr. Gregory House",
        "bed_number": "5-502",
        "admission_notes": "84yo female admitted following a mechanical fall at home with rib contusion and mild dehydration. Patient has mild cognitive impairment and unsteady gait using a front-wheeled walker. Vitals stable: BP 136/78 mmHg, HR 72 bpm, SpO2 96% room air. Patient is unsafe to discharge home alone without 24/7 family oversight or visiting home health aide.",
        "medication_list": "Donepezil 5mg oral nightly; Calcium carbonate 500mg plus Vitamin D oral BID; Acetaminophen 500mg oral q8h PRN",
        "lab_summary": "BMP normal, Cr 0.8, electrolytes balanced. No pending labs.",
        "caregiver_notes": "Patient lives completely alone in a two-story home. Only daughter lives out of state (California) and cannot relocate. No confirmed caregiver or home aide arranged yet.",
        "insurance_notes": "Medicare Advantage plan has limited home health aide benefit; social work referral submitted for community waiver support.",
        "scenario_type": "Elderly Living Alone - Zero Caregiver Support",
    },
    {
        "patient_id": "P-1007",
        "name": "Raymond Hayes",
        "age": 71,
        "admission_date": "2026-08-16",
        "days_admitted": 3,
        "attending_md": "Dr. Robert Chen",
        "bed_number": "3-314",
        "admission_notes": "71yo male with chronic atrial fibrillation, hypertension, coronary artery disease, and systemic candidiasis. Hemodynamically stable with rate-controlled atrial fibrillation (HR 78 bpm, BP 126/74 mmHg, SpO2 98% room air). Clinical pharmacist flagged severe cytochrome P450 drug interaction between newly initiated fluconazole and maintenance warfarin.",
        "medication_list": "Warfarin 5mg oral daily; Fluconazole 200mg oral daily (flagged drug-drug interaction with Warfarin - high bleeding risk); Atorvastatin 40mg oral nightly; Metoprolol succinate 50mg oral daily; Lisinopril 20mg oral daily; Omeprazole 20mg oral daily",
        "lab_summary": "INR 3.8 (elevated, supra-therapeutic). LFTs mild transaminitis. Repeat INR pending draw tomorrow morning.",
        "caregiver_notes": "Wife assists with pillbox organization but confused by recent dosing changes.",
        "insurance_notes": "Prescriptions active; clinical pharmacist review required prior to safe discharge dispensing.",
        "scenario_type": "Polypharmacy - Flagged Drug-Drug Interaction",
    },
    {
        "patient_id": "P-1008",
        "name": "Lucas Davies",
        "age": 29,
        "admission_date": "2026-08-18",
        "days_admitted": 1,
        "attending_md": "Dr. James Wilson",
        "bed_number": "2-210",
        "admission_notes": "29yo male status post uncomplicated laparoscopic appendectomy for acute appendicitis yesterday. Tolerating regular diet, voiding spontaneously, ambulating independently in hallway without assistance. Vitals: BP 118/74 mmHg, HR 68 bpm, Temp 98.2 F, SpO2 99% on room air. Surgical port sites clean with dermabond intact. Cleared by general surgery team.",
        "medication_list": "Ibuprofen 600mg oral q8h PRN mild pain; Acetaminophen 500mg oral q6h PRN pain; Docusate sodium 100mg oral daily",
        "lab_summary": "Post-op CBC: WBC 6.8, Hgb 14.5. BMP unremarkable. No pending labs.",
        "caregiver_notes": "Lives with roommate who drove patient to hospital and is available to drive home.",
        "insurance_notes": "Employer commercial plan active. Prescriptions sent to local pharmacy and ready for pickup.",
        "scenario_type": "Appendectomy Recovery - Fully Ready",
    },
    {
        "patient_id": "P-1009",
        "name": "Geraldine Ross",
        "age": 63,
        "admission_date": "2026-08-12",
        "days_admitted": 7,
        "attending_md": "Dr. Sarah Smith",
        "bed_number": "4-419",
        "admission_notes": "63yo female with severe COPD and stage 3 chronic kidney disease admitted for recurrent acute COPD exacerbation. This is the patient's 4th inpatient admission in the past 90 days. Vitals currently stable: BP 138/82 mmHg, HR 80 bpm, SpO2 93% on room air with baseline dyspnea on moderate exertion. High risk of 30-day readmission due to frequent disease exacerbations and poor adherence history.",
        "medication_list": "Fluticasone-vilanterol 100-25mcg 1 puff inhaled daily; Tiotropium 18mcg 1 capsule inhaled daily; Prednisone 10mg oral daily; Furosemide 20mg oral daily",
        "lab_summary": "ABG: pH 7.38, pCO2 48, pO2 68 (chronic baseline retention). BUN 28, Cr 1.9 (stable baseline). No pending labs.",
        "caregiver_notes": "Patient lives with elderly sibling who has limited mobility. Requires visiting nurse support.",
        "insurance_notes": "Enrolled in high-risk care coordination program with payer. Follow-up clinic appointment scheduled in 5 days.",
        "scenario_type": "High Readmission Risk - Frequent Hospitalizer",
    },
    {
        "patient_id": "P-1010",
        "name": "Patricia Zimmerman",
        "age": 59,
        "admission_date": "2026-08-14",
        "days_admitted": 5,
        "attending_md": "Dr. Gregory House",
        "bed_number": "5-508",
        "admission_notes": "59yo female with multiple sclerosis admitted for cellulitis of the left lower extremity. Cellulitis has fully resolved after 4 days of IV cefazolin, skin clear without erythema or warmth. Afebrile, vitals normal: BP 120/78 mmHg, HR 72 bpm, SpO2 98% room air. Clinically cleared for discharge by primary team, but discharge is blocked solely awaiting DME delivery of a specialized motorized wheelchair to home.",
        "medication_list": "Cephalexin 500mg oral QID x 5 days; Baclofen 10mg oral TID; Glatiramer acetate 20mg subcutaneous daily",
        "lab_summary": "CBC: WBC 6.2 (normalized). CRP down from 48 to 3.2. No pending labs.",
        "caregiver_notes": "Husband present at bedside, eager to take patient home once wheelchair arrives.",
        "insurance_notes": "Prior authorization approved for motorized wheelchair; medical equipment supplier delivery delayed until tomorrow afternoon.",
        "scenario_type": "Administrative Logistics Block - DME Wheelchair Pending",
    },
    {
        "patient_id": "P-1011",
        "name": "Clifford Barnes",
        "age": 66,
        "admission_date": "2026-08-16",
        "days_admitted": 3,
        "attending_md": "Dr. Robert Chen",
        "bed_number": "3-322",
        "admission_notes": "66yo male with severe tobacco use disorder admitted with acute COPD exacerbation. Wheezing resolved, breath sounds clear bilaterally. Vitals: BP 132/80 mmHg, HR 76 bpm, SpO2 95% on room air. Inpatient respiratory therapist flagged improper inhaler technique and lack of spacer at home, leading to frequent medication underdosing.",
        "medication_list": "Ipratropium-albuterol 0.5-2.5mg nebulized q6h; Budesonide-formoterol 160-4.5mcg 2 puffs inhaled BID; Nicotine transdermal patch 21mg daily",
        "lab_summary": "CBC normal. BMP normal. Sputum culture showed no growth. No pending labs.",
        "caregiver_notes": "Spouse present, smoke-free home environment established.",
        "insurance_notes": "Inhaler spacer device covered with copay voucher; respiratory therapy teaching scheduled for 2 PM.",
        "scenario_type": "COPD Exacerbation - Inhaler Technique & Education Needed",
    },
    {
        "patient_id": "P-1012",
        "name": "Dominic Thorne",
        "age": 51,
        "admission_date": "2026-08-17",
        "days_admitted": 2,
        "attending_md": "Dr. James Wilson",
        "bed_number": "2-218",
        "admission_notes": "51yo male admitted with asymptomatic hypertensive urgency (admission BP 210/115 mmHg) in setting of medication non-adherence. After restarting anti-hypertensives and adding amlodipine, blood pressure has steadily improved to 138/86 mmHg. Asymptomatic with no end-organ damage. Vitals: BP 136/84 mmHg, HR 72 bpm, SpO2 98% room air.",
        "medication_list": "Amlodipine 10mg oral daily; Losartan 100mg oral daily; Hydrochlorothiazide 25mg oral daily",
        "lab_summary": "Urinalysis: negative for proteinuria. Troponin negative x 2. Cr 1.1 (normal). All labs completed.",
        "caregiver_notes": "Patient lives with supportive partner who purchased a digital home BP monitoring cuff.",
        "insurance_notes": "Generic 90-day supply auto-refill active at retail pharmacy. Outpatient PCP follow-up booked for 48 hours post-discharge.",
        "scenario_type": "Hypertensive Urgency - Regimen Adjustment - Near Ready",
    },
    {
        "patient_id": "P-1013",
        "name": "Victor Delgado",
        "age": 45,
        "admission_date": "2026-08-16",
        "days_admitted": 3,
        "attending_md": "Dr. Sarah Smith",
        "bed_number": "4-425",
        "admission_notes": "45yo male diagnosed with acute lower extremity deep vein thrombosis (DVT) following a long international flight. Pain and calf swelling significantly decreased. Vitals stable: BP 124/76 mmHg, HR 68 bpm, SpO2 99% on room air. Initiated on rivaroxaban loading dose. Patient requires comprehensive education on DOAC adherence and bleeding precautions.",
        "medication_list": "Rivaroxaban 15mg oral BID with food x 21 days; Acetaminophen 500mg oral q8h PRN calf discomfort",
        "lab_summary": "Venous duplex ultrasound: occlusive thrombus in right popliteal vein. CBC: Hgb 15.1, Platelets 245. Renal function normal (eGFR > 90). No pending labs.",
        "caregiver_notes": "Patient active and independent, plans to return to remote work next week.",
        "insurance_notes": "Specialty copay assistance card applied for rivaroxaban starter pack; copay $10.",
        "scenario_type": "Acute DVT - Direct Oral Anticoagulant Education",
    },
    {
        "patient_id": "P-1014",
        "name": "Helen Montgomery",
        "age": 70,
        "admission_date": "2026-08-15",
        "days_admitted": 4,
        "attending_md": "Dr. Gregory House",
        "bed_number": "5-515",
        "admission_notes": "70yo female admitted with prerenal acute kidney injury and orthostatic dizziness secondary to viral gastroenteritis. Treated with IV crystalloid hydration. Creatinine recovered from admission peak of 2.8 down to baseline 0.9 mg/dL. Orthostatics negative, voiding robustly with clear urine. Vitals: BP 126/78 mmHg, HR 74 bpm, SpO2 98% room air.",
        "medication_list": "Lisinopril 5mg oral daily (restarted at half dose); Ondansetron 4mg oral q8h PRN nausea",
        "lab_summary": "BMP: Na 140, K 4.0, Cl 102, HCO3 24, BUN 14, Cr 0.9. Urinalysis clear. All labs resulted.",
        "caregiver_notes": "Daughter at bedside assisting with oral rehydration and meal prep.",
        "insurance_notes": "Standard coverage active; routine outpatient nephrology/PCP follow-up scheduled in 7 days.",
        "scenario_type": "Acute Kidney Injury - Prerenal Resolved - Ready",
    },
]


def generate_synthetic_patients() -> List[SyntheticPatient]:
    """
    Returns validated list of SyntheticPatient Pydantic models.
    """
    return [SyntheticPatient(**item) for item in SYNTHETIC_PATIENT_RECORDS]


def save_synthetic_patients_to_json(filepath: str = "data/synthetic_patients.json") -> str:
    """
    Saves the synthetic patient dataset to a static JSON file.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(SYNTHETIC_PATIENT_RECORDS, f, indent=2)
    return filepath


if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_patients.json")
    saved_path = save_synthetic_patients_to_json(output_path)
    print(f"Successfully generated and saved {len(SYNTHETIC_PATIENT_RECORDS)} synthetic patients to: {saved_path}")
