import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

import db
from auth import CurrentUser, get_current_user, require_roles
from clients import UpstreamError, extract_entities, orchestrate_evaluation
from guardrail import apply_guardrail
from models import (
    DischargeReadinessEvaluation,
    OverrideRequest,
    PatientCreate,
    SignoffRequest,
    TaskResolveRequest,
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discharge-backend-core")

CORS_ALLOWED_ORIGIN = os.getenv("CORS_ALLOWED_ORIGIN", "http://localhost:5173")
TOTAL_BEDS = int(os.getenv("TOTAL_BEDS", "20"))

app = FastAPI(title="Discharge Backend Core")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    db.init_db()


# --------------------------------------------------------------------------
# Small internal helpers
# --------------------------------------------------------------------------

def now_iso() -> str:
    """ISO-8601 with microsecond precision. Used as the sk suffix for EVAL#
    and AUDIT# items -- lexical sort order == chronological order, and the
    microsecond precision keeps two evaluations issued in the same second
    from colliding on the same primary key."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def patient_pk(patient_id: str) -> str:
    return f"PATIENT#{patient_id}"


def get_patient_or_404(patient_id: str) -> Dict[str, Any]:
    meta = db.get_item(patient_pk(patient_id), "METADATA")
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")
    return meta["data"]


def get_latest_eval(patient_id: str) -> Optional[Dict[str, Any]]:
    """Most recent EVAL# item for a patient, or None if never evaluated.
    Relies on sk being lexically sortable (see now_iso)."""
    evals = db.query_by_pk_prefix(patient_pk(patient_id), "EVAL#")
    return evals[-1] if evals else None


def write_audit(patient_id: str, actor: str, action: str, details: Dict[str, Any]) -> None:
    db.put_item(
        patient_pk(patient_id),
        f"AUDIT#{now_iso()}",
        "AUDIT",
        {"timestamp": now_iso(), "actor": actor, "action": action, "details": details},
    )


def barrier_task_key(category: str, barrier_description: str) -> str:
    """Deterministic id for a barrier, stable across repeated /evaluate calls
    for the same patient. Without this, re-running an evaluation for a
    barrier that's still unresolved creates a brand-new task every time,
    orphaning the old one -- a physician could resolve the task shown on
    screen and still be blocked from signoff by an invisible duplicate.
    Keying off (category, description) instead of a random uuid means a
    persisting barrier maps to the same task record, so resolution status
    carries forward across evaluations."""
    raw = f"{category}|{barrier_description}".strip().lower()
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def bucket_ready_time(value: str) -> str:
    """Normalize estimated_ready_time into one of the three operational
    buckets. Handles both the literal enum-like strings the AI is instructed
    to return, and a raw ISO timestamp, since the schema allows either."""
    if value in ("now", "within_4h", "by_tomorrow_am"):
        return value
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        delta_seconds = (dt - datetime.now(timezone.utc)).total_seconds()
        if delta_seconds <= 0:
            return "now"
        if delta_seconds <= 4 * 3600:
            return "within_4h"
        return "by_tomorrow_am"
    except (ValueError, AttributeError):
        # Unknown/unparseable format -- be conservative, don't claim a bed is free.
        return "by_tomorrow_am"


# --------------------------------------------------------------------------
# Health
# --------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# --------------------------------------------------------------------------
# Patients
# --------------------------------------------------------------------------

@app.get("/patients")
def list_patients(user: CurrentUser = Depends(get_current_user)):
    metas = db.scan_by_entity_type("PATIENT_METADATA")
    out: List[Dict[str, Any]] = []
    for m in metas:
        p = m["data"]
        latest = get_latest_eval(p["patient_id"])
        out.append(
            {
                "patient_id": p["patient_id"],
                "name": p["name"],
                "age": p["age"],
                "admission_date": p["admission_date"],
                "attending_md": p["attending_md"],
                "bed_number": p["bed_number"],
                "days_admitted": p["days_admitted"],
                "readiness_tier": latest["data"]["readiness_tier"] if latest else "Not_Evaluated",
                "readiness_score": latest["data"]["readiness_score"] if latest else None,
            }
        )
    return out


@app.get("/patients/{patient_id}")
def get_patient(patient_id: str, user: CurrentUser = Depends(get_current_user)):
    profile = get_patient_or_404(patient_id)
    latest = get_latest_eval(patient_id)
    tasks = db.query_by_pk_prefix(patient_pk(patient_id), "TASK#")
    return {
        "profile": profile,
        "latest_evaluation": latest["data"] if latest else None,
        "tasks": [t["data"] for t in tasks],
    }


@app.post("/patients", status_code=201)
def create_patient(patient: PatientCreate, user: CurrentUser = Depends(get_current_user)):
    """Seed-script use only -- no role restriction per the spec. Upserts:
    re-running seed.py with the same patient_id overwrites cleanly instead
    of erroring, which matters because seed.py gets run more than once
    during development."""
    db.put_item(patient_pk(patient.patient_id), "METADATA", "PATIENT_METADATA", patient.model_dump())
    return {"status": "created", "patient_id": patient.patient_id}


# --------------------------------------------------------------------------
# Evaluation -- the core pipeline: NLP -> AI orchestrator -> guardrail -> persist
# --------------------------------------------------------------------------

@app.post("/evaluate/{patient_id}")
async def evaluate_patient(
    patient_id: str,
    user: CurrentUser = Depends(require_roles("Physician", "Nurse", "Case_Manager")),
):
    profile = get_patient_or_404(patient_id)

    raw_context = {
        "admission_notes": profile["admission_notes"],
        "medication_list": profile["medication_list"],
        "lab_summary": profile["lab_summary"],
        "caregiver_notes": profile["caregiver_notes"],
        "insurance_notes": profile["insurance_notes"],
        "days_admitted": profile["days_admitted"],
    }

    evaluation: Optional[DischargeReadinessEvaluation] = None
    source = "live"

    # Broad except is intentional here: ANY failure in the live pipeline --
    # network error, timeout, non-2xx, or a response that doesn't validate
    # against our schema -- must fall back to cache. A live-call failure
    # must never surface to the caller as a broken demo.
    try:
        structured = await extract_entities(
            profile["admission_notes"], profile["medication_list"], profile["lab_summary"]
        )
        orchestrated = await orchestrate_evaluation(patient_id, structured, raw_context)
        evaluation = DischargeReadinessEvaluation(**orchestrated)
    except (UpstreamError, ValidationError, TypeError, KeyError) as e:
        logger.warning("Live evaluation pipeline failed for %s: %s", patient_id, e)
        source = "cache"
        cached = get_latest_eval(patient_id)
        if cached is None:
            raise HTTPException(
                status_code=502,
                detail=(
                    f"Live evaluation failed for patient '{patient_id}' and no cached "
                    f"result exists yet. Run pregenerate_cache.py before demoing."
                ),
            )
        evaluation = DischargeReadinessEvaluation(**cached["data"])

    # Guardrail runs unconditionally, on both the live and cached path.
    evaluation = apply_guardrail(evaluation)
    logger.info("Evaluation for %s served from %s", patient_id, source)

    # Persist as a new EVAL# item -- we keep full history, not just latest.
    timestamp = now_iso()
    db.put_item(patient_pk(patient_id), f"EVAL#{timestamp}", "EVALUATION", evaluation.model_dump())

    # Upsert one task per barrier, keyed deterministically (see barrier_task_key)
    # so a barrier that persists across evaluations reuses its existing task
    # and resolution status instead of forking a duplicate.
    for barrier in evaluation.clinical_barriers:
        task_key = barrier_task_key(barrier.category.value, barrier.barrier_description)
        sk = f"TASK#{task_key}"
        existing = db.get_item(patient_pk(patient_id), sk)
        db.put_item(
            patient_pk(patient_id),
            sk,
            "TASK",
            {
                "task_id": task_key,
                "patient_id": patient_id,
                "eval_id": timestamp,  # most recent eval that surfaced this barrier
                "category": barrier.category.value,
                "role": barrier.assigned_role.value,
                "description": barrier.required_action,
                "barrier_description": barrier.barrier_description,
                "severity": barrier.severity.value,
                "source_field": barrier.source_field.value,
                # Preserve resolution state if this barrier already had a task.
                "is_resolved": existing["data"]["is_resolved"] if existing else False,
                "resolved_by": existing["data"]["resolved_by"] if existing else None,
            },
        )

    write_audit(patient_id, actor=user.user_id, action="evaluation_run", details={"source": source})

    return evaluation.model_dump()


# --------------------------------------------------------------------------
# Tasks
# --------------------------------------------------------------------------

@app.get("/patients/{patient_id}/tasks")
def list_tasks(patient_id: str, user: CurrentUser = Depends(get_current_user)):
    get_patient_or_404(patient_id)
    tasks = db.query_by_pk_prefix(patient_pk(patient_id), "TASK#")
    return [t["data"] for t in tasks]


@app.patch("/tasks/{task_id}/resolve")
def resolve_task(
    task_id: str, body: TaskResolveRequest, user: CurrentUser = Depends(get_current_user)
):
    matches = db.scan_by_sk(f"TASK#{task_id}")
    if not matches:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    item = matches[0]
    task = item["data"]

    if user.role != "Admin" and user.role != task["role"]:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{user.role}' cannot resolve a task assigned to '{task['role']}'",
        )

    task["is_resolved"] = True
    task["resolved_by"] = body.resolved_by
    db.put_item(item["pk"], item["sk"], "TASK", task)

    write_audit(
        task["patient_id"],
        actor=user.user_id,
        action="task_resolved",
        details={"task_id": task_id, "resolved_by": body.resolved_by},
    )
    return task


# --------------------------------------------------------------------------
# Physician actions: signoff and override
# --------------------------------------------------------------------------

@app.post("/patients/{patient_id}/signoff")
def signoff(
    patient_id: str, body: SignoffRequest, user: CurrentUser = Depends(require_roles("Physician"))
):
    get_patient_or_404(patient_id)
    latest = get_latest_eval(patient_id)
    if latest is None:
        raise HTTPException(status_code=409, detail="Cannot sign off: patient has no evaluation yet")

    eval_data = latest["data"]

    if eval_data["readiness_tier"] == "High_Risk_Blocked":
        # Derive blocking status from the CURRENT evaluation's own barrier
        # list (not a stored task filter) -- this stays correct even if the
        # task was created by an earlier evaluation of the same barrier.
        blocking = []
        for barrier in eval_data["clinical_barriers"]:
            if barrier["severity"] != "Critical":
                continue
            task_key = barrier_task_key(barrier["category"], barrier["barrier_description"])
            task_item = db.get_item(patient_pk(patient_id), f"TASK#{task_key}")
            if task_item is None or not task_item["data"]["is_resolved"]:
                blocking.append(barrier["barrier_description"])
        if blocking:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot sign off: unresolved Critical barriers -- {', '.join(blocking)}",
            )

    record = {
        "status": "Approved",
        "physician_id": body.physician_id,
        "rationale": body.rationale,
        "timestamp": now_iso(),
    }
    db.put_item(patient_pk(patient_id), "SIGNOFF", "SIGNOFF", record)
    write_audit(
        patient_id,
        actor=user.user_id,
        action="signoff_approved",
        details={"physician_id": body.physician_id, "rationale": body.rationale},
    )
    return record


@app.post("/patients/{patient_id}/override")
def override_tier(
    patient_id: str, body: OverrideRequest, user: CurrentUser = Depends(require_roles("Physician"))
):
    get_patient_or_404(patient_id)
    latest = get_latest_eval(patient_id)
    if latest is None:
        raise HTTPException(status_code=404, detail="No evaluation exists yet to override")

    old_tier = latest["data"]["readiness_tier"]
    latest["data"]["readiness_tier"] = body.new_tier.value
    db.put_item(latest["pk"], latest["sk"], "EVALUATION", latest["data"])

    write_audit(
        patient_id,
        actor=user.user_id,
        action="tier_override",
        details={
            "old_tier": old_tier,
            "new_tier": body.new_tier.value,
            "rationale": body.rationale,
            "physician_id": body.physician_id,
        },
    )
    return latest["data"]


# --------------------------------------------------------------------------
# Audit log
# --------------------------------------------------------------------------

@app.get("/audit-log/{patient_id}")
def get_audit_log(patient_id: str, user: CurrentUser = Depends(get_current_user)):
    get_patient_or_404(patient_id)
    entries = db.query_by_pk_prefix(patient_pk(patient_id), "AUDIT#")
    entries_sorted = sorted(entries, key=lambda e: e["sk"], reverse=True)  # newest first
    return [e["data"] for e in entries_sorted]


# --------------------------------------------------------------------------
# Hospital-wide operations -- pure Python aggregation, zero AI calls
# --------------------------------------------------------------------------

@app.get("/hospital-overview")
def hospital_overview(user: CurrentUser = Depends(get_current_user)):
    metas = db.scan_by_entity_type("PATIENT_METADATA")

    evaluated: List[tuple] = []
    for m in metas:
        latest = get_latest_eval(m["data"]["patient_id"])
        if latest:
            evaluated.append((m["data"], latest["data"]))

    free_now = expected_soon = expected_tomorrow = 0
    for _, ev in evaluated:
        bucket = bucket_ready_time(ev["estimated_ready_time"])
        if bucket == "now":
            free_now += 1
        elif bucket == "within_4h":
            expected_soon += 1
        else:
            expected_tomorrow += 1

    patients_tracked = len(metas)
    ready_now = sum(1 for _, ev in evaluated if ev["readiness_tier"] == "Ready")
    expected_discharges_today = free_now + expected_soon
    avg_readiness_score = (
        round(sum(ev["readiness_score"] for _, ev in evaluated) / len(evaluated), 1)
        if evaluated
        else 0
    )

    # Priority ranking: who should staff work on next. Lower readiness score,
    # higher readmission risk, and more days already admitted all push a
    # patient UP the list -- these are the patients who most need attention,
    # not necessarily the ones closest to a "Ready" badge.
    risk_weight = {"low": 0, "medium": 15, "high": 30}
    ranking = []
    for profile, ev in evaluated:
        priority_score = (
            (100 - ev["readiness_score"])
            + risk_weight.get(ev["readmission_risk"], 0)
            + min(profile["days_admitted"], 10) * 2
        )
        ranking.append(
            {
                "patient_id": profile["patient_id"],
                "name": profile["name"],
                "readiness_score": ev["readiness_score"],
                "readmission_risk": ev["readmission_risk"],
                "days_admitted": profile["days_admitted"],
                "_priority_score": priority_score,
            }
        )
    ranking.sort(key=lambda r: r["_priority_score"], reverse=True)
    for i, r in enumerate(ranking, start=1):
        r["priority_rank"] = i
        del r["_priority_score"]

    return {
        "bed_availability": {
            "total_beds": TOTAL_BEDS,
            "free_now": free_now,
            "expected_soon": expected_soon,
            "expected_tomorrow": expected_tomorrow,
        },
        "summary_stats": {
            "patients_tracked": patients_tracked,
            "ready_now": ready_now,
            "expected_discharges_today": expected_discharges_today,
            "avg_readiness_score": avg_readiness_score,
        },
        "priority_ranking": ranking,
    }
