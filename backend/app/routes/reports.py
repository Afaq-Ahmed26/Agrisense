import asyncio
import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

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


def _aggregate_readings(readings, bucket_kind: str) -> List[dict]:
    def _to_utc_naive(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    grouped = {}
    for reading in readings:
        # Handle both dict and object
        ts = reading["timestamp"] if isinstance(reading, dict) else reading.timestamp
        ts = _to_utc_naive(ts)
        
        if bucket_kind == "hour":
            key = ts.replace(minute=0, second=0, microsecond=0)
        else:
            key = ts.replace(hour=0, minute=0, second=0, microsecond=0)

        grouped.setdefault(
            key,
            {"soil_moisture": [], "temperature": [], "humidity": [], "light_level": []},
        )
        
        val_map = reading if isinstance(reading, dict) else reading.model_dump()
        for field in ["soil_moisture", "temperature", "humidity", "light_level"]:
            if val_map.get(field) is not None:
                grouped[key][field].append(float(val_map[field]))

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

    # Filter to only include devices that actually have data in PostgreSQL
    ids_with_data = set(await asyncio.to_thread(postgres_service.get_device_ids_with_sensor_data))
    if ids_with_data:
        # Combine devices from repository with any other device IDs that have data
        devices_list = []
        existing_ids = set()
        
        for d in devices:
            if d.id in ids_with_data:
                devices_list.append({"id": d.id, "name": d.name, "location": d.location})
                existing_ids.add(d.id)
        
        for device_id in sorted(ids_with_data):
            if device_id not in existing_ids:
                devices_list.append({"id": device_id, "name": f"Device {device_id}", "location": "Unknown"})
        
        return devices_list

    return []


@router.get("/daily")
async def get_daily_report(
    device_id: str,
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(current_user, device_id)
    rows = await asyncio.to_thread(postgres_service.get_daily_report_series, device_id)
    return _format_report_response(rows, "%H:%M")


@router.get("/weekly")
async def get_weekly_report(
    device_id: str,
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(current_user, device_id)
    rows = await asyncio.to_thread(postgres_service.get_weekly_report_series, device_id)
    return _format_report_response(rows, "%d %b")


@router.get("/monthly")
async def get_monthly_report(
    device_id: str,
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(current_user, device_id)
    rows = await asyncio.to_thread(postgres_service.get_monthly_report_series, device_id)
    return _format_report_response(rows, "%d %b")


@router.get("/custom")
async def get_custom_report(
    device_id: str,
    start_date: datetime,
    end_date: datetime,
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(current_user, device_id)

    diff = end_date - start_date
    bucket = "hour" if diff.days <= 2 else "day"
    label_fmt = "%H:%M" if diff.days <= 2 else "%d %b"

    readings = await asyncio.to_thread(postgres_service.get_sensor_readings_for_range, device_id, start_date, end_date)
    rows = _aggregate_readings(readings, bucket)
    return _format_report_response(rows, label_fmt)


@router.get("/export")
async def export_report_csv(
    device_id: str,
    start_date: datetime,
    end_date: datetime,
    current_user: User = Depends(get_current_user),
):
    ensure_device_access(current_user, device_id)

    readings = await asyncio.to_thread(postgres_service.get_sensor_readings_for_range, device_id, start_date, end_date)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "Soil Moisture (%)", "Temperature (C)", "Humidity (%)", "Light Level (lx)"])

    for r in readings:
        ts = r["timestamp"]
        if isinstance(ts, datetime):
            ts = ts.strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([ts, r.get("soil_moisture"), r.get("temperature"), r.get("humidity"), r.get("light_level")])

    output.seek(0)
    filename = f"report_{device_id}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
