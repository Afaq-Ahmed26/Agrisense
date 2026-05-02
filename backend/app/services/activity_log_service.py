import asyncio
from datetime import datetime
from typing import Optional, Dict, List
import uuid
from app.models.activity_log import ActivityLog
from app.repositories.activity_log_repository import activity_log_repository


async def log_activity(user_id: str, action: str, details: Optional[Dict] = None):
    """
    Logs an activity to the PostgreSQL activity_logs table.
    """
    log_entry = ActivityLog(
        id=str(uuid.uuid4()),
        timestamp=datetime.utcnow(),
        user_id=user_id,
        action=action,
        details=details
    )
    await asyncio.to_thread(activity_log_repository.create, log_entry)
    print(f"Activity Logged to PostgreSQL: User {user_id}, Action: {action}")

async def get_activity_logs(
    limit: int = 100, 
    skip: int = 0, 
    user_id: Optional[str] = None, 
    action: Optional[str] = None
) -> List[ActivityLog]:
    """
    Retrieves activity logs from PostgreSQL with optional filtering and pagination.
    """
    return await asyncio.to_thread(
        activity_log_repository.list,
        limit,
        skip,
        user_id,
        action,
    )
