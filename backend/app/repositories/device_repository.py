from datetime import datetime
from typing import List, Optional

from app.models.sensor import Device
from app.services.postgres_service import postgres_service


class DeviceRepository:
    def is_enabled(self) -> bool:
        return postgres_service.enabled

    def create(self, device: Device) -> Device:
        postgres_service.execute(
            """
            INSERT INTO devices (
                id, name, location, owner_id, type, zone_id, crop_type, area_size,
                created_at, updated_at, is_active,
                pairing_code, pairing_code_generated_at, pairing_code_expires_at, pairing_code_generated_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                location = EXCLUDED.location,
                owner_id = EXCLUDED.owner_id,
                type = EXCLUDED.type,
                zone_id = EXCLUDED.zone_id,
                crop_type = EXCLUDED.crop_type,
                area_size = EXCLUDED.area_size,
                updated_at = EXCLUDED.updated_at,
                is_active = EXCLUDED.is_active,
                pairing_code = EXCLUDED.pairing_code,
                pairing_code_generated_at = EXCLUDED.pairing_code_generated_at,
                pairing_code_expires_at = EXCLUDED.pairing_code_expires_at,
                pairing_code_generated_by = EXCLUDED.pairing_code_generated_by;
            """,
            (
                device.id,
                device.name,
                device.location,
                device.owner_id,
                device.type,
                device.zone_id,
                device.crop_type,
                device.area_size,
                device.created_at,
                device.updated_at,
                device.is_active,
                None,
                None,
                None,
                None,
            ),
        )
        return device

    def get_by_id(self, device_id: str) -> Optional[Device]:
        row = postgres_service.execute(
            """
            SELECT id, name, location, owner_id, type, zone_id, crop_type, area_size,
                   created_at, updated_at, is_active
            FROM devices
            WHERE id = %s
            LIMIT 1;
            """,
            (device_id,),
            fetchone=True,
        )
        return Device(**dict(row)) if row else None

    def get_raw_by_id(self, device_id: str) -> Optional[dict]:
        row = postgres_service.execute(
            """
            SELECT *
            FROM devices
            WHERE id = %s
            LIMIT 1;
            """,
            (device_id,),
            fetchone=True,
        )
        return dict(row) if row else None

    def list(self, owner_id: Optional[str] = None) -> List[Device]:
        if owner_id:
            rows = postgres_service.execute(
                """
                SELECT id, name, location, owner_id, type, zone_id, crop_type, area_size,
                       created_at, updated_at, is_active
                FROM devices
                WHERE owner_id = %s
                ORDER BY created_at ASC;
                """,
                (owner_id,),
                fetchall=True,
            ) or []
        else:
            rows = postgres_service.execute(
                """
                SELECT id, name, location, owner_id, type, zone_id, crop_type, area_size,
                       created_at, updated_at, is_active
                FROM devices
                ORDER BY created_at ASC;
                """,
                fetchall=True,
            ) or []
        return [Device(**dict(row)) for row in rows]

    def assign_owner(self, device_id: str, owner_id: str) -> None:
        postgres_service.execute(
            """
            UPDATE devices
            SET owner_id = %s, updated_at = %s
            WHERE id = %s;
            """,
            (owner_id, datetime.utcnow(), device_id),
        )

    def save_pairing_code(self, device_id: str, pairing_code: str, generated_by: str, expires_at: datetime) -> None:
        postgres_service.execute(
            """
            UPDATE devices
            SET pairing_code = %s,
                pairing_code_generated_at = %s,
                pairing_code_expires_at = %s,
                pairing_code_generated_by = %s,
                updated_at = %s
            WHERE id = %s;
            """,
            (pairing_code, datetime.utcnow(), expires_at, generated_by, datetime.utcnow(), device_id),
        )

    def clear_pairing_code(self, device_id: str) -> None:
        postgres_service.execute(
            """
            UPDATE devices
            SET pairing_code = NULL,
                pairing_code_generated_at = NULL,
                pairing_code_expires_at = NULL,
                pairing_code_generated_by = NULL,
                updated_at = %s
            WHERE id = %s;
            """,
            (datetime.utcnow(), device_id),
        )


device_repository = DeviceRepository()
