import os
from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException

JWT_SECRET = os.getenv("JWT_SHARED_SECRET", "discharge-planner-2026-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


class CurrentUser:
    def __init__(self, user_id: str, role: str, name: str):
        self.user_id = user_id
        self.role = role
        self.name = name


def get_current_user(authorization: Optional[str] = Header(None)) -> CurrentUser:
    """Every endpoint except /health depends on this. Covers every failure mode
    a bearer token can hit: missing header, wrong scheme, bad signature,
    expired token, and a token that's valid but missing required claims."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0] != "Bearer":
        raise HTTPException(status_code=401, detail="Authorization header must be 'Bearer <token>'")
    token = parts[1]

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    role = payload.get("role")
    name = payload.get("name")
    if not user_id or not role:
        raise HTTPException(status_code=401, detail="Token is missing required claims (sub/role)")

    return CurrentUser(user_id=user_id, role=role, name=name or user_id)


def require_roles(*allowed_roles: str):
    """Dependency factory: 403s unless the caller's role is in allowed_roles,
    or the caller is Admin (Admin can always act, per the team contract)."""

    def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role != "Admin" and user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user.role}' is not permitted. Requires one of {list(allowed_roles)} (or Admin).",
            )
        return user

    return checker
