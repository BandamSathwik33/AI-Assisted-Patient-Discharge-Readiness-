"""
Unit and Integration Tests for AI Multi-Agent Orchestrator (Person 3).
Tests:
- Deterministic aggregator math & hard-override safety rules
- Citation source-field tagging
- Concurrent pipeline execution
- Schema validation against team data contract
- FastAPI endpoint responses (/health, /orchestrate/evaluate)
"""

import json
import pytest
import asyncio
import sys
from pathlib import Path
from starlette.testclient import TestClient

# Add current folder to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from models import (
    ClinicalBarrier,
    SubAgentBarrierItem,
    EvaluateRequest,
    DischargeReadinessEvaluation,
)
from aggregator import tag_clinical_barrier, compute_deterministic_readiness
from agents import AIOrchestrationPipeline
from main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# -----------------------------------------------------------------------------
# 1. Deterministic Aggregator & Safety Rules Tests
# -----------------------------------------------------------------------------

def test_aggregator_zero_barriers():
    """Clean patient should have score=100, tier='Ready', estimated_ready_time='now'."""
    score, tier, est_time = compute_deterministic_readiness([])
    assert score == 100
    assert tier == "Ready"
    assert est_time == "now"


def test_aggregator_moderate_barriers():
    """
    1 Moderate barrier: 100 - 15 = 85 -> tier='Ready', est_time='now'.
    2 Moderate barriers: 100 - 30 = 70 -> tier='Near_Ready', est_time='within_4h'.
    """
    b1 = ClinicalBarrier(
        category="Clinical",
        barrier_description="Pending PT evaluation",
        severity="Moderate",
        required_action="Complete PT clearance",
        assigned_role="Nurse",
        source_field="clinical_note"
    )
    score1, tier1, est1 = compute_deterministic_readiness([b1])
    assert score1 == 85
    assert tier1 == "Ready"
    assert est1 == "now"

    b2 = ClinicalBarrier(
        category="Administrative",
        barrier_description="DME delivery pending",
        severity="Moderate",
        required_action="Confirm delivery window",
        assigned_role="Case_Manager",
        source_field="insurance_notes"
    )
    score2, tier2, est2 = compute_deterministic_readiness([b1, b2])
    assert score2 == 70
    assert tier2 == "Near_Ready"
    assert est2 == "within_4h"


def test_aggregator_critical_barrier_hard_override():
    """
    ANY Critical barrier MUST force readiness_tier='High_Risk_Blocked'
    and estimated_ready_time='by_tomorrow_am', regardless of score.
    """
    b_crit = ClinicalBarrier(
        category="Clinical",
        barrier_description="Pending blood culture result in sepsis",
        severity="Critical",
        required_action="Await microbiology clearance",
        assigned_role="Physician",
        source_field="lab_summary"
    )
    score, tier, est_time = compute_deterministic_readiness([b_crit])
    assert score == 60  # 100 - 40
    assert tier == "High_Risk_Blocked"
    assert est_time == "by_tomorrow_am"


def test_aggregator_floor_at_zero():
    """Scores below 0 must be floored at 0."""
    crit_barriers = [
        ClinicalBarrier(
            category="Clinical",
            barrier_description=f"Critical issue {i}",
            severity="Critical",
            required_action="Action",
            assigned_role="Physician",
            source_field="clinical_note"
        )
        for i in range(4)  # 4 * 40 = 160 deduction
    ]
    score, tier, est_time = compute_deterministic_readiness(crit_barriers)
    assert score == 0
    assert tier == "High_Risk_Blocked"
    assert est_time == "by_tomorrow_am"


# -----------------------------------------------------------------------------
# 2. Source-Field Citation Tagging Tests
# -----------------------------------------------------------------------------

def test_source_field_tagging():
    """Verify programmatic tagging maps correctly to citations without LLM hallucination."""
    # Clinical agent with lab keyword
    sub_lab = SubAgentBarrierItem(
        barrier_description="Blood culture results still pending",
        severity="Critical",
        required_action="Await final culture clearance",
        assigned_role="Physician"
    )
    barr_lab = tag_clinical_barrier(sub_lab, "Clinical", "clinical_note")
    assert barr_lab.source_field == "lab_summary"
    assert barr_lab.category == "Clinical"

    # Clinical agent with general note keyword
    sub_clin = SubAgentBarrierItem(
        barrier_description="Unstable ambulatory balance on room air",
        severity="Moderate",
        required_action="Assess fall risk",
        assigned_role="Nurse"
    )
    barr_clin = tag_clinical_barrier(sub_clin, "Clinical", "clinical_note")
    assert barr_clin.source_field == "clinical_note"

    # Medication agent
    sub_med = SubAgentBarrierItem(
        barrier_description="High-risk drug interaction",
        severity="Critical",
        required_action="Reconcile profile",
        assigned_role="Pharmacist"
    )
    barr_med = tag_clinical_barrier(sub_med, "Medication", "medications")
    assert barr_med.source_field == "medications"
    assert barr_med.category == "Medication"

    # SDOH agent
    sub_sdoh = SubAgentBarrierItem(
        barrier_description="Lives alone with no family support",
        severity="Critical",
        required_action="Arrange home health aide",
        assigned_role="Case_Manager"
    )
    barr_sdoh = tag_clinical_barrier(sub_sdoh, "Caregiver_SDOH", "caregiver_notes")
    assert barr_sdoh.source_field == "caregiver_notes"
    assert barr_sdoh.category == "Caregiver_SDOH"


# -----------------------------------------------------------------------------
# 3. Pipeline Execution Against Test Fixtures
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pipeline_case_1_ready():
    """Case 1 (CHF resolved) should be Ready or Near_Ready with valid schema."""
    with open(FIXTURES_DIR / "case_1_ready.json", "r") as f:
        data = json.load(f)
    req = EvaluateRequest.model_validate(data)

    pipeline = AIOrchestrationPipeline()
    res = await pipeline.evaluate(req)

    assert isinstance(res, DischargeReadinessEvaluation)
    assert res.patient_id == "P-1001"
    assert res.readiness_tier in ["Ready", "Near_Ready"]
    assert res.patient_friendly_summary.reading_grade_level == "6th Grade"
    assert len(res.patient_friendly_summary.red_flag_warning_signs) > 0


@pytest.mark.asyncio
async def test_pipeline_case_2_critical_sepsis():
    """Case 2 (Sepsis pending cultures) MUST be High_Risk_Blocked with Mandatory follow-up."""
    with open(FIXTURES_DIR / "case_2_critical_sepsis.json", "r") as f:
        data = json.load(f)
    req = EvaluateRequest.model_validate(data)

    pipeline = AIOrchestrationPipeline()
    res = await pipeline.evaluate(req)

    assert isinstance(res, DischargeReadinessEvaluation)
    assert res.patient_id == "P-1005"
    assert res.readiness_tier == "High_Risk_Blocked"
    assert res.estimated_ready_time == "by_tomorrow_am"

    # Confirm at least one critical barrier exists with lab_summary source citation
    has_crit_lab = any(
        b.severity == "Critical" and b.source_field == "lab_summary"
        for b in res.clinical_barriers
    )
    assert has_crit_lab

    # Confirm at least one Mandatory follow-up exists
    assert any(r.priority == "Mandatory" for r in res.follow_up_recommendations)


@pytest.mark.asyncio
async def test_pipeline_case_3_sdoh_polypharmacy():
    """Case 3 (Living alone + Drug interaction) should detect barriers across multiple categories."""
    with open(FIXTURES_DIR / "case_3_sdoh_polypharmacy.json", "r") as f:
        data = json.load(f)
    req = EvaluateRequest.model_validate(data)

    pipeline = AIOrchestrationPipeline()
    res = await pipeline.evaluate(req)

    assert isinstance(res, DischargeReadinessEvaluation)
    categories = {b.category for b in res.clinical_barriers}
    assert "Medication" in categories or "Caregiver_SDOH" in categories
    assert res.readmission_risk in ["high", "medium"]


# -----------------------------------------------------------------------------
# 4. FastAPI Service Endpoints Test
# -----------------------------------------------------------------------------

def test_fastapi_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_fastapi_orchestrate_evaluate():
    with open(FIXTURES_DIR / "case_2_critical_sepsis.json", "r") as f:
        payload = json.load(f)

    with TestClient(app) as client:
        response = client.post("/orchestrate/evaluate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == "P-1005"
        assert data["readiness_tier"] == "High_Risk_Blocked"
        assert "clinical_barriers" in data
        assert "patient_friendly_summary" in data
        assert data["patient_friendly_summary"]["reading_grade_level"] == "6th Grade"
