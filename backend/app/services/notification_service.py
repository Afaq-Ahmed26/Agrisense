from typing import Optional, List
from google.cloud.firestore_v1.base_query import FieldFilter

from app.services.firebase_service import firebase_service
from app.models.notification import Notification, NotificationCreate
from datetime import datetime
import uuid

db = firebase_service.db # Using the Firestore client from firebase_service

def create_notification(notification_data: NotificationCreate, user_id: str):
    """
    Creates a new notification in Firestore.
    """
    notification_id = str(uuid.uuid4())
    notification = Notification(
        id=notification_id,
        user_id=user_id,
        message=notification_data.message,
        type=notification_data.type,
        created_at=datetime.utcnow(),
        is_read=False,
        is_archived=False # Default to not archived
    )
    db.collection('notifications').document(notification_id).set(notification.model_dump())
    return notification

def get_notifications_for_user(
    user_id: str,
    limit: int = 100,
    skip: int = 0,
    is_archived: Optional[bool] = False
) -> List[Notification]:
    """
    Retrieves notifications for a specific user, with optional archiving filter, ordered by creation date.
    """
    query = db.collection('notifications').where(filter=FieldFilter("user_id", "==", user_id))

    if is_archived is not None:
        query = query.where(filter=FieldFilter("is_archived", "==", is_archived))
    
    query = query.order_by("created_at", direction="DESCENDING")
    
    # Apply skip and limit for pagination
    query = query.offset(skip).limit(limit)

    notifications = []
    for doc in query.stream():
        try:
            notifications.append(Notification(**doc.to_dict()))
        except Exception as e:
            print(f"Error parsing notification {doc.id}: {e}")
            continue
    return notifications


def mark_notification_as_read(notification_id: str, user_id: str) -> Optional[Notification]:
    """
    Marks a specific notification as read.
    Ensures that a user can only mark their own notifications as read.
    """
    notification_ref = db.collection('notifications').document(notification_id)
    notification_doc = notification_ref.get()

    if not notification_doc.exists:
        return None

    notification = Notification(**notification_doc.to_dict())

    if notification.user_id != user_id:
        return None

    notification_ref.update({"is_read": True, "updated_at": datetime.utcnow()})
    updated_doc = notification_ref.get()
    return Notification(**updated_doc.to_dict())

def archive_notification(notification_id: str, user_id: str) -> Optional[Notification]:
    """
    Archives a specific notification.
    Ensures that a user can only archive their own notifications.
    """
    notification_ref = db.collection('notifications').document(notification_id)
    notification_doc = notification_ref.get()

    if not notification_doc.exists:
        return None

    notification = Notification(**notification_doc.to_dict())

    if notification.user_id != user_id:
        return None

    notification_ref.update({"is_archived": True, "updated_at": datetime.utcnow()})
    updated_doc = notification_ref.get()
    return Notification(**updated_doc.to_dict())


def unarchive_notification(notification_id: str, user_id: str) -> Optional[Notification]:
    """
    Unarchives a specific notification.
    Ensures that a user can only unarchive their own notifications.
    """
    notification_ref = db.collection('notifications').document(notification_id)
    notification_doc = notification_ref.get()

    if not notification_doc.exists:
        return None

    notification = Notification(**notification_doc.to_dict())

    if notification.user_id != user_id:
        return None

    notification_ref.update({"is_archived": False, "updated_at": datetime.utcnow()})
    updated_doc = notification_ref.get()
    return Notification(**updated_doc.to_dict())
