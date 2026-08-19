# AI Multi-Agent Orchestration Engine (`discharge-ai-orchestrator`)

## Overview
The **AI Multi-Agent Orchestration Engine** (Port `8001`) provides clinical-grade reasoning for the *AI-Assisted Patient Discharge Readiness & Follow-Up Planner*.

It ingests structured clinical entities and raw EHR notes, executes **4 specialized category agents concurrently** with forced tool use, feeds the findings into a **pure Python deterministic aggregator** (non-LLM), and synthesizes a patient-friendly care transition plan at a **6th-grade reading level**.

---

## Key Clinical & Architectural Innovations

1. **Deterministic Safety Guardrails (Non-LLM Overrides)**:
   - Scoring is purely mathematical:
     $$\text{readiness\_score} = \max(0, 100 - (40 \times N_{\text{Critical}} + 15 \times N_{\text{Moderate}} + 5 \times N_{\text{Minor}}))$$
   - **Hard Safety Override**: Any Critical barrier (e.g. pending blood culture in sepsis, unconfirmed home oxygen, severe drug-drug interaction) **unconditionally forces** `readiness_tier = "High_Risk_Blocked"` and `estimated_ready_time = "by_tomorrow_am"`, regardless of the numeric score.
   - The AI is never the sole gatekeeper: the same deterministic rule is independently enforced by Core Backend (Person 2) for multi-layered defense-in-depth.

2. **Source-Field Citation ("The Wow Moment")**:
   - Every identified barrier is programmatically linked to its exact provenance field (`clinical_note`, `medications`, `lab_summary`, `caregiver_notes`, or `insurance_notes`).
   - Prevents AI hallucinations and gives clinicians complete visibility into why a recommendation was made.

3. **Concurrent 4-Domain Multi-Agent Architecture**:
   - Executes across 4 specialized domain subagents simultaneously via `asyncio.gather`, minimizing latency to match clinical workflows.
   - Forced Tool Use (`tool_choice`) ensures strict JSON compliance and zero schema drifting.

4. **Patient-Facing 6th-Grade Synthesis**:
   - Downstream Synthesis Agent produces calm, jargon-free instructions and concrete red-flag emergency symptoms (e.g., *"Call 911 if you have sudden chest pain or trouble breathing"*).
   - Automatically injects **Mandatory** follow-up recommendations whenever any Critical clinical barrier is detected.

---

## 5-Agent Pipeline Architecture

```mermaid
flowchart TD
    Req[POST /orchestrate/evaluate] --> Split[Concurrent Dispatch]
    
    subgraph Concurrent Category Agents [Phase 1: asyncio.gather with Forced Tool Use]
        A1[1. Clinical Stability Agent\n- Vitals, Pending Labs, Infection\n- Citation: lab_summary / clinical_note]
        A2[2. Medication Recon Agent\n- Interactions, Missing Doses\n- Citation: medications]
        A3[3. Caregiver / SDOH Agent\n- Home Safety, Support System\n- Citation: caregiver_notes]
        A4[4. Admin & Logistics Agent\n- Prior Auth, DME, Transport\n- Citation: insurance_notes]
    end
    
    Split --> A1
    Split --> A2
    Split --> A3
    Split --> A4
    
    A1 --> Merge[Barriers Aggregated]
    A2 --> Merge
    A3 --> Merge
    A4 --> Merge
    
    subgraph Deterministic Core [Phase 2: Pure Python Aggregator]
        Merge --> Agg[Deterministic Scoring & Guardrail\n- Score = 100 - 40*Crit - 15*Mod - 5*Min\n- ANY Critical -> High_Risk_Blocked\n- Estimated Ready Time Calculation]
    end
    
    subgraph Synthesis [Phase 3: Synthesis Agent]
        Agg --> Synth[5. Synthesis Agent\n- 6th-Grade Patient Summary\n- Concrete Red-Flag Warning Signs\n- Readmission Risk Assessment\n- Mandatory Clinical Follow-ups]
    end
    
    Synth --> Validate[Pydantic V2 Schema Validation]
    Validate --> Res[Final DischargeReadinessEvaluation JSON]
```

---

## Data Contract: `DischargeReadinessEvaluation`

```json
{
  "patient_id": "P-1005",
  "readiness_score": 60,
  "readiness_tier": "High_Risk_Blocked",
  "estimated_ready_time": "by_tomorrow_am",
  "clinical_barriers": [
    {
      "category": "Clinical",
      "barrier_description": "Pending critical microbiology culture: Blood culture (x2 sets, drawn 36h ago, final growth/sensitivity pending)",
      "severity": "Critical",
      "required_action": "Review final blood culture results and confirm no organism growth prior to discharge.",
      "assigned_role": "Physician",
      "source_field": "lab_summary"
    }
  ],
  "follow_up_recommendations": [
    {
      "timeframe_days": 2,
      "specialty": "Primary Care / Attending Physician",
      "priority": "Mandatory",
      "rationale": "Required follow-up due to unresolved critical clinical issues during admission."
    }
  ],
  "readmission_risk": "high",
  "readmission_risk_reason": "High readmission risk driven by 1 critical safety barrier(s) and 4 days inpatient length of stay.",
  "patient_friendly_summary": {
    "reading_grade_level": "6th Grade",
    "medication_schedule": "Take all medicines exactly as written on your pill bottles...",
    "red_flag_warning_signs": [
      "Call 911 immediately if you have trouble breathing, chest pain, or sudden dizziness.",
      "Call your doctor right away if your fever goes over 101°F."
    ],
    "next_appointment_notes": "Your follow-up visit is scheduled within 2 to 3 days..."
  }
}
```

---

## Getting Started

### 1. Requirements
- Python 3.11+
- Anthropic API Key (from [console.anthropic.com](https://console.anthropic.com))

### 2. Installation
```bash
cd discharge-ai-orchestrator
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure `.env` contains:
```env
PORT=8001
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
MODEL_ID=claude-sonnet-5
CORS_ALLOWED_ORIGIN=http://localhost:5173
```

### 4. Running the Service
```bash
uvicorn main:app --port 8001 --reload
```
Interactive OpenAPI documentation will be live at `http://localhost:8001/docs`.

### 5. Running Automated Tests
```bash
pytest test_orchestrator.py -v
```

---

## API Endpoints

### `GET /health`
Returns service operational status:
```json
{ "status": "ok" }
```

### `POST /orchestrate/evaluate`
Accepts `EvaluateRequest` (structured data + raw clinical context) and returns the validated `DischargeReadinessEvaluation`.

---

## Demo Narration & Judge Q&A Guide

### Demo Narration Points
1. **"The Wow Moment" (Source Citation)**:
   *Point to the barrier citation badge on the UI:*
   > "Notice how every barrier points directly to its source note — like 'pending blood culture — from lab_summary'. Clinicians never have to guess or trust a black box."

2. **Deterministic Safety (Non-LLM Overrides)**:
   *Explain the scoring mechanism:*
   > "The AI does not decide the final score. Our deterministic aggregator applies strict mathematical deductions and forces High_Risk_Blocked if any Critical barrier exists, regardless of model confidence."

3. **Parallel Concurrency**:
   *Explain latency efficiency:*
   > "All 4 domain agents run concurrently via asyncio.gather in a single round-trip, keeping response times fast and actionable for emergency departments and hospital floors."

### Likely Judge Questions

- **Q: What if the Anthropic API is slow or down during a live demo?**
  - **A**: The architecture incorporates pre-cached evaluations in the Core Backend (Person 2) and deterministic fallback extractors within this service, guaranteeing zero demo crashes.
- **Q: How do you prevent hallucinations in medications or lab results?**
  - **A**: The Medication Agent is strictly prompted and tool-bounded to never infer missing dosages; missing fields are flagged as barriers themselves. Entity extraction grounds every check in source EHR text.
- **Q: How does this map to enterprise AWS production?**
  - **A**: This orchestrator maps directly to **AWS Lambda** integrated with **Amazon Bedrock (Claude 3.5 Sonnet)**, with Amazon DynamoDB handling caching and audit logs.
