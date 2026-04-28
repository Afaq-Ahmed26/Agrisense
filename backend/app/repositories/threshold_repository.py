from datetime import datetime
from typing import Optional

from app.models.thresholds import AlertThresholds
from app.services.postgres_service import postgres_service


class ThresholdRepository:
    def is_enabled(self) -> bool:
        return postgres_service.enabled

    def get_alert_thresholds(self) -> Optional[AlertThresholds]:
        row = postgres_service.execute(
            """
            SELECT soil_moisture_low, soil_moisture_critical, temperature_high, temperature_critical,
                   humidity_low, humidity_high
            FROM thresholds
            WHERE scope = 'global'
            LIMIT 1;
            """,
            fetchone=True,
        )
        if not row:
            return None
        return AlertThresholds(**dict(row))

    def upsert_alert_thresholds(self, thresholds: AlertThresholds) -> AlertThresholds:
        postgres_service.execute(
            """
            INSERT INTO thresholds (
                scope, soil_moisture_low, soil_moisture_critical, temperature_high,
                temperature_critical, humidity_low, humidity_high, updated_at
            )
            VALUES ('global', %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (scope) DO UPDATE SET
                soil_moisture_low = EXCLUDED.soil_moisture_low,
                soil_moisture_critical = EXCLUDED.soil_moisture_critical,
                temperature_high = EXCLUDED.temperature_high,
                temperature_critical = EXCLUDED.temperature_critical,
                humidity_low = EXCLUDED.humidity_low,
                humidity_high = EXCLUDED.humidity_high,
                updated_at = EXCLUDED.updated_at;
            """,
            (
                thresholds.soil_moisture_low,
                thresholds.soil_moisture_critical,
                thresholds.temperature_high,
                thresholds.temperature_critical,
                thresholds.humidity_low,
                thresholds.humidity_high,
                datetime.utcnow(),
            ),
        )
        return thresholds


threshold_repository = ThresholdRepository()

