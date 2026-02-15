from fastapi import Depends, HTTPException, status, Request
from typing import List
from app.services.user_service import get_user_from_firestore
from app.middleware.auth import JWTBearer

security = JWTBearer()

def require_roles(required_roles: List[str]):
    """
    Dependency that checks if the current user has one of the required roles.
    """
    async def role_checker(request: Request, token: str = Depends(security)):
        user_payload = request.state.user
        uid = user_payload.get("uid")

        if not uid:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials.")

        user = get_user_from_firestore(uid)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        if user.role not in required_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have the required permissions.")
            
        return user

    return role_checker
