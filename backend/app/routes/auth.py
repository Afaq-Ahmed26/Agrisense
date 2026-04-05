from fastapi import APIRouter, Depends, HTTPException, status, Body # Import Body
from fastapi.security import HTTPBearer
from typing import Optional
from datetime import timedelta, datetime
from app.models.user import UserCreate, User
from app.services.auth_service import get_password_hash, verify_token
from app.services.firebase_service import firebase_service
from app.services.user_service import create_user_in_firestore, get_user_from_firestore # Import create_user_in_firestore and get_user_from_firestore
from app.services.activity_log_service import log_activity
from app.utils.validators import EmailValidator, PasswordValidator
from app.config import settings
from app.middleware.auth import JWTBearer


router = APIRouter()
security = JWTBearer()


@router.post("/register", response_model=User)
async def register(user: UserCreate):
    print(f"DEBUG: Register endpoint - Received user data for {user.email}")
    
    # Check if user already exists in Firebase (Auth and Firestore)
    existing_firebase_user = firebase_service.get_user_by_email(user.email)
    if existing_firebase_user:
        # Check if the user exists in Firestore and is not soft-deleted
        firestore_user = await get_user_from_firestore(existing_firebase_user.uid, include_deleted=True)
        if firestore_user and not firestore_user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered and active"
            )
        elif firestore_user and firestore_user.is_deleted:
            # User exists but is soft-deleted, allow re-registration
            fb_user_details = firebase_service.get_user_by_uid(existing_firebase_user.uid)
            if fb_user_details and fb_user_details.disabled:
                firebase_service.enable_firebase_user(existing_firebase_user.uid)
            
            # Update existing firestore user and mark as not deleted
            from app.services.user_service import update_user_in_firestore
            await update_user_in_firestore(existing_firebase_user.uid, {"is_deleted": False, "deleted_at": None})
            
            # After reactivating, we should update their display name if provided and return them
            if user.username:
                firebase_service.update_firebase_user(existing_firebase_user.uid, display_name=user.username)
            
            reactivated_user = await get_user_from_firestore(existing_firebase_user.uid)
            if reactivated_user:
                return reactivated_user
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to reactivate user profile after re-registration."
                )
        else:
            # User in Firebase Auth but not in Firestore, proceed to create in Firestore
            pass
    
    # Create user in Firebase Auth
    firebase_user = firebase_service.create_firebase_user(
        email=user.email,
        password=user.password,
        display_name=user.username
    )
    
    if not firebase_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user in Firebase Authentication"
        )
    
    # Create user in Firestore
    now = datetime.utcnow()
    new_user_doc = User(
        id=firebase_user.uid,
        email=user.email,
        username=user.username,
        role=user.role,
        created_at=now,
        updated_at=now,
        is_active=True,
        is_deleted=False,
        deleted_at=None
    )
    
    try:
        await create_user_in_firestore(new_user_doc)
    except Exception as e:
        print(f"Error creating user in Firestore: {e}")
        firebase_service.delete_firebase_user(firebase_user.uid)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user profile in Firestore"
        )

    # Return the created user
    return new_user_doc


@router.post("/login")
async def login(id_token: str = Body(..., embed=True)): # Accept id_token from request body
    # Verify the Firebase ID token
    decoded_token = firebase_service.verify_token(id_token)
    if not decoded_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase ID token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    uid = decoded_token.get("uid")
    email = decoded_token.get("email")

    # Get user role from Firestore
    user_from_firestore = await get_user_from_firestore(uid)
    if not user_from_firestore or user_from_firestore.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account is disabled/deleted",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Log the login activity
    await log_activity(
        user_id=uid,
        action="User Login",
        details={"email": email}
    )

    # Return a success message or relevant user info. The Firebase ID token itself
    # will be used by the frontend for subsequent authenticated requests.
    return {
        "message": "Login successful",
        "uid": uid,
        "email": email,
        "role": user_from_firestore.role
    }





@router.post("/logout")
async def logout(token: str = Depends(security)):
    # In a real implementation with token blacklisting, you would add the token to a blacklist.
    # For this simplified version, we just return a success message.
    # The frontend is responsible for clearing the token.
    payload = verify_token(token)
    if payload:
        log_activity(
            user_id=payload.get("sub"),
            action="User Logout",
            details={"email": payload.get("email")}
        )
    return {"message": "Successfully logged out"}
