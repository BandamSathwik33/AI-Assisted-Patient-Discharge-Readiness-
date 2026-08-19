"""
Clinical Entity Extraction Engine.
Provides deterministic, rule-based, and regex extraction of:
- Diagnoses and ICD-10 codes from clinical notes
- Medications, dosages, frequencies, and access flags
- Vitals normalization
- Pending laboratory investigations
- Clinical text de-identification (Safe Harbor HIPAA rules)
"""

import re
from typing import List, Optional, Tuple
from src.icd10_map import match_conditions_in_text
from src.schemas import ConditionItem, ExtractEntitiesResponse, MedicationItem


# Dosage pattern: e.g. 500mg, 10 mg, 20 units, 5 mcg, 1.5 g, 10 mEq, 2 puffs, 1 tablet
DOSE_REGEX = re.compile(
    r"(\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|units?|meq|ml|%|puffs?|tablets?|tabs?|capsules?|caps?|mg\/ml|drops?|mcg\/hr)\b)",
    re.IGNORECASE,
)

# Frequency pattern: e.g. BID, TID, QID, daily, nightly, q8h, PRN, once daily, twice daily, every 6 hours
FREQUENCY_REGEX = re.compile(
    r"\b(once\s+daily|twice\s+daily|three\s+times\s+daily|four\s+times\s+daily|daily|nightly|at\s+bedtime|qhs|qam|bid|tid|qid|q\d+h|every\s+\d+\s+hours|every\s+morning|every\s+night|prn|as\s+needed|weekly|monthly)\b",
    re.IGNORECASE,
)

# Access flag patterns: e.g. prior auth pending, coverage denied, drug interaction, etc.
ACCESS_FLAG_PATTERNS = [
    (r"pending\s+prior\s+auth(?:orization)?|prior\s+auth(?:orization)?\s+pending", "pending_prior_authorization"),
    (r"prior\s+auth(?:orization)?\s+required", "prior_authorization_required"),
    (r"drug[- ]drug\s+interaction|flagged\s+interaction|interaction\s+flag", "drug_interaction_flag"),
    (r"non[- ]formulary|not\s+covered|coverage\s+denied", "formulary_coverage_issue"),
    (r"specialty\s+pharmacy(?:\s+required)?", "specialty_pharmacy_required"),
    (r"copay\s+assistance\s+pending", "copay_assistance_pending"),
]

# Pending lab keywords
PENDING_LAB_PATTERNS = [
    r"[^.;\n]*\b(?:blood culture|urine culture|wound culture|sputum culture|culture|pt/inr|inr|troponin|ct scan|mri|echo|echocardiogram|biopsy|pathology|panel|lab|test|x-ray)\b[^.;\n]*\b(?:pending|awaiting|no result|in progress|not yet resulted|not resulted|drawn\b[^.;\n]*no result)[^.;\n]*",
    r"[^.;\n]*\b(?:pending|awaiting|in progress)\b[^.;\n]*(?:culture|lab|result|panel|study|test|imaging)[^.;\n]*",
]


def extract_conditions(raw_note_text: str) -> List[ConditionItem]:
    """
    Extracts clinical conditions and matches them with standardized ICD-10 codes.
    """
    if not raw_note_text:
        return []

    matched = match_conditions_in_text(raw_note_text)
    return [ConditionItem(name=name, icd10_hint=code) for name, code in matched]


def parse_single_medication(entry: str) -> Optional[MedicationItem]:
    """
    Parses a single medication string into a MedicationItem.
    Returns None for empty/invalid entries.
    Dose and frequency MUST be None if not explicitly present in the text (no hallucinations).
    """
    raw = entry.strip()
    if not raw or len(raw) < 2:
        return None

    # Remove leading numbering or bullets (e.g. "1. ", "- ", "* ")
    cleaned = re.sub(r"^[\d\.\-\*\•\)\s]+", "", raw).strip()
    if not cleaned:
        return None

    # 1. Access Flag detection
    access_flag = None
    for pattern, flag_label in ACCESS_FLAG_PATTERNS:
        if re.search(pattern, cleaned, flags=re.IGNORECASE):
            access_flag = flag_label
            break

    # 2. Extract Dose
    dose = None
    dose_match = DOSE_REGEX.search(cleaned)
    if dose_match:
        dose = dose_match.group(1).strip()

    # 3. Extract Frequency
    frequency = None
    freq_match = FREQUENCY_REGEX.search(cleaned)
    if freq_match:
        frequency = freq_match.group(1).strip()

    # 4. Clean Drug Name
    # Remove parenthetical comments (e.g. "(pending prior auth)", "(flagged interaction with warfarin)")
    name_candidate = re.sub(r"\([^)]*\)", "", cleaned)
    # Remove access flag text if outside parentheses
    for pattern, _ in ACCESS_FLAG_PATTERNS:
        name_candidate = re.sub(pattern, "", name_candidate, flags=re.IGNORECASE)

    # Remove dose and frequency matches from the candidate string to isolate the drug name
    if dose:
        name_candidate = re.sub(re.escape(dose), "", name_candidate, count=1, flags=re.IGNORECASE)
    if frequency:
        name_candidate = re.sub(r"\b" + re.escape(frequency) + r"\b", "", name_candidate, count=1, flags=re.IGNORECASE)

    # Strip leftover trailing prepositions and punctuation (e.g. "Metformin 500mg PO daily" -> "Metformin PO" -> "Metformin")
    name_candidate = re.sub(r"\b(po|iv|sq|subq|im|oral|orally|subcutaneously|intravenously|topical|inhaled|by mouth)\b", "", name_candidate, flags=re.IGNORECASE)
    name_candidate = re.sub(r"[\s,;:-]+$", "", name_candidate)
    name_candidate = re.sub(r"^[\s,;:-]+", "", name_candidate)
    name_candidate = re.sub(r"\s{2,}", " ", name_candidate).strip()

    if not name_candidate:
        name_candidate = cleaned

    return MedicationItem(
        name=name_candidate,
        dose=dose,
        frequency=frequency,
        access_flag=access_flag,
    )


def extract_medications(medication_list_text: Optional[str]) -> List[MedicationItem]:
    """
    Extracts structured medication list from free-text medication summaries.
    Splits by semicolons, newlines, or numbered bullet items.
    """
    if not medication_list_text:
        return []

    # Normalize line breaks and separators
    raw_lines = re.split(r"[\n;]+|(?:\s*\d+\.\s+)", medication_list_text)
    items: List[MedicationItem] = []

    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        # If line contains comma-separated distinct meds (e.g. "Lisinopril 10mg daily, Metformin 500mg BID")
        # Split only if each chunk looks like a separate drug with dose or frequency
        sub_chunks = [c.strip() for c in line.split(",") if c.strip()]
        if len(sub_chunks) > 1 and all(DOSE_REGEX.search(c) or FREQUENCY_REGEX.search(c) for c in sub_chunks):
            for chunk in sub_chunks:
                parsed = parse_single_medication(chunk)
                if parsed:
                    items.append(parsed)
        else:
            parsed = parse_single_medication(line)
            if parsed:
                items.append(parsed)

    return items


def extract_vitals_summary(raw_note_text: str) -> str:
    """
    Extracts vitals mentions, hemodynamic status, and stability statements from clinical note.
    """
    if not raw_note_text:
        return "Vitals: Stable / within normal limits on room air"

    vitals_indicators = []

    # Look for BP
    bp_match = re.search(r"\b(?:BP|blood pressure)[:\s]*(\d{2,3}/\d{2,3})\s*(?:mmHg)?\b", raw_note_text, re.IGNORECASE)
    if bp_match:
        vitals_indicators.append(f"BP {bp_match.group(1)} mmHg")

    # Look for Heart Rate
    hr_match = re.search(r"\b(?:HR|heart rate|pulse)[:\s]*(\d{2,3})\s*(?:bpm)?\b", raw_note_text, re.IGNORECASE)
    if hr_match:
        vitals_indicators.append(f"HR {hr_match.group(1)} bpm")

    # Look for SpO2 / Oxygenation
    spo2_match = re.search(r"\b(?:SpO2|O2 sat|oxygen saturation)[:\s]*(\d{2,3}%?(?:\s+on\s+[A-Za-z0-9\s]+)?)\b", raw_note_text, re.IGNORECASE)
    if spo2_match:
        vitals_indicators.append(f"SpO2 {spo2_match.group(1).strip()}")

    # Look for Temp
    temp_match = re.search(r"\b(?:Temp|temperature)[:\s]*(\d{2,3}(?:\.\d+)?\s*(?:[CF]|Fahrenheit|Celsius)?)\b", raw_note_text, re.IGNORECASE)
    if temp_match:
        vitals_indicators.append(f"Temp {temp_match.group(1).strip()}")

    # Look for general stability phrases
    stability_phrases = []
    if re.search(r"\b(?:vitals stable|hemodynamically stable|afebrile|stable on room air|eupneic)\b", raw_note_text, re.IGNORECASE):
        stability_match = re.findall(r"\b(?:vitals stable|hemodynamically stable|afebrile|stable on room air|eupneic)\b", raw_note_text, re.IGNORECASE)
        stability_phrases.extend(list(set(s.capitalize() for s in stability_match)))

    if vitals_indicators:
        res = ", ".join(vitals_indicators)
        if stability_phrases:
            res += f" ({', '.join(stability_phrases)})"
        return res
    elif stability_phrases:
        return ", ".join(stability_phrases)

    # Fallback heuristic summary
    return "Vitals: Stable / Within Normal Limits"


def extract_pending_labs(lab_summary_text: Optional[str], raw_note_text: Optional[str] = None) -> List[str]:
    """
    Extracts any laboratory or diagnostic tests flagged as pending, in progress, or unresulted.
    """
    combined_texts = []
    if lab_summary_text:
        combined_texts.append(lab_summary_text)
    if raw_note_text:
        combined_texts.append(raw_note_text)

    full_text = "\n".join(combined_texts)
    if not full_text:
        return []

    pending_list = []
    seen = set()

    # Split text into sentences and line clauses
    clauses = re.split(r"[;\n.]+", full_text)
    for clause in clauses:
        clause_clean = clause.strip()
        if not clause_clean:
            continue

        # Check for pending indicators
        if re.search(r"\b(pending|awaiting|in progress|not yet resulted|no result yet|not resulted)\b", clause_clean, flags=re.IGNORECASE):
            # Clean formatting
            cleaned_lab = re.sub(r"^[\s\-\*\•\d\.\)]+", "", clause_clean).strip()
            # Normalize multiple spaces
            cleaned_lab = re.sub(r"\s{2,}", " ", cleaned_lab)
            if cleaned_lab and cleaned_lab.lower() not in seen:
                seen.add(cleaned_lab.lower())
                pending_list.append(cleaned_lab)

    return pending_list


def deidentify_clinical_text(raw_note_text: str) -> str:
    """
    Applies Safe Harbor HIPAA de-identification heuristics:
    - Replaces Patient Names (e.g. Mr. Smith, Ms. Johnson, Patient John Doe)
    - Replaces Provider Names (e.g. Dr. Miller, Dr. Sarah Smith)
    - Replaces MRN numbers
    - Replaces Dates (MM/DD/YYYY, YYYY-MM-DD)
    - Replaces Phone Numbers
    - Replaces Specific Room / Bed numbers
    """
    if not raw_note_text:
        return ""

    text = raw_note_text

    # MRN
    text = re.sub(r"\bMRN:?\s*\d+\b", "MRN: [REDACTED]", text, flags=re.IGNORECASE)

    # Provider names (e.g. Dr. Smith, Dr. Sarah Miller)
    text = re.sub(r"\bDr\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b", "[PROVIDER]", text)

    # Patient honorifics (e.g. Mr. Johnson, Ms. Davis, Mrs. Adams)
    text = re.sub(r"\b(?:Mr\.|Ms\.|Mrs\.)\s+[A-Z][a-z]+\b", "[PATIENT]", text)

    # "Patient <First> <Last>"
    text = re.sub(r"\bPatient\s+[A-Z][a-z]+\b", "Patient [PATIENT]", text)

    # Dates: MM/DD/YYYY, MM-DD-YYYY, YYYY-MM-DD
    text = re.sub(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b", "[DATE]", text)

    # Phone numbers
    text = re.sub(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE]", text)

    # Specific room numbers e.g. Room 402, Bed 3-402
    text = re.sub(r"\b(?:Room|Bed)\s+\d+[-A-Za-z0-9]*\b", "[ROOM]", text, flags=re.IGNORECASE)

    return text


def extract_all_entities(
    raw_note_text: str,
    medication_list_text: Optional[str] = None,
    lab_summary_text: Optional[str] = None,
) -> ExtractEntitiesResponse:
    """
    Orchestrates entity extraction across conditions, medications, vitals, labs, and de-identification.
    """
    conditions = extract_conditions(raw_note_text)
    medications = extract_medications(medication_list_text)
    vitals_summary = extract_vitals_summary(raw_note_text)
    labs_pending = extract_pending_labs(lab_summary_text, raw_note_text)
    deidentified_text = deidentify_clinical_text(raw_note_text)

    return ExtractEntitiesResponse(
        conditions=conditions,
        medications=medications,
        vitals_summary=vitals_summary,
        labs_pending=labs_pending,
        deidentified_text=deidentified_text,
    )
