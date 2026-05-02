from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
import asyncio
import time
import secrets
import hashlib
from pydantic import BaseModel, Field
from app.middleware.auth import JWTBearer
from app.models.sensor import SensorReading, SensorReadingCreate, Device, DeviceCreate, DeviceUpdate, HourlyAverageReadings, DailySummaryReadings
from app.models.irrigation import IrrigationEventCreate, ControlState
from app.services.firebase_service import firebase_service
from app.services.alert_service import alert_service
from app.services.sensor_service import sensor_service
from app.services.irrigation_service import irrigation_service
from app.services.user_service import update_user, get_user
from app.services.activity_log_service import log_activity
from app.services.email_service import send_device_otp_email
from app.repositories.device_repository import device_repository
from app.repositories.user_repository import user_repository
from app.repositories.device_otp_repository import device_otp_repository
from app.repositories.threshold_repository import threshold_repository
from app.config import settings
from app.services.ml_service import ml_service
from app.utils.helpers import calculate_dew_point, calculate_heat_index
from app.dependencies import (
    get_current_user,
    ensure_device_access,
    get_assigned_device_ids,
    ASSIGNED_DEVICE_ROLES,
    normalize_role
)
from app.models.user import User


router = APIRouter()
security = JWTBearer()

# Debounce configuration: minimum seconds between state changes
DEBOUNCE_INTERVAL_SECONDS = 2
_last_state_change_time: Dict[str, float] = {}


class PairingCodeRequest(BaseModel):
    expires_minutes: int = Field(default=10, ge=1, le=60)


class PairingCodeResponse(BaseModel):
    device_id: str
    pairing_code: str
    expires_at: datetime


class DeviceClaimRequest(BaseModel):
    pairing_code: str = Field(min_length=4, max_length=32)


class DeviceConnectOtpRequest(BaseModel):
    pass


class DeviceConnectOtpVerifyRequest(BaseModel):
    otp: str = Field(min_length=4, max_length=12)


async def handle_auto_irrigation(device_id: str, soil_moisture: Optional[float], temperature: Optional[float] = None, humidity: Optional[float] = None, light_level: Optional[float] = None):
    """
    Real-time irrigation control based on ML prediction (AUTO) or user command (MANUAL).
    """
    try:
        control = await irrigation_service.get_control_state(device_id)

        if control.mode == "MANUAL":
            return

        if soil_moisture is None:
            return

        sensor_data = {
            'soil_moisture': soil_moisture,
            'temperature': temperature,
            'humidity': humidity,
            'light_level': light_level
        }
        
        ml_prediction_duration = 0
        ml_error = None
        ml_triggered_by_prediction = False
        
        if ml_service.model:
            prediction = await ml_service.predict_irrigation_need(sensor_data)
            ml_prediction_duration = prediction.get("predicted_valve_duration_s", 0)
            ml_error = prediction.get("error")
            
            if not ml_error and ml_prediction_duration > 0:
                ml_triggered_by_prediction = True

        threshold_low = 30.0
        threshold_critical = 20.0
        
        system_thresholds = await asyncio.to_thread(threshold_repository.get_alert_thresholds)
        if system_thresholds:
            threshold_low = getattr(system_thresholds, "soil_moisture_low", 30.0)
            threshold_critical = getattr(system_thresholds, "soil_moisture_critical", 20.0)
        
        ml_triggered = False
        threshold_triggered = False

        if ml_triggered_by_prediction and not ml_error and soil_moisture < threshold_low:
            ml_triggered = True

        if soil_moisture < threshold_critical:
            threshold_triggered = True

        if control.pump_state and soil_moisture >= 60.0:
            new_pump_state = False
        else:
            new_pump_state = ml_triggered or threshold_triggered
        
        now = time.time()
        last_change = _last_state_change_time.get(device_id, 0)
        if (now - last_change) < DEBOUNCE_INTERVAL_SECONDS:
            return

        if control.pump_state == new_pump_state:
            return

        control.pump_state = new_pump_state
        await irrigation_service.update_control_state(control)
        _last_state_change_time[device_id] = now

        state_str = "ON" if new_pump_state else "OFF"
        print(f"💧 [Auto Irrigation] Device {device_id}: Pump turned {state_str}")

    except Exception as e:
        print(f"❌ [Irrigation Control] Error for device {device_id}: {e}")


def _build_otp_doc_id(user_id: str, device_id: str) -> str:
    return f"{user_id}:{device_id}"


def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


async def _assign_device_to_user(current_user: User, device_id: str) -> None:
    now = datetime.utcnow()

    # Assign owner in PostgreSQL
    await asyncio.to_thread(device_repository.assign_owner, device_id, current_user.id)

    # Update claimant's device IDs in PostgreSQL
    claimant_assigned_device_ids = get_assigned_device_ids(current_user)
    claimant_assigned_device_ids.add(device_id)
    await update_user(
        current_user.id,
        {"assigned_device_ids": sorted(claimant_assigned_device_ids), "updated_at": now},
    )

    # Remove device ID from other users in PostgreSQL
    all_users = await asyncio.to_thread(user_repository.get_all, 0, 5000, True)
    for user in all_users:
        if user.id == current_user.id:
            continue
        existing_ids = [value for value in (user.assigned_device_ids or []) if isinstance(value, str)]
        if device_id in existing_ids:
            remaining_ids = [value for value in existing_ids if value != device_id]
            await update_user(
                user.id,
                {"assigned_device_ids": remaining_ids, "updated_at": now},
            )


@router.post("/", response_model=Device)
async def create_device(device: DeviceCreate, token: str = Depends(security)):
    new_device = await sensor_service.create_device(device)
    return new_device


@router.get("/", response_model=List[Device])
async def get_devices(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    devices = await sensor_service.get_devices()

    if normalize_role(current_user.role) in ASSIGNED_DEVICE_ROLES:
        assigned_device_ids = get_assigned_device_ids(current_user)
        devices = [device for device in devices if device.id in assigned_device_ids]

    return devices[skip : skip + limit]


@router.get("/{device_id}", response_model=Device)
async def get_device(
    device_id: str,
    current_user: User = Depends(get_current_user)
):
    ensure_device_access(current_user, device_id)
    device = await sensor_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.put("/{device_id}", response_model=Device)
async def update_device(device_id: str, device_update: DeviceUpdate, token: str = Depends(security)):
    # Simple update in PostgreSQL via repository
    current_device = await sensor_service.get_device(device_id)
    if not current_device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    update_data = device_update.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        # Note: Assuming device_repository has an update method, otherwise we'd need to add one.
        # For now, let's keep it consistent with other updates.
        await asyncio.to_thread(postgres_service.execute, 
            "UPDATE devices SET name = %s, location = %s, type = %s, zone_id = %s, crop_type = %s, area_size = %s, updated_at = %s WHERE id = %s",
            (
                update_data.get("name", current_device.name),
                update_data.get("location", current_device.location),
                update_data.get("type", current_device.type),
                update_data.get("zone_id", current_device.zone_id),
                update_data.get("crop_type", current_device.crop_type),
                update_data.get("area_size", current_device.area_size),
                update_data["updated_at"],
                device_id
            )
        )
    return await sensor_service.get_device(device_id)


@router.delete("/{device_id}")
async def delete_device(device_id: str, token: str = Depends(security)):
    # Delete from PostgreSQL
    await asyncio.to_thread(postgres_service.execute, "DELETE FROM devices WHERE id = %s", (device_id,))
    return {"message": "Device deleted successfully"}


@router.post("/{device_id}/connect/request-otp")
async def request_device_connect_otp(
    device_id: str,
    payload: DeviceConnectOtpRequest,
    current_user: User = Depends(get_current_user)
):
    if normalize_role(current_user.role) != "farmer":
        raise HTTPException(status_code=403, detail="Only farmers can connect devices.")

    device = await sensor_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    otp = "".join(secrets.choice("0123456789") for _ in range(6))
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=settings.DEVICE_OTP_EXPIRE_MINUTES)

    otp_doc_id = _build_otp_doc_id(current_user.id, device_id)
    otp_payload = {
        "otp_hash": _hash_otp(otp),
        "device_id": device_id,
        "email": current_user.email,
        "user_id": current_user.id,
        "expires_at": expires_at,
        "attempts": 0,
        "blocked": False,
        "created_at": now,
        "updated_at": now,
    }
    await asyncio.to_thread(device_otp_repository.upsert, otp_doc_id, otp_payload)

    try:
        await asyncio.to_thread(send_device_otp_email, current_user.email, device_id, otp, settings.DEVICE_OTP_EXPIRE_MINUTES)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to send OTP email: {exc}")

    await log_activity(current_user.id, "Device Connect OTP Requested", {"device_id": device_id})

    return {
        "message": "OTP sent to your email.",
        "email": current_user.email,
        "device_id": device_id,
        "expires_at": expires_at,
    }


@router.post("/{device_id}/connect/verify-otp")
async def verify_device_connect_otp(
    device_id: str,
    payload: DeviceConnectOtpVerifyRequest,
    current_user: User = Depends(get_current_user)
):
    if normalize_role(current_user.role) != "farmer":
        raise HTTPException(status_code=403, detail="Only farmers can connect devices.")

    otp_doc_id = _build_otp_doc_id(current_user.id, device_id)
    otp_data = await asyncio.to_thread(device_otp_repository.get, otp_doc_id)

    if not otp_data:
        raise HTTPException(status_code=404, detail="No active OTP found.")

    attempts = int(otp_data.get("attempts", 0))
    max_attempts = max(1, settings.DEVICE_OTP_MAX_ATTEMPTS)

    if bool(otp_data.get("blocked", False)) or attempts >= max_attempts:
        raise HTTPException(status_code=403, detail="OTP blocked.")

    expires_at = otp_data.get("expires_at")
    expires_at = expires_at.replace(tzinfo=None) if expires_at and expires_at.tzinfo else expires_at
    if not expires_at or expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired.")

    if _hash_otp(payload.otp.strip()) != otp_data.get("otp_hash"):
        new_attempts = attempts + 1
        is_blocked = new_attempts >= max_attempts
        await asyncio.to_thread(device_otp_repository.update_attempts, otp_doc_id, new_attempts, is_blocked)
        raise HTTPException(status_code=403, detail="Invalid OTP.")

    await _assign_device_to_user(current_user, device_id)
    await asyncio.to_thread(device_otp_repository.delete, otp_doc_id)
    await log_activity(current_user.id, "Device Connected via OTP", {"device_id": device_id})

    return {"message": "Device connected successfully.", "device_id": device_id}


@router.post("/{device_id}/pairing-code", response_model=PairingCodeResponse)
async def generate_pairing_code(
    device_id: str,
    payload: PairingCodeRequest,
    current_user: User = Depends(get_current_user)
):
    if normalize_role(current_user.role) != "admin":
        raise HTTPException(status_code=403, detail="Only admins can generate pairing codes.")

    device = await sensor_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    pairing_code = "".join(secrets.choice("0123456789") for _ in range(6))
    expires_at = datetime.utcnow() + timedelta(minutes=payload.expires_minutes)

    await asyncio.to_thread(device_repository.save_pairing_code, device_id, pairing_code, current_user.id, expires_at)
    await log_activity(current_user.id, "Device Pairing Code Generated", {"device_id": device_id})

    return PairingCodeResponse(device_id=device_id, pairing_code=pairing_code, expires_at=expires_at)


@router.post("/{device_id}/claim")
async def claim_device(
    device_id: str,
    payload: DeviceClaimRequest,
    current_user: User = Depends(get_current_user)
):
    if normalize_role(current_user.role) != "farmer":
        raise HTTPException(status_code=403, detail="Only farmers can claim devices.")

    device_data = await asyncio.to_thread(device_repository.get_raw_by_id, device_id)
    if not device_data:
        raise HTTPException(status_code=404, detail="Device not found")
        
    expected_code = str(device_data.get("pairing_code") or "").strip()
    if not expected_code or payload.pairing_code.strip() != expected_code:
        raise HTTPException(status_code=403, detail="Invalid pairing code.")

    expires_at = device_data.get("pairing_code_expires_at")
    expires_at = expires_at.replace(tzinfo=None) if expires_at and expires_at.tzinfo else expires_at
    if not expires_at or expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Pairing code has expired.")

    await _assign_device_to_user(current_user, device_id)
    await asyncio.to_thread(device_repository.clear_pairing_code, device_id)
    await log_activity(current_user.id, "Device Claimed", {"device_id": device_id})

    return {"message": "Device claimed successfully.", "device_id": device_id}


@router.post("/{device_id}/readings", response_model=SensorReading)
async def create_sensor_reading(device_id: str, reading: SensorReadingCreate):
    if device_id != reading.device_id:
        raise HTTPException(status_code=400, detail="Device ID mismatch")

    sensor_reading = await sensor_service.create_sensor_reading(device_id, reading)

    sensor_data_for_alert = {
        "device_id": sensor_reading.device_id,
        "soil_moisture": sensor_reading.soil_moisture,
        "temperature": sensor_reading.temperature,
        "humidity": sensor_reading.humidity,
        "timestamp": sensor_reading.timestamp
    }

    alerts = await alert_service.evaluate_sensor_data(sensor_data_for_alert)
    for alert in alerts:
        await alert_service.create_alert(alert)

    await handle_auto_irrigation(
        device_id=sensor_reading.device_id,
        soil_moisture=sensor_reading.soil_moisture,
        temperature=sensor_reading.temperature,
        humidity=sensor_reading.humidity,
        light_level=sensor_reading.light_level
    )

    return sensor_reading


@router.get("/{device_id}/readings", response_model=List[SensorReading])
async def get_sensor_readings(
    device_id: str, 
    start_time: datetime = None, 
    end_time: datetime = None, 
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(get_current_user)
):
    ensure_device_access(current_user, device_id)
    return await sensor_service.get_sensor_readings(device_id, start_time, end_time, skip, limit)


@router.get("/{device_id}/latest-reading", response_model=SensorReading)
async def get_latest_reading(
    device_id: str,
    current_user: User = Depends(get_current_user)
):
    ensure_device_access(current_user, device_id)
    latest_reading = await sensor_service.get_latest_sensor_reading(device_id)
    if not latest_reading:
        raise HTTPException(status_code=404, detail="No readings found")
    return latest_reading


@router.get("/{device_id}/hourly-average", response_model=HourlyAverageReadings)
async def get_hourly_average_readings_route(
    device_id: str,
    current_user: User = Depends(get_current_user)
):
    ensure_device_access(current_user, device_id)
    hourly_averages = await sensor_service.get_hourly_average_readings(device_id)
    if not hourly_averages["count"]:
        raise HTTPException(status_code=404, detail="No readings found in the last hour")
    return hourly_averages


@router.get("/{device_id}/daily-summary", response_model=DailySummaryReadings)
async def get_daily_summary_readings_route(
    device_id: str, 
    date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user)
):
    ensure_device_access(current_user, device_id)
    daily_summary = await sensor_service.get_daily_summary_readings(device_id, date)
    if not daily_summary["count"]:
        raise HTTPException(status_code=404, detail="No readings found on specified date")
    return daily_summary
