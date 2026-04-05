import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from typing import List, Optional
from app.middleware.auth import JWTBearer
from app.models.user import User, UserUpdate
from app.models.preferences import UserPreferences
from app.models.notification_preferences import NotificationPreferences
from app.services.firebase_service import firebase_service
from app.services.user_service import update_user_in_firestore, get_user_from_firestore, get_all_users_from_firestore
from app.services.activity_log_service import log_activity
from datetime import datetime
import uuid


router = APIRouter()
security = JWTBearer()


@router.get("/", response_model=List[User])
async def get_users(skip: int = 0, limit: int = 100, include_deleted: bool = False, token: str = Depends(security)): # Added include_deleted
    all_users = await get_all_users_from_firestore(skip=skip, limit=limit, include_deleted=include_deleted)
    
    # Filter out deleted users if not explicitly requested
    if not include_deleted:
        all_users = [user for user in all_users if not user.is_deleted]
        
    return all_users


@router.get("/me", response_model=User)
async def get_current_user(request: Request, token: str = Depends(security)):
    # Get the current authenticated user's information
    user_payload = request.state.user
    print(f"DEBUG: /me - user_payload from token: {user_payload}")
    uid = user_payload.get("user_id") # Extract UID from the decoded Firebase token
    print(f"DEBUG: /me - extracted UID: {uid}")

    if not uid:
        print("DEBUG: /me - UID is missing from token payload")
        raise HTTPException(status_code=403, detail="Could not validate user credentials (missing UID).")

    # Fetch the complete user profile from Firestore
    print(f"DEBUG: /me - calling get_user_from_firestore with UID: {uid}")
    user_from_firestore = await get_user_from_firestore(uid)
    
    if not user_from_firestore:
        print(f"DEBUG: /me - get_user_from_firestore returned None for UID: {uid}")
        raise HTTPException(status_code=404, detail="User not found in Firestore.")
    
    if user_from_firestore.is_deleted:
        print(f"DEBUG: /me - user with UID {uid} is marked as deleted.")
        raise HTTPException(status_code=404, detail="User account is deleted.")

    print(f"DEBUG: /me - successfully found user: {user_from_firestore.username}")
    return user_from_firestore


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str, include_deleted: bool = False, token: str = Depends(security)): # Added include_deleted
    user_from_firestore = await get_user_from_firestore(user_id, include_deleted=include_deleted)
    
    if not user_from_firestore:
        raise HTTPException(status_code=404, detail="User not found.")
    
    if user_from_firestore.is_deleted and not include_deleted:
        raise HTTPException(status_code=404, detail="User not found (account is deleted).")
        
    return user_from_firestore


@router.patch("/{user_id}", response_model=User)
async def update_user(user_id: str, user_update: UserUpdate, request: Request, token: str = Depends(security)):
    user_payload = request.state.user
    acting_user_uid = user_payload.get('user_id')

    if not acting_user_uid:
        raise HTTPException(status_code=403, detail="Could not validate user credentials.")

    # Fetch the full profile of the user performing the action to check their role
    acting_user = await get_user_from_firestore(acting_user_uid)
    if not acting_user:
        raise HTTPException(status_code=404, detail="Acting user not found.")

    print(f"DEBUG: update_user - acting_user: {acting_user.username}, role: {acting_user.role}")

    if acting_user.role != 'admin' and acting_user_uid != user_id: # Only admin or self can update
        raise HTTPException(status_code=403, detail="Not authorized to update this user.")

    # Prepare updates for Firebase Auth
    firebase_auth_updates = {}
    if user_update.email:
        firebase_auth_updates['email'] = user_update.email
    if user_update.username:
        firebase_auth_updates['display_name'] = user_update.username
    if user_update.password:
        firebase_auth_updates['password'] = user_update.password

    # Prepare updates for Firestore
    firestore_updates = {"updated_at": datetime.utcnow()}
    if user_update.username:
        firestore_updates['username'] = user_update.username
    if user_update.email: # Update email in Firestore if it changes
        firestore_updates['email'] = user_update.email
    if user_update.full_name:
        firestore_updates['full_name'] = user_update.full_name
    if user_update.dashboard_preferences is not None:
        firestore_updates['dashboard_preferences'] = user_update.dashboard_preferences
    if user_update.is_active is not None:
        firestore_updates['is_active'] = user_update.is_active
    
    # Get current user data for logging changes
    target_user_current_data = await get_user_from_firestore(user_id)
    if not target_user_current_data:
        raise HTTPException(status_code=404, detail="Target user not found for logging.")

    changes = {}
    if user_update.username and user_update.username != target_user_current_data.username:
        changes['username'] = {"old": target_user_current_data.username, "new": user_update.username}
    if user_update.email and user_update.email != target_user_current_data.email:
        changes['email'] = {"old": target_user_current_data.email, "new": user_update.email}
    if user_update.full_name and user_update.full_name != target_user_current_data.full_name:
        changes['full_name'] = {"old": target_user_current_data.full_name, "new": user_update.full_name}

    # Handle role update (only if admin is making the request)
    if user_update.role is not None:
        if acting_user.role == 'admin':
            if user_update.role != target_user_current_data.role:
                changes['role'] = {"old": target_user_current_data.role, "new": user_update.role}
            firestore_updates['role'] = user_update.role
        else:
            raise HTTPException(status_code=403, detail="Only admins can change user roles.")

    try:
        # Update Firebase Auth if there are changes
        if firebase_auth_updates:
            # Note: firebase_service.update_firebase_user is not explicitly async but we should treat it as blocking I/O
            updated_fb_user = await asyncio.to_thread(firebase_service.update_firebase_user, user_id, **firebase_auth_updates)
            if not updated_fb_user:
                raise HTTPException(status_code=404, detail="User not found in Firebase Auth or update failed.")

        # Update Firestore
        if firestore_updates:
            await update_user_in_firestore(user_id, firestore_updates)

        # Log activity if there were changes
        if changes:
            log_activity(
                user_id=acting_user_uid,
                action="User Profile Update",
                details={"target_user_id": user_id, "changes": changes}
            )

        # Fetch the updated user from Firestore to return the complete and latest profile
        updated_user = await get_user_from_firestore(user_id)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found after update.")

        return updated_user
    except HTTPException:
        raise # Re-raise HTTPExceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user: {e}")


@router.delete("/{user_id}")
async def delete_user(user_id: str, request: Request, token: str = Depends(security)): # Added request
    user_payload = request.state.user
    print(f"DEBUG: delete_user - user_payload: {user_payload}")
    if user_payload['user_id'] != user_id and user_payload.get('role') != 'admin': # Only admin or self can delete
        raise HTTPException(status_code=403, detail="Not authorized to delete this user.")

    try:
        # Perform soft delete in Firestore
        await update_user_in_firestore(user_id, {"is_deleted": True, "deleted_at": datetime.utcnow()})
        
        # Hard delete user in Firebase Auth
        await asyncio.to_thread(firebase_service.delete_firebase_user, user_id)
        
        return {"message": "User deleted permanently from Firebase Auth and marked as deleted in Firestore."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {e}")


@router.get("/{user_id}/preferences", response_model=UserPreferences)
async def get_user_preferences(user_id: str, token: str = Depends(security)):
    """
    Retrieve a user's preferences.
    If no preferences are set, return the default preferences.
    """
    prefs_ref = firebase_service.db.collection('user_preferences').document(user_id)
    doc = await asyncio.to_thread(prefs_ref.get)
    if doc.exists:
        return UserPreferences(**doc.to_dict())
    return UserPreferences()


@router.put("/{user_id}/preferences", response_model=UserPreferences)
async def update_user_preferences(user_id: str, preferences: UserPreferences, request: Request, token: str = Depends(security)):
    """
    Update a user's preferences.
    Only the user themselves or an admin can update preferences.
    """
    user_payload = request.state.user
    acting_user_uid = user_payload.get('user_id') or user_payload.get('uid')
    
    # To get the role, we need to fetch the user's profile from Firestore
    acting_user = await get_user_from_firestore(acting_user_uid)
    if not acting_user:
        raise HTTPException(status_code=404, detail="Acting user not found.")

    if acting_user.role != 'admin' and acting_user_uid != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update these preferences.")

    prefs_ref = firebase_service.db.collection('user_preferences').document(user_id)
    
    # For logging, get old preferences
    old_prefs_doc = await asyncio.to_thread(prefs_ref.get)
    old_prefs = UserPreferences(**old_prefs_doc.to_dict()) if old_prefs_doc.exists else UserPreferences()

    # Set the new preferences
    await asyncio.to_thread(prefs_ref.set, preferences.model_dump())

    # Log the activity
    changes = {k: {"old": getattr(old_prefs, k), "new": getattr(preferences, k)} for k in preferences.model_dump().keys() if getattr(old_prefs, k) != getattr(preferences, k)}
    if changes:
        log_activity(
            user_id=acting_user_uid,
            action="User Preferences Update",
            details={"target_user_id": user_id, "changes": changes}
        )

    return preferences


@router.get("/{user_id}/notification-preferences", response_model=NotificationPreferences)
async def get_user_notification_preferences(user_id: str, token: str = Depends(security)):
    """
    Retrieve a user's notification preferences.
    """
    prefs_ref = firebase_service.db.collection('notification_preferences').document(user_id)
    doc = await asyncio.to_thread(prefs_ref.get)
    if doc.exists:
        return NotificationPreferences(**doc.to_dict())
    return NotificationPreferences()


@router.put("/{user_id}/notification-preferences", response_model=NotificationPreferences)
async def update_user_notification_preferences(user_id: str, preferences: NotificationPreferences, request: Request, token: str = Depends(security)):
    """
    Update a user's notification preferences.
    """
    user_payload = request.state.user
    acting_user_uid = user_payload.get('user_id') or user_payload.get('uid')
    
    acting_user = await get_user_from_firestore(acting_user_uid)
    if not acting_user:
        raise HTTPException(status_code=404, detail="Acting user not found.")

    if acting_user.role != 'admin' and acting_user_uid != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update these preferences.")

    prefs_ref = firebase_service.db.collection('notification_preferences').document(user_id)
    
    old_prefs_doc = await asyncio.to_thread(prefs_ref.get)
    old_prefs = NotificationPreferences(**old_prefs_doc.to_dict()) if old_prefs_doc.exists else NotificationPreferences()

    await asyncio.to_thread(prefs_ref.set, preferences.model_dump())

    changes = {k: {"old": getattr(old_prefs, k), "new": getattr(preferences, k)} for k in preferences.model_dump().keys() if getattr(old_prefs, k) != getattr(preferences, k)}
    if changes:
        log_activity(
            user_id=acting_user_uid,
            action="Notification Preferences Update",
            details={"target_user_id": user_id, "changes": changes}
        )

    return preferences
