from datetime import datetime
from typing import Optional, Dict, List
import uuid

from app.services.firebase_service import firebase_service
from app.models.activity_log import ActivityLog


def log_activity(user_id: str, action: str, details: Optional[Dict] = None):
    """
    Logs an activity to the Firestore 'activity_logs' collection.
    """
    log_entry = ActivityLog(
        id=str(uuid.uuid4()),
        timestamp=datetime.utcnow(),
        user_id=user_id,
        action=action,
        details=details
    )
    firebase_service.db.collection('activity_logs').document(log_entry.id).set(log_entry.model_dump())
    print(f"Activity Logged: User {user_id}, Action: {action}, Details: {details}")

def get_activity_logs(limit: int = 100) -> List[ActivityLog]:
    """
    Retrieves activity logs from Firestore, ordered by timestamp descending.
    """
    logs_ref = firebase_service.db.collection('activity_logs').order_by('timestamp', direction='DESCENDING').limit(limit)
    logs = []
    for doc in logs_ref.stream():
        try:
            log_data = doc.to_dict()
            log_data['id'] = doc.id
            logs.append(ActivityLog(**log_data))
        except Exception as e:
            print(f"Error parsing activity log {doc.id}: {e}")
            continue
    return logs
