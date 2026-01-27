from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional # Import Optional
from app.middleware.auth import JWTBearer
from app.models.user import User, UserUpdate
from app.services.firebase_service import firebase_service
from app.services.user_service import update_user_in_firestore, get_user_from_firestore, get_all_users_from_firestore # Import necessary functions
from datetime import datetime


router = APIRouter()
security = JWTBearer()


@router.get("/", response_model=List[User])
async def get_users(skip: int = 0, limit: int = 100, include_deleted: bool = False, token: str = Depends(security)): # Added include_deleted
    all_users = get_all_users_from_firestore(skip=skip, limit=limit, include_deleted=include_deleted)
    
    # Filter out deleted users if not explicitly requested
    if not include_deleted:
        all_users = [user for user in all_users if not user.is_deleted]
        
    return all_users


@router.get("/me", response_model=User)
async def get_current_user(request: Request, token: str = Depends(security)):
    # Get the current authenticated user's information
    user_payload = request.state.user
    print(f"DEBUG: /me - user_payload from token: {user_payload}")
    uid = user_payload.get("uid") # Extract UID from the decoded Firebase token
    print(f"DEBUG: /me - extracted UID: {uid}")

    if not uid:
        print("DEBUG: /me - UID is missing from token payload")
        raise HTTPException(status_code=403, detail="Could not validate user credentials (missing UID).")

    # Fetch the complete user profile from Firestore
    print(f"DEBUG: /me - calling get_user_from_firestore with UID: {uid}")
    user_from_firestore = get_user_from_firestore(uid)
    
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
    user_from_firestore = get_user_from_firestore(user_id, include_deleted=include_deleted)
    
    if not user_from_firestore:
        raise HTTPException(status_code=404, detail="User not found.")
    
    if user_from_firestore.is_deleted and not include_deleted:
        raise HTTPException(status_code=404, detail="User not found (account is deleted).")
        
    return user_from_firestore


@router.patch("/{user_id}", response_model=User)
async def update_user(user_id: str, user_update: UserUpdate, request: Request, token: str = Depends(security)):
    user_payload = request.state.user
    acting_user_uid = user_payload.get('uid')

    if not acting_user_uid:
        raise HTTPException(status_code=403, detail="Could not validate user credentials.")

    # Fetch the full profile of the user performing the action to check their role
    acting_user = get_user_from_firestore(acting_user_uid)
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
    
    # Handle role update (only if admin is making the request)
    if user_update.role is not None:
        if acting_user.role == 'admin':
            firestore_updates['role'] = user_update.role
        else:
            raise HTTPException(status_code=403, detail="Only admins can change user roles.")

    try:
        # Update Firebase Auth if there are changes
        if firebase_auth_updates:
            updated_fb_user = firebase_service.update_firebase_user(user_id, **firebase_auth_updates)
            if not updated_fb_user:
                raise HTTPException(status_code=404, detail="User not found in Firebase Auth or update failed.")

        # Update Firestore
        if firestore_updates:
            update_user_in_firestore(user_id, firestore_updates)

        # Fetch the updated user from Firestore to return the complete and latest profile
        updated_user = get_user_from_firestore(user_id)
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
    if user_payload['uid'] != user_id and user_payload.get('role') != 'admin': # Only admin or self can delete
        raise HTTPException(status_code=403, detail="Not authorized to delete this user.")

    try:
        # Perform soft delete in Firestore
        update_user_in_firestore(user_id, {"is_deleted": True, "deleted_at": datetime.utcnow()})
        
        # Hard delete user in Firebase Auth
        firebase_service.delete_firebase_user(user_id)
        
        return {"message": "User deleted permanently from Firebase Auth and marked as deleted in Firestore."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {e}")