from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from app.middleware.auth import JWTBearer
from app.models.sensor import SensorReading, SensorReadingCreate, Device, DeviceCreate, DeviceUpdate
from app.services.firebase_service import firebase_service
from app.services.alert_service import alert_service
from app.utils.helpers import calculate_dew_point, calculate_heat_index


router = APIRouter()
security = JWTBearer()


@router.post("/", response_model=Device)
async def create_device(device: DeviceCreate, token: str = Depends(security)):
    # In a real implementation, this would create a device record in Firestore
    # For now, returning a placeholder
    from app.utils.helpers import generate_device_id
    
    new_device = Device(
        id=generate_device_id(),
        name=device.name,
        location=device.location,
        owner_id=device.owner_id,
        type=device.type,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # In a real implementation, we would save this to Firestore
    # firebase_service.db.collection('devices').document(new_device.id).set(...)
    
    return new_device


@router.get("/", response_model=List[Device])
async def get_devices(skip: int = 0, limit: int = 100, token: str = Depends(security)):
    # In a real implementation, this would fetch devices from Firestore
    # For now, returning empty list as placeholder
    return []


@router.get("/{device_id}", response_model=Device)
async def get_device(device_id: str, token: str = Depends(security)):
    # In a real implementation, this would fetch a specific device from Firestore
    # For now, returning placeholder
    raise HTTPException(status_code=404, detail="Device not found")


@router.put("/{device_id}", response_model=Device)
async def update_device(device_id: str, device_update: DeviceUpdate, token: str = Depends(security)):
    # In a real implementation, this would update a device in Firestore
    raise HTTPException(status_code=404, detail="Device not found")


@router.delete("/{device_id}")
async def delete_device(device_id: str, token: str = Depends(security)):
    # In a real implementation, this would delete a device from Firestore
    raise HTTPException(status_code=404, detail="Device not found")


@router.post("/{device_id}/readings", response_model=SensorReading)
async def create_sensor_reading(device_id: str, reading: SensorReadingCreate, token: str = Depends(security)):
    # Validate that the device_id in the path matches the one in the reading
    if device_id != reading.device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device ID in path does not match device ID in request body"
        )

    # Calculate derived values
    dew_point = calculate_dew_point(reading.temperature, reading.humidity)
    heat_index = calculate_heat_index(reading.temperature, reading.humidity)

    # Create sensor reading with calculated values
    sensor_reading = SensorReading(
        id=f"reading_{datetime.utcnow().timestamp()}",
        device_id=reading.device_id,
        soil_moisture=reading.soil_moisture,
        temperature=reading.temperature,
        humidity=reading.humidity,
        timestamp=reading.timestamp or datetime.utcnow()
    )

    # In a real implementation, we would save this to Firestore
    # doc_ref = firebase_service.db.collection('sensor_readings').add(sensor_reading.dict())

    # Evaluate the sensor data for potential alerts
    sensor_data_for_alert = {
        "device_id": sensor_reading.device_id,
        "soil_moisture": sensor_reading.soil_moisture,
        "temperature": sensor_reading.temperature,
        "humidity": sensor_reading.humidity,
        "timestamp": sensor_reading.timestamp
    }

    alerts = alert_service.evaluate_sensor_data(sensor_data_for_alert)
    for alert in alerts:
        await alert_service.create_alert(alert)

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
    # In a real implementation, this would fetch sensor readings from Firestore
    # with filtering options
    # For now, returning empty list as placeholder
    return []