from fastapi import APIRouter, Depends, HTTPException, status, Body # Import Body
from fastapi.security import HTTPBearer
from typing import Optional
from datetime import timedelta, datetime
from app.models.user import UserCreate, User
from app.services.auth_service import create_access_token, get_password_hash, verify_token
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
    print(f"DEBUG: Register endpoint - Received user data: {user.model_dump_json()}")

    # Validate email format
    try:
        EmailValidator(email=user.email)
    except ValueError:
        print(f"DEBUG: Register endpoint - Invalid email format for {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Validate password strength
    try:
        PasswordValidator(password=user.password)
    except ValueError as e:
        print(f"DEBUG: Register endpoint - Invalid password for {user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Check if user already exists in Firebase (Auth and Firestore)
    existing_firebase_user = firebase_service.get_user_by_email(user.email)
    if existing_firebase_user:
        # Check if the user exists in Firestore and is not soft-deleted
        firestore_user = get_user_from_firestore(existing_firebase_user.uid, include_deleted=True) # Corrected function call
        if firestore_user and not firestore_user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered and active"
            )
        elif firestore_user and firestore_user.is_deleted:
            # User exists but is soft-deleted, allow re-registration
            # Potentially re-enable the Firebase Auth user if disabled
            # This needs a new function in firebase_service.py: enable_firebase_user
            # For now, we'll assume the user will be re-enabled if they re-register.
            # If firebase_user is disabled, enable it
            fb_user_details = firebase_service.get_user_by_uid(existing_firebase_user.uid)
            if fb_user_details and fb_user_details.disabled:
                firebase_service.enable_firebase_user(existing_firebase_user.uid)
            
            # Update existing firestore user and mark as not deleted
            # This logic will be handled when we implement update user endpoint,
            # but for re-registration, we want to immediately reactivate in Firestore.
            from app.services.user_service import update_user_in_firestore
            update_user_in_firestore(existing_firebase_user.uid, {"is_deleted": False, "deleted_at": None})
            
            # After reactivating, we should update their display name if provided and return them
            if user.username:
                firebase_service.update_firebase_user(existing_firebase_user.uid, display_name=user.username)
            
            reactivated_user = get_user_from_firestore(existing_firebase_user.uid)
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Changed to 500 as Firebase user creation failed
            detail="Failed to create user in Firebase Authentication"
        )
    
    # Create user in Firestore
    now = datetime.utcnow()
    new_user_doc = User(
        id=firebase_user.uid,
        email=user.email,
        username=user.username,
        role=user.role, # Use role from request
        created_at=now,
        updated_at=now,
        is_deleted=False,
        deleted_at=None
    )
    
    try:
        create_user_in_firestore(new_user_doc)
    except Exception as e:
        # If Firestore creation fails, consider rolling back Firebase Auth user creation
        # For simplicity, we'll just log and raise an error for now
        print(f"Error creating user in Firestore: {e}")
        # Optionally, delete the Firebase Auth user if Firestore creation fails
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
    user_from_firestore = get_user_from_firestore(uid)
    if not user_from_firestore or user_from_firestore.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account is disabled/deleted",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Log the login activity
    log_activity(
        user_id=uid,
        action="User Login",
        details={"email": email}
    )

    # Create our own access token containing relevant user info including role
    token_data = {
        "sub": uid, # Use UID as subject
        "email": email,
        "role": user_from_firestore.role, # Use role from Firestore
        "exp": (datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh")
async def refresh_token(token: str = Depends(security)):
    # Verify the current token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create a new token with extended expiry
    new_token_data = {
        "sub": payload.get("sub"),
        "role": payload.get("role", "farmer"),
        "exp": (datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()
    }
    
    new_access_token = create_access_token(data=new_token_data)
    
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(token: str = Depends(security)):
    # In a real implementation with token blacklisting, you would add the token to a blacklist.
    # For this simplified version, we just return a success message.
    # The frontend is responsible for clearing the token.
    return {"message": "Successfully logged out"}