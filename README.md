# AI-Assisted Patient Discharge Readiness & Follow-Up Planner

[![Architecture: Microservices](https://img.shields.io/badge/Architecture-5--Service%20Microservices-blue.svg)](#system-architecture)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.11-009688.svg)](https://fastapi.tiangolo.com)
[![React/Vite](https://img.shields.io/badge/Frontend-React%20%7C%20Vite%20%7C%205173-646CFF.svg)](https://vitejs.dev)
[![Safety Guardrails](https://img.shields.io/badge/Clinical%20Guardrails-Pillars%201--5%20Active-brightgreen.svg)](SAFETY_POLICY.md)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-grade, clinical decision support platform designed to streamline inpatient discharge planning, prevent premature hospital discharges, enforce deterministic safety guardrails, coordinate multidisciplinary care teams, and generate plain-language (6th-grade level) patient care instructions.

---

## System Architecture & Port Allocation

The repository is organized into five modular services operating concurrently:

```
+-----------------------------------------------------------------------------------+
|                     DISCHARGE PLANNER REPOSITORY ARCHITECTURE                     |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|   +---------------------------------------------------------------------------+   |
|   |                  discharge-frontend (Vite Dev / Port 5173)                |   |
|   |         React Dashboard, Clinical CDS Banners, Plain-Language View       |   |
|   +---------------------------------------------------------------------------+   |
|                                       │                                           |
|                   ┌───────────────────┼───────────────────┐                       |
|                   ▼                   ▼                   ▼                       |
|         +──────────────────+ +─────────────────+ +──────────────────+             |
|         | discharge-auth-  | | discharge-      | | discharge-       |             |
|         | service          | | backend-core    | | ai-orchestrator  |             |
|         | (Port 8003)      | | (Port 8000)     | | (Port 8001)      |             |
|         | JWT, RBAC, Auth  | | EHR, Tasks,     | | Claude LLM,      |             |
|         |                  | | Bed Triage,     | | Evaluation,      |             |
|         |                  | | Audit Log       | | Plain-Lang Synth |             |
|         +──────────────────+ +─────────────────+ +──────────────────+             |
|                                       │                   │                       |
|                                       └─────────┬─────────┘                       |
|                                                 ▼                                 |
|                                      +─────────────────────+                      |
|                                      | discharge-nlp-data  |                      |
|                                      | (Port 8002)         |                      |
|                                      | Clinical NLP Parser |                      |
|                                      | Lab & Entity Extr.  |                      |
|                                      +─────────────────────+                      |
+-----------------------------------------------------------------------------------+
```

### Microservice Catalog

| Directory | Port | Primary Responsibilities | Tech Stack |
| :--- | :--- | :--- | :--- |
| [`discharge-frontend/`](discharge-frontend/) | **5173** | Multi-role clinician dashboard, patient risk triage, interactive task board, patient-facing plain language handouts. | React, Vite, Vanilla CSS |
| [`discharge-backend-core/`](discharge-backend-core/) | **8000** | Patient registry, bed occupancy analytics, task state machine, physician sign-off gating, immutable audit trail. | Python 3.11, FastAPI, SQLite |
| [`discharge-ai-orchestrator/`](discharge-ai-orchestrator/) | **8001** | LLM scoring pipeline, barrier classification, deterministic guardrail integration, plain-language instruction generator. | Python 3.11, FastAPI, Anthropic Claude |
| [`discharge-nlp-data/`](discharge-nlp-data/) | **8002** | Synthetic EHR ingestion, clinical text parsing, abnormal lab & pending culture extraction, medical entity tagging. | Python 3.11, FastAPI, Regex/Spacy/Transformers |
| [`discharge-auth-service/`](discharge-auth-service/) | **8003** | User authentication, HS256 JWT minting & verification, Role-Based Access Control (`Physician`, `Nurse`, `Pharmacist`, `Case_Manager`, `Admin`). | Python 3.11, FastAPI, PyJWT |

---

## Clinical Safety & Deterministic Guardrails

The platform adheres to strict clinical safety guardrails detailed in [`SAFETY_POLICY.md`](SAFETY_POLICY.md):

1. **Deterministic Guardrail (Pillar 1)**: Any clinical barrier flagged as `Critical` (e.g. pending blood culture with suspected sepsis) forces the readiness tier to `High_Risk_Blocked`, regardless of model confidence or numerical readiness scores.
2. **Mandatory Human Sign-off (Pillar 2)**: Physician sign-off is programmatically blocked with **`HTTP 409 Conflict`** if any `Critical` task remains unresolved.
3. **Audited Overrides (Pillar 3)**: Clinicians may override AI recommendations only with a verified justification ($\ge 10$ chars), permanently recorded in an immutable audit log.
4. **Advisory CDS Status (Pillar 4)**: AI outputs display persistent clinical decision support banners and are strictly non-autonomous until licensed clinician approval.
5. **Reliability as Safety (Pillar 5)**: High-availability cached fallbacks prevent disruption to hospital rounds when cloud APIs encounter latency or downtime.

---

## Quick Start Guide

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm (for frontend)
- Git

### 2. Environment Setup
Copy `.env.example` to `.env` at the root and in each microservice folder:
```bash
cp .env.example .env
```

Shared Environment Variables:
```ini
PORT_AUTH=8003
PORT_CORE=8000
PORT_AI=8001
PORT_NLP=8002
JWT_SHARED_SECRET=discharge-planner-2026-secret
JWT_ALGORITHM=HS256
CORS_ALLOWED_ORIGIN=http://localhost:5173
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch All Backend Microservices
Run all 4 backend services with a single cross-platform command:
```bash
python run_all.py
```
This starts:
- Auth Service on `http://localhost:8003`
- Backend Core on `http://localhost:8000`
- AI Orchestrator on `http://localhost:8001`
- NLP Data Service on `http://localhost:8002`

Logs from each service are multiplexed and color-coded in your terminal (`[AUTH]`, `[BACKEND]`, `[AI]`, `[NLP]`). Press `Ctrl+C` for graceful shutdown.

### 5. Launch the Frontend
In a separate terminal window:
```bash
cd discharge-frontend
npm install
npm run dev
```
Open your browser to `http://localhost:5173`.

---

## Running the Automated Integration Test Suite

The comprehensive end-to-end integration test verifies all 5 microservices, RBAC security, deterministic safety guardrails, task resolution flows, blocked physician sign-off (HTTP 409), and offline cache reliability:

```bash
python integration_test.py
```

### Verified Test Workflow Steps:
- [x] **Step A**: Authenticate as `nurse.jane` via `POST /auth/login` and validate JWT token claims.
- [x] **Step B**: Retrieve patient cohort via `GET /patients` and select target critical scenario.
- [x] **Step C**: Execute `POST /evaluate/{id}` and verify deterministic tier clamp (`High_Risk_Blocked`).
- [x] **Step D**: Retrieve task list and resolve disciplinary task via `PATCH /tasks/{id}/resolve`.
- [x] **Step E**: Login as `dr.smith` and verify physician sign-off is **BLOCKED (HTTP 409 Conflict)** due to pending critical barrier.
- [x] **Step F**: Clear remaining critical prerequisites and verify physician sign-off **SUCCEEDS (HTTP 200 OK)**.
- [x] **Step G**: Verify immutable trail via `GET /audit-log/{id}`.
- [x] **Step H**: Verify hospital-wide bed occupancy and triage ranking via `GET /hospital-overview`.
- [x] **Step I**: Validate high-availability offline cached assessment fallback.

---

## Demo Credentials & Role Directory

| Username | Password | Role | Responsibilities |
| :--- | :--- | :--- | :--- |
| `dr.smith` | `password123` | `Physician` | Final clinical discharge sign-off, medical review, tier overrides |
| `nurse.jane` | `password123` | `Nurse` | Vital sign monitoring, bedside checks, sepsis protocol tracking |
| `pharm.lee` | `password123` | `Pharmacist` | Medication reconciliation, high-risk drug monitoring (anticoagulants/insulin) |
| `case.taylor` | `password123` | `Case_Manager` | Social determinants of health (SDOH), transport, home health & DME equipment |
| `admin` | `password123` | `Admin` | System telemetry, audit log inspection, user governance |

---

## AWS Production Cloud Parity Architecture

For enterprise healthcare deployment, this local prototype maps 1-to-1 to managed AWS cloud services:

```
+-----------------------------------------------------------------------------------+
|                             AWS ENTERPRISE ARCHITECTURE                           |
+-----------------------------------------------------------------------------------+
|  • Identity & Access:      Amazon Cognito User Pools + SAML/EHR SSO (Epic/Cerner) |
|  • Backend Compute:        Amazon ECS Fargate / AWS App Runner                    |
|  • Database & State:       Amazon DynamoDB + Amazon Aurora PostgreSQL             |
|  • GenAI Reasoning:        AWS Bedrock (Claude 3.5 Sonnet) + Bedrock Guardrails   |
|  • Clinical NLP:           Amazon Comprehend Medical (Entity & ICD-10 Extraction) |
|  • Web Delivery:           AWS Amplify + Amazon CloudFront (CDN)                  |
|  • Compliance & Auditing:  AWS CloudTrail + Amazon CloudWatch (WORM Audit Trail)  |
+-----------------------------------------------------------------------------------+
```

---

## Presentation & Live Demonstration Guide

Refer to [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) for a structured 3-4 minute presentation walkthrough, complete talking points, and answers to likely judge questions regarding HIPAA, AI guardrails, offline caching, and multi-disciplinary clinical workflows.
