from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta # Added timedelta
from app.middleware.auth import JWTBearer
from app.models.sensor import SensorReading, SensorReadingCreate, Device, DeviceCreate, DeviceUpdate, HourlyAverageReadings, DailySummaryReadings
from app.models.irrigation import IrrigationEventCreate # Added IrrigationEventCreate
from app.services.firebase_service import firebase_service
from app.services.alert_service import alert_service
from app.services.sensor_service import sensor_service
from app.services.ml_service import ml_service
from app.config import settings
from app.services.irrigation_service import irrigation_service # Added irrigation_service
from app.utils.helpers import calculate_dew_point, calculate_heat_index


router = APIRouter()
security = JWTBearer()


@router.post("/", response_model=Device)
async def create_device(device: DeviceCreate, token: str = Depends(security)):
    new_device = await sensor_service.create_device(device)
    return new_device


@router.get("/", response_model=List[Device])
async def get_devices(skip: int = 0, limit: int = 100, token: str = Depends(security)):
    devices = await sensor_service.get_devices()
    return devices[skip : skip + limit]


@router.get("/{device_id}", response_model=Device)
async def get_device(device_id: str, token: str = Depends(security)):
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

    # ML Auto-Trigger Logic - COMMENTED OUT (Not testing ML today)
    return sensor_reading


@router.get("/{device_id}/readings", response_model=List[SensorReading])
async def get_sensor_readings(
    device_id: str, 
    start_time: datetime = None, 
    end_time: datetime = None, 
    skip: int = 0, 
    limit: int = 100, 
    token: str = Depends(security)
):
    readings = await sensor_service.get_sensor_readings(
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )
    return readings


@router.get("/{device_id}/latest-reading", response_model=SensorReading)
async def get_latest_reading(device_id: str, token: str = Depends(security)):
    latest_reading = await sensor_service.get_latest_sensor_reading(device_id)
    if not latest_reading:
        raise HTTPException(status_code=404, detail="No sensor readings found for this device")
    return latest_reading


@router.get("/{device_id}/hourly-average", response_model=HourlyAverageReadings)
async def get_hourly_average_readings_route(device_id: str, token: str = Depends(security)):
    hourly_averages = await sensor_service.get_hourly_average_readings(device_id)
    if not hourly_averages["count"]:
        raise HTTPException(status_code=404, detail="No sensor readings found for this device in the last hour")
    return hourly_averages


@router.get("/{device_id}/daily-summary", response_model=DailySummaryReadings)
async def get_daily_summary_readings_route(
    device_id: str, 
    date: Optional[date] = Query(None), # Optional date parameter
    token: str = Depends(security)
):
    daily_summary = await sensor_service.get_daily_summary_readings(device_id, date)
    if not daily_summary["count"]:
        raise HTTPException(status_code=404, detail="No sensor readings found for this device on the specified date")
    return daily_summary
