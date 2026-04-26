from fastapi import Depends, HTTPException, status, Request
from typing import List, Set
from app.services.user_service import get_user_from_firestore
from app.middleware.auth import JWTBearer
from app.models.user import User

security = JWTBearer()
OFFICER_ROLES = {"officer", "middleman"}
ASSIGNED_DEVICE_ROLES = {"farmer", "officer"}


def normalize_role(role: str) -> str:
    normalized = (role or "").strip().lower()
    if normalized in OFFICER_ROLES:
        return "officer"
    return normalized


def get_assigned_device_ids(user: User) -> Set[str]:
    assigned_ids = set()

    for device_id in user.assigned_device_ids or []:
        if isinstance(device_id, str) and device_id.strip():
            assigned_ids.add(device_id.strip())

    # Backward-compatible support for any legacy single assignment field.
    legacy_assigned_id = getattr(user, "assigned_device_id", None)
    if isinstance(legacy_assigned_id, str) and legacy_assigned_id.strip():
        assigned_ids.add(legacy_assigned_id.strip())

    return assigned_ids


async def get_current_user(request: Request, token: str = Depends(security)) -> User:
    user_payload = getattr(request.state, "user", {}) or {}
    uid = user_payload.get("user_id") or user_payload.get("uid")

    if not uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials."
        )

    user = await get_user_from_firestore(uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    return user


def ensure_device_access(user: User, device_id: str) -> None:
    role = normalize_role(user.role)
    if role not in ASSIGNED_DEVICE_ROLES:
        return

    assigned_device_ids = get_assigned_device_ids(user)
    if device_id not in assigned_device_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User is not assigned to device {device_id}."
        )


def require_roles(required_roles: List[str]):
    """
    Dependency that checks if the current user has one of the required roles.
    """
    normalized_required_roles = {normalize_role(role) for role in required_roles}

    async def role_checker(current_user: User = Depends(get_current_user)):
        if normalize_role(current_user.role) not in normalized_required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required permissions."
            )

        return current_user

    return role_checker
