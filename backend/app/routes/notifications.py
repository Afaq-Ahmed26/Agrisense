from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List, Optional
from app.middleware.auth import JWTBearer
from app.models.notification import Notification, NotificationUpdate
from app.services import notification_service

router = APIRouter()
security = JWTBearer()

@router.get("/", response_model=List[Notification])
async def get_my_notifications(
    request: Request,
    token: str = Depends(security),
    is_archived: Optional[bool] = False,
    skip: int = 0,
    limit: int = 100
):
    """
    Get all notifications for the currently authenticated user, with optional archiving filter and pagination.
    """
    user_payload = request.state.user
    user_id = user_payload.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=403, detail="Could not validate user credentials.")
        
    notifications = await notification_service.get_notifications_for_user(
        user_id,
        limit=limit,
        skip=skip,
        is_archived=is_archived
    )
    return notifications

@router.patch("/{notification_id}/read", response_model=Notification)
async def mark_as_read(notification_id: str, request: Request, token: str = Depends(security)):
    """
    Mark a notification as read.
    """
    user_payload = request.state.user
    user_id = user_payload.get("user_id")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate user credentials.")

    updated_notification = await notification_service.mark_notification_as_read(notification_id, user_id)

    if not updated_notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found or you do not have permission to modify it.")
        
    return updated_notification

@router.patch("/{notification_id}/archive", response_model=Notification)
async def archive_notification_route(notification_id: str, request: Request, token: str = Depends(security)):
    """
    Archive a notification.
    """
    user_payload = request.state.user
    user_id = user_payload.get("user_id")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate user credentials.")
    
    archived_notification = await notification_service.archive_notification(notification_id, user_id)

    if not archived_notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found or you do not have permission to modify it.")
    
    return archived_notification

@router.patch("/{notification_id}/unarchive", response_model=Notification)
async def unarchive_notification_route(notification_id: str, request: Request, token: str = Depends(security)):
    """
    Unarchive a notification.
    """
    user_payload = request.state.user
    user_id = user_payload.get("user_id")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate user credentials.")
    
    unarchived_notification = await notification_service.unarchive_notification(notification_id, user_id)

    if not unarchived_notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found or you do not have permission to modify it.")
    
    return unarchived_notification
