from datetime import datetime
from typing import List, Optional

from app.models.notification import Notification
from app.services.postgres_service import postgres_service


class NotificationRepository:
    def is_enabled(self) -> bool:
        return postgres_service.enabled

    def create(self, notification: Notification) -> Notification:
        postgres_service.execute(
            """
            INSERT INTO notifications (id, user_id, message, type, created_at, is_read, is_archived, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
            """,
            (
                notification.id,
                notification.user_id,
                notification.message,
                notification.type,
                notification.created_at,
                notification.is_read,
                notification.is_archived,
                datetime.utcnow(),
            ),
        )
        return notification

    def list_for_user(
        self,
        user_id: str,
        limit: int = 100,
        skip: int = 0,
        is_archived: Optional[bool] = False,
    ) -> List[Notification]:
        params = [user_id]
        where = ["user_id = %s"]
        if is_archived is not None:
            where.append("is_archived = %s")
            params.append(is_archived)
        params.extend([skip, min(limit, 50)])

        rows = postgres_service.execute(
            f"""
            SELECT id, user_id, message, type, created_at, is_read, is_archived
            FROM notifications
            WHERE {" AND ".join(where)}
            ORDER BY created_at DESC
            OFFSET %s
            LIMIT %s;
            """,
            tuple(params),
            fetchall=True,
        ) or []
        return [Notification(**dict(row)) for row in rows]

    def update_read_status(self, notification_id: str, user_id: str, is_read: bool) -> Optional[Notification]:
        row = postgres_service.execute(
            """
            UPDATE notifications
            SET is_read = %s, updated_at = %s
            WHERE id = %s AND user_id = %s
            RETURNING id, user_id, message, type, created_at, is_read, is_archived;
            """,
            (is_read, datetime.utcnow(), notification_id, user_id),
            fetchone=True,
        )
        return Notification(**dict(row)) if row else None

    def update_archive_status(self, notification_id: str, user_id: str, is_archived: bool) -> Optional[Notification]:
        row = postgres_service.execute(
            """
            UPDATE notifications
            SET is_archived = %s, updated_at = %s
            WHERE id = %s AND user_id = %s
            RETURNING id, user_id, message, type, created_at, is_read, is_archived;
            """,
            (is_archived, datetime.utcnow(), notification_id, user_id),
            fetchone=True,
        )
        return Notification(**dict(row)) if row else None


notification_repository = NotificationRepository()

