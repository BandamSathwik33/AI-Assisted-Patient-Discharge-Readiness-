import os
import sys

# Add discharge-auth-service to python path
sys.path.insert(0, os.path.abspath("discharge-auth-service"))

from fastapi.testclient import TestClient
from main import app, USERS_DB

client = TestClient(app)

def test_auth_service():
    print("Testing GET /health...")
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    print("  -> /health PASS")

    print("\nTesting POST /auth/login for all users...")
    tokens = {}
    for username, info in USERS_DB.items():
        resp = client.post("/auth/login", json={"username": username, "password": "password123"})
        assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
        data = resp.json()
        assert "access_token" in data
        assert data["role"] == info["role"]
        assert data["user_id"] == username
        assert data["full_name"] == info["full_name"]
        tokens[username] = data["access_token"]
        print(f"  -> Login PASS for {username} (Role: {data['role']}, Name: {data['full_name']})")

    print("\nTesting POST /auth/login invalid credentials...")
    resp = client.post("/auth/login", json={"username": "dr.smith", "password": "wrongpassword"})
    assert resp.status_code == 401
    resp = client.post("/auth/login", json={"username": "nonexistent", "password": "password123"})
    assert resp.status_code == 401
    print("  -> Invalid credentials rejected PASS (HTTP 401)")

    print("\nTesting GET /auth/me with tokens...")
    for username, token in tokens.items():
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"/auth/me failed for {username}: {resp.text}"
        data = resp.json()
        assert data["user_id"] == username
        assert data["role"] == USERS_DB[username]["role"]
        assert data["full_name"] == USERS_DB[username]["full_name"]
        print(f"  -> /auth/me PASS for {username}")

    print("\nTesting GET /auth/me invalid / missing tokens...")
    resp = client.get("/auth/me")
    assert resp.status_code == 401
    resp = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.payload"})
    assert resp.status_code == 401
    print("  -> Invalid / missing token rejected PASS (HTTP 401)")

    print("\n=======================================================")
    print("ALL AUTH SERVICE TESTS PASSED PERFECTLY!")
    print("=======================================================")

if __name__ == "__main__":
    test_auth_service()
