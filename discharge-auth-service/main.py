import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load environment variables
load_dotenv()

PORT = int(os.getenv("PORT", "8003"))
JWT_SHARED_SECRET = os.getenv("JWT_SHARED_SECRET", "discharge-planner-2026-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "8"))
CORS_ALLOWED_ORIGIN = os.getenv("CORS_ALLOWED_ORIGIN", "http://localhost:5173")

# Initialize FastAPI app
app = FastAPI(
    title="AI-Assisted Patient Discharge Planner - Auth Service",
    description="Authentication & RBAC Service for Patient Discharge Readiness Platform",
    version="1.0.0",
)

# Configure CORS
origins = [origin.strip() for origin in CORS_ALLOWED_ORIGIN.split(",") if origin.strip()]
if "*" not in origins and "http://localhost:5173" not in origins:
    origins.append("http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if "*" not in origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo User Directory
USERS_DB = {
    "dr.smith": {
        "password": "password123",
        "role": "Physician",
        "full_name": "Dr. Sarah Smith",
    },
    "nurse.jane": {
        "password": "password123",
        "role": "Nurse",
        "full_name": "Jane Rodriguez, RN",
    },
    "pharm.lee": {
        "password": "password123",
        "role": "Pharmacist",
        "full_name": "Pharm. David Lee",
    },
    "case.taylor": {
        "password": "password123",
        "role": "Case_Manager",
        "full_name": "Taylor Brooks",
    },
    "admin": {
        "password": "password123",
        "role": "Admin",
        "full_name": "System Admin",
    },
}


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    full_name: str


class UserProfileResponse(BaseModel):
    user_id: str
    role: str
    full_name: str


def create_access_token(username: str, role: str, full_name: str) -> str:
    """Generate a signed JWT token containing user identity and role."""
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    payload = {
        "sub": username,
        "role": role,
        "name": full_name,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    encoded_jwt = jwt.encode(payload, JWT_SHARED_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and validate a signed JWT token."""
    try:
        payload = jwt.decode(token, JWT_SHARED_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/health", summary="Health check")
def health_check():
    """Returns service health status."""
    return {"status": "ok"}


@app.post(
    "/auth/login",
    response_model=LoginResponse,
    summary="User Login",
    description="Authenticate clinical user and receive JWT access token",
)
def login(credentials: LoginRequest):
    user = USERS_DB.get(credentials.username)
    if not user or user["password"] != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        username=credentials.username,
        role=user["role"],
        full_name=user["full_name"],
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        role=user["role"],
        user_id=credentials.username,
        full_name=user["full_name"],
    )


@app.get(
    "/auth/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
    description="Decodes the provided Bearer token and returns user profile info",
)
def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme. Must be Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    payload = decode_token(token)

    username = payload.get("sub")
    role = payload.get("role")
    full_name = payload.get("name")

    if not username or not role or not full_name:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incomplete token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserProfileResponse(
        user_id=username,
        role=role,
        full_name=full_name,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
