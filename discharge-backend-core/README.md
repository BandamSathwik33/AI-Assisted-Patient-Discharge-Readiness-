# discharge-backend-core

Core Backend API (Person 2) for the AI-Assisted Patient Discharge Readiness &
Follow-Up Planner. Owns patient data, the safety guardrail, the cache
fallback that makes the demo failure-proof, and the hospital-ops
aggregation endpoint.

## Setup

```bash
python3 -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for the full OpenAPI spec.

## Seeding data

```bash
python seed.py                      # loads data/synthetic_patients.json
python seed.py --file other.json    # or a different file
```

`seed.py` logs into the Auth service (`AUTH_URL`, default `localhost:8003`)
as `admin` and uses that token to `POST /patients`. It's idempotent --
re-running it overwrites existing patients rather than erroring, so you can
run it as many times as you want during development.

If Person 4 hasn't handed off their real `synthetic_patients.json` yet, a
10-patient placeholder set is already in `data/` so you can build and test
this service independently.

## Pre-generating the cache (mandatory reliability checkpoint)

```bash
python pregenerate_cache.py
```

Run this **while the AI orchestrator is healthy**, once for every seeded
patient, before integration/demo. It's what lets `/evaluate/{id}` degrade
to a cached result instead of a 502 if the live LLM call fails on stage.
Treat any failure in its output as a P0 blocker, not something to fix later.

## Endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | No auth required |
| GET | `/patients` | List with latest tier/score per patient |
| GET | `/patients/{id}` | Profile + latest evaluation + tasks |
| POST | `/patients` | Seed-script use; upserts by `patient_id` |
| POST | `/evaluate/{id}` | Physician/Nurse/Case_Manager/Admin. Full pipeline below |
| GET | `/patients/{id}/tasks` | |
| PATCH | `/tasks/{task_id}/resolve` | Role must match task's `assigned_role`, or Admin |
| POST | `/patients/{id}/signoff` | Physician only. 409 if a Critical barrier's task is unresolved |
| POST | `/patients/{id}/override` | Physician only. `rationale` must be >= 10 chars |
| GET | `/audit-log/{id}` | Newest first |
| GET | `/hospital-overview` | Pure Python aggregation, zero AI calls |

### `/evaluate/{id}` pipeline

1. Load patient's raw text fields.
2. Call NLP service `/extract-entities` (10s timeout).
3. Call AI orchestrator `/orchestrate/evaluate` (20s timeout).
4. **Any failure** in steps 2-3 (network error, timeout, non-2xx, schema
   validation failure) falls back to the most recent cached evaluation for
   that patient. Only if none exists does this return a 502.
5. **The guardrail runs unconditionally**, on both the live and cached path:
   any Critical-severity barrier forces `readiness_tier = "High_Risk_Blocked"`
   and caps `readiness_score` at 30, regardless of what the AI said. Verified
   in testing: a deliberately "wrong" upstream response of `Ready`/78 with a
   Critical barrier present was correctly overridden.
6. Persists a new `EVAL#<timestamp>` record (full history is kept, not just
   the latest).
7. Upserts one task per barrier (see design note below).

## Design decision worth knowing about: deterministic task keys

The original plan (per the brief) was "auto-create a task per barrier on
every `/evaluate` call." Testing surfaced a real bug with that: re-running
an evaluation for a barrier that's still present created a **second,
random-UUID task** for the same barrier, orphaning the first one. A
physician could resolve the task visible on screen and still be blocked
from signing off by an invisible duplicate tied to the newer evaluation.

Fix: tasks are now keyed by a deterministic hash of
`(category, barrier_description)` instead of a random UUID
(`barrier_task_key()` in `main.py`). Re-evaluating a persisting barrier
**updates** its existing task and preserves resolution state, instead of
forking a new one. Signoff blocking is derived directly from the current
evaluation's barrier list (not a stored `eval_id` filter), so it stays
correct even across repeated evaluations. Regression-tested in
`main.py`'s logic: evaluate -> evaluate again -> resolve -> evaluate again
-> signoff now succeeds, where it previously stayed falsely blocked.

## Testing notes

Endpoints were exercised directly with curl against hand-crafted JWTs and a
stub AI orchestrator/NLP service (not included here -- Person 3 and Person 4
own those for real). Verified: every 401/403/404/409/422/502 path listed
above, the guardrail override, the cache fallback (AI killed mid-session),
and the full seed -> pregenerate_cache flow against a stub auth service.

## Data model

Single-table SQLite (`db.py`) with `(pk, sk)` composite key, shaped to
mirror a DynamoDB single-table design so it's a straightforward swap to
real DynamoDB later:

```
PATIENT#<id> | METADATA          -> patient profile
PATIENT#<id> | EVAL#<iso-ts>     -> a stored evaluation (full history kept)
PATIENT#<id> | TASK#<barrier-hash> -> a discharge task (deterministic key, see above)
PATIENT#<id> | AUDIT#<iso-ts>    -> an audit log entry
PATIENT#<id> | SIGNOFF           -> current signoff status
```

## Env vars

See `.env.example`. `JWT_SHARED_SECRET` and `JWT_ALGORITHM` must match
Person 5's Auth service exactly, or every request will 401.
