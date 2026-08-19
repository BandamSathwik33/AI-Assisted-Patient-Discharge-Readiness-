# AI-Assisted Patient Discharge Readiness & Follow-Up Planner (`discharge-frontend`)

A clinical-grade, multi-role hospital dashboard frontend built with **React 18**, **TypeScript**, **Vite**, **Tailwind CSS**, **React Router v6**, **Recharts**, and **Axios**.

Designed for physicians, nurses, pharmacists, and case managers to evaluate discharge readiness, resolve clinical barriers, manage bed capacity, and review safety-critical patient instructions.

---

## 🚀 Quick Start Guide

### 1. Installation

Navigate into the `discharge-frontend/` directory and install dependencies:

```bash
cd discharge-frontend
npm install
```

### 2. Environment Setup

Create or verify the `.env` file in the root of `discharge-frontend/`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_AUTH_BASE_URL=http://localhost:8003
VITE_USE_MOCK=true
```

### 3. Start the Development Server

```bash
npm run dev
```

Open your browser at **`http://localhost:5173/`**.

---

## 🔀 How to Flip from Mock Mode to Live Backend Mode

The application includes a dual-mode API client (`src/api/client.ts`). 

- **Mock Mode (Default for Demo)**: `VITE_USE_MOCK=true`  
  Uses an in-memory stateful store with realistic network latency (300ms–6s), reactive state mutations, simulated AI evaluation runs, and HTTP status handling (such as `409 Conflict` on signoff).
- **Live Backend Mode**: `VITE_USE_MOCK=false`  
  Passes requests directly to `VITE_API_BASE_URL` and `VITE_AUTH_BASE_URL` with standard `Authorization: Bearer <token>` headers.

To connect to a live backend API, update `.env`:

```env
VITE_USE_MOCK=false
VITE_API_BASE_URL=https://your-live-core-api.hospital.org
VITE_AUTH_BASE_URL=https://your-live-auth-api.hospital.org
```

No UI code changes are needed when switching modes!

---

## 👥 Demo Quick-Login Accounts

On the Login screen, click any of the 5 one-click demo login buttons to test role-gated permissions:

| Username | Role | Full Name | Primary Responsibilities |
| :--- | :--- | :--- | :--- |
| `dr.smith` | **Physician** | Dr. Arthur Smith, MD | Discharge Sign-Off, Tier Override, Medical clearance |
| `nurse.jane` | **Nurse** | Jane Miller, RN | Wound care, vital signs, transportation coordination |
| `pharm.lee` | **Pharmacist** | David Lee, PharmD | High-risk drug reconciliation, INR/Anticoagulation clearance |
| `case.taylor` | **Case_Manager** | Taylor Morgan, MSW | Prior authorization, DME delivery, SDOH care management |
| `admin` | **Admin** | Sarah Connor | Global resolution overrides and administrative access |

*You can also switch active demo roles on any screen using the top navigation bar dropdown.*

---

## 📊 Core Features & UI Highlights

1. **Persistent Clinical Decision Support Banner**:
   - Displays mandatory safety disclosure on all clinical views:
     > `"AI-Generated Clinical Decision Support. All recommendations require verification by a licensed healthcare provider prior to patient discharge."`

2. **Hospital Operational Overview Dashboard**:
   - **Summary Stats**: Tracks active inpatients, ready now, expected discharges today, and average unit readiness index.
   - **Bed Availability Widget**: Visually distinct indicators for beds *Free Now*, *Expected Soon (Today)*, and *Expected Tomorrow*.
   - **Priority Queue Table**: Patients ranked by readiness severity and risk, sortable by priority rank, readiness score, and length of stay.

3. **Patient Evaluation & Clinical Barrier Management**:
   - **Readiness Radial Gauge**: Recharts 0–100 score visualization with color-coded tier badges (`Ready`, `Near_Ready`, `High_Risk_Blocked`).
   - **Source-Field Citations**: Every clinical barrier features an unmistakable citation badge pointing to its medical record source (`— from lab_summary`, `— from medications`, `— from clinical_note`, `— from caregiver_notes`, `— from insurance_notes`).
   - **Role-Gated Barrier Resolution**: "Resolve" buttons are enabled only for matching roles (or Admin). Disabled buttons display helpful permission tooltips.
   - **Physician Sign-Off (409 Conflict Simulation)**: Signing off on a patient with unresolved Critical barriers triggers a `409 Conflict` error banner detailing the blocked critical items.
   - **Physician Tier Override Form**: Modal requiring a formal clinical rationale (min 10 characters) to override algorithmic readiness.
   - **"Run New AI Evaluation"**: Asynchronous calculation simulation with loading feedback.

4. **Patient & Caregiver View**:
   - Accessible, calm typography at a **6th Grade reading level**.
   - **Red-Flag Warning Signs**: Prominent, high-visibility warning box highlighting safety-critical symptoms requiring immediate emergency care (911).

5. **Chronological Audit Trail**:
   - Chronological event logging tracking AI runs, physician overrides, signoffs, and barrier resolutions.

---

## 📜 Data Contract (DischargeReadinessEvaluation)

```json
{
  "patient_id": "P101",
  "readiness_score": 34,
  "readiness_tier": "High_Risk_Blocked",
  "estimated_ready_time": "by_tomorrow_am",
  "clinical_barriers": [
    {
      "category": "Clinical",
      "barrier_description": "Elevated cardiac Troponin-I repeat lab pending confirmation",
      "severity": "Critical",
      "required_action": "Physician review repeat Troponin panel and approve clearance",
      "assigned_role": "Physician",
      "source_field": "lab_summary"
    }
  ],
  "follow_up_recommendations": [
    {
      "timeframe_days": 3,
      "specialty": "Cardiology Clinic",
      "priority": "Mandatory",
      "rationale": "Post-stent coronary evaluation"
    }
  ],
  "readmission_risk": "high",
  "readmission_risk_reason": "Recent stent placement and unresolved troponin trend",
  "patient_friendly_summary": {
    "reading_grade_level": "6th Grade",
    "medication_schedule": "Take Ticagrelor 90mg twice daily with food...",
    "red_flag_warning_signs": ["Chest discomfort or tightness", "Shortness of breath"],
    "next_appointment_notes": "Cardiology follow-up scheduled for Friday at 10:00 AM."
  }
}
```

---

## 🛠 Project Structure

```
discharge-frontend/
├── .env
├── .env.example
├── index.html
├── package.json
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
├── README.md
└── src/
    ├── api/
    │   └── client.ts            # Dual-mode API client (Mock vs Real HTTP)
    ├── components/
    │   ├── AuditLogList.tsx     # Chronological log entries
    │   ├── BarrierCard.tsx      # Citation-tagged barrier cards with role gating
    │   ├── BedAvailabilityWidget.tsx # Capacity planning metrics widget
    │   ├── FollowUpList.tsx     # Timed outpatient care plan list
    │   ├── Navbar.tsx           # Hospital branding and demo role switcher
    │   ├── PatientCaregiverView.tsx # Accessible patient summary & Red-Flag warnings
    │   ├── PhysicianActions.tsx # Signoff 409 handling and Tier Override form
    │   ├── PriorityRankingTable.tsx # Sortable queue table with tier badges
    │   ├── ReadinessGauge.tsx   # Recharts radial score gauge
    │   └── SafetyBanner.tsx     # Top AI decision support banner
    ├── context/
    │   └── AuthContext.tsx      # Auth & demo role state provider
    ├── mock/
    │   └── mockData.ts          # 6 rich mock patients across all tiers
    ├── pages/
    │   ├── LoginPage.tsx        # Single-click demo user login
    │   ├── OverviewPage.tsx     # Operational hospital dashboard
    │   └── PatientDetailPage.tsx# 4-tab clinical patient workspace
    ├── types/
    │   └── index.ts             # Exact TypeScript data contract interfaces
    ├── App.tsx                  # React Router v6 setup
    ├── index.css                # Tailwind directives & dark clinical theme
    └── main.tsx                 # React DOM root mounting
```
