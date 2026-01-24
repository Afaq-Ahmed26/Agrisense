from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
from app.middleware.auth import JWTBearer
from app.models.user import User, UserUpdate
from app.services.firebase_service import firebase_service
from datetime import datetime


router = APIRouter()
security = JWTBearer()


@router.get("/", response_model=List[User])
async def get_users(skip: int = 0, limit: int = 100, token: str = Depends(security)):
    firebase_users, _ = firebase_service.list_firebase_users(max_results=limit)
    users = []
    for fb_user in firebase_users:
        users.append(User(
            id=fb_user.uid,
            email=fb_user.email,
            username=fb_user.display_name if fb_user.display_name else fb_user.email.split('@')[0],
            role="farmer", # Default role, in real app would be from custom claims or Firestore
            created_at=datetime.fromtimestamp(fb_user.user_metadata.creation_timestamp / 1000) if fb_user.user_metadata.creation_timestamp else datetime.now(),
            updated_at=datetime.fromtimestamp(fb_user.user_metadata.last_sign_in_timestamp / 1000) if fb_user.user_metadata.last_sign_in_timestamp else datetime.now(),
        ))
    return users


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str, token: str = Depends(security)):
    try:
        fb_user = firebase_service.get_user_by_uid(user_id)
        if not fb_user:
            raise HTTPException(status_code=404, detail="User not found.")
        
        # In a real app, you might have more user details in a Firestore document.
        # We are constructing the User object from what we have.
        return User(
            id=fb_user.uid,
            email=fb_user.email,
            username=fb_user.display_name if fb_user.display_name else fb_user.email.split('@')[0],
            role="farmer", # Default role, in real app would be from custom claims or Firestore
            created_at=datetime.fromtimestamp(fb_user.user_metadata.creation_timestamp / 1000) if fb_user.user_metadata.creation_timestamp else datetime.now(),
            updated_at=datetime.fromtimestamp(fb_user.user_metadata.last_sign_in_timestamp / 1000) if fb_user.user_metadata.last_sign_in_timestamp else datetime.now(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user: {e}")


@router.put("/{user_id}", response_model=User)
async def update_user(user_id: str, user_update: UserUpdate, request: Request, token: str = Depends(security)): # Added request
    user_payload = request.state.user
    if user_payload['uid'] != user_id and user_payload.get('role') != 'admin': # Only admin or self can update
        raise HTTPException(status_code=403, detail="Not authorized to update this user.")

    update_fields = {}
    if user_update.email:
        update_fields['email'] = user_update.email
    if user_update.username:
        update_fields['display_name'] = user_update.username # Firebase uses display_name
    if user_update.password:
        update_fields['password'] = user_update.password
    
    try:
        updated_fb_user = firebase_service.update_firebase_user(user_id, **update_fields)
        if not updated_fb_user:
            raise HTTPException(status_code=404, detail="User not found or update failed.")
        
        # Re-fetch the user to get the latest metadata after update
        fb_user = firebase_service.get_user_by_uid(user_id)
        if not fb_user:
            raise HTTPException(status_code=404, detail="User not found after update.")

        # Assuming role is stored in custom claims or a separate DB.
        # For now, we'll use the role from the token, or default.
        role = user_payload.get("role", "farmer") # Use role from the token that made the request
        
        return User(
            id=fb_user.uid,
            email=fb_user.email,
            username=fb_user.display_name if fb_user.display_name else fb_user.email.split('@')[0],
            role=role,
            created_at=datetime.fromtimestamp(fb_user.user_metadata.creation_timestamp / 1000) if fb_user.user_metadata.creation_timestamp else datetime.now(),
            updated_at=datetime.fromtimestamp(fb_user.user_metadata.last_sign_in_timestamp / 1000) if fb_user.user_metadata.last_sign_in_timestamp else datetime.now(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user: {e}")


@router.delete("/{user_id}")
async def delete_user(user_id: str, request: Request, token: str = Depends(security)): # Added request
    user_payload = request.state.user
    if user_payload['uid'] != user_id and user_payload.get('role') != 'admin': # Only admin or self can delete
        raise HTTPException(status_code=403, detail="Not authorized to delete this user.")

    try:
        firebase_service.delete_firebase_user(user_id)
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {e}")


@router.get("/me", response_model=User)
async def get_current_user(request: Request, token: str = Depends(security)):
    # Get the current authenticated user's information
    user_payload = request.state.user
    email = user_payload.get("sub") or user_payload.get("email") # Firebase token uses 'email', local uses 'sub'

    if not email:
        raise HTTPException(status_code=403, detail="Could not validate user credentials.")

    # Fetch the complete user profile from Firebase
    firebase_user = firebase_service.get_user_by_email(email)
    if not firebase_user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Assuming role is stored in custom claims or a separate DB.
    # For now, we'll use the role from the token, or default.
    role = user_payload.get("role", "farmer")
    
    # In a real app, you might have more user details in a Firestore document.
    # We are constructing the User object from what we have.
    return User(
        id=firebase_user.uid,
        email=firebase_user.email,
        username=firebase_user.display_name or "N/A",
        role=role,
        created_at=firebase_user.user_metadata.creation_timestamp,
        updated_at=firebase_user.user_metadata.last_sign_in_timestamp or firebase_user.user_metadata.creation_timestamp,
    )