import asyncio
from datetime import datetime
from typing import List, Optional
from app.services.postgres_service import postgres_service
from app.services.sensor_service import sensor_service
from app.models.irrigation import IrrigationEvent, IrrigationEventCreate, IrrigationSchedule, IrrigationScheduleCreate, ControlState

class IrrigationService:
    def __init__(self):
        pass

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
        await asyncio.to_thread(postgres_service.save_irrigation_schedule, new_schedule.model_dump())
        return new_schedule
    
    async def get_irrigation_schedules(self, device_id: Optional[str] = None) -> List[IrrigationSchedule]:
        rows = await asyncio.to_thread(postgres_service.get_irrigation_schedules, device_id)
        return [IrrigationSchedule(**row) for row in rows]

    async def create_irrigation_event(self, event_create: IrrigationEventCreate) -> IrrigationEvent:
        event_id = f"event_{datetime.utcnow().timestamp()}"
        new_event = IrrigationEvent(
            id=event_id,
            device_id=event_create.device_id,
            start_time=event_create.start_time,
            end_time=event_create.end_time,
            duration_actual_seconds=event_create.duration_actual_seconds,
            status=event_create.status,
            temperature=event_create.temperature,
            humidity=event_create.humidity,
            soil_moisture=event_create.soil_moisture,
            light_level=event_create.light_level,
            user_triggered=event_create.user_triggered,
            created_at=datetime.utcnow()
        )
        await asyncio.to_thread(postgres_service.save_irrigation_event, new_event.model_dump())

        # Simulate irrigation effect
        if new_event.duration_actual_seconds is not None and new_event.duration_actual_seconds > 0:
            print(f"Irrigation event created for device {new_event.device_id}. Simulating effect for {new_event.duration_actual_seconds} seconds.")
            await sensor_service.simulate_irrigation_effect(new_event.device_id, new_event.duration_actual_seconds)

        return new_event

    async def get_irrigation_events(self, device_id: Optional[str] = None, limit: int = 100) -> List[IrrigationEvent]:
        rows = await asyncio.to_thread(postgres_service.get_irrigation_events, device_id, limit)
        return [IrrigationEvent(**row) for row in rows]

    async def stop_irrigation_event(self, device_id: str) -> Optional[IrrigationEvent]:
        """
        Finds the most recent active irrigation event for a device and stops it.
        """
        row = await asyncio.to_thread(postgres_service.stop_latest_active_event, device_id, datetime.utcnow())
        if not row:
            return None
        return IrrigationEvent(**row)

    async def get_control_state(self, device_id: str) -> ControlState:
        row = await asyncio.to_thread(postgres_service.get_control_state, device_id)
        if row:
            return ControlState(**row)
        return ControlState(device_id=device_id)

    async def update_control_state(self, control_state: ControlState) -> ControlState:
        # Update last_change_time whenever the state is updated
        control_state.last_change_time = datetime.utcnow()
        row = await asyncio.to_thread(postgres_service.upsert_control_state, control_state.model_dump())
        return ControlState(**row)


# Initialize the service
irrigation_service = IrrigationService()
