from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import asyncio
from app.models.user import User, UserUpdate, DeletedUserResponse
from app.services.user_service import get_user, update_user, get_all_users, get_deleted_users
from app.services.activity_log_service import log_activity
from app.middleware.auth import JWTBearer

router = APIRouter()
security = JWTBearer()


@router.get("/", response_model=List[User])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    token: str = Depends(security)
):
    # For now, allow any authenticated user to list users, 
    # but in a real app, this should be restricted to admins.
    all_users = await get_all_users(skip=skip, limit=limit, include_deleted=include_deleted)
    return all_users


@router.get("/deleted/list", response_model=List[DeletedUserResponse])
async def list_deleted_users(
    skip: int = 0,
    limit: int = 100,
    token: str = Depends(security)
):
    """
    Get the list of soft-deleted users with recovery information. Only admins should be able to see this.
    """
    from app.services.auth_service import verify_token
    payload = verify_token(token)
    acting_user_uid = payload.get("uid") or payload.get("sub")
    
    acting_user = await get_user(acting_user_uid)
    if not acting_user or acting_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view deleted users")

    deleted_users = await get_deleted_users(skip=skip, limit=limit)
    
    now = datetime.now(timezone.utc)
    response_data = []
    for user in deleted_users:
        # PostgreSQL should ensure deleted_at is set for deleted users, but we check for safety
        d_at = user.deleted_at
        if d_at is None:
            continue
            
        # Ensure d_at is timezone-aware if it's naive
        if d_at.tzinfo is None:
            d_at = d_at.replace(tzinfo=timezone.utc)
        
        recovery_deadline = d_at + timedelta(days=7)
        # Calculate days remaining, ensuring it doesn't go below 0
        diff = recovery_deadline - now
        days_remaining = max(0, diff.days)
        is_recoverable = now < recovery_deadline
        
        response_data.append(DeletedUserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role,
            deleted_at=d_at,
            recovery_deadline=recovery_deadline,
            days_remaining=days_remaining,
            days_until_expiry=days_remaining,
            is_recoverable=is_recoverable
        ))
        
    return response_data


@router.get("/me", response_model=User)
async def get_current_user_profile(token: str = Depends(security)):
    from app.services.auth_service import verify_token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    uid = payload.get("uid") or payload.get("sub")
    email = payload.get("email")
    username = payload.get("name") or (email.split("@")[0] if email else "user")
    
    print(f"DEBUG: /me - fetching user with UID: {uid}")
    db_user = await get_user(uid)
    
    if not db_user:
        print(f"DEBUG: /me - user NOT found in database for UID: {uid}. Auto-creating profile...")
        now = datetime.now(timezone.utc)
        new_user = User(
            id=uid,
            email=email or "",
            username=username,
            role="farmer",
            created_at=now,
            updated_at=now,
            is_active=True,
            is_deleted=False,
            deleted_at=None
        )
        try:
            await create_user(new_user)
            db_user = new_user
        except Exception as e:
            print(f"ERROR: Failed to create JIT user profile in /me: {e}")
            raise HTTPException(status_code=500, detail="Failed to initialize user profile.")
        
    if db_user.is_deleted:
        raise HTTPException(status_code=403, detail="User account is deleted.")
        
    print(f"DEBUG: /me - successfully found user: {db_user.username}")
    return db_user


@router.get("/{user_id}", response_model=User)
async def get_user_profile(user_id: str, include_deleted: bool = False, token: str = Depends(security)):
    db_user = await get_user(user_id, include_deleted=include_deleted)
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if db_user.is_deleted and not include_deleted:
        raise HTTPException(status_code=404, detail="User not found (deleted)")
        
    return db_user


@router.patch("/{user_id}", response_model=User)
async def update_user_profile(
    user_id: str,
    user_update: UserUpdate,
    token: str = Depends(security)
):
    from app.services.auth_service import verify_token
    payload = verify_token(token)
    acting_user_uid = payload.get("uid") or payload.get("sub")
    
    acting_user = await get_user(acting_user_uid)
    if not acting_user:
        raise HTTPException(status_code=404, detail="Acting user not found")

    # RBAC: Only admin or the user themselves can update the profile
    if acting_user.role != "admin" and acting_user_uid != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")

    # Prepare updates for PostgreSQL
    db_updates = {"updated_at": datetime.now(timezone.utc)}
    
    if user_update.username:
        db_updates['username'] = user_update.username
    if user_update.email:
        db_updates['email'] = user_update.email
    if user_update.full_name is not None:
        db_updates['full_name'] = user_update.full_name
    if user_update.dashboard_preferences is not None:
        db_updates['dashboard_preferences'] = user_update.dashboard_preferences
    if user_update.is_active is not None:
        db_updates['is_active'] = user_update.is_active
    
    # Handle role and managed_farmer_ids (Admin only)
    if acting_user.role == "admin":
        if user_update.role:
            db_updates['role'] = user_update.role
        if user_update.assigned_device_ids is not None:
            db_updates['assigned_device_ids'] = user_update.assigned_device_ids
        if user_update.managed_farmer_ids is not None:
            db_updates['managed_farmer_ids'] = user_update.managed_farmer_ids

    if db_updates:
        await update_user(user_id, db_updates)
        
    # Log the update activity
    await log_activity(
        user_id=acting_user_uid,
        action="Update User Profile",
        details={"target_user_id": user_id, "updates": list(db_updates.keys())}
    )

    updated_user = await get_user(user_id)
    return updated_user


@router.delete("/{user_id}")
async def delete_user(user_id: str, token: str = Depends(security)):
    from app.services.auth_service import verify_token
    payload = verify_token(token)
    acting_user_id = payload.get("uid") or payload.get("sub")
    
    acting_user = await get_user(acting_user_id)
    if not acting_user or acting_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")

    user_to_delete = await get_user(user_id, include_deleted=True)
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_to_delete.is_deleted:
        return {"message": "User is already deleted"}

    # Perform soft delete in PostgreSQL
    await update_user(user_id, {
        "is_deleted": True,
        "deleted_at": datetime.now(timezone.utc),
        "is_active": False
    })

    # Log the deletion
    await log_activity(
        user_id=acting_user_id,
        action="Delete User (Soft)",
        details={"target_user_id": user_id}
    )

    return {"message": "User successfully soft-deleted"}


@router.post("/{user_id}/undelete")
async def restore_user(user_id: str, token: str = Depends(security)):
    from app.services.auth_service import verify_token
    payload = verify_token(token)
    acting_user_id = payload.get("uid") or payload.get("sub")
    
    acting_user = await get_user(acting_user_id)
    if not acting_user or acting_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can restore users")

    deleted_user = await get_user(user_id, include_deleted=True)
    if not deleted_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not deleted_user.is_deleted:
        return {"message": "User is not deleted"}

    # Restore in PostgreSQL
    await update_user(user_id, {
        "is_deleted": False,
        "deleted_at": None,
        "is_active": True
    })

    # Log the restoration
    await log_activity(
        user_id=acting_user_id,
        action="Restore User",
        details={"target_user_id": user_id}
    )

    restored_user = await get_user(user_id)
    return restored_user


@router.get("/{user_id}/preferences")
async def get_user_preferences(user_id: str, token: str = Depends(security)):
    from app.services.auth_service import verify_token
    payload = verify_token(token)
    acting_user_uid = payload.get("uid") or payload.get("sub")
    
    # RBAC: Only admin or the user themselves can view preferences
    acting_user = await get_user(acting_user_uid)
    if not acting_user:
        raise HTTPException(status_code=404, detail="Acting user not found")
        
    if acting_user.role != "admin" and acting_user_uid != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view these preferences")

    db_user = await get_user(user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return db_user.preferences or {
        "temperature_unit": "Celsius",
        "volume_unit": "liters",
        "time_zone": "UTC"
    }


@router.put("/{user_id}/preferences")
async def update_user_preferences(
    user_id: str, 
    preferences: dict, 
    token: str = Depends(security)
):
    from app.services.auth_service import verify_token
    payload = verify_token(token)
    acting_user_uid = payload.get("uid") or payload.get("sub")
    
    acting_user = await get_user(acting_user_uid)
    if not acting_user:
        raise HTTPException(status_code=404, detail="Acting user not found")
        
    # RBAC: Only admin or the user themselves can update preferences
    if acting_user.role != "admin" and acting_user_uid != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update these preferences")

    await update_user(user_id, {"preferences": preferences})
    
    # Log the activity
    await log_activity(
        user_id=acting_user_uid,
        action="Update User Preferences",
        details={"target_user_id": user_id}
    )
    
    return preferences


@router.get("/{user_id}/notification-preferences")
async def get_user_notification_preferences(user_id: str, token: str = Depends(security)):
    from app.services.auth_service import verify_token
    payload = verify_token(token)
    acting_user_uid = payload.get("uid") or payload.get("sub")
    
    # RBAC: Only admin or the user themselves can view preferences
    acting_user = await get_user(acting_user_uid)
    if not acting_user:
        raise HTTPException(status_code=404, detail="Acting user not found")
        
    if acting_user.role != "admin" and acting_user_uid != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view these preferences")

    db_user = await get_user(user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return db_user.notification_preferences or {
        "on_critical_alert": "email",
        "on_high_alert": "in_app",
        "on_medium_alert": "in_app",
        "on_low_alert": "none"
    }


@router.put("/{user_id}/notification-preferences")
async def update_user_notification_preferences(
    user_id: str, 
    preferences: dict, 
    token: str = Depends(security)
):
    from app.services.auth_service import verify_token
    payload = verify_token(token)
    acting_user_uid = payload.get("uid") or payload.get("sub")
    
    acting_user = await get_user(acting_user_uid)
    if not acting_user:
        raise HTTPException(status_code=404, detail="Acting user not found")
        
    # RBAC: Only admin or the user themselves can update preferences
    if acting_user.role != "admin" and acting_user_uid != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update these preferences")

    await update_user(user_id, {"notification_preferences": preferences})
    
    # Log the activity
    await log_activity(
        user_id=acting_user_uid,
        action="Update Notification Preferences",
        details={"target_user_id": user_id}
    )
    
    return preferences
