from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
from app.middleware.auth import JWTBearer
from app.models.activity_log import ActivityLog
from app.services.activity_log_service import get_activity_logs
from app.services.user_service import get_user_from_firestore # To check user role


router = APIRouter()
security = JWTBearer()


@router.get("/", response_model=List[ActivityLog])
async def get_all_activity_logs(
    request: Request,
    token: str = Depends(security),
    limit: int = 100
):
    """
    Retrieve all activity logs (admin only).
    """
    user_payload = request.state.user
    acting_user_uid = user_payload.get('uid')

    acting_user = get_user_from_firestore(acting_user_uid)
    if not acting_user or acting_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view activity logs"
        )
        
    return get_activity_logs(limit=limit)