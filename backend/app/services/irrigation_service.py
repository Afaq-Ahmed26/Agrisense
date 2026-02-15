from datetime import datetime
from typing import List, Optional
from app.services.firebase_service import firebase_service
from app.services.sensor_service import sensor_service # Added
from app.models.irrigation import IrrigationEvent, IrrigationEventCreate, IrrigationSchedule, IrrigationScheduleCreate

class IrrigationService:
    def __init__(self):
        self.db = firebase_service.db

    def create_irrigation_schedule(self, schedule_create: IrrigationScheduleCreate) -> IrrigationSchedule:
        schedule_id = f"schedule_{datetime.utcnow().timestamp()}"
        new_schedule = IrrigationSchedule(
            id=schedule_id,
            device_id=schedule_create.device_id,
            start_time=schedule_create.start_time,
            duration_minutes=schedule_create.duration_minutes,
            is_recurring=schedule_create.is_recurring,
            recurrence_pattern=schedule_create.recurrence_pattern,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        self.db.collection('irrigation_schedules').document(schedule_id).set(new_schedule.dict())
        return new_schedule
    
    def get_irrigation_schedules(self, device_id: Optional[str] = None) -> List[IrrigationSchedule]:
        query = self.db.collection('irrigation_schedules')
        if device_id:
            query = query.where('device_id', '==', device_id)
        docs = query.get()
        return [IrrigationSchedule(**doc.to_dict()) for doc in docs]

    def create_irrigation_event(self, event_create: IrrigationEventCreate) -> IrrigationEvent:
        event_id = f"event_{datetime.utcnow().timestamp()}"
        new_event = IrrigationEvent(
            id=event_id,
            device_id=event_create.device_id,
            start_time=event_create.start_time,
            end_time=event_create.end_time,
            duration_actual_minutes=event_create.duration_actual_minutes,
            status=event_create.status,
            temperature=event_create.temperature,
            humidity=event_create.humidity,
            soil_moisture=event_create.soil_moisture,
            light_level=event_create.light_level,
            created_at=datetime.utcnow()
        )
        self.db.collection('irrigation_events').document(event_id).set(new_event.dict())

        # --- NEW CODE: Simulate irrigation effect ---
        if new_event.duration_actual_minutes and new_event.duration_actual_minutes > 0:
            print(f"Irrigation event created for device {new_event.device_id}. Simulating effect for {new_event.duration_actual_minutes} minutes.")
            # Call sensor_service to simulate the effect
            sensor_service.simulate_irrigation_effect(new_event.device_id, new_event.duration_actual_minutes)
        # --- END NEW CODE ---

        return new_event

    def get_irrigation_events(self, device_id: Optional[str] = None, limit: int = 100) -> List[IrrigationEvent]:
        query = self.db.collection('irrigation_events')
        if device_id:
            query = query.where('device_id', '==', device_id)
        query = query.order_by('created_at', direction='DESCENDING').limit(limit)
        docs = query.get()
        return [IrrigationEvent(**doc.to_dict()) for doc in docs]


# Initialize the service
irrigation_service = IrrigationService()
