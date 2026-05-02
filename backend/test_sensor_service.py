import asyncio
from datetime import datetime

import app.services.sensor_service as sensor_service_mod
from app.services.sensor_service import SensorService


class FakeSnapshot:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return self._data


class FakeQueryWithGet:
    def __init__(self, snapshots):
        self._snapshots = snapshots

    def where(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def get(self):
        return self._snapshots


class FakeQueryWithStream:
    def __init__(self, snapshots):
        self._snapshots = snapshots

    def where(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def stream(self):
        return iter(self._snapshots)


class FakeDB:
    def __init__(self, query):
        self._query = query

    def collection(self, name):
        return self._query


def test_get_latest_sensor_reading_uses_bound_get(monkeypatch):
    service = SensorService()
    service.db = FakeDB(
        FakeQueryWithGet([
            FakeSnapshot({
                "device_id": "device-1",
                "timestamp": datetime.utcnow(),
                "temperature": 20.0,
                "humidity": 40.0,
                "light_level": 100.0,
                "soil_moisture": 30.0,
                "id": "reading-1",
            })
        ])
    )
    monkeypatch.setattr(sensor_service_mod.postgres_service, "enabled", False)

    reading = asyncio.run(service.get_latest_sensor_reading("device-1"))

    assert reading is not None
    assert reading.device_id == "device-1"
    assert float(reading.temperature) == 20.0


def test_get_latest_sensor_reading_falls_back_to_stream(monkeypatch):
    service = SensorService()
    service.db = FakeDB(
        FakeQueryWithStream([
            FakeSnapshot({
                "device_id": "device-1",
                "timestamp": datetime.utcnow(),
                "temperature": 21.0,
                "humidity": 45.0,
                "light_level": 120.0,
                "soil_moisture": 35.0,
                "id": "reading-2",
            })
        ])
    )
    monkeypatch.setattr(sensor_service_mod.postgres_service, "enabled", False)

    reading = asyncio.run(service.get_latest_sensor_reading("device-1"))

    assert reading is not None
    assert reading.device_id == "device-1"
    assert float(reading.temperature) == 21.0
