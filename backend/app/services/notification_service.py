import asyncio
from typing import Optional, List
from app.models.notification import Notification, NotificationCreate
from datetime import datetime
import uuid
from app.repositories.notification_repository import notification_repository

async def create_notification(notification_data: NotificationCreate, user_id: str):
    """
    Creates a new notification in PostgreSQL.
    """
    notification_id = str(uuid.uuid4())
    notification = Notification(
        id=notification_id,
        user_id=user_id,
        message=notification_data.message,
        type=notification_data.type,
        created_at=datetime.utcnow(),
        is_read=False,
        is_archived=False
    )
    await asyncio.to_thread(notification_repository.create, notification)
    return notification

async def get_notifications_for_user(
    user_id: str,
    limit: int = 100,
    skip: int = 0,
    is_archived: Optional[bool] = False
) -> List[Notification]:
    """
    Retrieves notifications for a specific user from PostgreSQL.
    """
    return await asyncio.to_thread(
        notification_repository.list_for_user,
        user_id,
        limit,
        skip,
        is_archived,
    )


async def mark_notification_as_read(notification_id: str, user_id: str) -> Optional[Notification]:
    """
    Marks a specific notification as read in PostgreSQL.
    """
    return await asyncio.to_thread(notification_repository.update_read_status, notification_id, user_id, True)

async def archive_notification(notification_id: str, user_id: str) -> Optional[Notification]:
    """
    Archives a specific notification in PostgreSQL.
    """
    return await asyncio.to_thread(notification_repository.update_archive_status, notification_id, user_id, True)


async def unarchive_notification(notification_id: str, user_id: str) -> Optional[Notification]:
    """
    Unarchives a specific notification in PostgreSQL.
    """
    return await asyncio.to_thread(notification_repository.update_archive_status, notification_id, user_id, False)
