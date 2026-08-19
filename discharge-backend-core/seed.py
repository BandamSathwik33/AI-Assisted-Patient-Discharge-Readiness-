"""
Loads data/synthetic_patients.json and POSTs each patient to the backend.

POST /patients still requires a valid bearer token (every endpoint except
/health does), so this script logs in against the Auth service first --
any of the 5 demo users works since /patients has no role restriction.

Usage:
    python seed.py
    python seed.py --file path/to/other_patients.json
"""
import argparse
import json
import os
import sys

import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8003")
SEED_USERNAME = os.getenv("SEED_USERNAME", "admin")
SEED_PASSWORD = os.getenv("SEED_PASSWORD", "password123")


def login() -> str:
    try:
        resp = requests.post(
            f"{AUTH_URL}/auth/login",
            json={"username": SEED_USERNAME, "password": SEED_PASSWORD},
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="data/synthetic_patients.json")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"ERROR: {args.file} not found. Did Person 4 hand off their real dataset yet?")
        sys.exit(1)

    with open(args.file) as f:
        patients = json.load(f)

    if not patients:
        print(f"WARNING: {args.file} contains zero patients -- nothing to seed.")
        return

    token = login()
    headers = {"Authorization": f"Bearer {token}"}

    ok, failed = 0, []
    for p in patients:
        try:
            resp = requests.post(f"{BACKEND_URL}/patients", json=p, headers=headers, timeout=10)
        except requests.RequestException as e:
            failed.append((p.get("patient_id", "?"), str(e)))
            continue
        if resp.status_code == 201:
            ok += 1
            print(f"  seeded {p['patient_id']} ({p['name']})")
        else:
            failed.append((p.get("patient_id", "?"), f"{resp.status_code}: {resp.text}"))

    print(f"\n{ok}/{len(patients)} patients seeded successfully.")
    if failed:
        print(f"{len(failed)} failed:")
        for pid, err in failed:
            print(f"  {pid}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
