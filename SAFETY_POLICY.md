# Clinical Safety Guardrail Policy & Governance Architecture

**Platform**: AI-Assisted Patient Discharge Readiness & Follow-Up Planner  
**Version**: 2026.1  
**Classification**: Clinical Decision Support (CDS) System & Guardrail Specification  
**Compliance Standard**: Software as a Medical Device (SaMD) CDS Framework / HIPAA / Zero-Trust Role-Based Access  

---

## Executive Summary & Core Mandate

The **AI-Assisted Patient Discharge Readiness & Follow-Up Planner** augments multidisciplinary clinical care teams by aggregating electronic health record (EHR) data, identifying post-acute discharge barriers, recommending discharge readiness tiers, and generating patient-facing care instructions.

Because incorrect or premature discharge decisions pose life-threatening risks to patients (e.g., untreated bacteremia, acute decompensation, toxic drug interactions), **artificial intelligence models are strictly non-autonomous and subject to rigorous deterministic guardrails**.

This Safety Policy establishes five non-negotiable safety pillars governing all system operations, data flows, and code layers.

---

## Five Core Safety Pillars

```
+-------------------------------------------------------------------------------+
|                        CLINICAL SAFETY ARCHITECTURE                           |
+-------------------------------------------------------------------------------+
|  1. DETERMINISTIC GUARDRAILS                                                  |
|     * Any "Critical" barrier -> FORCED "High_Risk_Blocked" (Overrides LLM)    |
|                                                                               |
|  2. MANDATORY HUMAN-IN-THE-LOOP SIGN-OFF                                      |
|     * Physician sign-off is BLOCKED (HTTP 409) if Critical tasks unresolved   |
|                                                                               |
|  3. AUDITED CLINICAL OVERRIDES                                                |
|     * Manual tier changes require rationale (>= 10 chars) & permanent log     |
|                                                                               |
|  4. ADVISORY CLINICAL DECISION SUPPORT (CDS) STATUS                           |
|     * Prominent banner: All AI outputs are advisory until clinician approval  |
|                                                                               |
|  5. RELIABILITY AS SAFETY (HIGH AVAILABILITY & CACHING)                       |
|     * Cached & deterministic fallbacks prevent bedside workflow disruptions   |
+-------------------------------------------------------------------------------+
```

---

### Pillar 1: Deterministic Guardrail (Override Hierarchy)

> **Rule**: Any detected barrier with severity marked as **`Critical`** deterministically forces the patient's `readiness_tier` to **`High_Risk_Blocked`**, regardless of model confidence, composite numerical readiness scores, or statistical probabilities.

1. **Non-Negotiable Precedence**:
   - Probabilistic LLM scoring cannot downgrade a `Critical` risk.
   - If an LLM or scoring algorithm outputs `Tier 1: Ready_For_Discharge` or `Tier 2: Moderate_Risk_Pending` with a 99% confidence score, but any active barrier has severity = `"Critical"` (such as *pending blood cultures with suspected sepsis*, *acute telemetry arrhythmia*, or *unverified INR on warfarin*), the system layer intercepts the payload and enforces:
     ```json
     {
       "readiness_tier": "High_Risk_Blocked",
       "guardrail_triggered": true,
       "blocking_reasons": ["Critical barrier: Pending Blood Cultures - Sepsis Protocol Active"]
     }
     ```
2. **Clinical Rationale**:
   - Statistical models can suffer from hallucinations, missed negative constraints, or over-optimistic aggregations. Deterministic rules act as an impassable safety net against premature discharge.

---

### Pillar 2: Mandatory Human Sign-Off (Gated Discharge)

> **Rule**: Physician sign-off for discharge is strictly blocked with **`HTTP 409 Conflict`** if any `Critical`-severity task or clinical prerequisite remains unresolved.

1. **Enforcement Mechanism**:
   - When a clinician initiates `POST /patients/{id}/signoff`, the backend core performs an atomic check against all active tasks associated with the patient.
   - If `count(tasks.filter(severity == 'Critical' AND status != 'Resolved')) > 0`:
     - The sign-off operation is rejected with status `409 Conflict`.
     - The response returns the list of unresolved blocking tasks and responsible roles.
2. **Role Boundaries**:
   - Only users with the authenticated role of **`Physician`** (`dr.smith`) possess cryptographic authorization to issue final clinical discharge approval.
   - Other roles (Nurse, Pharmacist, Case Manager) resolve disciplinary tasks within their scope, clearing individual prerequisites before the Physician can sign off.

---

### Pillar 3: Audited Override Protocol

> **Rule**: Clinicians may override an AI-suggested readiness tier only by submitting a structured clinical justification containing a written rationale of **at least 10 non-whitespace characters**. Every override is permanently written to an immutable audit trail.

1. **Payload Requirement**:
   - `POST /patients/{id}/override` requires:
     ```json
     {
       "new_tier": "Moderate_Risk_Pending",
       "override_rationale": "Blood culture finalized negative at 48h; patient afebrile and hemodynamically stable."
     }
     ```
   - Requests with missing rationales or strings shorter than 10 characters are rejected with `HTTP 422 Unprocessable Entity` or `HTTP 400 Bad Request`.
2. **Audit Trail Persistence**:
   - Overrides generate an immutable event in the audit log recording:
     * `timestamp`: ISO-8601 UTC timestamp.
     * `actor_user_id`: Authenticated user ID (e.g. `dr.smith`).
     * `actor_role`: Clinician role (`Physician`).
     * `action`: `"TIER_OVERRIDE"`.
     * `previous_tier`: Original readiness tier.
     * `updated_tier`: Overridden readiness tier.
     * `rationale`: Verbatim clinical explanation.

---

### Pillar 4: Advisory CDS Banner & Patient Literacy Protection

> **Rule**: All AI-synthesized assessments, risk scores, and instructions are explicitly labeled as **Advisory Clinical Decision Support** until licensed clinician sign-off.

1. **Advisory CDS Banner**:
   - Every user interface view displaying AI recommendations features a persistent, high-contrast banner:
     > ⚠️ **CLINICAL ADVISORY**: *This AI-generated assessment is a decision support tool and does not constitute a final medical order. All recommendations, barriers, and instructions must be verified by a licensed clinician prior to patient discharge.*
2. **Patient-Facing Communication Literacy (6th-Grade Standard)**:
   - Patient discharge packets synthesized by the LLM must adhere to plain-language communication guidelines (~6th-grade reading level).
   - Medical jargon (e.g., *"hyponatremia"*, *"dyspnea on exertion"*, *"q8h po"*) must be translated to accessible instructions (*"low blood salt"*, *"shortness of breath when walking"*, *"take by mouth every 8 hours with water"*).
   - Plain-language packets require mandatory clinical review before delivery to the patient.

---

### Pillar 5: Reliability as Safety (High-Availability Fallbacks)

> **Rule**: When live generative LLM services or NLP extraction pipelines encounter network latency, API rate limits, or outages, the system seamlessly falls back to cached assessments and deterministic rule engines.

1. **Zero Clinical Downtime**:
   - Clinical rounds cannot stall due to third-party AI downtime or cloud connectivity failure.
   - The backend maintains an encrypted cache of recent evaluations.
   - If `discharge-ai-orchestrator` or upstream LLM providers (e.g., Anthropic Claude / AWS Bedrock) fail to respond within timeout limits, the system serves the latest cached evaluation with a status indicator: `{"mode": "offline_cache_fallback", "live_eval_available": false}`.
2. **Deterministic Baseline**:
   - In total offline scenarios, deterministic rules evaluate critical EHR flags (vital sign thresholds, lab flags, active IV medications) to maintain baseline safety barrier detection.

---

## Threat Matrix & Mitigation Summary

| Threat / Failure Mode | Clinical Risk | System Mitigation |
| :--- | :--- | :--- |
| **Hallucinated Readiness Score** | High score generated despite positive sepsis lab. | **Pillar 1**: Deterministic guardrail forces `High_Risk_Blocked` regardless of score. |
| **Accidental Early Sign-Off** | Physician signs off before high-risk medication checked. | **Pillar 2**: HTTP 409 Conflict blocks sign-off until critical pharmacy task resolved. |
| **Unjustified Clinician Override** | Unsubstantiated downgrade of risk level. | **Pillar 3**: Mandatory $\ge 10$-character clinical justification & permanent audit trail. |
| **Clinician Over-Reliance** | Blind trust in AI recommendations. | **Pillar 4**: Advisory CDS banner on all screens + human-in-the-loop requirement. |
| **Upstream AI API Outage** | Bedside clinical delays during hospital rounds. | **Pillar 5**: Sub-second cached fallback response with explicit offline indicators. |

---

## Regulatory and Ethical Compliance Sign-off

This policy complies with:
- **FDA Guidance for Clinical Decision Support Software (2022)**: Preserving clinician independence to independently review underlying data.
- **HIPAA Security & Privacy Rules**: 45 CFR Part 160 and Part 164 (Access controls, audit logging, zero-trust token authentication).
- **AMA Ethical Guidelines for Augmented Intelligence in Healthcare**: Human clinician maintains final authority and accountability for patient care.
