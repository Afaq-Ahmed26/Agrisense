import os
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from app.config import settings

try:
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import RealDictCursor
except Exception:  # pragma: no cover - handled via enabled flag
    psycopg2 = None
    pool = None
    RealDictCursor = None


class PostgresService:
    def __init__(self) -> None:
        self.enabled = bool(settings.DATABASE_URL and pool is not None)
        self._pool: Optional[pool.SimpleConnectionPool] = None

        if not self.enabled:
            return

        try:
            self._pool = pool.SimpleConnectionPool(
                minconn=int(os.getenv("PG_MIN_CONN", "1")),
                maxconn=int(os.getenv("PG_MAX_CONN", "8")),
                dsn=settings.DATABASE_URL,
            )
            self._init_schema()
            print("✅ PostgreSQL initialized successfully.")
        except Exception as exc:
            print(f"❌ PostgreSQL initialization failed: {exc}")
            self.enabled = False
            self._pool = None

    def _with_connection(self):
        if not self._pool:
            raise RuntimeError("PostgreSQL connection pool is not initialized.")
        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)

    def _init_schema(self) -> None:
        ddl_statements = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'farmer',
                full_name TEXT,
                assigned_device_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
                dashboard_preferences JSONB NOT NULL DEFAULT '[]'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                deleted_at TIMESTAMPTZ
            );
            """,
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);",
            "CREATE INDEX IF NOT EXISTS idx_users_is_deleted ON users (is_deleted);",
            """
            CREATE TABLE IF NOT EXISTS devices (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT,
                owner_id TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'irrigation_device',
                zone_id TEXT,
                crop_type TEXT,
                area_size DOUBLE PRECISION,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                pairing_code TEXT,
                pairing_code_generated_at TIMESTAMPTZ,
                pairing_code_expires_at TIMESTAMPTZ,
                pairing_code_generated_by TEXT
            );
            """,
            "CREATE INDEX IF NOT EXISTS idx_devices_owner ON devices (owner_id);",
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                device_id TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                acknowledged_by TEXT,
                acknowledged_at TIMESTAMPTZ,
                resolved_by TEXT,
                resolved_at TIMESTAMPTZ
            );
            """,
            "CREATE INDEX IF NOT EXISTS idx_alerts_device_status ON alerts (device_id, status);",
            "CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts (timestamp DESC);",
            """
            CREATE TABLE IF NOT EXISTS thresholds (
                scope TEXT PRIMARY KEY,
                soil_moisture_low DOUBLE PRECISION NOT NULL DEFAULT 30.0,
                soil_moisture_critical DOUBLE PRECISION NOT NULL DEFAULT 20.0,
                temperature_high DOUBLE PRECISION NOT NULL DEFAULT 40.0,
                temperature_critical DOUBLE PRECISION NOT NULL DEFAULT 45.0,
                humidity_low DOUBLE PRECISION NOT NULL DEFAULT 20.0,
                humidity_high DOUBLE PRECISION NOT NULL DEFAULT 85.0,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS activity_logs (
                id TEXT PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                details JSONB
            );
            """,
            "CREATE INDEX IF NOT EXISTS idx_activity_logs_user_time ON activity_logs (user_id, timestamp DESC);",
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                is_read BOOLEAN NOT NULL DEFAULT FALSE,
                is_archived BOOLEAN NOT NULL DEFAULT FALSE,
                updated_at TIMESTAMPTZ
            );
            """,
            "CREATE INDEX IF NOT EXISTS idx_notifications_user_time ON notifications (user_id, created_at DESC);",
            """
            CREATE TABLE IF NOT EXISTS device_otps (
                id TEXT PRIMARY KEY,
                device_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                email TEXT NOT NULL,
                otp_hash TEXT NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                blocked BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            );
            """,
            "CREATE INDEX IF NOT EXISTS idx_device_otps_expires_at ON device_otps (expires_at);",
            """
            CREATE TABLE IF NOT EXISTS irrigation_schedules (
                id TEXT PRIMARY KEY,
                device_id TEXT NOT NULL,
                start_time TIMESTAMPTZ NOT NULL,
                duration_minutes INTEGER NOT NULL,
                is_recurring BOOLEAN NOT NULL DEFAULT FALSE,
                recurrence_pattern TEXT,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS device_pairing_codes (
                id TEXT PRIMARY KEY,
                device_id TEXT NOT NULL,
                pairing_code TEXT NOT NULL,
                generated_by TEXT NOT NULL,
                generated_at TIMESTAMPTZ NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                claimed_by TEXT,
                claimed_at TIMESTAMPTZ
            );
            """,
            "CREATE INDEX IF NOT EXISTS idx_pairing_code_device ON device_pairing_codes (device_id);",
            """
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id TEXT PRIMARY KEY,
                device_id TEXT NOT NULL,
                soil_moisture DOUBLE PRECISION,
                temperature DOUBLE PRECISION,
                humidity DOUBLE PRECISION,
                light_level DOUBLE PRECISION,
                timestamp TIMESTAMPTZ NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_sensor_readings_device_timestamp
            ON sensor_readings (device_id, timestamp DESC);
            """,
            """
            CREATE TABLE IF NOT EXISTS irrigation_events (
                id TEXT PRIMARY KEY,
                device_id TEXT NOT NULL,
                start_time TIMESTAMPTZ NOT NULL,
                end_time TIMESTAMPTZ,
                duration_actual_seconds INTEGER,
                status TEXT NOT NULL DEFAULT 'pending',
                temperature DOUBLE PRECISION,
                humidity DOUBLE PRECISION,
                soil_moisture DOUBLE PRECISION,
                light_level DOUBLE PRECISION,
                user_triggered BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_irrigation_events_device_created
            ON irrigation_events (device_id, created_at DESC);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_irrigation_events_status
            ON irrigation_events (status);
            """,
            """
            CREATE TABLE IF NOT EXISTS irrigation_control_states (
                device_id TEXT PRIMARY KEY,
                mode TEXT NOT NULL DEFAULT 'AUTO',
                pump_state BOOLEAN NOT NULL DEFAULT FALSE,
                threshold DOUBLE PRECISION NOT NULL DEFAULT 30.0,
                last_change_time TIMESTAMPTZ
            );
            """,
        ]

        for statement in ddl_statements:
            self.execute(statement)

    def execute(
        self,
        query: str,
        params: Optional[tuple] = None,
        *,
        fetchone: bool = False,
        fetchall: bool = False,
    ) -> Any:
        if not self.enabled:
            return None

        for conn in self._with_connection():
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                result = None
                if fetchone:
                    result = cur.fetchone()
                elif fetchall:
                    result = cur.fetchall()
                conn.commit()
                return result

    def save_sensor_reading(self, reading: Dict[str, Any]) -> None:
        self.execute(
            """
            INSERT INTO sensor_readings
                (id, device_id, soil_moisture, temperature, humidity, light_level, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
            """,
            (
                reading["id"],
                reading["device_id"],
                reading.get("soil_moisture"),
                reading.get("temperature"),
                reading.get("humidity"),
                reading.get("light_level"),
                reading["timestamp"],
            ),
        )

    def get_latest_sensor_reading(self, device_id: str) -> Optional[Dict[str, Any]]:
        row = self.execute(
            """
            SELECT id, device_id, soil_moisture, temperature, humidity, light_level, timestamp
            FROM sensor_readings
            WHERE device_id = %s
            ORDER BY timestamp DESC
            LIMIT 1;
            """,
            (device_id,),
            fetchone=True,
        )
        return dict(row) if row else None

    def get_sensor_readings(
        self,
        device_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        where_clauses = ["device_id = %s"]
        params: List[Any] = [device_id]

        if start_time:
            where_clauses.append("timestamp >= %s")
            params.append(start_time)
        if end_time:
            where_clauses.append("timestamp <= %s")
            params.append(end_time)

        params.extend([limit, skip])

        rows = self.execute(
            f"""
            SELECT id, device_id, soil_moisture, temperature, humidity, light_level, timestamp
            FROM sensor_readings
            WHERE {' AND '.join(where_clauses)}
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s;
            """,
            tuple(params),
            fetchall=True,
        )
        return [dict(row) for row in (rows or [])]

    def get_sensor_readings_for_range(
        self,
        device_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Dict[str, Any]]:
        rows = self.execute(
            """
            SELECT id, device_id, soil_moisture, temperature, humidity, light_level, timestamp
            FROM sensor_readings
            WHERE device_id = %s
              AND timestamp >= %s
              AND timestamp < %s
            ORDER BY timestamp ASC;
            """,
            (device_id, start_time, end_time),
            fetchall=True,
        )
        return [dict(row) for row in (rows or [])]

    def save_irrigation_event(self, event: Dict[str, Any]) -> None:
        self.execute(
            """
            INSERT INTO irrigation_events
                (id, device_id, start_time, end_time, duration_actual_seconds, status,
                 temperature, humidity, soil_moisture, light_level, user_triggered, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                end_time = EXCLUDED.end_time,
                duration_actual_seconds = EXCLUDED.duration_actual_seconds,
                status = EXCLUDED.status,
                temperature = EXCLUDED.temperature,
                humidity = EXCLUDED.humidity,
                soil_moisture = EXCLUDED.soil_moisture,
                light_level = EXCLUDED.light_level,
                user_triggered = EXCLUDED.user_triggered;
            """,
            (
                event["id"],
                event["device_id"],
                event["start_time"],
                event.get("end_time"),
                event.get("duration_actual_seconds"),
                event.get("status", "pending"),
                event.get("temperature"),
                event.get("humidity"),
                event.get("soil_moisture"),
                event.get("light_level"),
                bool(event.get("user_triggered", False)),
                event.get("created_at"),
            ),
        )

    def get_irrigation_events(self, device_id: Optional[str], limit: int) -> List[Dict[str, Any]]:
        if device_id:
            rows = self.execute(
                """
                SELECT *
                FROM irrigation_events
                WHERE device_id = %s
                ORDER BY created_at DESC
                LIMIT %s;
                """,
                (device_id, limit),
                fetchall=True,
            )
        else:
            rows = self.execute(
                """
                SELECT *
                FROM irrigation_events
                ORDER BY created_at DESC
                LIMIT %s;
                """,
                (limit,),
                fetchall=True,
            )
        return [dict(row) for row in (rows or [])]

    def stop_latest_active_event(self, device_id: str, end_time: datetime) -> Optional[Dict[str, Any]]:
        row = self.execute(
            """
            UPDATE irrigation_events
            SET status = 'stopped', end_time = %s
            WHERE id = (
                SELECT id
                FROM irrigation_events
                WHERE device_id = %s
                  AND status = 'active'
                ORDER BY start_time DESC
                LIMIT 1
            )
            RETURNING *;
            """,
            (end_time, device_id),
            fetchone=True,
        )
        return dict(row) if row else None

    def get_control_state(self, device_id: str) -> Optional[Dict[str, Any]]:
        row = self.execute(
            """
            SELECT device_id, mode, pump_state, threshold, last_change_time
            FROM irrigation_control_states
            WHERE device_id = %s;
            """,
            (device_id,),
            fetchone=True,
        )
        return dict(row) if row else None

    def upsert_control_state(self, control_state: Dict[str, Any]) -> Dict[str, Any]:
        row = self.execute(
            """
            INSERT INTO irrigation_control_states (device_id, mode, pump_state, threshold, last_change_time)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (device_id) DO UPDATE SET
                mode = EXCLUDED.mode,
                pump_state = EXCLUDED.pump_state,
                threshold = EXCLUDED.threshold,
                last_change_time = EXCLUDED.last_change_time
            RETURNING device_id, mode, pump_state, threshold, last_change_time;
            """,
            (
                control_state["device_id"],
                control_state.get("mode", "AUTO"),
                bool(control_state.get("pump_state", False)),
                float(control_state.get("threshold", 30.0)),
                control_state.get("last_change_time"),
            ),
            fetchone=True,
        )
        return dict(row) if row else control_state

    def get_model_training_dataset(self, device_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT
                sr.device_id,
                sr.soil_moisture,
                sr.temperature,
                sr.humidity,
                sr.light_level,
                ie.duration_actual_seconds AS valve_duration_seconds,
                ie.created_at AS irrigation_timestamp
            FROM irrigation_events ie
            JOIN LATERAL (
                SELECT *
                FROM sensor_readings s
                WHERE s.device_id = ie.device_id
                  AND s.timestamp <= ie.start_time
                ORDER BY s.timestamp DESC
                LIMIT 1
            ) sr ON TRUE
            WHERE ie.duration_actual_seconds IS NOT NULL
        """
        params: List[Any] = []
        if device_id:
            query += " AND ie.device_id = %s"
            params.append(device_id)
        query += " ORDER BY ie.created_at DESC;"
        rows = self.execute(query, tuple(params) if params else None, fetchall=True)
        return [dict(row) for row in (rows or [])]

    def get_device_ids_with_sensor_data(self) -> List[str]:
        rows = self.execute(
            """
            SELECT DISTINCT device_id
            FROM sensor_readings
            ORDER BY device_id ASC;
            """,
            fetchall=True,
        ) or []
        return [str(row["device_id"]) for row in rows if row.get("device_id")]

    def get_daily_report_series(self, device_id: str) -> List[Dict[str, Any]]:
        rows = self.execute(
            """
            WITH buckets AS (
                SELECT generate_series(
                    date_trunc('hour', NOW() - INTERVAL '23 hours'),
                    date_trunc('hour', NOW()),
                    INTERVAL '1 hour'
                ) AS bucket
            ),
            agg AS (
                SELECT
                    date_trunc('hour', timestamp) AS bucket,
                    AVG(soil_moisture) AS soil_moisture,
                    AVG(temperature) AS temperature,
                    AVG(humidity) AS humidity,
                    AVG(light_level) AS light_level
                FROM sensor_readings
                WHERE device_id = %s
                  AND timestamp >= NOW() - INTERVAL '24 hours'
                GROUP BY 1
            )
            SELECT
                buckets.bucket,
                agg.soil_moisture,
                agg.temperature,
                agg.humidity,
                agg.light_level
            FROM buckets
            LEFT JOIN agg ON agg.bucket = buckets.bucket
            ORDER BY buckets.bucket ASC;
            """,
            (device_id,),
            fetchall=True,
        )
        return [dict(row) for row in (rows or [])]

    def get_weekly_report_series(self, device_id: str) -> List[Dict[str, Any]]:
        rows = self.execute(
            """
            WITH buckets AS (
                SELECT generate_series(
                    date_trunc('day', NOW() - INTERVAL '6 days'),
                    date_trunc('day', NOW()),
                    INTERVAL '1 day'
                ) AS bucket
            ),
            agg AS (
                SELECT
                    date_trunc('day', timestamp) AS bucket,
                    AVG(soil_moisture) AS soil_moisture,
                    AVG(temperature) AS temperature,
                    AVG(humidity) AS humidity,
                    AVG(light_level) AS light_level
                FROM sensor_readings
                WHERE device_id = %s
                  AND timestamp >= NOW() - INTERVAL '7 days'
                GROUP BY 1
            )
            SELECT
                buckets.bucket,
                agg.soil_moisture,
                agg.temperature,
                agg.humidity,
                agg.light_level
            FROM buckets
            LEFT JOIN agg ON agg.bucket = buckets.bucket
            ORDER BY buckets.bucket ASC;
            """,
            (device_id,),
            fetchall=True,
        )
        return [dict(row) for row in (rows or [])]

    def get_monthly_report_series(self, device_id: str) -> List[Dict[str, Any]]:
        rows = self.execute(
            """
            WITH buckets AS (
                SELECT generate_series(
                    date_trunc('day', NOW() - INTERVAL '29 days'),
                    date_trunc('day', NOW()),
                    INTERVAL '1 day'
                ) AS bucket
            ),
            agg AS (
                SELECT
                    date_trunc('day', timestamp) AS bucket,
                    AVG(soil_moisture) AS soil_moisture,
                    AVG(temperature) AS temperature,
                    AVG(humidity) AS humidity,
                    AVG(light_level) AS light_level
                FROM sensor_readings
                WHERE device_id = %s
                  AND timestamp >= NOW() - INTERVAL '30 days'
                GROUP BY 1
            )
            SELECT
                buckets.bucket,
                agg.soil_moisture,
                agg.temperature,
                agg.humidity,
                agg.light_level
            FROM buckets
            LEFT JOIN agg ON agg.bucket = buckets.bucket
            ORDER BY buckets.bucket ASC;
            """,
            (device_id,),
            fetchall=True,
        )
        return [dict(row) for row in (rows or [])]


postgres_service = PostgresService()
