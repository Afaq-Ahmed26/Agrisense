import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from app.services.postgres_service import postgres_service
from app.services.user_service import get_user
from app.services import notification_service
from app.models.notification import NotificationCreate


async def get_expired_deleted_users(days: int = 7) -> List[dict]:
    """
    Get all users whose deletion window has expired (beyond the recovery period) from PostgreSQL.
    """
    try:
        expiry_threshold = datetime.utcnow() - timedelta(days=days)
        
        rows = postgres_service.execute(
            "SELECT * FROM users WHERE is_deleted = TRUE AND deleted_at < %s;",
            (expiry_threshold,),
            fetchall=True
        ) or []
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"ERROR: Failed to get expired deleted users from PostgreSQL: {e}")
        return []


async def get_users_near_expiry(days: int = 7, warning_days: int = 1) -> List[dict]:
    """
    Get users whose deletion window is expiring soon from PostgreSQL.
    """
    try:
        expiry_threshold = datetime.utcnow() - timedelta(days=days - warning_days)
        final_threshold = datetime.utcnow() - timedelta(days=days)
        
        rows = postgres_service.execute(
            "SELECT * FROM users WHERE is_deleted = TRUE AND deleted_at >= %s AND deleted_at < %s;",
            (final_threshold, expiry_threshold),
            fetchall=True
        ) or []
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"ERROR: Failed to get users near expiry from PostgreSQL: {e}")
        return []


async def create_deletion_expiry_notification(admin_id: str, expired_user_ids: List[str]) -> bool:
    """
    Create a notification to admin about expired user deletions in PostgreSQL.
    """
    try:
        if not expired_user_ids:
            return False
        
        msg = f"{len(expired_user_ids)} deleted user(s) can now be permanently deleted. Their {7}-day recovery window has expired."
        notification_data = NotificationCreate(
            user_id=admin_id,
            message=msg,
            type="deletion_expiry"
        )
        
        await notification_service.create_notification(notification_data, admin_id)
        print(f"DEBUG: Created deletion expiry notification for admin {admin_id}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to create deletion expiry notification: {e}")
        return False


async def create_deletion_warning_notification(user_id: str, admin_ids: List[str]) -> bool:
    """
    Create notifications to admins warning about upcoming deletion expiry in PostgreSQL.
    """
    try:
        user = await get_user(user_id, include_deleted=True)
        if not user or not user.deleted_at:
            return False
        
        recovery_deadline = user.deleted_at + timedelta(days=7)
        msg = f"User {user.username} ({user.email}) deletion window expires on {recovery_deadline.isoformat()}."
        
        for admin_id in admin_ids:
            notification_data = NotificationCreate(
                user_id=admin_id,
                message=msg,
                type="deletion_expiry_warning"
            )
            await notification_service.create_notification(notification_data, admin_id)
        
        print(f"DEBUG: Created deletion warning notifications for {len(admin_ids)} admins")
        return True
    except Exception as e:
        print(f"ERROR: Failed to create deletion warning notification: {e}")
        return False


async def get_all_admins() -> List[str]:
    """
    Get all active admin user IDs from PostgreSQL.
    """
    try:
        rows = postgres_service.execute(
            "SELECT id FROM users WHERE role = 'admin' AND is_deleted = FALSE;",
            fetchall=True
        ) or []
        return [row["id"] for row in rows]
    except Exception as e:
        print(f"ERROR: Failed to get all admins from PostgreSQL: {e}")
        return []


async def cleanup_expired_users(permanently_delete: bool = False) -> dict:
    """
    Process expired user deletions.
    """
    try:
        from app.services.firebase_service import firebase_service as fb_service
        
        expired_users = await get_expired_deleted_users(days=7)
        admin_ids = await get_all_admins()
        
        result = {
            "expired_count": len(expired_users),
            "deleted_count": 0,
            "notification_sent": False
        }
        
        if expired_users:
            expired_user_ids = [user['id'] for user in expired_users]
            
            if admin_ids:
                result["notification_sent"] = await create_deletion_expiry_notification(
                    admin_ids[0],
                    expired_user_ids
                )
            
            if permanently_delete:
                for user_id in expired_user_ids:
                    try:
                        await asyncio.to_thread(fb_service.delete_firebase_user, user_id)
                        # Also delete from PostgreSQL for complete removal if permanently deleting
                        postgres_service.execute("DELETE FROM users WHERE id = %s;", (user_id,))
                        result["deleted_count"] += 1
                    except Exception as e:
                        print(f"WARNING: Failed to permanently delete user {user_id}: {e}")
        
        return result
    except Exception as e:
        print(f"ERROR: Failed to cleanup expired users: {e}")
        return {"expired_count": 0, "deleted_count": 0, "notification_sent": False, "error": str(e)}
