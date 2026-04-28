import json
from typing import List, Optional

from app.models.activity_log import ActivityLog
from app.services.postgres_service import postgres_service


class ActivityLogRepository:
    def is_enabled(self) -> bool:
        return postgres_service.enabled

    def create(self, log: ActivityLog) -> ActivityLog:
        postgres_service.execute(
            """
            INSERT INTO activity_logs (id, timestamp, user_id, action, details)
            VALUES (%s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (id) DO NOTHING;
            """,
            (
                log.id,
                log.timestamp,
                log.user_id,
                log.action,
                json.dumps(log.details or {}),
            ),
        )
        return log

    def list(
        self,
        limit: int = 100,
        skip: int = 0,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
    ) -> List[ActivityLog]:
        where_parts = []
        params = []
        if user_id:
            where_parts.append("user_id = %s")
            params.append(user_id)
        if action:
            where_parts.append("action = %s")
            params.append(action)

        where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        params.extend([skip, limit])

        rows = postgres_service.execute(
            f"""
            SELECT id, timestamp, user_id, action, details
            FROM activity_logs
            {where_sql}
            ORDER BY timestamp DESC
            OFFSET %s
            LIMIT %s;
            """,
            tuple(params),
            fetchall=True,
        ) or []

        logs = []
        for row in rows:
            item = dict(row)
            details = item.get("details")
            if isinstance(details, str):
                details = json.loads(details)
            item["details"] = details
            logs.append(ActivityLog(**item))
        return logs


activity_log_repository = ActivityLogRepository()

