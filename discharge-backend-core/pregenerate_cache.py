"""
THE FAILURE PLAN. Run this once, with the AI orchestrator and NLP service
healthy, so every seeded patient has at least one cached EVAL# item before
integration/demo. This is what lets /evaluate degrade gracefully to a
cached result if the live LLM call fails on stage.

Run this from the 2:00-2:25 checkpoint (Section 0.7 of the kickoff brief).
Not optional polish -- if this doesn't run cleanly for every patient, that
patient has zero fallback and a live-demo LLM hiccup on their card is a
hard failure, not a degraded one.

Usage:
    python pregenerate_cache.py
"""
import os
import sys
import time

import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8003")
RUN_USERNAME = os.getenv("SEED_USERNAME", "nurse.jane")
RUN_PASSWORD = os.getenv("SEED_PASSWORD", "password123")


def login() -> str:
    try:
        resp = requests.post(
            f"{AUTH_URL}/auth/login",
            json={"username": RUN_USERNAME, "password": RUN_PASSWORD},
            timeout=5,
        )
    except requests.RequestException as e:
        print(f"ERROR: could not reach Auth service at {AUTH_URL} -- is it running? ({e})")
        sys.exit(1)
    if resp.status_code != 200:
        print(f"ERROR: login failed ({resp.status_code}): {resp.text}")
        sys.exit(1)
    return resp.json()["access_token"]


def main():
    token = login()
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.get(f"{BACKEND_URL}/patients", headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"ERROR: could not fetch patient list from {BACKEND_URL} -- is the backend running? ({e})")
        sys.exit(1)

    patients = resp.json()
    if not patients:
        print("No patients found. Run seed.py first.")
        sys.exit(1)

    print(f"Pre-generating cache for {len(patients)} patients...\n")

    ok, failed = [], []
    for p in patients:
        pid = p["patient_id"]
        start = time.time()
        try:
            eval_resp = requests.post(f"{BACKEND_URL}/evaluate/{pid}", headers=headers, timeout=30)
        except requests.RequestException as e:
            failed.append((pid, str(e)))
            print(f"  FAIL {pid}: {e}")
            continue
        elapsed = time.time() - start
        if eval_resp.status_code == 200:
            tier = eval_resp.json().get("readiness_tier", "?")
            ok.append(pid)
            print(f"  OK   {pid} -> {tier} ({elapsed:.1f}s)")
        else:
            failed.append((pid, f"{eval_resp.status_code}: {eval_resp.text}"))
            print(f"  FAIL {pid}: {eval_resp.status_code} {eval_resp.text}")

    print(f"\n{len(ok)}/{len(patients)} patients cached successfully.")
    if failed:
        print("\nP0 BLOCKER -- these patients have NO cached fallback and will")
        print("502 if the live pipeline fails during the demo:")
        for pid, err in failed:
            print(f"  {pid}: {err}")
        sys.exit(1)
    else:
        print("Every patient has a cached fallback. Safe to demo.")


if __name__ == "__main__":
    main()
