"""
Clinical ICD-10 and Condition Mapping Dictionary.
Provides deterministic matching of clinical synonyms and free-text terms to canonical condition names and ICD-10 diagnostic codes.
"""

from typing import Dict, List, Optional, Tuple
import re

CLINICAL_CONDITION_REGISTRY: List[Dict[str, any]] = [
    {
        "name": "Sepsis",
        "icd10_hint": "A41.9",
        "patterns": [
            r"\bsepsis\b",
            r"\bseptic(?:emia)?\b",
            r"\burosepsis\b",
            r"\bbacteremia\b",
            r"\bsevere sepsis\b",
        ],
    },
    {
        "name": "Congestive Heart Failure Exacerbation",
        "icd10_hint": "I50.9",
        "patterns": [
            r"\bchf\b",
            r"\bcongestive heart failure\b",
            r"\bheart failure(?:\s+exacerbation)?\b",
            r"\bhfref\b",
            r"\bhfpef\b",
            r"\bacute decompensated heart failure\b",
            r"\bcardiomyopathy\b",
            r"\bpulmonary edema\b",
        ],
    },
    {
        "name": "Pneumonia",
        "icd10_hint": "J18.9",
        "patterns": [
            r"\bpneumonia\b",
            r"\bcap\b",
            r"\bcommunity[- ]acquired pneumonia\b",
            r"\baspiration pneumonia\b",
            r"\bbronchopneumonia\b",
            r"\blung infiltrate\b",
        ],
    },
    {
        "name": "Post-operative Total Hip Arthroplasty",
        "icd10_hint": "Z96.641",
        "patterns": [
            r"\bhip replacement\b",
            r"\btotal hip arthroplasty\b",
            r"\btha\b",
            r"\bpost[- ]op(?:erative)? hip\b",
            r"\bhip arthroplasty\b",
            r"\bhip fracture(?:\s+repair)?\b",
        ],
    },
    {
        "name": "Type 2 Diabetes Mellitus",
        "icd10_hint": "E11.9",
        "patterns": [
            r"\btype 2 diabetes(?: mellitus)?\b",
            r"\bt2dm\b",
            r"\bdiabetic\b",
            r"\bdiabetes(?: mellitus)?\b",
            r"\bhyperglycemia\b",
            r"\bdka\b",
            r"\bdiabetic ketoacidosis\b",
        ],
    },
    {
        "name": "Acute Appendicitis status post appendectomy",
        "icd10_hint": "K35.80",
        "patterns": [
            r"\bappendicitis\b",
            r"\bappendectomy\b",
            r"\bpost[- ]appendectomy\b",
            r"\blaparoscopic appendectomy\b",
        ],
    },
    {
        "name": "COPD Exacerbation",
        "icd10_hint": "J44.1",
        "patterns": [
            r"\bcopd\b",
            r"\bchronic obstructive pulmonary disease\b",
            r"\bcopd exacerbation\b",
            r"\bemphysema\b",
            r"\bchronic bronchitis\b",
        ],
    },
    {
        "name": "Essential Hypertension",
        "icd10_hint": "I10",
        "patterns": [
            r"\bhypertension\b",
            r"\bhtn\b",
            r"\bhypertensive urgency\b",
            r"\bhypertensive crisis\b",
            r"\bhigh blood pressure\b",
            r"\belevated bp\b",
        ],
    },
    {
        "name": "Atrial Fibrillation",
        "icd10_hint": "I48.91",
        "patterns": [
            r"\batrial fibrillation\b",
            r"\bafib\b",
            r"\ba-fib\b",
            r"\batrial flutter\b",
        ],
    },
    {
        "name": "Deep Vein Thrombosis",
        "icd10_hint": "I82.40",
        "patterns": [
            r"\bdeep vein thrombosis\b",
            r"\bdvt\b",
            r"\bvenous thromboembolism\b",
            r"\bvte\b",
            r"\bpulmonary embolism\b",
            r"\bpe\b",
        ],
    },
    {
        "name": "Acute Kidney Injury",
        "icd10_hint": "N17.9",
        "patterns": [
            r"\bacute kidney injury\b",
            r"\baki\b",
            r"\bacute renal failure\b",
            r"\brenal insufficiency\b",
        ],
    },
    {
        "name": "Cellulitis",
        "icd10_hint": "L03.90",
        "patterns": [
            r"\bcellulitis\b",
            r"\bskin and soft tissue infection\b",
            r"\bssti\b",
            r"\berysipelas\b",
            r"\bwound infection\b",
        ],
    },
    {
        "name": "Cerebrovascular Accident",
        "icd10_hint": "I63.9",
        "patterns": [
            r"\bcerebrovascular accident\b",
            r"\bcva\b",
            r"\bischemic stroke\b",
            r"\bstroke\b",
            r"\btia\b",
            r"\btransient ischemic attack\b",
        ],
    },
    {
        "name": "Urinary Tract Infection",
        "icd10_hint": "N39.0",
        "patterns": [
            r"\burinary tract infection\b",
            r"\buti\b",
            r"\bpyelonephritis\b",
            r"\bcystitis\b",
        ],
    },
    {
        "name": "Coronary Artery Disease",
        "icd10_hint": "I25.10",
        "patterns": [
            r"\bcoronary artery disease\b",
            r"\bcad\b",
            r"\bmyocardial infarction\b",
            r"\bnstemi\b",
            r"\bstemi\b",
            r"\bangina\b",
        ],
    },
    {
        "name": "Gastrointestinal Hemorrhage",
        "icd10_hint": "K92.2",
        "patterns": [
            r"\bgastrointestinal bleed\b",
            r"\bgi bleed\b",
            r"\bmelena\b",
            r"\bpeptic ulcer\b",
            r"\bupper gi bleed\b",
        ],
    },
    {
        "name": "Post-operative Total Knee Arthroplasty",
        "icd10_hint": "Z96.651",
        "patterns": [
            r"\bknee replacement\b",
            r"\btotal knee arthroplasty\b",
            r"\btka\b",
            r"\bpost[- ]op(?:erative)? knee\b",
        ],
    },
    {
        "name": "Asthma Exacerbation",
        "icd10_hint": "J45.901",
        "patterns": [
            r"\basthma\b",
            r"\basthma exacerbation\b",
            r"\bbronchial asthma\b",
            r"\bbronchospasm\b",
        ],
    },
    {
        "name": "Metabolic Encephalopathy",
        "icd10_hint": "G93.41",
        "patterns": [
            r"\bencephalopathy\b",
            r"\baltered mental status\b",
            r"\bams\b",
            r"\bdelirium\b",
        ],
    },
]


def match_conditions_in_text(text: str) -> List[Tuple[str, str]]:
    """
    Scans free text and returns matched (condition_name, icd10_hint) pairs.
    Deduplicates results while preserving order.
    """
    if not text:
        return []

    matched = []
    seen = set()

    for item in CLINICAL_CONDITION_REGISTRY:
        name = item["name"]
        code = item["icd10_hint"]
        for pattern in item["patterns"]:
            if re.search(pattern, text, flags=re.IGNORECASE):
                if name not in seen:
                    seen.add(name)
                    matched.append((name, code))
                break

    return matched
