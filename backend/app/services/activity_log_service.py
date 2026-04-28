import asyncio
from datetime import datetime
from typing import Optional, Dict, List
import uuid

from app.services.firebase_service import firebase_service
from app.models.activity_log import ActivityLog
from app.repositories.activity_log_repository import activity_log_repository


async def log_activity(user_id: str, action: str, details: Optional[Dict] = None):
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
    if activity_log_repository.is_enabled():
        await asyncio.to_thread(activity_log_repository.create, log_entry)
        return

    doc_ref = firebase_service.db.collection('activity_logs').document(log_entry.id)
    await asyncio.to_thread(doc_ref.set, log_entry.model_dump())
    print(f"Activity Logged: User {user_id}, Action: {action}, Details: {details}")

async def get_activity_logs(
    limit: int = 100, 
    skip: int = 0, 
    user_id: Optional[str] = None, 
    action: Optional[str] = None
) -> List[ActivityLog]:
    """
    Retrieves activity logs from Firestore with optional filtering and pagination.
    NOTE: Firestore requires composite indexes for queries that filter on multiple 
          fields and order by another. You may need to create indexes for combinations
          of (user_id, timestamp) and (action, timestamp).
    """
    if activity_log_repository.is_enabled():
        return await asyncio.to_thread(
            activity_log_repository.list,
            limit,
            skip,
            user_id,
            action,
        )

    query = firebase_service.db.collection('activity_logs')

    # Apply filters
    if user_id:
        query = query.where('user_id', '==', user_id)
    if action:
        query = query.where('action', '==', action)

    # Apply ordering and pagination
    query = query.order_by('timestamp', direction='DESCENDING').offset(skip).limit(limit)
    
    docs = await asyncio.to_thread(lambda: query.get())
    
    logs = []
    for doc in docs:
        try:
            log_data = doc.to_dict()
            log_data['id'] = doc.id
            logs.append(ActivityLog(**log_data))
        except Exception as e:
            print(f"Error parsing activity log {doc.id}: {e}")
            continue
    return logs
