from google.cloud.firestore_v1.base_query import FieldFilter

from app.services.firebase_service import firebase_service
from app.models.notification import Notification, NotificationCreate
from datetime import datetime
import uuid

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
        is_read=False
    )
    db.collection('notifications').document(notification_id).set(notification.model_dump())
    return notification

def get_notifications_for_user(user_id: str, limit: int = 100):
    """
    Retrieves all notifications for a specific user, ordered by creation date.
    """
    notifications_ref = firebase_service.db.collection('notifications').where(filter=FieldFilter("user_id", "==", user_id)).order_by("created_at", direction="DESCENDING").limit(limit)
    notifications = []
    for doc in notifications_ref.stream():
        notifications.append(Notification(**doc.to_dict()))
    return notifications

def mark_notification_as_read(notification_id: str, user_id: str):
    """
    Marks a specific notification as read.
    Ensures that a user can only mark their own notifications as read.
    """
    notification_ref = firebase_service.db.collection('notifications').document(notification_id)
    notification_doc = notification_ref.get()

    if not notification_doc.exists:
        return None  # Or raise HTTPException(404)

    notification = Notification(**notification_doc.to_dict())

    if notification.user_id != user_id:
        return None # Or raise HTTPException(403)

    notification_ref.update({"is_read": True, "updated_at": datetime.utcnow()})
    updated_doc = notification_ref.get()
    return Notification(**updated_doc.to_dict())
