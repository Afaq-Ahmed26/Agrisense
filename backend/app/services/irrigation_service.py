import asyncio
from datetime import datetime
from typing import List, Optional
from app.services.firebase_service import firebase_service
from app.services.sensor_service import sensor_service # Added
from app.models.irrigation import IrrigationEvent, IrrigationEventCreate, IrrigationSchedule, IrrigationScheduleCreate, ControlState

class IrrigationService:
    def __init__(self):
        self.db = firebase_service.db

    async def create_irrigation_schedule(self, schedule_create: IrrigationScheduleCreate) -> IrrigationSchedule:
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
        doc_ref = self.db.collection('irrigation_schedules').document(schedule_id)
        await asyncio.to_thread(doc_ref.set, new_schedule.dict())
        return new_schedule
    
    async def get_irrigation_schedules(self, device_id: Optional[str] = None) -> List[IrrigationSchedule]:
        query = self.db.collection('irrigation_schedules')
        if device_id:
            query = query.where('device_id', '==', device_id)
        
        docs = await asyncio.to_thread(lambda: query.get())
        return [IrrigationSchedule(**doc.to_dict()) for doc in docs]

    async def create_irrigation_event(self, event_create: IrrigationEventCreate) -> IrrigationEvent:
        event_id = f"event_{datetime.utcnow().timestamp()}"
        new_event = IrrigationEvent(
            id=event_id,
            device_id=event_create.device_id,
            start_time=event_create.start_time,
            end_time=event_create.end_time,
            duration_actual_seconds=event_create.duration_actual_seconds, # Changed to seconds
            status=event_create.status,
            temperature=event_create.temperature,
            humidity=event_create.humidity,
            soil_moisture=event_create.soil_moisture,
            light_level=event_create.light_level,
            user_triggered=event_create.user_triggered, # Added user_triggered
            created_at=datetime.utcnow()
        )
        doc_ref = self.db.collection('irrigation_events').document(event_id)
        await asyncio.to_thread(doc_ref.set, new_event.dict())

        # --- NEW CODE: Simulate irrigation effect ---
        if new_event.duration_actual_seconds is not None and new_event.duration_actual_seconds > 0:
            print(f"Irrigation event created for device {new_event.device_id}. Simulating effect for {new_event.duration_actual_seconds} seconds.")
            # Call sensor_service to simulate the effect, passing seconds directly
            await sensor_service.simulate_irrigation_effect(new_event.device_id, new_event.duration_actual_seconds)
        # --- END NEW CODE ---

        return new_event

    async def get_irrigation_events(self, device_id: Optional[str] = None, limit: int = 100) -> List[IrrigationEvent]:
        query = self.db.collection('irrigation_events')
        if device_id:
            query = query.where('device_id', '==', device_id)
        query = query.order_by('created_at', direction='DESCENDING').limit(limit)
        
        docs = await asyncio.to_thread(lambda: query.get())
        return [IrrigationEvent(**doc.to_dict()) for doc in docs]

    async def stop_irrigation_event(self, device_id: str) -> Optional[IrrigationEvent]:
        """
        Finds the most recent active irrigation event for a device and stops it.
        """
        query = self.db.collection('irrigation_events') \
            .where('device_id', '==', device_id) \
            .where('status', '==', 'active') \
            .order_by('start_time', direction='DESCENDING') \
            .limit(1)
        
        docs = await asyncio.to_thread(lambda: query.get())
        
        if not docs:
            return None # No active event found
        
        active_event_doc = docs[0]
        event_id = active_event_doc.id
        
        update_data = {
            "status": "stopped",
            "end_time": datetime.utcnow(),
            "updated_at": datetime.utcnow() # Assuming updated_at field exists in model
        }
        
        doc_ref = self.db.collection('irrigation_events').document(event_id)
        await asyncio.to_thread(doc_ref.update, update_data)
        
        updated_event_doc = await asyncio.to_thread(doc_ref.get)
        return IrrigationEvent(**updated_event_doc.to_dict())

    # --- NEW CODE: Control State Management ---
    CONTROL_STATE_COLLECTION = "irrigation_control"
    CONTROL_STATE_DOCUMENT_ID_PREFIX = "control_state_"

    async def get_control_state(self, device_id: str) -> ControlState:
        doc_ref = self.db.collection(self.CONTROL_STATE_COLLECTION).document(f"{self.CONTROL_STATE_DOCUMENT_ID_PREFIX}{device_id}")
        doc = await asyncio.to_thread(doc_ref.get)
        if doc.exists:
            return ControlState(**doc.to_dict())
        # Return a default state if no document exists
        return ControlState(device_id=device_id)

    async def update_control_state(self, control_state: ControlState) -> ControlState:
        doc_ref = self.db.collection(self.CONTROL_STATE_COLLECTION).document(f"{self.CONTROL_STATE_DOCUMENT_ID_PREFIX}{control_state.device_id}")
        # Update last_change_time whenever the state is updated
        control_state.last_change_time = datetime.utcnow()
        await asyncio.to_thread(doc_ref.set, control_state.model_dump())
        return control_state
    # --- END NEW CODE ---


# Initialize the service
irrigation_service = IrrigationService()
