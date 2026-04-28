import json
from datetime import datetime
from typing import List, Optional

from app.models.user import User
from app.services.postgres_service import postgres_service


class UserRepository:
    def is_enabled(self) -> bool:
        return postgres_service.enabled

    def get_by_id(self, user_id: str, include_deleted: bool = False) -> Optional[User]:
        where = "id = %s"
        params = [user_id]
        if not include_deleted:
            where += " AND is_deleted = FALSE"

        row = postgres_service.execute(
            f"""
            SELECT id, email, username, role, full_name, assigned_device_ids,
                   dashboard_preferences, created_at, updated_at, is_active, is_deleted, deleted_at
            FROM users
            WHERE {where}
            LIMIT 1;
            """,
            tuple(params),
            fetchone=True,
        )
        if not row:
            return None
        return self._to_model(dict(row))

    def get_all(self, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[User]:
        where = "" if include_deleted else "WHERE is_deleted = FALSE"
        rows = postgres_service.execute(
            f"""
            SELECT id, email, username, role, full_name, assigned_device_ids,
                   dashboard_preferences, created_at, updated_at, is_active, is_deleted, deleted_at
            FROM users
            {where}
            ORDER BY created_at ASC
            OFFSET %s
            LIMIT %s;
            """,
            (skip, limit),
            fetchall=True,
        ) or []
        return [self._to_model(dict(row)) for row in rows]

    def create(self, user: User) -> User:
        postgres_service.execute(
            """
            INSERT INTO users (
                id, email, username, role, full_name, assigned_device_ids,
                dashboard_preferences, created_at, updated_at, is_active, is_deleted, deleted_at
            )
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                email = EXCLUDED.email,
                username = EXCLUDED.username,
                role = EXCLUDED.role,
                full_name = EXCLUDED.full_name,
                assigned_device_ids = EXCLUDED.assigned_device_ids,
                dashboard_preferences = EXCLUDED.dashboard_preferences,
                updated_at = EXCLUDED.updated_at,
                is_active = EXCLUDED.is_active,
                is_deleted = EXCLUDED.is_deleted,
                deleted_at = EXCLUDED.deleted_at;
            """,
            (
                user.id,
                user.email,
                user.username,
                user.role,
                user.full_name,
                json.dumps(user.assigned_device_ids or []),
                json.dumps(user.dashboard_preferences or []),
                user.created_at,
                user.updated_at,
                user.is_active,
                user.is_deleted,
                user.deleted_at,
            ),
        )
        return user

    def update(self, user_id: str, update_data: dict) -> Optional[User]:
        if not update_data:
            return self.get_by_id(user_id, include_deleted=True)

        field_map = {
            "email": "email",
            "username": "username",
            "role": "role",
            "full_name": "full_name",
            "assigned_device_ids": "assigned_device_ids",
            "dashboard_preferences": "dashboard_preferences",
            "is_active": "is_active",
            "is_deleted": "is_deleted",
            "deleted_at": "deleted_at",
            "updated_at": "updated_at",
        }

        clauses = []
        params = []
        for key, value in update_data.items():
            column = field_map.get(key)
            if not column:
                continue
            if column in {"assigned_device_ids", "dashboard_preferences"}:
                clauses.append(f"{column} = %s::jsonb")
                params.append(json.dumps(value or []))
            else:
                clauses.append(f"{column} = %s")
                params.append(value)

        if "updated_at" not in update_data:
            clauses.append("updated_at = %s")
            params.append(datetime.utcnow())

        if not clauses:
            return self.get_by_id(user_id, include_deleted=True)

        params.append(user_id)
        postgres_service.execute(
            f"""
            UPDATE users
            SET {", ".join(clauses)}
            WHERE id = %s;
            """,
            tuple(params),
        )
        return self.get_by_id(user_id, include_deleted=True)

    def get_by_email(self, email: str, include_deleted: bool = False) -> Optional[User]:
        where = "email = %s"
        params = [email.lower()]
        if not include_deleted:
            where += " AND is_deleted = FALSE"

        row = postgres_service.execute(
            f"""
            SELECT id, email, username, role, full_name, assigned_device_ids,
                   dashboard_preferences, created_at, updated_at, is_active, is_deleted, deleted_at
            FROM users
            WHERE {where}
            LIMIT 1;
            """,
            tuple(params),
            fetchone=True,
        )
        if not row:
            return None
        return self._to_model(dict(row))

    @staticmethod
    def _to_model(row: dict) -> User:
        assigned = row.get("assigned_device_ids") or []
        dashboard_preferences = row.get("dashboard_preferences") or []
        if isinstance(assigned, str):
            assigned = json.loads(assigned)
        if isinstance(dashboard_preferences, str):
            dashboard_preferences = json.loads(dashboard_preferences)
        row["assigned_device_ids"] = assigned
        row["dashboard_preferences"] = dashboard_preferences
        return User(**row)


user_repository = UserRepository()

