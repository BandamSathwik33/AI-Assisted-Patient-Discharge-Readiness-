# Live Demo Presentation Script & Judge Q&A Guide

**Platform**: AI-Assisted Patient Discharge Readiness & Follow-Up Planner  
**Duration**: 3 to 4 Minutes  
**Target Audience**: Clinical Leads, Hospital Informatics Executives, Hackathon Judges  

---

## 3-4 Minute Presentation Walkthrough

```
[0:00 - 0:40]  Hospital Overview & Live Triage Dashboard
[0:40 - 1:30]  The High-Risk Patient: Pending Blood Culture & Sepsis Barrier
[1:30 - 2:15]  Deterministic Guardrail & Blocked Physician Sign-Off Demo
[2:15 - 2:55]  Multidisciplinary Task Resolution & Authorized Doctor Sign-Off
[2:55 - 3:30]  6th-Grade Patient-Facing Care Packet
[3:30 - 4:00]  Reliability: Zero-Downtime Cache Fallback & Wrap-Up
```

---

### Act 1: Hospital Overview & Bedside Triage (0:00 - 0:40)
- **Visual**: Navigate to `http://localhost:5173/` (Dashboard). Logged in as `nurse.jane`.
- **Speaker**:
  > *"Good morning. Today, hospital floor crowding and premature discharge are two sides of the same crisis. Inpatient teams struggle to track dozens of post-acute discharge criteria across EHR notes, labs, and social work.*
  >
  > *Here on our Hospital Overview screen, you see real-time bed occupancy, discharge velocity, and automated patient risk tiers ranging from Tier 1 (Ready) down to Tier 3 (High-Risk Blocked).*
  >
  > *Notice our persistent **Advisory Clinical Decision Support** banner across the top: AI augments our team, but clinicians maintain absolute authority."*

---

### Act 2: High-Risk Patient Evaluation (0:40 - 1:30)
- **Visual**: Select patient **Marcus Vance (Room 402 - Suspected Sepsis / Post-Pneumonia)**. Click **"Run Clinical AI Evaluation"**.
- **Speaker**:
  > *"Let’s look at Marcus Vance. Marcus is recovering well from pneumonia, his vitals are stable, and a standard checklist might mistakenly flag him as discharge-ready.*
  >
  > *However, our NLP extraction pipeline identified an active EHR lab order: **Blood Cultures Pending at 24 hours**.*
  >
  > *Because an undetected bacteremia could trigger fatal septic shock at home, our system flags this as a **Critical Barrier**."*

---

### Act 3: The Deterministic Guardrail in Action (1:30 - 2:15)
- **Visual**: Show Marcus's tier forced to **`High_Risk_Blocked`**. Switch user to `dr.smith` (Physician) and click **"Attempt Sign-Off"**.
- **Speaker**:
  > *"Watch what happens here: Even if an AI model predicts a 95% readiness score, our **Pillar 1 Deterministic Guardrail** activates. Any Critical barrier forcefully overrides the score and clamps the patient into **High_Risk_Blocked**.*
  >
  > *Now, Dr. Sarah Smith logs in and attempts to sign off on discharge.*
  >
  > *The system immediately rejects the order with **HTTP 409 Conflict**: 'Physician sign-off is blocked until all Critical tasks are resolved.' Premature discharge is cryptographically and logically impossible."*

---

### Act 4: Multidisciplinary Resolution & Sign-Off (2:15 - 2:55)
- **Visual**: Show Disciplinary Tasks list. Resolve the Nursing lab check (`nurse.jane`), Pharmacy med check (`pharm.lee`), and confirm blood culture negative. Click **"Sign-Off Discharge"** as `dr.smith`.
- **Speaker**:
  > *"Discharge is a team sport. Nurse Jane checks the negative preliminary stain. Pharmacist Lee reconciles his oral antibiotics. Case Manager Taylor confirms home oxygen delivery.*
  >
  > *With all critical barriers resolved, Dr. Smith submits the clinical sign-off with her licensed physician credentials. The order is approved, timestamped, and immutably written to the audit log."*

---

### Act 5: 6th-Grade Patient Care Packet (2:55 - 3:30)
- **Visual**: Switch to **"Patient & Family Instructions"** tab.
- **Speaker**:
  > *"Once cleared, we generate patient-facing discharge instructions tailored to a **6th-grade reading level**.*
  >
  > *Instead of confusing jargon like 'Dyspnea on exertion' or 'Take PO Q12H', Marcus receives: 'Call the clinic if you feel short of breath while walking. Take 1 red pill with food every morning and evening.'*
  >
  > *Clear communication cuts 30-day hospital readmission rates by over 25%."*

---

### Act 6: Zero-Downtime Cache Reliability (3:30 - 4:00)
- **Visual**: Toggle offline / cached mode demonstration.
- **Speaker**:
  > *"Finally, clinical safety requires system availability. If the cloud LLM experiences latency or an API outage, our local cached evaluation engine serves sub-second assessments without dropping bedside continuity.*
  >
  > *Safety, deterministic guardrails, multi-role collaboration, and patient literacy—that is the AI-Assisted Patient Discharge Planner. Thank you."*

---

## Likely Judge Questions & Rock-Solid Answers

### 1. Data Privacy & PHI (HIPAA Compliance)
- **Judge Question**: *"How do you handle Protected Health Information (PHI) and HIPAA compliance when sending patient data to LLMs?"*
- **Answer**:
  > *"All data in our demo and testing pipelines is 100% synthetically generated with zero real patient PHI. In production, our architecture leverages zero-retention HIPAA-compliant enterprise LLM endpoints (or local on-premise models via vLLM / AWS Bedrock VPC endpoints). Furthermore, our NLP layer strips direct patient identifiers (names, MRNs, exact addresses) prior to LLM synthesis, transmitting only de-identified clinical features."*

---

### 2. Guardrails & Preventing Hallucination
- **Judge Question**: *"How do you prevent the AI from hallucinating a patient's readiness and causing a dangerous discharge?"*
- **Answer**:
  > *"We follow a strict **Dual-Layer Architecture**: Generative models propose recommendations, but deterministic rule engines enforce safety. Under our Safety Policy (Pillar 1), any 'Critical' barrier (e.g., pending blood cultures, abnormal cardiac telemetry, unconfirmed anticoagulation) hard-codes the readiness tier to `High_Risk_Blocked`, regardless of model confidence. Additionally, physician sign-off is gated by a hard `HTTP 409 Conflict` rule if critical tasks remain open."*

---

### 3. High Availability & Cloud Outages
- **Judge Question**: *"What happens if your LLM provider goes down during hospital rounds?"*
- **Answer**:
  > *"We treat system reliability as a core clinical safety requirement (Pillar 5). The backend core maintains an encrypted local evaluation cache. If the AI Orchestrator or upstream API fails or times out, the system automatically falls back to cached assessments with prominent UI indicators, allowing floor staff to continue discharge workflows without interruption."*

---

### 4. AWS Cloud Parity Architecture Mapping
- **Judge Question**: *"How does this prototype translate into an enterprise AWS cloud deployment?"*
- **Answer**:
  > *"Every microservice in our 5-folder architecture has a direct 1-to-1 parity mapping to enterprise AWS healthcare services:*
  >
  > | Local Microservice | AWS Production Cloud Parity |
  > | :--- | :--- |
  > | `discharge-auth-service` (8003) | **Amazon Cognito User Pools** with OAuth2/JWT & SAML/EHR SSO integration |
  > | `discharge-backend-core` (8000) | **Amazon ECS Fargate** with **Amazon DynamoDB** / **Amazon Aurora PostgreSQL** |
  > | `discharge-ai-orchestrator` (8001) | **AWS Bedrock (Claude 3.5 Sonnet)** with Bedrock Guardrails & Step Functions |
  > | `discharge-nlp-data` (8002) | **Amazon Comprehend Medical** for clinical entity & ICD-10 extraction |
  > | `discharge-frontend` (5173) | **AWS Amplify** / **Amazon CloudFront** + **S3 Bucket** |
  > | Audit Logging & Compliance | **AWS CloudTrail** + **Amazon CloudWatch Logs** (WORM immutable storage) |"

---

### 5. Multi-Role Collaboration & Workflows
- **Judge Question**: *"Why separate roles into Physician, Nurse, Pharmacist, and Case Manager?"*
- **Answer**:
  > *"Discharge failures rarely occur because of one doctor—they happen because multidisciplinary handoffs fail. For example, a doctor might approve medical readiness, but the patient lacks transportation, home oxygen, or insulin affordability. Our role-based task engine assigns domain-specific tasks to Nurses, Pharmacists, and Case Managers, ensuring full cross-functional clearance before final Physician sign-off."*
