"""
Multi-Agent Reasoning Engine for AI Discharge Readiness.
Implements 4 concurrent category agents via asyncio.gather and 1 downstream Synthesis Agent
using the Anthropic Python SDK with forced tool use.
"""

import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from anthropic import AsyncAnthropic

try:
    from .models import (
        EvaluateRequest,
        ClinicalBarrier,
        FollowUpRecommendation,
        PatientFriendlySummary,
        DischargeReadinessEvaluation,
        SubAgentBarrierItem,
        ReportBarriersPayload,
        SynthesisPayload,
        ReadinessTier,
    )
    from .aggregator import tag_clinical_barrier, compute_deterministic_readiness
except ImportError:
    from models import (
        EvaluateRequest,
        ClinicalBarrier,
        FollowUpRecommendation,
        PatientFriendlySummary,
        DischargeReadinessEvaluation,
        SubAgentBarrierItem,
        ReportBarriersPayload,
        SynthesisPayload,
        ReadinessTier,
    )
    from aggregator import tag_clinical_barrier, compute_deterministic_readiness

logger = logging.getLogger("ai_orchestrator")
logging.basicConfig(level=logging.INFO)


# --- Anthropic Tool Schemas for Forced Tool Use ---

REPORT_BARRIERS_TOOL = {
    "name": "report_barriers",
    "description": "Reports identified discharge barriers for a specific domain with assigned roles and severity.",
    "input_schema": {
        "type": "object",
        "properties": {
            "barriers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "barrier_description": {
                            "type": "string",
                            "description": "Clear clinical description of the discharge barrier."
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["Critical", "Moderate", "Minor"],
                            "description": "Severity level of the barrier."
                        },
                        "required_action": {
                            "type": "string",
                            "description": "Actionable next step required to clear the barrier."
                        },
                        "assigned_role": {
                            "type": "string",
                            "enum": ["Physician", "Nurse", "Pharmacist", "Case_Manager"],
                            "description": "Healthcare role responsible for resolving this barrier."
                        },
                        "source_field_hint": {
                            "type": "string",
                            "description": "Optional hint on the source note."
                        }
                    },
                    "required": ["barrier_description", "severity", "required_action", "assigned_role"]
                }
            }
        },
        "required": ["barriers"]
    }
}

SYNTHESIZE_PLAN_TOOL = {
    "name": "synthesize_discharge_plan",
    "description": "Produces follow-up recommendations, readmission risk assessment, and 6th-grade patient-friendly summary.",
    "input_schema": {
        "type": "object",
        "properties": {
            "follow_up_recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "timeframe_days": {
                            "type": "integer",
                            "description": "Days post-discharge for follow-up appointment or lab."
                        },
                        "specialty": {
                            "type": "string",
                            "description": "Medical specialty (e.g. Primary Care, Cardiology)."
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["Mandatory", "Recommended"],
                            "description": "Priority. Mandatory for critical clinical issues."
                        },
                        "rationale": {
                            "type": "string",
                            "description": "Clinical rationale for this follow-up."
                        }
                    },
                    "required": ["timeframe_days", "specialty", "priority", "rationale"]
                }
            },
            "readmission_risk": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Overall readmission risk classification."
            },
            "readmission_risk_reason": {
                "type": "string",
                "description": "Single concrete sentence explaining readmission drivers (length of stay, SDOH, severity mix)."
            },
            "patient_friendly_summary": {
                "type": "object",
                "properties": {
                    "reading_grade_level": {
                        "type": "string",
                        "enum": ["6th Grade"],
                        "description": "Fixed at '6th Grade'"
                    },
                    "medication_schedule": {
                        "type": "string",
                        "description": "Clear, jargon-free instructions on when and how to take medications."
                    },
                    "red_flag_warning_signs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Actionable emergency warning signs (e.g. 'Call 911 if you have sudden chest pain')."
                    },
                    "next_appointment_notes": {
                        "type": "string",
                        "description": "Simple summary of what appointments are scheduled and what to bring."
                    }
                },
                "required": ["reading_grade_level", "medication_schedule", "red_flag_warning_signs", "next_appointment_notes"]
            }
        },
        "required": ["follow_up_recommendations", "readmission_risk", "readmission_risk_reason", "patient_friendly_summary"]
    }
}


class AIOrchestrationPipeline:
    def __init__(self, api_key: Optional[str] = None, model_id: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model_id = model_id or os.getenv("MODEL_ID", "claude-3-5-sonnet-20241022")
        # Handle custom / standard alias
        if self.model_id in ["claude-sonnet-5", "claude-sonnet", "default"]:
            self.model_id = "claude-3-5-sonnet-20241022"

        self.client: Optional[AsyncAnthropic] = None
        if self.api_key and not self.api_key.startswith("sk-ant-your-key"):
            try:
                self.client = AsyncAnthropic(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Anthropic client: {e}")

    # --------------------------------------------------------------------------
    # Sub-Agent 1: Clinical Stability Agent
    # --------------------------------------------------------------------------
    async def run_clinical_agent(self, request: EvaluateRequest) -> List[ClinicalBarrier]:
        system_prompt = (
            "You are a Hospital Clinical Stability Agent. Analyze vitals, pending labs, conditions, and clinical notes. "
            "Identify ONLY Category='Clinical' barriers to discharge (e.g. pending critical labs/cultures, unstable vitals, "
            "unconfirmed home oxygen, pending therapy clearance). "
            "CONSERVATIVE CLINICAL POLICY: When in doubt, flag the issue rather than clearing the patient. "
            "For any pending blood culture, sepsis marker, or critical lab without final result, assign severity='Critical' "
            "and required_action='Await final lab/culture clearance before discharge' with assigned_role='Physician'. "
            "You must invoke the tool 'report_barriers'."
        )

        user_content = (
            f"Conditions: {request.structured_clinical_data.conditions}\n"
            f"Vitals Summary: {request.structured_clinical_data.vitals_summary}\n"
            f"Labs Pending: {request.structured_clinical_data.labs_pending}\n"
            f"Admission Notes: {request.raw_context.admission_notes}\n"
            f"Lab Summary Notes: {request.raw_context.lab_summary}"
        )

        items = await self._call_barrier_agent("Clinical", system_prompt, user_content, request)
        return [tag_clinical_barrier(item, "Clinical", "clinical_note") for item in items]

    # --------------------------------------------------------------------------
    # Sub-Agent 2: Medication Reconciliation Agent
    # --------------------------------------------------------------------------
    async def run_medication_agent(self, request: EvaluateRequest) -> List[ClinicalBarrier]:
        system_prompt = (
            "You are a Hospital Medication Reconciliation Agent. Analyze prescribed medications and notes. "
            "Identify ONLY Category='Medication' barriers (drug-drug interactions, high-risk polypharmacy without renal adjust, "
            "missing dosage or frequency, pending prior authorizations for critical meds). "
            "CRITICAL SAFETY RULE: NEVER invent or assume a dosage or frequency that is missing in the data. "
            "A missing dosage or frequency is itself a Medication barrier (assigned_role='Pharmacist' or 'Physician'). "
            "You must invoke the tool 'report_barriers'."
        )

        user_content = (
            f"Structured Medications: {request.structured_clinical_data.medications}\n"
            f"Medication List Text: {request.raw_context.medication_list}\n"
            f"Admission Notes: {request.raw_context.admission_notes}"
        )

        items = await self._call_barrier_agent("Medication", system_prompt, user_content, request)
        return [tag_clinical_barrier(item, "Medication", "medications") for item in items]

    # --------------------------------------------------------------------------
    # Sub-Agent 3: Caregiver & SDOH Agent
    # --------------------------------------------------------------------------
    async def run_sdoh_agent(self, request: EvaluateRequest) -> List[ClinicalBarrier]:
        system_prompt = (
            "You are a Hospital Social Determinants of Health (SDOH) and Caregiver Readiness Agent. "
            "Analyze caregiver notes and patient social context. "
            "Identify ONLY Category='Caregiver_SDOH' barriers (e.g. lives alone without confirmed home support, "
            "unsafe home environment/stairs without ramp, lack of transportation for follow-ups, cognitive impairment without caregiver). "
            "Assign assigned_role='Case_Manager' or 'Nurse'. "
            "You must invoke the tool 'report_barriers'."
        )

        user_content = (
            f"Caregiver Notes: {request.raw_context.caregiver_notes}\n"
            f"Admission Notes: {request.raw_context.admission_notes}"
        )

        items = await self._call_barrier_agent("Caregiver_SDOH", system_prompt, user_content, request)
        return [tag_clinical_barrier(item, "Caregiver_SDOH", "caregiver_notes") for item in items]

    # --------------------------------------------------------------------------
    # Sub-Agent 4: Admin & Logistics Agent
    # --------------------------------------------------------------------------
    async def run_admin_agent(self, request: EvaluateRequest) -> List[ClinicalBarrier]:
        system_prompt = (
            "You are a Hospital Administrative and Logistics Clearance Agent. "
            "Analyze insurance notes and discharge planning administrative requirements. "
            "Identify ONLY Category='Administrative' barriers (e.g. pending prior authorization for DME/equipment, "
            "no confirmed primary care follow-up slot, durable medical equipment not delivered, pending transportation booking). "
            "Assign assigned_role='Case_Manager' or 'Physician'. "
            "You must invoke the tool 'report_barriers'."
        )

        user_content = (
            f"Insurance & Admin Notes: {request.raw_context.insurance_notes}\n"
            f"Caregiver Notes: {request.raw_context.caregiver_notes}"
        )

        items = await self._call_barrier_agent("Administrative", system_prompt, user_content, request)
        return [tag_clinical_barrier(item, "Administrative", "insurance_notes") for item in items]

    # --------------------------------------------------------------------------
    # Generic Helper for Category Agent Calls (with Anthropic forced tool use)
    # --------------------------------------------------------------------------
    async def _call_barrier_agent(
        self,
        domain: str,
        system_prompt: str,
        user_content: str,
        request: EvaluateRequest,
    ) -> List[SubAgentBarrierItem]:
        if not self.client:
            # Fallback to local heuristic extractor if no Anthropic API client is configured
            return self._heuristic_barrier_fallback(domain, request)

        try:
            response = await asyncio.wait_for(
                self.client.messages.create(
                    model=self.model_id,
                    max_tokens=1000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_content}],
                    tools=[REPORT_BARRIERS_TOOL],
                    tool_choice={"type": "tool", "name": "report_barriers"},
                ),
                timeout=18.0
            )

            # Extract tool use block
            for block in response.content:
                if block.type == "tool_use" and block.name == "report_barriers":
                    payload = ReportBarriersPayload.model_validate(block.input)
                    return payload.barriers

            logger.warning(f"[{domain} Agent] No tool_use block in response.")
            return []

        except Exception as e:
            logger.warning(f"[{domain} Agent] Call failed or timed out: {e}. Using deterministic fallback.")
            return self._heuristic_barrier_fallback(domain, request)

    # --------------------------------------------------------------------------
    # Sub-Agent 5: Synthesis Agent
    # --------------------------------------------------------------------------
    async def run_synthesis_agent(
        self,
        request: EvaluateRequest,
        barriers: List[ClinicalBarrier],
        score: int,
        tier: ReadinessTier,
    ) -> SynthesisPayload:
        system_prompt = (
            "You are a Hospital Discharge Synthesis and Patient Education Specialist. "
            "You will synthesize post-discharge follow-up recommendations, readmission risk, and a patient-friendly discharge guide. "
            "MANDATORY GUIDELINES:\n"
            "1. 6th-Grade Reading Level: Write medication_schedule and next_appointment_notes with simple words, short sentences, and zero medical jargon. Define any unavoidable term.\n"
            "2. Red-Flag Warning Signs: Provide 3-5 concrete, urgent, actionable warning symptoms (e.g. 'Call 911 if you have chest pain, shortness of breath, or sudden weakness').\n"
            "3. Mandatory Follow-Ups: For EVERY Critical clinical barrier present, you MUST create at least one follow-up recommendation with priority='Mandatory'.\n"
            "4. Readmission Risk: Assign low, medium, or high. Formulate a single concrete sentence for readmission_risk_reason weighing days admitted, SDOH gaps (e.g. living alone), and barrier severity mix.\n"
            "You must invoke the tool 'synthesize_discharge_plan'."
        )

        barriers_summary = [b.model_dump() for b in barriers]
        user_content = (
            f"Patient ID: {request.patient_id}\n"
            f"Days Admitted: {request.raw_context.days_admitted}\n"
            f"Computed Readiness Score: {score}/100\n"
            f"Computed Readiness Tier: {tier}\n"
            f"All Identified Barriers: {json.dumps(barriers_summary, indent=2)}\n"
            f"Admission Notes: {request.raw_context.admission_notes}\n"
            f"Medication List: {request.raw_context.medication_list}\n"
            f"Caregiver Notes: {request.raw_context.caregiver_notes}\n"
            f"Insurance Notes: {request.raw_context.insurance_notes}"
        )

        if not self.client:
            return self._heuristic_synthesis_fallback(request, barriers, score, tier)

        try:
            response = await asyncio.wait_for(
                self.client.messages.create(
                    model=self.model_id,
                    max_tokens=1500,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_content}],
                    tools=[SYNTHESIZE_PLAN_TOOL],
                    tool_choice={"type": "tool", "name": "synthesize_discharge_plan"},
                ),
                timeout=18.0
            )

            for block in response.content:
                if block.type == "tool_use" and block.name == "synthesize_discharge_plan":
                    return SynthesisPayload.model_validate(block.input)

            logger.warning("[Synthesis Agent] No tool_use block in response. Using fallback synthesis.")
            return self._heuristic_synthesis_fallback(request, barriers, score, tier)

        except Exception as e:
            logger.warning(f"[Synthesis Agent] Call failed or timed out: {e}. Using fallback synthesis.")
            return self._heuristic_synthesis_fallback(request, barriers, score, tier)

    # --------------------------------------------------------------------------
    # Full Concurrent Multi-Agent Pipeline
    # --------------------------------------------------------------------------
    async def evaluate(self, request: EvaluateRequest) -> DischargeReadinessEvaluation:
        """
        Executes the 4 category agents concurrently via asyncio.gather,
        runs the deterministic aggregator (pure Python),
        and invokes the Synthesis agent to assemble the final contract.
        """
        logger.info(f"Starting multi-agent evaluation for patient: {request.patient_id}")

        # Phase 1: 4 Category Agents run CONCURRENTLY
        clinical_barriers, med_barriers, sdoh_barriers, admin_barriers = await asyncio.gather(
            self.run_clinical_agent(request),
            self.run_medication_agent(request),
            self.run_sdoh_agent(request),
            self.run_admin_agent(request),
            return_exceptions=False
        )

        all_barriers: List[ClinicalBarrier] = (
            clinical_barriers + med_barriers + sdoh_barriers + admin_barriers
        )

        # Phase 2: Pure Python Deterministic Aggregator
        score, tier, estimated_time = compute_deterministic_readiness(all_barriers)
        logger.info(
            f"Aggregator computed for {request.patient_id}: score={score}, tier={tier}, "
            f"barriers={len(all_barriers)}, estimated_ready_time={estimated_time}"
        )

        # Phase 3: Synthesis Agent
        synthesis = await self.run_synthesis_agent(request, all_barriers, score, tier)

        # Ensure mandatory follow-up rule is satisfied deterministically
        has_crit_clinical = any(b.category == "Clinical" and b.severity == "Critical" for b in all_barriers)
        if has_crit_clinical and not any(r.priority == "Mandatory" for r in synthesis.follow_up_recommendations):
            synthesis.follow_up_recommendations.insert(
                0,
                FollowUpRecommendation(
                    timeframe_days=2,
                    specialty="Primary Care / Attending Physician",
                    priority="Mandatory",
                    rationale="Required follow-up due to unresolved critical clinical issues during admission."
                )
            )

        # Phase 4: Final Pydantic Schema Assembly & Validation
        evaluation = DischargeReadinessEvaluation(
            patient_id=request.patient_id,
            readiness_score=score,
            readiness_tier=tier,
            estimated_ready_time=estimated_time,
            clinical_barriers=all_barriers,
            follow_up_recommendations=synthesis.follow_up_recommendations,
            readmission_risk=synthesis.readmission_risk,
            readmission_risk_reason=synthesis.readmission_risk_reason,
            patient_friendly_summary=synthesis.patient_friendly_summary,
        )

        return evaluation

    # --------------------------------------------------------------------------
    # Deterministic Heuristic Fallbacks (Offline & Fault-Tolerant Engine)
    # --------------------------------------------------------------------------
    def _heuristic_barrier_fallback(self, domain: str, request: EvaluateRequest) -> List[SubAgentBarrierItem]:
        barriers: List[SubAgentBarrierItem] = []
        raw_text = (
            f"{request.raw_context.admission_notes} {request.raw_context.medication_list} "
            f"{request.raw_context.lab_summary} {request.raw_context.caregiver_notes} "
            f"{request.raw_context.insurance_notes}"
        ).lower()

        if domain == "Clinical":
            # Check pending labs
            for lab in request.structured_clinical_data.labs_pending:
                lab_l = str(lab).lower()
                if "blood culture" in lab_l or "sepsis" in lab_l or "culture" in lab_l:
                    barriers.append(SubAgentBarrierItem(
                        barrier_description=f"Pending critical microbiology culture: {lab}",
                        severity="Critical",
                        required_action="Review final blood culture results and confirm no organism growth prior to discharge.",
                        assigned_role="Physician"
                    ))
                elif "pending" in lab_l or "no result" in lab_l:
                    barriers.append(SubAgentBarrierItem(
                        barrier_description=f"Pending laboratory result: {lab}",
                        severity="Moderate",
                        required_action="Verify pending laboratory test result is within safe range.",
                        assigned_role="Physician"
                    ))
            # Check notes for oxygen or therapy
            if "oxygen" in raw_text and ("pending" in raw_text or "not confirmed" in raw_text or "ordered" in raw_text):
                barriers.append(SubAgentBarrierItem(
                    barrier_description="Home oxygen ordered but delivery setup is not yet verified.",
                    severity="Critical",
                    required_action="Confirm home oxygen delivery and verify room-air vs oxygen titration with respiratory therapy.",
                    assigned_role="Physician"
                ))
            if "physical therapy" in raw_text or "pt clearance" in raw_text or "mobility" in raw_text:
                if "pending" in raw_text or "moderate" in raw_text:
                    barriers.append(SubAgentBarrierItem(
                        barrier_description="Physical therapy mobility evaluation pending safe discharge clearance.",
                        severity="Moderate",
                        required_action="Complete PT functional assessment for safe home ambulation.",
                        assigned_role="Nurse"
                    ))

        elif domain == "Medication":
            med_text = (request.raw_context.medication_list or "").lower()
            if "interaction" in med_text or "flagged drug-drug" in med_text:
                barriers.append(SubAgentBarrierItem(
                    barrier_description="Flagged drug-drug interaction on active medication profile.",
                    severity="Critical",
                    required_action="Pharmacist reconciliation required to adjust dosing or substitute interacting agent.",
                    assigned_role="Pharmacist"
                ))
            if "prior auth" in med_text or "prior authorization" in med_text:
                barriers.append(SubAgentBarrierItem(
                    barrier_description="High-cost medication requires pending prior authorization approval.",
                    severity="Moderate",
                    required_action="Submit insurance prior authorization or arrange interim pharmacy bridge supply.",
                    assigned_role="Pharmacist"
                ))
            # Check structured meds with null dose
            for m in request.structured_clinical_data.medications:
                if isinstance(m, dict) and (m.get("dose") is None or m.get("frequency") is None):
                    barriers.append(SubAgentBarrierItem(
                        barrier_description=f"Medication '{m.get('name')}' missing explicit dosage or administration frequency.",
                        severity="Moderate",
                        required_action="Clarify order dosage and frequency with ordering provider.",
                        assigned_role="Pharmacist"
                    ))

        elif domain == "Caregiver_SDOH":
            cg_text = (request.raw_context.caregiver_notes or "").lower()
            if "lives alone" in cg_text and ("no confirmed" in cg_text or "daughter out of state" in cg_text or "no support" in cg_text):
                barriers.append(SubAgentBarrierItem(
                    barrier_description="Patient lives alone with no confirmed family or caregiver support at home.",
                    severity="Critical",
                    required_action="Arrange home health aide support or verify community social services before discharge.",
                    assigned_role="Case_Manager"
                ))
            elif "transportation" in cg_text or "ride" in cg_text:
                barriers.append(SubAgentBarrierItem(
                    barrier_description="Transportation gap identified for post-discharge medical visits.",
                    severity="Minor",
                    required_action="Schedule medical transit voucher or confirm family ride.",
                    assigned_role="Case_Manager"
                ))

        elif domain == "Administrative":
            ins_text = (request.raw_context.insurance_notes or "").lower()
            if "prior auth" in ins_text and ("pending" in ins_text or "submitted" in ins_text):
                barriers.append(SubAgentBarrierItem(
                    barrier_description="Insurance prior authorization for post-acute services/equipment is pending approval.",
                    severity="Moderate",
                    required_action="Expedite insurance case review and obtain approval reference number.",
                    assigned_role="Case_Manager"
                ))
            if "equipment" in ins_text and ("not yet delivered" in ins_text or "pending" in ins_text):
                barriers.append(SubAgentBarrierItem(
                    barrier_description="Durable medical equipment (DME) delivery not yet confirmed at residence.",
                    severity="Moderate",
                    required_action="Contact medical equipment vendor to confirm same-day delivery time window.",
                    assigned_role="Case_Manager"
                ))

        return barriers

    def _heuristic_synthesis_fallback(
        self,
        request: EvaluateRequest,
        barriers: List[ClinicalBarrier],
        score: int,
        tier: ReadinessTier,
    ) -> SynthesisPayload:
        # Determine readmission risk
        crit_count = sum(1 for b in barriers if b.severity == "Critical")
        has_sdoh = any(b.category == "Caregiver_SDOH" for b in barriers)
        days = request.raw_context.days_admitted or 0

        if crit_count > 0 or (has_sdoh and days >= 4):
            risk = "high"
            reason = f"High readmission risk driven by {crit_count} critical safety barrier(s) and {days} days inpatient length of stay."
        elif len(barriers) > 0 or days >= 3:
            risk = "medium"
            reason = f"Moderate readmission risk due to active care transition barriers and post-discharge recovery needs."
        else:
            risk = "low"
            reason = "Low readmission risk; patient meets clinical stabilization milestones with adequate transition planning."

        # Follow ups
        recs = [
            FollowUpRecommendation(
                timeframe_days=3 if tier != "Ready" else 7,
                specialty="Primary Care Physician",
                priority="Mandatory" if tier != "Ready" else "Recommended",
                rationale="Routine post-discharge clinical evaluation and medication reconciliation check."
            )
        ]
        if any(b.category == "Clinical" for b in barriers):
            recs.append(
                FollowUpRecommendation(
                    timeframe_days=2,
                    specialty="Specialty Care / Outpatient Clinic",
                    priority="Mandatory" if tier == "High_Risk_Blocked" else "Recommended",
                    rationale="Monitor resolution of acute clinical conditions and review laboratory values."
                )
            )

        med_schedule = (
            "Take all medicines exactly as written on your pill bottles. "
            "Take morning pills with a full glass of water and breakfast. "
            "Do not stop taking any medicine without calling your doctor first."
        )

        red_flags = [
            "Call 911 immediately if you have trouble breathing, chest pain, or sudden dizziness.",
            "Call your doctor right away if your fever goes over 101°F or if your symptoms get worse.",
            "Call your clinic if you cannot keep food or fluids down for more than 12 hours."
        ]

        appts = (
            "Your follow-up visit is scheduled within 3 to 7 days. "
            "Please bring all your medicine bottles and your hospital discharge papers to your appointment."
        )

        summary = PatientFriendlySummary(
            reading_grade_level="6th Grade",
            medication_schedule=med_schedule,
            red_flag_warning_signs=red_flags,
            next_appointment_notes=appts,
        )

        return SynthesisPayload(
            follow_up_recommendations=recs,
            readmission_risk=risk,
            readmission_risk_reason=reason,
            patient_friendly_summary=summary,
        )
