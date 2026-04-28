from datetime import datetime
from typing import List, Optional

from app.services.postgres_service import postgres_service


class AlertRepository:
    def is_enabled(self) -> bool:
        return postgres_service.enabled

    def upsert(self, alert: dict) -> None:
        postgres_service.execute(
            """
            INSERT INTO alerts (
                id, device_id, alert_type, severity, message, timestamp, status,
                acknowledged_by, acknowledged_at, resolved_by, resolved_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                severity = EXCLUDED.severity,
                message = EXCLUDED.message,
                timestamp = EXCLUDED.timestamp,
                status = EXCLUDED.status,
                acknowledged_by = EXCLUDED.acknowledged_by,
                acknowledged_at = EXCLUDED.acknowledged_at,
                resolved_by = EXCLUDED.resolved_by,
                resolved_at = EXCLUDED.resolved_at;
            """,
            (
                alert["id"],
                alert["device_id"],
                alert["alert_type"],
                alert["severity"],
                alert["message"],
                alert["timestamp"],
                alert["status"],
                alert.get("acknowledged_by"),
                alert.get("acknowledged_at"),
                alert.get("resolved_by"),
                alert.get("resolved_at"),
            ),
        )

    def get_by_device(self, device_id: str, status: Optional[str] = None, limit: int = 50) -> List[dict]:
        if status:
            rows = postgres_service.execute(
                """
                SELECT *
                FROM alerts
                WHERE device_id = %s AND status = %s
                ORDER BY timestamp DESC
                LIMIT %s;
                """,
                (device_id, status, limit),
                fetchall=True,
            ) or []
        else:
            rows = postgres_service.execute(
                """
                SELECT *
                FROM alerts
                WHERE device_id = %s
                ORDER BY timestamp DESC
                LIMIT %s;
                """,
                (device_id, limit),
                fetchall=True,
            ) or []
        return [dict(row) for row in rows]

    def get_open(self, limit: int = 50) -> List[dict]:
        rows = postgres_service.execute(
            """
            SELECT *
            FROM alerts
            WHERE status = %s
            ORDER BY timestamp DESC
            LIMIT %s;
            """,
            ("open", limit),
            fetchall=True,
        ) or []
        return [dict(row) for row in rows]

    def resolve_latest_open_by_type(self, device_id: str, alert_type: str) -> None:
        postgres_service.execute(
            """
            UPDATE alerts
            SET status = %s,
                resolved_at = %s
            WHERE id = (
                SELECT id
                FROM alerts
                WHERE device_id = %s
                  AND alert_type = %s
                  AND status = %s
                ORDER BY timestamp DESC
                LIMIT 1
            );
            """,
            (
                "resolved",
                datetime.utcnow(),
                device_id,
                alert_type,
                "open",
            ),
        )

    def acknowledge(self, alert_id: str, user_id: str) -> None:
        postgres_service.execute(
            """
            UPDATE alerts
            SET status = %s, acknowledged_by = %s, acknowledged_at = %s
            WHERE id = %s;
            """,
            ("acknowledged", user_id, datetime.utcnow(), alert_id),
        )

    def resolve(self, alert_id: str, user_id: str) -> None:
        postgres_service.execute(
            """
            UPDATE alerts
            SET status = %s, resolved_by = %s, resolved_at = %s
            WHERE id = %s;
            """,
            ("resolved", user_id, datetime.utcnow(), alert_id),
        )


alert_repository = AlertRepository()
