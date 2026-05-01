from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
import asyncio
import time  # For debounce timing
import secrets
import hashlib
from pydantic import BaseModel, Field
from firebase_admin import firestore
from app.middleware.auth import JWTBearer
from app.models.sensor import SensorReading, SensorReadingCreate, Device, DeviceCreate, DeviceUpdate, HourlyAverageReadings, DailySummaryReadings
from app.models.irrigation import IrrigationEventCreate, ControlState
from app.services.firebase_service import firebase_service
from app.services.alert_service import alert_service
from app.services.sensor_service import sensor_service
from app.services.irrigation_service import irrigation_service
from app.services.user_service import update_user_in_firestore
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

# =============================================================================
# AUTO IRRIGATION CONTROL (ML-Driven)
# =============================================================================

# Debounce configuration: minimum seconds between state changes
DEBOUNCE_INTERVAL_SECONDS = 2

# Track last state change time per device (in-memory)
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


OTP_COLLECTION = "device_connect_otps"


async def handle_auto_irrigation(device_id: str, soil_moisture: Optional[float], temperature: Optional[float] = None, humidity: Optional[float] = None, light_level: Optional[float] = None):
    """
    Real-time irrigation control based on ML prediction (AUTO) or user command (MANUAL).
    Only updates if state actually changes + debounce prevents rapid toggling.
    """
    try:
        control = await irrigation_service.get_control_state(device_id)

        # In MANUAL mode, we don't override the pump_state automatically.
        if control.mode == "MANUAL":
            return

        # --- AUTO MODE LOGIC (ML-DRIVEN with Safety Fallback) ---
        if soil_moisture is None:
            print(f"DEBUG: Device {device_id} - Soil moisture is None. Skipping auto-irrigation decision.")
            return  # Skip if no soil moisture data

        # Prepare data for ML prediction
        sensor_data = {
            'soil_moisture': soil_moisture,
            'temperature': temperature,
            'humidity': humidity,
            'light_level': light_level
        }
        
        # Attempt ML prediction
        ml_prediction_duration = 0
        ml_error = None
        ml_triggered_by_prediction = False # Flag for ML prediction suggesting irrigation
        
        if ml_service.model: # Ensure model is loaded
            prediction = await ml_service.predict_irrigation_need(sensor_data)
            ml_prediction_duration = prediction.get("predicted_valve_duration_s", 0)
            ml_error = prediction.get("error")
            
            if ml_error:
                print(f"DEBUG: Device {device_id} - ML Prediction Error: {ml_error}")
            else:
                if ml_prediction_duration > 0:
                    ml_triggered_by_prediction = True
                    print(f"DEBUG: Device {device_id} - ML predicted irrigation needed: {ml_prediction_duration}s")
                else:
                    print(f"DEBUG: Device {device_id} - ML predicted no irrigation needed (duration: {ml_prediction_duration}s).")
        else:
            ml_error = "ML model not loaded." # Treat as ML failure if model not loaded
            print(f"DEBUG: Device {device_id} - ML Model Status: Not Loaded. Treating as ML error.")

        # Liters per second conversion (Example: 0.05 L/s)
        FLOW_RATE_LPS = 0.05
        predicted_liters = round(ml_prediction_duration * FLOW_RATE_LPS, 2)

        # Fetch system-wide thresholds for safety/fallback
        # Default fallback: 30% low, 20% critical
        threshold_low = 30.0
        threshold_critical = 20.0
        
        if threshold_repository.is_enabled():
            system_thresholds = await asyncio.to_thread(threshold_repository.get_alert_thresholds)
            if system_thresholds:
                threshold_low = getattr(system_thresholds, "soil_moisture_low", 30.0)
                threshold_critical = getattr(system_thresholds, "soil_moisture_critical", 20.0)
                print(f"DEBUG: Device {device_id} - Fetched system thresholds: Low={threshold_low}%, Critical={threshold_critical}%.")
            else:
                print(f"DEBUG: Device {device_id} - No system thresholds found in DB. Using defaults.")
        else:
            print(f"DEBUG: Device {device_id} - Threshold repository not enabled. Using default thresholds.")
        
        # --- DECISION LOGIC WITH SAFETY FALLBACK ---
        ml_triggered = False # Final decision based on ML for pump activation
        threshold_triggered = False # Final decision based on critical threshold for pump activation

        # 1. Primary: ML-Driven trigger condition
        # Trigger if ML works, predicts duration > 0, AND soil moisture is below the 'low' threshold.
        # Ensure ML is not in an error state.
        if ml_triggered_by_prediction and not ml_error and soil_moisture < threshold_low:
            ml_triggered = True
            print(f"DEBUG: Device {device_id} - ML condition met: soil_moisture ({soil_moisture}%) < Low Threshold ({threshold_low}%) AND ML predicted > 0.")

        # 2. Fallback: Threshold-Driven trigger condition
        # Trigger if soil moisture is critically low, regardless of ML output.
        if soil_moisture < threshold_critical:
            threshold_triggered = True
            print(f"DEBUG: Device {device_id} - Critical Threshold condition met: soil_moisture ({soil_moisture}%) < Critical Threshold ({threshold_critical}%).")

        # Final decision: pump is ON if ML triggered it OR if the critical threshold dictates it.
        # This ensures the safety fallback takes precedence.
        # New: Automatically stop if moisture >= 60%
        if control.pump_state and soil_moisture >= 60.0:
            new_pump_state = False
            trigger_type = "Stop-Condition (>=60%)"
        else:
            new_pump_state = ml_triggered or threshold_triggered
            trigger_type = "ML-Driven" if ml_triggered else ("Threshold-Fallback" if threshold_triggered else "None")
        
        # Add detailed print statements for debugging as requested
        print(f"DEBUG: Device {device_id} - Final Decision Trace: Soil: {soil_moisture:.1f}%, ML Pred Duration: {ml_prediction_duration}s, ML Error: {ml_error}, ML Triggered (by logic): {ml_triggered}, Threshold Triggered: {threshold_triggered}, Final Pump State Decision: {new_pump_state} (via {trigger_type})")

        # ✅ Debounce: prevent rapid toggling
        now = time.time()
        last_change = _last_state_change_time.get(device_id, 0)
        if (now - last_change) < DEBOUNCE_INTERVAL_SECONDS:
            print(f"DEBUG: Device {device_id} - Debounce active. Skipping state change to {new_pump_state}.")
            return  # Too soon, skip this change

        # Only proceed if state actually changes
        if control.pump_state == new_pump_state:
            print(f"DEBUG: Device {device_id} - Pump state unchanged ({new_pump_state}). Skipping database update.")
            return

        # Update control state
        control.pump_state = new_pump_state
        await irrigation_service.update_control_state(control)
        print(f"DEBUG: Device {device_id} - Database control state updated to pump_state={new_pump_state}.")

        # Track change time for debounce
        _last_state_change_time[device_id] = now

        # Log only on actual state changes
        state_str = "ON" if new_pump_state else "OFF"
        ml_info = f"ML Predicted: {ml_prediction_duration}s ({predicted_liters}L)" if ml_triggered else ""
        print(f"💧 [Auto Irrigation] Device {device_id}: Pump turned {state_str} (moisture={soil_moisture:.1f}%, Low={threshold_low:.1f}%, Critical={threshold_critical:.1f}%) {ml_info}")

    except Exception as e:
        print(f"❌ [Irrigation Control] Error for device {device_id}: {e}")


def _build_otp_doc_id(user_id: str, device_id: str) -> str:
    return f"{user_id}:{device_id}"


def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


async def _assign_device_to_user(current_user: User, device_id: str) -> None:
    now = datetime.utcnow()

    if device_repository.is_enabled():
        await asyncio.to_thread(device_repository.assign_owner, device_id, current_user.id)
    else:
        device_ref = firebase_service.db.collection("devices").document(device_id)
        await asyncio.to_thread(
            device_ref.update,
            {
                "owner_id": current_user.id,
                "updated_at": now,
            },
        )

    claimant_assigned_device_ids = get_assigned_device_ids(current_user)
    claimant_assigned_device_ids.add(device_id)
    await update_user_in_firestore(
        current_user.id,
        {"assigned_device_ids": sorted(claimant_assigned_device_ids), "updated_at": now},
    )

    if user_repository.is_enabled():
        users = await asyncio.to_thread(user_repository.get_all, 0, 5000, True)
        for user in users:
            if user.id == current_user.id:
                continue
            existing_ids = [value for value in (user.assigned_device_ids or []) if isinstance(value, str)]
            if device_id not in existing_ids:
                continue
            remaining_ids = [value for value in existing_ids if value != device_id]
            await update_user_in_firestore(
                user.id,
                {"assigned_device_ids": remaining_ids, "updated_at": now},
            )
    else:
        users_query = firebase_service.db.collection("users").where(
            "assigned_device_ids", "array_contains", device_id
        )
        users_docs = await asyncio.to_thread(lambda: users_query.get())
        for user_doc in users_docs:
            if user_doc.id == current_user.id:
                continue
            user_data = user_doc.to_dict() or {}
            existing_ids = [
                value.strip()
                for value in (user_data.get("assigned_device_ids") or [])
                if isinstance(value, str) and value.strip()
            ]
            if device_id not in existing_ids:
                continue
            remaining_ids = [value for value in existing_ids if value != device_id]
            await update_user_in_firestore(
                user_doc.id,
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
    # In a real implementation, this would update a device in Firestore
    raise HTTPException(status_code=404, detail="Device not found")


@router.delete("/{device_id}")
async def delete_device(device_id: str, token: str = Depends(security)):
    # In a real implementation, this would delete a device from Firestore
    raise HTTPException(status_code=404, detail="Device not found")


@router.post("/{device_id}/connect/request-otp")
async def request_device_connect_otp(
    device_id: str,
    payload: DeviceConnectOtpRequest,
    current_user: User = Depends(get_current_user)
):
    if normalize_role(current_user.role) != "farmer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only farmers can connect devices with OTP."
        )

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
    if device_otp_repository.is_enabled():
        await asyncio.to_thread(device_otp_repository.upsert, otp_doc_id, otp_payload)
    else:
        otp_ref = firebase_service.db.collection(OTP_COLLECTION).document(otp_doc_id)
        await asyncio.to_thread(otp_ref.set, otp_payload)

    try:
        await asyncio.to_thread(
            send_device_otp_email,
            current_user.email,
            device_id,
            otp,
            settings.DEVICE_OTP_EXPIRE_MINUTES,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP email: {exc}"
        )

    await log_activity(
        user_id=current_user.id,
        action="Device Connect OTP Requested",
        details={"device_id": device_id, "email": current_user.email}
    )

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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only farmers can connect devices with OTP."
        )

    otp_doc_id = _build_otp_doc_id(current_user.id, device_id)
    if device_otp_repository.is_enabled():
        otp_data = await asyncio.to_thread(device_otp_repository.get, otp_doc_id)
    else:
        otp_ref = firebase_service.db.collection(OTP_COLLECTION).document(otp_doc_id)
        otp_doc = await asyncio.to_thread(otp_ref.get)
        otp_data = otp_doc.to_dict() if otp_doc.exists else None

    if not otp_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active OTP found. Please request a new OTP."
        )

    attempts = int(otp_data.get("attempts", 0))
    blocked = bool(otp_data.get("blocked", False))
    max_attempts = max(1, settings.DEVICE_OTP_MAX_ATTEMPTS)

    if blocked or attempts >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OTP blocked after too many failed attempts. Request a new OTP."
        )

    expires_at = otp_data.get("expires_at")
    if not isinstance(expires_at, datetime):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP record is invalid. Request a new OTP."
        )
    expires_at = expires_at.replace(tzinfo=None) if expires_at.tzinfo else expires_at
    if expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired. Please request a new OTP."
        )

    provided_hash = _hash_otp(payload.otp.strip())
    if provided_hash != otp_data.get("otp_hash"):
        new_attempts = attempts + 1
        is_blocked = new_attempts >= max_attempts
        if device_otp_repository.is_enabled():
            await asyncio.to_thread(device_otp_repository.update_attempts, otp_doc_id, new_attempts, is_blocked)
        else:
            await asyncio.to_thread(
                otp_ref.update,
                {"attempts": new_attempts, "blocked": is_blocked, "updated_at": datetime.utcnow()},
            )
        attempts_left = max(0, max_attempts - new_attempts)
        detail = "Invalid OTP."
        if is_blocked:
            detail = "OTP blocked after too many failed attempts. Request a new OTP."
        else:
            detail = f"Invalid OTP. {attempts_left} attempts remaining."
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

    device = await sensor_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    await _assign_device_to_user(current_user, device_id)
    if device_otp_repository.is_enabled():
        await asyncio.to_thread(device_otp_repository.delete, otp_doc_id)
    else:
        await asyncio.to_thread(otp_ref.delete)

    await log_activity(
        user_id=current_user.id,
        action="Device Connected via OTP",
        details={"device_id": device_id}
    )

    return {
        "message": "Device connected successfully.",
        "device_id": device_id,
        "owner_id": current_user.id,
    }


@router.post("/{device_id}/pairing-code", response_model=PairingCodeResponse)
async def generate_pairing_code(
    device_id: str,
    payload: PairingCodeRequest,
    current_user: User = Depends(get_current_user)
):
    if normalize_role(current_user.role) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can generate pairing codes."
        )

    device = await sensor_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    pairing_code = "".join(secrets.choice("0123456789") for _ in range(6))
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=payload.expires_minutes)

    if device_repository.is_enabled():
        await asyncio.to_thread(
            device_repository.save_pairing_code,
            device_id,
            pairing_code,
            current_user.id,
            expires_at,
        )
    else:
        device_ref = firebase_service.db.collection("devices").document(device_id)
        await asyncio.to_thread(
            device_ref.update,
            {
                "pairing_code": pairing_code,
                "pairing_code_generated_at": now,
                "pairing_code_expires_at": expires_at,
                "pairing_code_generated_by": current_user.id,
                "updated_at": now,
            },
        )

    await log_activity(
        user_id=current_user.id,
        action="Device Pairing Code Generated",
        details={
            "device_id": device_id,
            "expires_at": expires_at.isoformat(),
        },
    )

    return PairingCodeResponse(
        device_id=device_id,
        pairing_code=pairing_code,
        expires_at=expires_at,
    )


@router.post("/{device_id}/claim")
async def claim_device(
    device_id: str,
    payload: DeviceClaimRequest,
    current_user: User = Depends(get_current_user)
):
    if normalize_role(current_user.role) != "farmer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only farmers can claim devices via pairing code."
        )

    if device_repository.is_enabled():
        device_data = await asyncio.to_thread(device_repository.get_raw_by_id, device_id)
    else:
        device_ref = firebase_service.db.collection("devices").document(device_id)
        device_doc = await asyncio.to_thread(device_ref.get)
        device_data = device_doc.to_dict() if device_doc.exists else None

    if not device_data:
        raise HTTPException(status_code=404, detail="Device not found")
    expected_code = str(device_data.get("pairing_code") or "").strip()
    if not expected_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active pairing code found for this device."
        )

    provided_code = payload.pairing_code.strip()
    if provided_code != expected_code:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid pairing code."
        )

    expires_at = device_data.get("pairing_code_expires_at")
    if not isinstance(expires_at, datetime):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pairing code configuration is invalid."
        )
    expires_at = expires_at.replace(tzinfo=None) if expires_at.tzinfo else expires_at
    if expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pairing code has expired."
        )

    now = datetime.utcnow()
    await _assign_device_to_user(current_user, device_id)
    if device_repository.is_enabled():
        await asyncio.to_thread(device_repository.clear_pairing_code, device_id)
    else:
        await asyncio.to_thread(
            device_ref.update,
            {
                "pairing_code": firestore.DELETE_FIELD,
                "pairing_code_generated_at": firestore.DELETE_FIELD,
                "pairing_code_expires_at": firestore.DELETE_FIELD,
                "pairing_code_generated_by": firestore.DELETE_FIELD,
                "updated_at": now,
            },
        )

    await log_activity(
        user_id=current_user.id,
        action="Device Claimed",
        details={"device_id": device_id},
    )

    return {
        "message": "Device claimed successfully.",
        "device_id": device_id,
        "owner_id": current_user.id,
    }


@router.post("/{device_id}/readings", response_model=SensorReading)
async def create_sensor_reading(device_id: str, reading: SensorReadingCreate):
    # Validate that the device_id in the path matches the one in the reading
    if device_id != reading.device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device ID in path does not match device ID in request body"
        )

    # Calculate derived values only if sensors are connected
    dew_point = None
    heat_index = None
    if reading.temperature is not None and reading.humidity is not None:
        dew_point = calculate_dew_point(reading.temperature, reading.humidity)
        heat_index = calculate_heat_index(reading.temperature, reading.humidity)

    # Use the service to create the sensor reading
    sensor_reading = await sensor_service.create_sensor_reading(device_id, reading)

    # Evaluate the sensor data for potential alerts
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

    # ✅ AUTO IRRIGATION CONTROL (Real sensor data → Real decision)
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
    readings = await sensor_service.get_sensor_readings(
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )
    return readings


@router.get("/{device_id}/latest-reading", response_model=SensorReading)
async def get_latest_reading(
    device_id: str,
    current_user: User = Depends(get_current_user)
):
    ensure_device_access(current_user, device_id)
    latest_reading = await sensor_service.get_latest_sensor_reading(device_id)
    if not latest_reading:
        raise HTTPException(status_code=404, detail="No sensor readings found for this device")
    return latest_reading


@router.get("/{device_id}/hourly-average", response_model=HourlyAverageReadings)
async def get_hourly_average_readings_route(
    device_id: str,
    current_user: User = Depends(get_current_user)
):
    ensure_device_access(current_user, device_id)
    hourly_averages = await sensor_service.get_hourly_average_readings(device_id)
    if not hourly_averages["count"]:
        raise HTTPException(status_code=404, detail="No sensor readings found for this device in the last hour")
    return hourly_averages


@router.get("/{device_id}/daily-summary", response_model=DailySummaryReadings)
async def get_daily_summary_readings_route(
    device_id: str, 
    date: Optional[date] = Query(None), # Optional date parameter
    current_user: User = Depends(get_current_user)
):
    ensure_device_access(current_user, device_id)
    daily_summary = await sensor_service.get_daily_summary_readings(device_id, date)
    if not daily_summary["count"]:
        raise HTTPException(status_code=404, detail="No sensor readings found for this device on the specified date")
    return daily_summary
