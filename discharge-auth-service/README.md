# Discharge Auth Service (Port 8003)

Authentication and Role-Based Access Control (RBAC) microservice for the AI-Assisted Patient Discharge Readiness & Follow-Up Planner platform.

## Overview
- Issues signed HS256 JSON Web Tokens (JWT) for healthcare staff.
- Implements role-based identification (`Physician`, `Nurse`, `Pharmacist`, `Case_Manager`, `Admin`).
- Exposes token validation and `/auth/me` inspection endpoints.
- Enforces strict CORS matching the frontend client (`http://localhost:5173`).

---

## Configuration

Default environment variables (see `.env.example`):
```ini
PORT=8003
JWT_SHARED_SECRET=discharge-planner-2026-secret
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=8
CORS_ALLOWED_ORIGIN=http://localhost:5173
```

---

## Demo User Directory

| Username | Password | Role | Full Name | Clinical Domain |
| :--- | :--- | :--- | :--- | :--- |
| `dr.smith` | `password123` | `Physician` | Dr. Sarah Smith | Final Clinical Sign-Off, Medical Review |
| `nurse.jane` | `password123` | `Nurse` | Jane Rodriguez, RN | Vitals, Sepsis Screening, Bedside Checks |
| `pharm.lee` | `password123` | `Pharmacist` | Pharm. David Lee | Medication Reconciliation, Interactions |
| `case.taylor`| `password123` | `Case_Manager`| Taylor Brooks | Social Determinants of Health, DME, Transport |
| `admin` | `password123` | `Admin` | System Admin | Platform Governance & Auditing |

---

## API Endpoints

### 1. Health Check
- **Endpoint**: `GET /health`
- **Response**:
```json
{
  "status": "ok"
}
```

### 2. Login
- **Endpoint**: `POST /auth/login`
- **Request Body**:
```json
{
  "username": "dr.smith",
  "password": "password123"
}
```
- **Success Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "Physician",
  "user_id": "dr.smith",
  "full_name": "Dr. Sarah Smith"
}
```
- **Error Response (401 Unauthorized)**:
```json
{
  "detail": "Invalid username or password"
}
```

### 3. Verify & Read Token Profile
- **Endpoint**: `GET /auth/me`
- **Headers**: `Authorization: Bearer <token>`
- **Success Response (200 OK)**:
```json
{
  "user_id": "dr.smith",
  "role": "Physician",
  "full_name": "Dr. Sarah Smith"
}
```

---

## How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Service
```bash
python main.py
# Or with uvicorn directly:
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

Interactive OpenAPI Documentation will be available at:
`http://localhost:8003/docs`
