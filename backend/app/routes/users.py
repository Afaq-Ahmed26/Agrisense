from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
from app.middleware.auth import JWTBearer
from app.models.user import User, UserUpdate
from app.services.firebase_service import firebase_service


router = APIRouter()
security = JWTBearer()


@router.get("/", response_model=List[User])
async def get_users(skip: int = 0, limit: int = 100, token: str = Depends(security)):
    # In a real implementation, this would fetch users from Firestore
    # For now, returning empty list as placeholder
    return []


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str, token: str = Depends(security)):
    # In a real implementation, this would fetch a specific user from Firestore
    # For now, returning placeholder as example
    raise HTTPException(status_code=404, detail="User not implemented yet")


@router.put("/{user_id}", response_model=User)
async def update_user(user_id: str, user_update: UserUpdate, token: str = Depends(security)):
    # Verify that the requesting user has permission to update this user
    # In a real implementation, this would update user data in Firestore
    raise HTTPException(status_code=404, detail="User update not implemented yet")


@router.delete("/{user_id}")
async def delete_user(user_id: str, token: str = Depends(security)):
    # In a real implementation, this would delete a user from Firestore and Firebase Auth
    raise HTTPException(status_code=404, detail="User deletion not implemented yet")


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