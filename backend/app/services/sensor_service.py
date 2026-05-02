import asyncio
import time
from datetime import datetime, timedelta, timezone
import random
from typing import List, Optional, Dict, Any
from app.services.postgres_service import postgres_service
from app.repositories.device_repository import device_repository
from app.models.sensor import Device, DeviceCreate, SensorReading, SensorReadingCreate
from app.utils.helpers import generate_device_id

class SensorService:
    def __init__(self):
        self._latest_sensor_data_cache: Dict[str, SensorReading] = {} # In-memory cache for live dashboard

    @staticmethod
    def _to_utc_naive(dt: Optional[datetime]) -> Optional[datetime]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

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
        await asyncio.to_thread(device_repository.create, new_device)
        return new_device

    async def get_device(self, device_id: str) -> Optional[Device]:
        return await asyncio.to_thread(device_repository.get_by_id, device_id)

    async def get_devices(self, owner_id: Optional[str] = None) -> List[Device]:
        return await asyncio.to_thread(device_repository.list, owner_id)

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
        
        # Update in-memory cache IMMEDIATELY (for live dashboard)
        self._latest_sensor_data_cache[device_id] = new_reading

        # Mandatory PostgreSQL save
        try:
            await asyncio.to_thread(postgres_service.save_sensor_reading, new_reading.model_dump())
        except Exception as e:
            print(f"❌ [SensorService] PostgreSQL save failed for {device_id}: {e}")
            # Re-raise or handle as needed, but here we prioritize continuing
        
        return new_reading

    async def get_latest_sensor_reading(self, device_id: str) -> Optional[SensorReading]:
        # Try to get from in-memory cache first
        if device_id in self._latest_sensor_data_cache:
            return self._latest_sensor_data_cache[device_id]

        try:
            latest_pg = await asyncio.to_thread(postgres_service.get_latest_sensor_reading, device_id)
            if latest_pg:
                latest_reading = SensorReading(**latest_pg)
                self._latest_sensor_data_cache[device_id] = latest_reading
                return latest_reading
        except Exception as e:
            print(f"❌ [SensorService] PostgreSQL latest read failed for {device_id}: {e}")
        
        return None

    async def get_sensor_readings(
        self, 
        device_id: str, 
        start_time: Optional[datetime] = None, 
        end_time: Optional[datetime] = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[SensorReading]:
        normalized_start = self._to_utc_naive(start_time)
        normalized_end = self._to_utc_naive(end_time)

        # Start with cached reading if applicable
        cached_readings = []
        if device_id in self._latest_sensor_data_cache:
            cached = self._latest_sensor_data_cache[device_id]
            cached_ts = self._to_utc_naive(cached.timestamp)
            # Check if it matches filters
            match = True
            if normalized_start and cached_ts and cached_ts < normalized_start:
                match = False
            if normalized_end and cached_ts and cached_ts > normalized_end:
                match = False
            
            if match:
                cached_readings.append(cached)

        try:
            rows = await asyncio.to_thread(
                postgres_service.get_sensor_readings,
                device_id,
                start_time,
                end_time,
                skip,
                limit,
            )
            db_readings = [SensorReading(**row) for row in rows]
            # Merge and deduplicate (by ID)
            seen_ids = {r.id for r in cached_readings}
            for r in db_readings:
                if r.id not in seen_ids:
                    cached_readings.append(r)
            
            # Sort by timestamp descending
            cached_readings.sort(key=lambda x: self._to_utc_naive(x.timestamp) or datetime.min, reverse=True)
            return cached_readings[skip : skip + limit]
        except Exception as e:
            print(f"❌ [SensorService] PostgreSQL range read failed for {device_id}: {e}")
            return cached_readings[skip : skip + limit]

    async def get_hourly_average_readings(self, device_id: str) -> Dict[str, float]:
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        try:
            rows = await asyncio.to_thread(
                postgres_service.get_sensor_readings_for_range,
                device_id,
                one_hour_ago,
                datetime.utcnow(),
            )
            readings = [SensorReading(**row) for row in rows]
            return self._build_summary_from_readings(device_id, readings, count_override=len(readings), include_date=False)
        except Exception as e:
            print(f"❌ [SensorService] PostgreSQL hourly summary failed for {device_id}: {e}")
            return {
                "device_id": device_id,
                "soil_moisture_avg": 0.0,
                "temperature_avg": 0.0,
                "humidity_avg": 0.0,
                "light_level_avg": 0.0,
                "count": 0
            }

    async def get_daily_summary_readings(self, device_id: str, date: Optional[datetime.date] = None) -> Dict[str, Any]:
        now_utc = datetime.utcnow()
        if date is None:
            # Default to today's date in UTC
            start_of_day = datetime(now_utc.year, now_utc.month, now_utc.day, 0, 0, 0, tzinfo=timezone.utc)
            end_of_day = start_of_day + timedelta(days=1)
        else:
            start_of_day = datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=timezone.utc)
            end_of_day = start_of_day + timedelta(days=1)

        try:
            rows = await asyncio.to_thread(
                postgres_service.get_sensor_readings_for_range,
                device_id,
                start_of_day,
                end_of_day,
            )
            readings = [SensorReading(**row) for row in rows]
            return self._build_daily_summary_from_readings(device_id, readings, date if date else now_utc.date())
        except Exception as e:
            print(f"❌ [SensorService] PostgreSQL daily summary failed for {device_id}: {e}")
            return self._empty_daily_summary(device_id, date if date else now_utc.date())

    async def simulate_irrigation_effect(self, device_id: str, duration_seconds: int) -> Optional[SensorReading]:
        # Fetch the latest reading to base the simulation on
        latest_reading = await self.get_latest_sensor_reading(device_id)
        
        if not latest_reading:
            print(f"WARNING: Cannot simulate irrigation effect for device {device_id}: no latest reading found.")
            return None
        
        # Calculate soil moisture increase: example 5-8% increase per 120s (2 minutes)
        increase_per_second = random.uniform(0.041, 0.066)
        
        current_moisture = latest_reading.soil_moisture if latest_reading.soil_moisture is not None else 30.0
        simulated_moisture_increase = increase_per_second * duration_seconds
        
        new_soil_moisture = min(100.0, current_moisture + simulated_moisture_increase)
        
        # Other values can be slightly randomized or kept the same
        new_temperature = round((latest_reading.temperature or 25.0) + random.uniform(-1.0, 1.0), 2)
        new_humidity = round((latest_reading.humidity or 50.0) + random.uniform(-2.0, 2.0), 2)
        new_light_level = round((latest_reading.light_level or 500.0) + random.uniform(-10.0, 10.0), 2)

        simulated_reading_create = SensorReadingCreate(
            device_id=device_id,
            soil_moisture=new_soil_moisture,
            temperature=new_temperature,
            humidity=new_humidity,
            light_level=new_light_level,
            timestamp=datetime.utcnow() + timedelta(seconds=1)
        )
        
        print(f"Simulating irrigation effect for device {device_id}: moisture increased from {current_moisture:.2f}% to {new_soil_moisture:.2f}% over {duration_seconds} seconds.")
        return await self.create_sensor_reading(device_id, simulated_reading_create)

    def _build_summary_from_readings(
        self,
        device_id: str,
        readings: List[SensorReading],
        *,
        count_override: Optional[int] = None,
        include_date: bool = False,
    ) -> Dict[str, Any]:
        soil_moisture_values = [r.soil_moisture for r in readings if r.soil_moisture is not None]
        temperature_values = [r.temperature for r in readings if r.temperature is not None]
        humidity_values = [r.humidity for r in readings if r.humidity is not None]
        light_level_values = [r.light_level for r in readings if r.light_level is not None]
        count = count_override if count_override is not None else len(readings)

        if count > 0:
            return {
                "device_id": device_id,
                "soil_moisture_avg": round(sum(soil_moisture_values) / len(soil_moisture_values), 2) if soil_moisture_values else 0.0,
                "temperature_avg": round(sum(temperature_values) / len(temperature_values), 2) if temperature_values else 0.0,
                "humidity_avg": round(sum(humidity_values) / len(humidity_values), 2) if humidity_values else 0.0,
                "light_level_avg": round(sum(light_level_values) / len(light_level_values), 2) if light_level_values else 0.0,
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

    def _build_daily_summary_from_readings(self, device_id: str, readings: List[SensorReading], summary_date: datetime.date) -> Dict[str, Any]:
        soil_moisture_values = [r.soil_moisture for r in readings if r.soil_moisture is not None]
        temperature_values = [r.temperature for r in readings if r.temperature is not None]
        humidity_values = [r.humidity for r in readings if r.humidity is not None]
        light_level_values = [r.light_level for r in readings if r.light_level is not None]

        return {
            "device_id": device_id,
            "date": summary_date.isoformat(),
            "count": len(readings),
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

    def _empty_daily_summary(self, device_id: str, summary_date: datetime.date) -> Dict[str, Any]:
        return {
            "device_id": device_id,
            "date": summary_date.isoformat(),
            "count": 0,
            "soil_moisture": {"min": 0.0, "max": 0.0, "avg": 0.0},
            "temperature": {"min": 0.0, "max": 0.0, "avg": 0.0},
            "humidity": {"min": 0.0, "max": 0.0, "avg": 0.0},
            "light_level": {"min": 0.0, "max": 0.0, "avg": 0.0}
        }


# Initialize the service
sensor_service = SensorService()
