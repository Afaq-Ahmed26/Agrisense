from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List
from app.middleware.auth import JWTBearer
from app.models.notification import Notification, NotificationUpdate
from app.services import notification_service

router = APIRouter()
security = JWTBearer()

@router.get("/", response_model=List[Notification])
async def get_my_notifications(request: Request, token: str = Depends(security)):
    """
    Get all notifications for the currently authenticated user.
    """
    user_payload = request.state.user
    user_id = user_payload.get("uid")
    
    if not user_id:
        raise HTTPException(status_code=403, detail="Could not validate user credentials.")
        
    notifications = notification_service.get_notifications_for_user(user_id)
    return notifications

@router.post("/{notification_id}/read", response_model=Notification)
async def mark_as_read(notification_id: str, request: Request, token: str = Depends(security)):
    """
    Mark a notification as read.
    """
    user_payload = request.state.user
    user_id = user_payload.get("uid")

    if not user_id:
        raise HTTPException(status_code=403, detail="Could not validate user credentials.")

    updated_notification = notification_service.mark_notification_as_read(notification_id, user_id)

    if not updated_notification:
        raise HTTPException(status_code=404, detail="Notification not found or you do not have permission to modify it.")
        
    return updated_notification
