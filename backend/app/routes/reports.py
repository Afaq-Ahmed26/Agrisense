import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import APIRouter, Depends

from app.dependencies import (
    ASSIGNED_DEVICE_ROLES,
    ensure_device_access,
    get_assigned_device_ids,
    get_current_user,
    normalize_role,
)
from app.models.user import User
from app.services.postgres_service import postgres_service
from app.services.sensor_service import sensor_service


router = APIRouter()


def _format_report_response(rows: List[dict], label_format: str) -> Dict[str, List]:
    labels: List[str] = []
    soil_moisture: List[float] = []
    temperature: List[float] = []
    humidity: List[float] = []
    light_level: List[float] = []

    for row in rows:
        bucket = row.get("bucket")
        if isinstance(bucket, datetime):
            labels.append(bucket.strftime(label_format))
        else:
            labels.append(str(bucket))

        soil_moisture.append(round(float(row["soil_moisture"]), 2) if row.get("soil_moisture") is not None else None)
        temperature.append(round(float(row["temperature"]), 2) if row.get("temperature") is not None else None)
        humidity.append(round(float(row["humidity"]), 2) if row.get("humidity") is not None else None)
        light_level.append(round(float(row["light_level"]), 2) if row.get("light_level") is not None else None)

    return {
        "labels": labels,
        "soil_moisture": soil_moisture,
        "temperature": temperature,
        "humidity": humidity,
        "light_level": light_level,
    }


def _aggregate_readings(readings, bucket_kind: str) -> Dict[str, List]:
    grouped = {}
    for reading in readings:
        ts = reading.timestamp
        if bucket_kind == "hour":
            key = ts.replace(minute=0, second=0, microsecond=0)
        else:
            key = ts.replace(hour=0, minute=0, second=0, microsecond=0)

        grouped.setdefault(
            key,
            {"soil_moisture": [], "temperature": [], "humidity": [], "light_level": []},
        )
        if reading.soil_moisture is not None:
            grouped[key]["soil_moisture"].append(reading.soil_moisture)
        if reading.temperature is not None:
            grouped[key]["temperature"].append(reading.temperature)
        if reading.humidity is not None:
            grouped[key]["humidity"].append(reading.humidity)
        if reading.light_level is not None:
            grouped[key]["light_level"].append(reading.light_level)

    rows = []
    for key in sorted(grouped.keys()):
        values = grouped[key]
        rows.append(
            {
                "bucket": key,
                "soil_moisture": (sum(values["soil_moisture"]) / len(values["soil_moisture"])) if values["soil_moisture"] else None,
                "temperature": (sum(values["temperature"]) / len(values["temperature"])) if values["temperature"] else None,
                "humidity": (sum(values["humidity"]) / len(values["humidity"])) if values["humidity"] else None,
                "light_level": (sum(values["light_level"]) / len(values["light_level"])) if values["light_level"] else None,
            }
        )
    return rows


@router.get("/devices")
async def get_report_devices(current_user: User = Depends(get_current_user)):
    devices = await sensor_service.get_devices()

    if normalize_role(current_user.role) in ASSIGNED_DEVICE_ROLES:
        assigned_ids = get_assigned_device_ids(current_user)
        devices = [device for device in devices if device.id in assigned_ids]

    deduped = {}
    for device in devices:
        deduped[device.id] = device
    devices = list(deduped.values())

    if postgres_service.enabled:
        ids_with_data = set(await asyncio.to_thread(postgres_service.get_device_ids_with_sensor_data))
        devices = [d for d in devices if d.id in ids_with_data]
    else:
        devices_with_data = []
        for device in devices:
            latest = await sensor_service.get_latest_sensor_reading(device.id)
            if latest:
                devices_with_data.append(device)
        devices = devices_with_data

    return [
        {"id": device.id, "name": device.name, "location": device.location}
        for device in devices
    ]


@router.get("/daily")
async def get_daily_report(
    device_id: str,
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(current_user, device_id)

    if postgres_service.enabled:
        rows = await asyncio.to_thread(postgres_service.get_daily_report_series, device_id)
        return _format_report_response(rows, "%H:%M")

    start = datetime.utcnow() - timedelta(hours=24)
    readings = await sensor_service.get_sensor_readings(device_id=device_id, start_time=start, limit=10000)
    rows = _aggregate_readings(readings, "hour")
    return _format_report_response(rows, "%H:%M")


@router.get("/weekly")
async def get_weekly_report(
    device_id: str,
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(current_user, device_id)

    if postgres_service.enabled:
        rows = await asyncio.to_thread(postgres_service.get_weekly_report_series, device_id)
        return _format_report_response(rows, "%d %b")

    start = datetime.utcnow() - timedelta(days=7)
    readings = await sensor_service.get_sensor_readings(device_id=device_id, start_time=start, limit=10000)
    rows = _aggregate_readings(readings, "day")
    return _format_report_response(rows, "%d %b")


@router.get("/monthly")
async def get_monthly_report(
    device_id: str,
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(current_user, device_id)

    if postgres_service.enabled:
        rows = await asyncio.to_thread(postgres_service.get_monthly_report_series, device_id)
        return _format_report_response(rows, "%d %b")

    start = datetime.utcnow() - timedelta(days=30)
    readings = await sensor_service.get_sensor_readings(device_id=device_id, start_time=start, limit=20000)
    rows = _aggregate_readings(readings, "day")
    return _format_report_response(rows, "%d %b")
