from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from app.models.activity_log import ActivityLog
from app.models.notification import Notification
from app.models.sensor import Device, SensorReading
from app.models.thresholds import AlertThresholds
from app.models.user import User
from app.repositories.activity_log_repository import activity_log_repository
from app.repositories.alert_repository import alert_repository
from app.repositories.device_otp_repository import device_otp_repository
from app.repositories.device_repository import device_repository
from app.repositories.notification_repository import notification_repository
from app.repositories.threshold_repository import threshold_repository
from app.repositories.user_repository import user_repository
from app.services.firebase_service import firebase_service
from app.services.postgres_service import postgres_service


def to_datetime(value: Any, default: Optional[datetime] = None) -> Optional[datetime]:
    if value is None:
        return default
    if isinstance(value, datetime):
        return value
    if hasattr(value, "to_datetime"):
        converted = value.to_datetime()
        if isinstance(converted, datetime):
            return converted
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return default
        normalized = raw.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return default
    return default


def to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return default


def iter_collection(name: str) -> Iterable[Any]:
    return firebase_service.db.collection(name).stream()


def migrate_users() -> tuple[int, int]:
    migrated = 0
    failed = 0
    now = datetime.now(timezone.utc)
    for doc in iter_collection("users"):
        try:
            data = doc.to_dict() or {}
            user = User(
                id=data.get("id") or doc.id,
                email=(data.get("email") or "").lower(),
                username=data.get("username") or data.get("email", "user"),
                role=data.get("role") or "farmer",
                full_name=data.get("full_name"),
                dashboard_preferences=data.get("dashboard_preferences") or [],
                assigned_device_ids=data.get("assigned_device_ids") or [],
                created_at=to_datetime(data.get("created_at"), now) or now,
                updated_at=to_datetime(data.get("updated_at"), now) or now,
                is_active=to_bool(data.get("is_active"), True),
                is_deleted=to_bool(data.get("is_deleted"), False),
                deleted_at=to_datetime(data.get("deleted_at")),
            )
            user_repository.create(user)
            migrated += 1
        except Exception as exc:
            failed += 1
            print(f"[users] failed doc={doc.id}: {exc}")
    return migrated, failed


def migrate_devices() -> tuple[int, int]:
    migrated = 0
    failed = 0
    now = datetime.now(timezone.utc)
    for doc in iter_collection("devices"):
        try:
            data = doc.to_dict() or {}
            device = Device(
                id=data.get("id") or doc.id,
                name=data.get("name") or f"Device {doc.id}",
                location=data.get("location") or "Unknown",
                owner_id=data.get("owner_id") or "unassigned",
                type=data.get("type") or "irrigation_device",
                zone_id=data.get("zone_id"),
                crop_type=data.get("crop_type"),
                area_size=data.get("area_size"),
                created_at=to_datetime(data.get("created_at"), now) or now,
                updated_at=to_datetime(data.get("updated_at"), now) or now,
                is_active=to_bool(data.get("is_active"), True),
            )
            device_repository.create(device)
            # Preserve pairing metadata directly.
            postgres_service.execute(
                """
                UPDATE devices
                SET pairing_code = %s,
                    pairing_code_generated_at = %s,
                    pairing_code_expires_at = %s,
                    pairing_code_generated_by = %s
                WHERE id = %s;
                """,
                (
                    data.get("pairing_code"),
                    to_datetime(data.get("pairing_code_generated_at")),
                    to_datetime(data.get("pairing_code_expires_at")),
                    data.get("pairing_code_generated_by"),
                    device.id,
                ),
            )
            migrated += 1
        except Exception as exc:
            failed += 1
            print(f"[devices] failed doc={doc.id}: {exc}")
    return migrated, failed


def migrate_alerts() -> tuple[int, int]:
    migrated = 0
    failed = 0
    now = datetime.now(timezone.utc)
    for doc in iter_collection("alerts"):
        try:
            data = doc.to_dict() or {}
            payload = {
                "id": data.get("id") or doc.id,
                "device_id": data.get("device_id"),
                "alert_type": data.get("alert_type") or "unusual_reading",
                "severity": data.get("severity") or "low",
                "message": data.get("message") or "",
                "timestamp": to_datetime(data.get("timestamp"), now) or now,
                "status": data.get("status") or "open",
                "acknowledged_by": data.get("acknowledged_by"),
                "acknowledged_at": to_datetime(data.get("acknowledged_at")),
                "resolved_by": data.get("resolved_by"),
                "resolved_at": to_datetime(data.get("resolved_at")),
            }
            if payload["device_id"]:
                alert_repository.upsert(payload)
                migrated += 1
            else:
                failed += 1
                print(f"[alerts] missing device_id doc={doc.id}")
        except Exception as exc:
            failed += 1
            print(f"[alerts] failed doc={doc.id}: {exc}")
    return migrated, failed


def migrate_thresholds() -> tuple[int, int]:
    try:
        doc = firebase_service.db.collection("system_settings").document("alert_thresholds").get()
        if not doc.exists:
            return 0, 0
        data = doc.to_dict() or {}
        thresholds = AlertThresholds(
            soil_moisture_low=float(data.get("soil_moisture_low", 30.0)),
            soil_moisture_critical=float(data.get("soil_moisture_critical", 20.0)),
            temperature_high=float(data.get("temperature_high", 40.0)),
            temperature_critical=float(data.get("temperature_critical", 45.0)),
            humidity_low=float(data.get("humidity_low", 20.0)),
            humidity_high=float(data.get("humidity_high", 85.0)),
        )
        threshold_repository.upsert_alert_thresholds(thresholds)
        return 1, 0
    except Exception as exc:
        print(f"[thresholds] failed: {exc}")
        return 0, 1


def migrate_activity_logs() -> tuple[int, int]:
    migrated = 0
    failed = 0
    now = datetime.now(timezone.utc)
    for doc in iter_collection("activity_logs"):
        try:
            data = doc.to_dict() or {}
            log = ActivityLog(
                id=data.get("id") or doc.id,
                timestamp=to_datetime(data.get("timestamp"), now) or now,
                user_id=data.get("user_id") or "unknown",
                action=data.get("action") or "unknown",
                details=data.get("details") if isinstance(data.get("details"), dict) else {},
            )
            activity_log_repository.create(log)
            migrated += 1
        except Exception as exc:
            failed += 1
            print(f"[activity_logs] failed doc={doc.id}: {exc}")
    return migrated, failed


def migrate_notifications() -> tuple[int, int]:
    migrated = 0
    failed = 0
    now = datetime.now(timezone.utc)
    for doc in iter_collection("notifications"):
        try:
            data = doc.to_dict() or {}
            notification = Notification(
                id=data.get("id") or doc.id,
                user_id=data.get("user_id") or "unknown",
                message=data.get("message") or "",
                type=data.get("type") or "info",
                created_at=to_datetime(data.get("created_at"), now) or now,
                is_read=to_bool(data.get("is_read"), False),
                is_archived=to_bool(data.get("is_archived"), False),
            )
            notification_repository.create(notification)
            migrated += 1
        except Exception as exc:
            failed += 1
            print(f"[notifications] failed doc={doc.id}: {exc}")
    return migrated, failed


def migrate_device_otps() -> tuple[int, int]:
    migrated = 0
    failed = 0
    now = datetime.now(timezone.utc)
    for doc in iter_collection("device_connect_otps"):
        try:
            data = doc.to_dict() or {}
            payload = {
                "device_id": data.get("device_id"),
                "user_id": data.get("user_id") or "unknown",
                "email": data.get("email") or "",
                "otp_hash": data.get("otp_hash") or "",
                "expires_at": to_datetime(data.get("expires_at"), now) or now,
                "attempts": int(data.get("attempts", 0) or 0),
                "blocked": to_bool(data.get("blocked"), False),
                "created_at": to_datetime(data.get("created_at"), now) or now,
                "updated_at": to_datetime(data.get("updated_at"), now) or now,
            }
            if payload["device_id"]:
                device_otp_repository.upsert(doc.id, payload)
                migrated += 1
            else:
                failed += 1
                print(f"[device_otps] missing device_id doc={doc.id}")
        except Exception as exc:
            failed += 1
            print(f"[device_otps] failed doc={doc.id}: {exc}")
    return migrated, failed


def migrate_sensor_readings() -> tuple[int, int]:
    migrated = 0
    failed = 0
    now = datetime.now(timezone.utc)
    for doc in iter_collection("sensor_readings"):
        try:
            data = doc.to_dict() or {}
            reading = SensorReading(
                id=data.get("id") or doc.id,
                device_id=data.get("device_id"),
                soil_moisture=data.get("soil_moisture"),
                temperature=data.get("temperature"),
                humidity=data.get("humidity"),
                light_level=data.get("light_level"),
                timestamp=to_datetime(data.get("timestamp"), now) or now,
            )
            postgres_service.save_sensor_reading(reading.model_dump())
            migrated += 1
        except Exception as exc:
            failed += 1
            print(f"[sensor_readings] failed doc={doc.id}: {exc}")
    return migrated, failed


def migrate_irrigation_events() -> tuple[int, int]:
    migrated = 0
    failed = 0
    now = datetime.now(timezone.utc)
    for doc in iter_collection("irrigation_events"):
        try:
            data = doc.to_dict() or {}
            payload = {
                "id": data.get("id") or doc.id,
                "device_id": data.get("device_id"),
                "start_time": to_datetime(data.get("start_time"), now) or now,
                "end_time": to_datetime(data.get("end_time")),
                "duration_actual_seconds": data.get("duration_actual_seconds")
                or (int(data.get("duration_actual_minutes", 0) * 60) if data.get("duration_actual_minutes") is not None else None),
                "status": data.get("status") or "pending",
                "temperature": data.get("temperature"),
                "humidity": data.get("humidity"),
                "soil_moisture": data.get("soil_moisture"),
                "light_level": data.get("light_level"),
                "user_triggered": to_bool(data.get("user_triggered"), False),
                "created_at": to_datetime(data.get("created_at"), now) or now,
            }
            if payload["device_id"]:
                postgres_service.save_irrigation_event(payload)
                migrated += 1
            else:
                failed += 1
                print(f"[irrigation_events] missing device_id doc={doc.id}")
        except Exception as exc:
            failed += 1
            print(f"[irrigation_events] failed doc={doc.id}: {exc}")
    return migrated, failed


def migrate_control_states() -> tuple[int, int]:
    migrated = 0
    failed = 0
    for doc in iter_collection("irrigation_control"):
        try:
            data = doc.to_dict() or {}
            device_id = data.get("device_id")
            if not device_id:
                raw_id = doc.id
                if raw_id.startswith("control_state_"):
                    device_id = raw_id[len("control_state_") :]
            if not device_id:
                failed += 1
                print(f"[irrigation_control] missing device_id doc={doc.id}")
                continue
            postgres_service.upsert_control_state(
                {
                    "device_id": device_id,
                    "mode": data.get("mode", "AUTO"),
                    "pump_state": to_bool(data.get("pump_state"), False),
                    "threshold": float(data.get("threshold", 30.0)),
                    "last_change_time": to_datetime(data.get("last_change_time")),
                }
            )
            migrated += 1
        except Exception as exc:
            failed += 1
            print(f"[irrigation_control] failed doc={doc.id}: {exc}")
    return migrated, failed


def main() -> None:
    if not postgres_service.enabled:
        raise SystemExit("PostgreSQL is not enabled. Set DATABASE_URL first.")

    tasks = [
        ("users", migrate_users),
        ("devices", migrate_devices),
        ("alerts", migrate_alerts),
        ("thresholds", migrate_thresholds),
        ("activity_logs", migrate_activity_logs),
        ("notifications", migrate_notifications),
        ("device_otps", migrate_device_otps),
        ("sensor_readings", migrate_sensor_readings),
        ("irrigation_events", migrate_irrigation_events),
        ("irrigation_control", migrate_control_states),
    ]

    print("Starting Firestore -> PostgreSQL migration...")
    summary: Dict[str, Dict[str, int]] = {}
    for name, fn in tasks:
        migrated, failed = fn()
        summary[name] = {"migrated": migrated, "failed": failed}
        print(f"{name}: migrated={migrated}, failed={failed}")

    print("\nMigration summary:")
    for name, data in summary.items():
        print(f"- {name}: migrated={data['migrated']}, failed={data['failed']}")


if __name__ == "__main__":
    main()
