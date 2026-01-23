from fastapi import APIRouter, Depends, HTTPException, status
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
async def get_current_user(token: str = Depends(security)):
    # Get the current authenticated user's information
    # This would typically decode the JWT and fetch user details from Firestore
    raise HTTPException(status_code=404, detail="Get current user not implemented yet")