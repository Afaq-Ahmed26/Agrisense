from datetime import datetime
from typing import Optional

from app.services.postgres_service import postgres_service


class DeviceOtpRepository:
    def is_enabled(self) -> bool:
        return postgres_service.enabled

    def upsert(self, otp_doc_id: str, payload: dict) -> None:
        postgres_service.execute(
            """
            INSERT INTO device_otps (
                id, device_id, user_id, email, otp_hash, expires_at, attempts, blocked, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                device_id = EXCLUDED.device_id,
                user_id = EXCLUDED.user_id,
                email = EXCLUDED.email,
                otp_hash = EXCLUDED.otp_hash,
                expires_at = EXCLUDED.expires_at,
                attempts = EXCLUDED.attempts,
                blocked = EXCLUDED.blocked,
                created_at = EXCLUDED.created_at,
                updated_at = EXCLUDED.updated_at;
            """,
            (
                otp_doc_id,
                payload["device_id"],
                payload["user_id"],
                payload["email"],
                payload["otp_hash"],
                payload["expires_at"],
                payload.get("attempts", 0),
                payload.get("blocked", False),
                payload["created_at"],
                payload["updated_at"],
            ),
        )

    def get(self, otp_doc_id: str) -> Optional[dict]:
        row = postgres_service.execute(
            """
            SELECT id, device_id, user_id, email, otp_hash, expires_at, attempts, blocked, created_at, updated_at
            FROM device_otps
            WHERE id = %s
            LIMIT 1;
            """,
            (otp_doc_id,),
            fetchone=True,
        )
        return dict(row) if row else None

    def update_attempts(self, otp_doc_id: str, attempts: int, blocked: bool) -> None:
        postgres_service.execute(
            """
            UPDATE device_otps
            SET attempts = %s, blocked = %s, updated_at = %s
            WHERE id = %s;
            """,
            (attempts, blocked, datetime.utcnow(), otp_doc_id),
        )

    def delete(self, otp_doc_id: str) -> None:
        postgres_service.execute(
            "DELETE FROM device_otps WHERE id = %s;",
            (otp_doc_id,),
        )


device_otp_repository = DeviceOtpRepository()

