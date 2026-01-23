from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional
from datetime import timedelta, datetime
from app.models.user import UserCreate, User
from app.services.auth_service import create_access_token, get_password_hash, verify_token
from app.services.firebase_service import firebase_service
from app.utils.validators import EmailValidator, PasswordValidator
from app.config import settings
from app.middleware.auth import JWTBearer


router = APIRouter()
security = JWTBearer()


@router.post("/register", response_model=User)
async def register(user: UserCreate):
    # Validate email format
    try:
        EmailValidator(email=user.email)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Validate password strength
    try:
        PasswordValidator(password=user.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Check if user already exists in Firebase
    try:
        existing_user = firebase_service.get_user_by_email(user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    except Exception:
        # If there's an issue with Firebase, continue with local processing
        pass
    
    # Create user in Firebase
    firebase_user = firebase_service.create_firebase_user(
        email=user.email,
        password=user.password,
        display_name=user.username
    )
    
    if not firebase_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user"
        )
    
    # In a real implementation, we would store additional user data in Firestore
    # For now, we'll return a basic user representation
    return User(
        id=firebase_user.uid,
        email=user.email,
        username=user.username,
        role=user.role,
        created_at=firebase_user.user_metadata.creation_timestamp,
        updated_at=firebase_user.user_metadata.last_sign_in_timestamp or firebase_user.user_metadata.creation_timestamp
    )


@router.post("/login")
async def login(email: str, password: str):
    # In a real implementation, we would verify credentials with Firebase
    # For now, we'll simulate the process
    try:
        # This is a simplified version - in reality, you'd use Firebase Auth API
        # to verify the credentials and get a token
        token_data = {
            "sub": email,
            "role": "farmer",  # Would come from user data in a real implementation
            "exp": (datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()
        }
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Incorrect email or password: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


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