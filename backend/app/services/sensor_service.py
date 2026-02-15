from datetime import datetime, timedelta, timezone
import random # Added
from firebase_admin import firestore
from typing import List, Optional, Dict, Any
from app.services.firebase_service import firebase_service
from app.models.sensor import Device, DeviceCreate, SensorReading, SensorReadingCreate
from app.utils.helpers import generate_device_id

class SensorService:
    def __init__(self):
        self.db = firebase_service.db

    async def create_device(self, device_create: DeviceCreate) -> Device:
        device_id = generate_device_id()
        new_device = Device(
            id=device_id,
            name=device_create.name,
            location=device_create.location,
            owner_id=device_create.owner_id,
            type=device_create.type,
            zone_id=device_create.zone_id,
            crop_type=device_create.crop_type,
            area_size=device_create.area_size,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        self.db.collection('devices').document(device_id).set(new_device.dict())
        return new_device

    async def get_device(self, device_id: str) -> Optional[Device]:
        doc = self.db.collection('devices').document(device_id).get()
        if doc.exists:
            return Device(**doc.to_dict())
        return None

    async def get_devices(self, owner_id: Optional[str] = None) -> List[Device]:
        query = self.db.collection('devices')
        if owner_id:
            query = query.where('owner_id', '==', owner_id)
        docs = query.get()
        return [Device(**doc.to_dict()) for doc in docs]

    async def create_sensor_reading(self, device_id: str, reading_create: SensorReadingCreate) -> SensorReading:
        sensor_reading_id = f"reading_{datetime.utcnow().timestamp()}"
        new_reading = SensorReading(
            id=sensor_reading_id,
            device_id=device_id,
            soil_moisture=reading_create.soil_moisture,
            temperature=reading_create.temperature,
            humidity=reading_create.humidity,
            light_level=reading_create.light_level,
            timestamp=reading_create.timestamp or datetime.utcnow()
        )
        self.db.collection('sensor_readings').document(sensor_reading_id).set(new_reading.dict())
        return new_reading

    def get_latest_sensor_reading(self, device_id: str) -> Optional[SensorReading]:
        readings = (
            self.db.collection('sensor_readings')
            .where('device_id', '==', device_id)
            .order_by('timestamp', direction=firestore.Query.DESCENDING)
            .limit(1)
            .get()
        )
        if readings:
            return SensorReading(**readings[0].to_dict())
        return None

    def get_hourly_average_readings(self, device_id: str) -> Dict[str, float]:
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        readings_query = (
            self.db.collection('sensor_readings')
            .where('device_id', '==', device_id)
            .where('timestamp', '>=', one_hour_ago)
            .order_by('timestamp', direction=firestore.Query.DESCENDING)
            .get()
        )
        
        soil_moisture_sum = 0.0
        temperature_sum = 0.0
        humidity_sum = 0.0
        light_level_sum = 0.0
        count = 0
        
        for doc in readings_query:
            reading = SensorReading(**doc.to_dict())
            soil_moisture_sum += reading.soil_moisture
            temperature_sum += reading.temperature
            humidity_sum += reading.humidity
            light_level_sum += reading.light_level
            count += 1
            
        if count > 0:
            return {
                "device_id": device_id,
                "soil_moisture_avg": round(soil_moisture_sum / count, 2),
                "temperature_avg": round(temperature_sum / count, 2),
                "humidity_avg": round(humidity_sum / count, 2),
                "light_level_avg": round(light_level_sum / count, 2),
                "count": count
            }
        return {
            "device_id": device_id,
            "soil_moisture_avg": 0.0,
            "temperature_avg": 0.0,
            "humidity_avg": 0.0,
            "light_level_avg": 0.0,
            "count": 0
        }

    def get_daily_summary_readings(self, device_id: str, date: Optional[datetime.date] = None) -> Dict[str, Any]:
        if date is None:
            # Default to today's date in UTC
            now_utc = datetime.utcnow()
            start_of_day = datetime(now_utc.year, now_utc.month, now_utc.day, 0, 0, 0, tzinfo=timezone.utc)
            end_of_day = start_of_day + timedelta(days=1)
        else:
            start_of_day = datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=timezone.utc)
            end_of_day = start_of_day + timedelta(days=1)
        
        readings_query = (
            self.db.collection('sensor_readings')
            .where('device_id', '==', device_id)
            .where('timestamp', '>=', start_of_day)
            .where('timestamp', '<', end_of_day)
            .order_by('timestamp') # Order by timestamp for consistent min/max if needed
            .get()
        )
        
        soil_moisture_values = []
        temperature_values = []
        humidity_values = []
        light_level_values = []
        
        for doc in readings_query:
            reading = SensorReading(**doc.to_dict())
            soil_moisture_values.append(reading.soil_moisture)
            temperature_values.append(reading.temperature)
            humidity_values.append(reading.humidity)
            light_level_values.append(reading.light_level)
            
        summary = {
            "device_id": device_id,
            "date": date.isoformat() if date else now_utc.date().isoformat(),
            "count": len(soil_moisture_values),
            "soil_moisture": {
                "min": min(soil_moisture_values) if soil_moisture_values else 0.0,
                "max": max(soil_moisture_values) if soil_moisture_values else 0.0,
                "avg": round(sum(soil_moisture_values) / len(soil_moisture_values), 2) if soil_moisture_values else 0.0
            },
            "temperature": {
                "min": min(temperature_values) if temperature_values else 0.0,
                "max": max(temperature_values) if temperature_values else 0.0,
                "avg": round(sum(temperature_values) / len(temperature_values), 2) if temperature_values else 0.0
            },
            "humidity": {
                "min": min(humidity_values) if humidity_values else 0.0,
                "max": max(humidity_values) if humidity_values else 0.0,
                "avg": round(sum(humidity_values) / len(humidity_values), 2) if humidity_values else 0.0
            },
            "light_level": {
                "min": min(light_level_values) if light_level_values else 0.0,
                "max": max(light_level_values) if light_level_values else 0.0,
                "avg": round(sum(light_level_values) / len(light_level_values), 2) if light_level_values else 0.0
            }
        }
        return summary

    async def simulate_irrigation_effect(self, device_id: str, duration_minutes: int) -> Optional[SensorReading]:
        # Fetch the latest reading to base the simulation on
        latest_reading = self.get_latest_sensor_reading(device_id)
        
        if not latest_reading:
            print(f"WARNING: Cannot simulate irrigation effect for device {device_id}: no latest reading found.")
            return None
        
        # Calculate soil moisture increase: example 5-8% increase per 120s (2 minutes)
        # So, per minute: (5-8)% / 2 = 2.5-4%
        increase_per_minute = random.uniform(2.5, 4.0)
        simulated_moisture_increase = increase_per_minute * duration_minutes
        
        new_soil_moisture = min(100.0, latest_reading.soil_moisture + simulated_moisture_increase)
        
        # Other values can be slightly randomized or kept the same
        new_temperature = round(latest_reading.temperature + random.uniform(-1.0, 1.0), 2)
        new_humidity = round(latest_reading.humidity + random.uniform(-2.0, 2.0), 2)
        new_light_level = round(latest_reading.light_level + random.uniform(-10.0, 10.0), 2)

        simulated_reading_create = SensorReadingCreate(
            device_id=device_id,
            soil_moisture=new_soil_moisture,
            temperature=new_temperature,
            humidity=new_humidity,
            light_level=new_light_level,
            timestamp=datetime.utcnow() + timedelta(seconds=1) # Slightly after the event for distinct timestamp
        )
        
        print(f"Simulating irrigation effect for device {device_id}: moisture increased from {latest_reading.soil_moisture:.2f}% to {new_soil_moisture:.2f}%")
        return await self.create_sensor_reading(device_id, simulated_reading_create)


# Initialize the service
sensor_service = SensorService()
