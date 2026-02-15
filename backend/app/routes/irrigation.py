from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
import random
from app.middleware.auth import JWTBearer
from app.models.irrigation import IrrigationSchedule, IrrigationScheduleCreate, IrrigationScheduleUpdate, IrrigationEvent, IrrigationEventCreate
from app.services.ml_service import ml_service
from app.services.firebase_service import firebase_service
from app.services.irrigation_service import irrigation_service



router = APIRouter()
security = JWTBearer()


@router.post("/schedule", response_model=IrrigationSchedule)
async def create_irrigation_schedule(schedule: IrrigationScheduleCreate, token: str = Depends(security)):
    new_schedule = irrigation_service.create_irrigation_schedule(schedule)
    return new_schedule


@router.get("/schedule", response_model=List[IrrigationSchedule])
async def get_irrigation_schedules(skip: int = 0, limit: int = 100, token: str = Depends(security)):
    schedules = irrigation_service.get_irrigation_schedules()
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
    new_event = irrigation_service.create_irrigation_event(event)
    return new_event


@router.get("/events", response_model=List[IrrigationEvent])
async def get_irrigation_events(device_id: Optional[str] = None, limit: int = 100, token: str = Depends(security)):
    events = irrigation_service.get_irrigation_events(device_id=device_id, limit=limit)
    return events


@router.post("/simulate", summary="Simulate irrigation for a device")
async def simulate_irrigation(device_id: str, duration_minutes: int = 30, token: str = Depends(security)):
    """
    Simulate irrigation for a device. This endpoint will be used when we don't have
    actual hardware connected to the system.
    """
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    dummy_sensor_data = {
        "temperature": 25 + (random.random() * 5 - 2.5),
        "humidity": 60 + (random.random() * 10 - 5),
        "soil_moisture": 45 + (random.random() * 10 - 5),
        "light_level": 800 + (random.random() * 200 - 100),
    }

    event_create = IrrigationEventCreate(
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
        duration_actual_minutes=duration_minutes,
        status="completed",
        **dummy_sensor_data
    )

    new_event = await create_irrigation_event(event_create, token)
    
    return new_event


@router.get("/recommendations/{device_id}")
async def get_irrigation_recommendations(device_id: str, token: str = Depends(security)):
    """
    Get irrigation recommendations for a specific device based on sensor data and ML predictions.
    This endpoint integrates with the ML service to provide intelligent recommendations.
    """
    # In a real implementation, this would fetch recent sensor data for the device
    # and pass it to the ML service for prediction
    # For now, we'll simulate with dummy data
    dummy_sensor_data = {
        "device_id": device_id,
        "soil_moisture": 35.0,
        "temperature": 28.5,
        "humidity": 45.0,
        "light_level": 500.0, # Added dummy light level
        "timestamp": datetime.utcnow().isoformat()
    }
    
    prediction_result = await ml_service.predict_irrigation_need(dummy_sensor_data)
    
    # Check for errors from the ML service
    if prediction_result.get("error"):
        raise HTTPException(status_code=500, detail=prediction_result["error"])

    predicted_duration = prediction_result.get("predicted_valve_duration_s", 0)
    
    recommendation_text = "No irrigation recommended at this time."
    if predicted_duration > 0.5: # If predicted duration is significant
        recommendation_text = f"Irrigate for approximately {predicted_duration:.2f} seconds."
    
    return {
        "device_id": device_id,
        "recommendation": recommendation_text,
        "predicted_valve_duration_s": predicted_duration,
        "predicted_at": prediction_result.get("predicted_at", datetime.utcnow().isoformat()),
        "current_conditions": dummy_sensor_data
    }