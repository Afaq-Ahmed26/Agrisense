from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import HTTPBearer
from typing import Optional
from datetime import timedelta, datetime, timezone
import asyncio
from app.models.user import UserCreate, User
from app.services.auth_service import get_password_hash, verify_token
from app.services.firebase_service import firebase_service
from app.services.user_service import create_user, get_user, update_user
from app.services.activity_log_service import log_activity
from app.utils.validators import EmailValidator, PasswordValidator
from app.config import settings
from app.middleware.auth import JWTBearer


router = APIRouter()
security = JWTBearer()


@router.post("/register", response_model=User)
async def register(user: UserCreate):
    print(f"DEBUG: Register endpoint - Received user data for {user.email}")
    
    # 1. Check if email already exists in PostgreSQL
    from app.repositories.user_repository import user_repository
    db_user_by_email = await asyncio.to_thread(user_repository.get_by_email, user.email, True)
    
    # 2. Check if user already exists in Firebase Auth
    existing_firebase_user = firebase_service.get_user_by_email(user.email)
    
    if existing_firebase_user:
        # Check if the user exists in PostgreSQL and is not soft-deleted
        db_user = await get_user(existing_firebase_user.uid, include_deleted=True)
        if db_user and not db_user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered and active"
            )
        elif db_user and db_user.is_deleted:
            # User exists but is soft-deleted, allow re-registration
            fb_user_details = firebase_service.get_user_by_uid(existing_firebase_user.uid)
            if fb_user_details and fb_user_details.disabled:
                firebase_service.enable_firebase_user(existing_firebase_user.uid)
            
            # Update existing PostgreSQL user and mark as not deleted
            await update_user(existing_firebase_user.uid, {"is_deleted": False, "deleted_at": None})
            
            # Update display name if provided
            if user.username:
                firebase_service.update_firebase_user(existing_firebase_user.uid, display_name=user.username)
            
            reactivated_user = await get_user(existing_firebase_user.uid)
            if reactivated_user:
                return reactivated_user
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to reactivate user profile after re-registration."
                )

    # If user doesn't exist in Firebase but exists in PostgreSQL
    if db_user_by_email:
        if not db_user_by_email.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists in the database. Please try logging in or reset your password."
            )
        else:
            # If it's a deleted user in DB but NOT in Firebase, this is a weird state.
            # We'll allow Firebase creation but update the existing DB profile later.
            print(f"DEBUG: Email {user.email} exists as deleted in DB but not in Firebase. Proceeding with Firebase creation.")
    
    # Create user in Firebase Auth
    try:
        firebase_user = firebase_service.create_firebase_user(
            email=user.email,
            password=user.password,
            display_name=user.username
        )
    except Exception as e:
        if "EMAIL_EXISTS" in str(e) or "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists"
            )
        print(f"ERROR: Failed to create user in Firebase Auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user in Firebase Authentication"
        )
    
    if not firebase_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user in Firebase Authentication"
        )
    
    # Create user in PostgreSQL
    now = datetime.now(timezone.utc)
    new_user = User(
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
        await create_user(new_user)
    except Exception as e:
        print(f"Error creating user in PostgreSQL: {e}")
        firebase_service.delete_firebase_user(firebase_user.uid)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user profile in database"
        )

    # Return the created user
    return new_user


@router.post("/login")
async def login(id_token: str = Body(..., embed=True)):
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
    username = decoded_token.get("name") or email.split("@")[0] # Fallback to email prefix

    # Get user from PostgreSQL
    user = await get_user(uid, include_deleted=True)
    if not user:
        print(f"DEBUG: login - user {email} not found in PostgreSQL. Creating profile...")
        now = datetime.now(timezone.utc)
        new_user = User(
            id=uid,
            email=email,
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
            user = new_user
        except Exception as e:
            print(f"ERROR: Failed to create JIT user profile during login: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize user profile"
            )
    
    # Check if user is deleted
    if user.is_deleted:
        if user.deleted_at:
            # Ensure deleted_at is aware for comparison
            d_at = user.deleted_at
            if d_at.tzinfo is None:
                d_at = d_at.replace(tzinfo=timezone.utc)
                
            recovery_deadline = d_at + timedelta(days=7)
            current_time = datetime.now(timezone.utc)
            
            if current_time < recovery_deadline:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Your account has been deleted. Contact an admin to restore it before {recovery_deadline.isoformat()}.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deleted and cannot be recovered",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Log the login activity
    await log_activity(
        user_id=uid,
        action="User Login",
        details={"email": email}
    )

    return {
        "message": "Login successful",
        "uid": uid,
        "email": email,
        "role": user.role
    }


@router.post("/logout")
async def logout(token: str = Depends(security)):
    payload = verify_token(token)
    if payload:
        await log_activity(
            user_id=payload.get("uid"),
            action="User Logout",
            details={"email": payload.get("email")}
        )
    return {"message": "Successfully logged out"}
