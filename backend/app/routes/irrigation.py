from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio
from app.middleware.auth import JWTBearer
from app.models.irrigation import IrrigationSchedule, IrrigationScheduleCreate, IrrigationScheduleUpdate, IrrigationEvent, IrrigationEventCreate, ControlState, ControlStateUpdate
from app.services.firebase_service import firebase_service
from app.services.irrigation_service import irrigation_service
from app.services.ml_service import ml_service
from app.services.sensor_service import sensor_service
from app.services.activity_log_service import log_activity
from app.dependencies import (
    get_current_user,
    ensure_device_access,
    get_assigned_device_ids,
    ASSIGNED_DEVICE_ROLES,
    normalize_role,
)
from app.models.user import User


router = APIRouter()
security = JWTBearer()


@router.post("/schedule", response_model=IrrigationSchedule)
async def create_irrigation_schedule(
    schedule: IrrigationScheduleCreate,
    current_user: User = Depends(get_current_user)
):
    ensure_device_access(current_user, schedule.device_id)
    new_schedule = await irrigation_service.create_irrigation_schedule(schedule)
    return new_schedule


@router.get("/schedule", response_model=List[IrrigationSchedule])
async def get_irrigation_schedules(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    schedules = await irrigation_service.get_irrigation_schedules()

    if normalize_role(current_user.role) in ASSIGNED_DEVICE_ROLES:
        assigned_device_ids = get_assigned_device_ids(current_user)
        schedules = [schedule for schedule in schedules if schedule.device_id in assigned_device_ids]

    return schedules[skip : skip + limit]


@router.get("/schedule/{schedule_id}", response_model=IrrigationSchedule)
async def get_irrigation_schedule(schedule_id: str, current_user: User = Depends(get_current_user)):
    schedules = await irrigation_service.get_irrigation_schedules()
    schedule = next((s for s in schedules if s.id == schedule_id), None)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    ensure_device_access(current_user, schedule.device_id)
    return schedule


@router.put("/schedule/{schedule_id}", response_model=IrrigationSchedule)
async def update_irrigation_schedule(
    schedule_id: str, 
    schedule_update: IrrigationScheduleUpdate, 
    current_user: User = Depends(get_current_user)
):
    schedules = await irrigation_service.get_irrigation_schedules()
    schedule = next((s for s in schedules if s.id == schedule_id), None)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    ensure_device_access(current_user, schedule.device_id)
    
    # Apply updates
    update_data = schedule_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(schedule, key, value)
    
    schedule.updated_at = datetime.utcnow()
    from app.services.postgres_service import postgres_service
    await asyncio.to_thread(postgres_service.save_irrigation_schedule, schedule.model_dump())
    return schedule


@router.delete("/schedule/{schedule_id}")
async def delete_irrigation_schedule(schedule_id: str, current_user: User = Depends(get_current_user)):
    schedules = await irrigation_service.get_irrigation_schedules()
    schedule = next((s for s in schedules if s.id == schedule_id), None)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    ensure_device_access(current_user, schedule.device_id)
    
    from app.services.postgres_service import postgres_service
    await asyncio.to_thread(postgres_service.execute, "DELETE FROM irrigation_schedules WHERE id = %s", (schedule_id,))
    return {"message": "Schedule deleted successfully"}


@router.post("/events", response_model=IrrigationEvent)
async def create_irrigation_event(
    event: IrrigationEventCreate,
    current_user: User = Depends(get_current_user)
):
    ensure_device_access(current_user, event.device_id)
    new_event = await irrigation_service.create_irrigation_event(event)
    return new_event


@router.get("/events", response_model=List[IrrigationEvent])
async def get_irrigation_events(
    device_id: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    if device_id:
        ensure_device_access(current_user, device_id)

    events = await irrigation_service.get_irrigation_events(device_id=device_id, limit=limit)

    if normalize_role(current_user.role) in ASSIGNED_DEVICE_ROLES and not device_id:
        assigned_device_ids = get_assigned_device_ids(current_user)
        events = [event for event in events if event.device_id in assigned_device_ids]

    return events


@router.post("/trigger", response_model=IrrigationEvent, summary="Trigger irrigation for a device")
async def trigger_irrigation(
    device_id: str,
    duration_seconds: Optional[int] = None, # Allow explicit duration in seconds or use ML prediction
    user_triggered: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Triggers an irrigation event for a specified device.
    If `duration_seconds` is not provided, the ML model will be used to predict 
    the optimal duration based on the latest sensor data.
    """
    ensure_device_access(current_user, device_id)
    current_control = await irrigation_service.get_control_state(device_id)

    start_time = datetime.utcnow()
    
    # If duration is not provided, use ML prediction
    if duration_seconds is None:
        latest_reading = await sensor_service.get_latest_sensor_reading(device_id)
        if not latest_reading:
            raise HTTPException(
                status_code=404,
                detail=f"No recent sensor data found for device {device_id}. Cannot predict irrigation duration."
            )

        sensor_data_for_ml = {
            "soil_moisture": latest_reading.soil_moisture,
            "temperature": latest_reading.temperature,
            "humidity": latest_reading.humidity,
            "light_level": latest_reading.light_level,
            "device_id": device_id
        }

        prediction_result = await ml_service.predict_irrigation_need(sensor_data_for_ml)
        if prediction_result.get("error"):
            raise HTTPException(status_code=400, detail=f"ML prediction failed: {prediction_result['error']}")

        predicted_duration_s = prediction_result.get("predicted_valve_duration_s", 0)
        duration_seconds = max(0, round(predicted_duration_s))


    if duration_seconds <= 0:
        raise HTTPException(status_code=400, detail=f"No irrigation needed for device {device_id} (predicted duration <= 0).")

    end_time = start_time + timedelta(seconds=duration_seconds)
    
    # Fetch latest sensor data for recording in the event
    latest_reading = await sensor_service.get_latest_sensor_reading(device_id)
    sensor_data_to_record = latest_reading.dict() if latest_reading else {}

    event_create = IrrigationEventCreate(
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
        duration_actual_seconds=duration_seconds, # Changed to seconds
        status="active", # Set to active so it can be stopped later
        user_triggered=(
            bool(user_triggered)
            if user_triggered is not None
            else str(current_control.mode).upper() != "AUTO"
        ),
        temperature=sensor_data_to_record.get('temperature'),
        humidity=sensor_data_to_record.get('humidity'),
        soil_moisture=sensor_data_to_record.get('soil_moisture'),
        light_level=sensor_data_to_record.get('light_level'),
    )

    new_event = await irrigation_service.create_irrigation_event(event_create)
    
    # Preserve control settings (like threshold and mode), only toggle pump state.
    # Do not override mode here; it is managed explicitly via /irrigation/control.
    current_control.pump_state = True
    
    # Update control state to turn pump ON
    await irrigation_service.update_control_state(current_control)

    await log_activity(
        user_id=current_user.id,
        action="Irrigation Start",
        details={
            "device_id": device_id,
            "duration_actual_seconds": duration_seconds,
            "event_id": new_event.id,
            "mode": "manual" if new_event.user_triggered else "auto",
        },
    )
    
    return new_event


@router.post("/stop/{device_id}", response_model=IrrigationEvent, summary="Stop active irrigation for a device")
async def stop_irrigation(
    device_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Stops any currently active irrigation event for the specified device.
    """
    ensure_device_access(current_user, device_id)

    stopped_event = await irrigation_service.stop_irrigation_event(device_id)
    if not stopped_event:
        raise HTTPException(status_code=404, detail=f"No active irrigation event found for device {device_id} to stop.")
    
    # Update control state to turn pump OFF
    current_control = await irrigation_service.get_control_state(device_id)
    current_control.pump_state = False
    await irrigation_service.update_control_state(current_control)

    await log_activity(
        user_id=current_user.id,
        action="Irrigation Stop",
        details={
            "device_id": device_id,
            "event_id": stopped_event.id,
            "status": stopped_event.status,
            "duration_actual_seconds": stopped_event.duration_actual_seconds,
        },
    )
    
    return stopped_event


@router.get("/recommendations/{device_id}")
async def get_irrigation_recommendations(
    device_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get irrigation recommendations for a specific device based on current sensor data.
    """
    ensure_device_access(current_user, device_id)

    latest_reading = await sensor_service.get_latest_sensor_reading(device_id)
    if not latest_reading:
        raise HTTPException(status_code=404, detail=f"No recent sensor data found for device {device_id}.")

    sensor_data_for_ml = {
        "device_id": device_id,
        "soil_moisture": latest_reading.soil_moisture,
        "temperature": latest_reading.temperature,
        "humidity": latest_reading.humidity,
        "light_level": latest_reading.light_level
    }

    prediction_result = await ml_service.predict_irrigation_need(sensor_data_for_ml)
    if prediction_result.get("error"):
        raise HTTPException(status_code=400, detail=prediction_result["error"])

    predicted_duration = prediction_result.get("predicted_valve_duration_s", 0)
    recommendation_text = "No irrigation recommended at this time."
    if predicted_duration > 0:
        recommendation_text = f"Irrigate for approximately {predicted_duration:.2f} seconds."

    return {
        "device_id": device_id,
        "recommendation": recommendation_text,
        "predicted_valve_duration_s": predicted_duration,
        "predicted_at": prediction_result.get("predicted_at", datetime.utcnow().isoformat()),
        "current_conditions": latest_reading.dict()
    }


# --- CONTROL STATE ROUTES ---

@router.get("/control/{device_id}", response_model=ControlState)
async def get_control_state(device_id: str):
    """
    Get the current irrigation control state (mode, pump_state, threshold) for a device.
    ESP32 polls this endpoint to get pump state (no auth required for hardware polling).
    """
    return await irrigation_service.get_control_state(device_id)


@router.put("/control/{device_id}", response_model=ControlState)
async def update_control_state(
device_id: str, 
control_update: ControlStateUpdate, 
    current_user: User = Depends(get_current_user)
):
    """
    Update the irrigation control state for a device.
    """
    ensure_device_access(current_user, device_id)

    current_state = await irrigation_service.get_control_state(device_id)

    if control_update.mode is not None:
        current_state.mode = control_update.mode
    if control_update.pump_state is not None:
        current_state.pump_state = control_update.pump_state
    if control_update.threshold is not None:
        current_state.threshold = control_update.threshold

    return await irrigation_service.update_control_state(current_state)
