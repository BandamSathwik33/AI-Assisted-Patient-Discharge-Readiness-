"""
Deterministic Aggregator for Discharge Readiness Evaluation.
Pure Python, non-LLM computation.

This module guarantees reproducible, auditable scoring and hard safety guardrails:
- Scoring: 100 - (40*Critical + 15*Moderate + 5*Minor), floored at 0.
- Safety Override: If any barrier is 'Critical' -> readiness_tier is ALWAYS 'High_Risk_Blocked'.
- Readiness Tiers:
    - Critical barrier present -> 'High_Risk_Blocked'
    - Score >= 85 -> 'Ready'
    - Otherwise -> 'Near_Ready'
- Estimated Ready Time:
    - High_Risk_Blocked -> 'by_tomorrow_am'
    - Near_Ready -> 'within_4h'
    - Ready -> 'now'
"""

from typing import List, Tuple
try:
    from .models import (
        ClinicalBarrier,
        SubAgentBarrierItem,
        BarrierCategory,
        SourceField,
        ReadinessTier,
    )
except ImportError:
    from models import (
        ClinicalBarrier,
        SubAgentBarrierItem,
        BarrierCategory,
        SourceField,
        ReadinessTier,
    )


def tag_clinical_barrier(
    item: SubAgentBarrierItem,
    category: BarrierCategory,
    default_source: SourceField,
) -> ClinicalBarrier:
    """
    Ensures category and source_field are set programmatically from agent domain,
    preventing any LLM hallucination of citation sources or domain fields.
    """
    source_field = default_source
    
    # Context-aware refinement for Clinical agent (differentiates lab vs clinical notes)
    if category == "Clinical":
        desc_lower = item.barrier_description.lower()
        if any(keyword in desc_lower for keyword in ["lab", "culture", "blood", "cbc", "panel", "test", "pending result", "biopsy"]):
            source_field = "lab_summary"
        else:
            source_field = "clinical_note"
            
    return ClinicalBarrier(
        category=category,
        barrier_description=item.barrier_description.strip(),
        severity=item.severity,
        required_action=item.required_action.strip(),
        assigned_role=item.assigned_role,
        source_field=source_field,
    )


def compute_deterministic_readiness(
    barriers: List[ClinicalBarrier],
) -> Tuple[int, ReadinessTier, str]:
    """
    Computes (readiness_score, readiness_tier, estimated_ready_time)
    strictly adhering to the team specification.

    Returns:
        (readiness_score: int, readiness_tier: ReadinessTier, estimated_ready_time: str)
    """
    crit_count = sum(1 for b in barriers if b.severity == "Critical")
    mod_count = sum(1 for b in barriers if b.severity == "Moderate")
    min_count = sum(1 for b in barriers if b.severity == "Minor")

    raw_score = 100 - (40 * crit_count + 15 * mod_count + 5 * min_count)
    readiness_score = max(0, min(100, raw_score))

    # Deterministic safety rule: ANY Critical barrier forces High_Risk_Blocked
    if crit_count > 0:
        readiness_tier: ReadinessTier = "High_Risk_Blocked"
        estimated_ready_time = "by_tomorrow_am"
    elif readiness_score >= 85:
        readiness_tier = "Ready"
        estimated_ready_time = "now"
    else:
        readiness_tier = "Near_Ready"
        estimated_ready_time = "within_4h"

    return readiness_score, readiness_tier, estimated_ready_time
