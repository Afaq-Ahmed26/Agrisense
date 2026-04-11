from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
from app.middleware.auth import JWTBearer
from app.models.irrigation import IrrigationSchedule, IrrigationScheduleCreate, IrrigationScheduleUpdate, IrrigationEvent, IrrigationEventCreate, ControlState, ControlStateUpdate
from app.services.firebase_service import firebase_service
from app.services.irrigation_service import irrigation_service
from app.services.ml_service import ml_service
from app.services.sensor_service import sensor_service


router = APIRouter()
security = JWTBearer()


@router.post("/schedule", response_model=IrrigationSchedule)
async def create_irrigation_schedule(schedule: IrrigationScheduleCreate, token: str = Depends(security)):
    new_schedule = await irrigation_service.create_irrigation_schedule(schedule)
    return new_schedule


@router.get("/schedule", response_model=List[IrrigationSchedule])
async def get_irrigation_schedules(skip: int = 0, limit: int = 100, token: str = Depends(security)):
    schedules = await irrigation_service.get_irrigation_schedules()
    return schedules[skip : skip + limit]


@router.get("/schedule/{schedule_id}", response_model=IrrigationSchedule)
async def get_irrigation_schedule(schedule_id: str, token: str = Depends(security)):
    # In a real implementation, this would fetch a specific schedule from Firestore
    raise HTTPException(status_code=404, detail="Schedule not found")


@router.put("/schedule/{schedule_id}", response_model=IrrigationSchedule)
async def update_irrigation_schedule(
    schedule_id: str, 
    schedule_update: IrrigationScheduleUpdate, 
    token: str = Depends(security)
):
    # In a real implementation, this would update a schedule in Firestore
    raise HTTPException(status_code=404, detail="Schedule not found")


@router.delete("/schedule/{schedule_id}")
async def delete_irrigation_schedule(schedule_id: str, token: str = Depends(security)):
    # In a real implementation, this would delete a schedule from Firestore
    raise HTTPException(status_code=404, detail="Schedule not found")


@router.post("/events", response_model=IrrigationEvent)
async def create_irrigation_event(event: IrrigationEventCreate, token: str = Depends(security)):
    new_event = await irrigation_service.create_irrigation_event(event)
    return new_event


@router.get("/events", response_model=List[IrrigationEvent])
async def get_irrigation_events(device_id: Optional[str] = None, limit: int = 100, token: str = Depends(security)):
    events = await irrigation_service.get_irrigation_events(device_id=device_id, limit=limit)
    return events


@router.post("/trigger", response_model=IrrigationEvent, summary="Trigger irrigation for a device")
async def trigger_irrigation(
    device_id: str,
    duration_seconds: Optional[int] = None, # Allow explicit duration in seconds or use ML prediction
    user_triggered: bool = True, # Default to true if called manually
    token: str = Depends(security)
):
    """
    Triggers an irrigation event for a specified device.
    If `duration_seconds` is not provided, the ML model will be used to predict 
    the optimal duration based on the latest sensor data.
    """
    start_time = datetime.utcnow()
    
    # If duration is not provided, use ML prediction
    if duration_seconds is None:
        # =========================
        # ML DISABLED (PHASE 2)
        # latest_reading = await sensor_service.get_latest_sensor_reading(device_id)
        
        # if not latest_reading:
        #     raise HTTPException(status_code=404, detail=f"No recent sensor data found for device {device_id}. Cannot predict irrigation duration.")

        # sensor_data_for_ml = {
        #     "soil_moisture": latest_reading.soil_moisture,
        #     "temperature": latest_reading.temperature,
        #     "humidity": latest_level.humidity,
        #     "light_level": latest_reading.light_level,
        #     "device_id": device_id
        # }
        
        # prediction_result = await ml_service.predict_irrigation_need(sensor_data_for_ml)
        
        # if prediction_result.get("error"):
        #     raise HTTPException(status_code=500, detail=f"ML prediction failed: {prediction_result['error']}")
        
        # predicted_duration_s = prediction_result.get("predicted_valve_duration_s", 0)
        # duration_seconds = max(0, round(predicted_duration_s)) # Use predicted seconds, ensure non-negative
        # =========================
        # For now, if duration is not provided and ML is disabled, default to a sensible duration or raise error
        raise HTTPException(status_code=400, detail="Duration must be provided explicitly when ML is disabled.")


    if duration_seconds <= 0:
        # If duration is 0 or negative, it means no irrigation is needed/possible
        # Create a "no irrigation" event for logging purposes if desired, or just return a message.
        # For now, let's just return a message without creating an event.
        return {
            "message": f"No irrigation triggered for device {device_id} as predicted duration was 0 or less seconds.",
            "device_id": device_id,
            "predicted_duration_s": 0, # Since ML is disabled
            "start_time": start_time, # Add start_time for consistency
            "end_time": start_time, # End time same as start time for 0 duration
            "duration_actual_seconds": 0,
            "status": "completed", # Mark as completed for 0 duration
            "user_triggered": user_triggered
        }

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
        user_triggered=user_triggered,
        temperature=sensor_data_to_record.get('temperature'),
        humidity=sensor_data_to_record.get('humidity'),
        soil_moisture=sensor_data_to_record.get('soil_moisture'),
        light_level=sensor_data_to_record.get('light_level'),
    )

    new_event = await irrigation_service.create_irrigation_event(event_create)
    
    # Fetch current control state to preserve settings (like threshold)
    current_control = await irrigation_service.get_control_state(device_id)
    current_control.pump_state = True
    current_control.mode = "MANUAL" if user_triggered else "AUTO"
    
    # Update control state to turn pump ON
    await irrigation_service.update_control_state(current_control)
    
    return new_event


@router.post("/stop/{device_id}", response_model=IrrigationEvent, summary="Stop active irrigation for a device")
async def stop_irrigation(device_id: str, token: str = Depends(security)):
    """
    Stops any currently active irrigation event for the specified device.
    """
    stopped_event = await irrigation_service.stop_irrigation_event(device_id)
    if not stopped_event:
        raise HTTPException(status_code=404, detail=f"No active irrigation event found for device {device_id} to stop.")
    
    # Update control state to turn pump OFF
    current_control = await irrigation_service.get_control_state(device_id)
    current_control.pump_state = False
    await irrigation_service.update_control_state(current_control)
    
    return stopped_event


# @router.get("/recommendations/{device_id}")
# async def get_irrigation_recommendations(device_id: str, token: str = Depends(security)):
#     """
#     Get irrigation recommendations for a specific device based on sensor data and ML predictions.
#     This endpoint integrates with the ML service to provide intelligent recommendations.
#     """
#     # =========================
#     # ML DISABLED (PHASE 2)
#     # latest_reading = await sensor_service.get_latest_sensor_reading(device_id)
    
#     # if not latest_reading:
#     #     raise HTTPException(status_code=404, detail=f"No recent sensor data found for device {device_id}.")

#     # sensor_data_for_ml = {
#     #     "device_id": device_id,
#     #     "soil_moisture": latest_reading.soil_moisture,
#     #     "temperature": latest_reading.temperature,
#     #     "humidity": latest_reading.humidity,
#     #     "light_level": latest_reading.light_level,
#     #     "timestamp": datetime.utcnow().isoformat()
#     # }
    
#     # prediction_result = await ml_service.predict_irrigation_need(sensor_data_for_ml)
    
#     # # Check for errors from the ML service
#     # if prediction_result.get("error"):
#     #     raise HTTPException(status_code=500, detail=prediction_result["error"])

#     # predicted_duration = prediction_result.get("predicted_valve_duration_s", 0)
    
#     # recommendation_text = "No irrigation recommended at this time."
#     # if predicted_duration > 0.5: # If predicted duration is significant
#     #     recommendation_text = f"Irrigate for approximately {predicted_duration:.2f} seconds."
    
#     # return {
#     #     "device_id": device_id,
#     #     "recommendation": recommendation_text,
#     #     "predicted_valve_duration_s": predicted_duration,
#     #     "predicted_at": prediction_result.get("predicted_at", datetime.utcnow().isoformat()),
#     #     "current_conditions": latest_reading.dict() # Use actual latest reading
#     # }
#     # =========================
# When ML is disabled, recommendations are not available.
# raise HTTPException(status_code=501, detail="ML-based irrigation recommendations are currently disabled.")


# --- CONTROL STATE ROUTES ---

@router.get("/control/{device_id}", response_model=ControlState)
async def get_control_state(device_id: str):
    """
    Get the current irrigation control state (mode, pump_state, threshold) for a device.
    """
    return await irrigation_service.get_control_state(device_id)


@router.put("/control/{device_id}", response_model=ControlState)
async def update_control_state(
device_id: str, 
control_update: ControlStateUpdate, 
token: str = Depends(security)
):
    """
    Update the irrigation control state for a device.
    """
    current_state = await irrigation_service.get_control_state(device_id)

    if control_update.mode is not None:
        current_state.mode = control_update.mode
    if control_update.pump_state is not None:
        current_state.pump_state = control_update.pump_state
    if control_update.threshold is not None:
        current_state.threshold = control_update.threshold

    return await irrigation_service.update_control_state(current_state)