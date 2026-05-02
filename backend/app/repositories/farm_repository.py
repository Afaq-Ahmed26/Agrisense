import json
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.models.farm import Farm, FarmCreate, FarmUpdate
from app.services.postgres_service import postgres_service
from app.services.user_service import get_user


class FarmRepository:
    def is_enabled(self) -> bool:
        return postgres_service.enabled

    def create(self, farm: Farm) -> Farm:
        postgres_service.execute(
            """
            INSERT INTO farms (
                id, name, owner_id, assigned_officer_id, assigned_middleman_ids, device_ids, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                owner_id = EXCLUDED.owner_id,
                assigned_officer_id = EXCLUDED.assigned_officer_id,
                assigned_middleman_ids = EXCLUDED.assigned_middleman_ids,
                device_ids = EXCLUDED.device_ids,
                updated_at = EXCLUDED.updated_at;
            """,
            (
                farm.id,
                farm.name,
                farm.owner_id,
                farm.assigned_officer_id,
                json.dumps(farm.assigned_middleman_ids or []),
                json.dumps(farm.device_ids or []),
                farm.created_at,
                farm.updated_at,
            )
        )
        return farm

    def get_by_id(self, farm_id: str) -> Optional[Farm]:
        row = postgres_service.execute(
            """
            SELECT id, name, owner_id, assigned_officer_id, assigned_middleman_ids, device_ids, created_at, updated_at
            FROM farms
            WHERE id = %s
            LIMIT 1;
            """,
            (farm_id,),
            fetchone=True,
        )
        return self._to_model(dict(row)) if row else None

    def get_farms_by_owner(self, owner_id: str) -> List[Farm]:
        rows = postgres_service.execute(
            """
            SELECT id, name, owner_id, assigned_officer_id, assigned_middleman_ids, device_ids, created_at, updated_at
            FROM farms
            WHERE owner_id = %s
            ORDER BY created_at ASC;
            """,
            (owner_id,),
            fetchall=True,
        ) or []
        return [self._to_model(dict(row)) for row in rows]

    def get_farms_assigned_to_officer(self, officer_id: str) -> List[Farm]:
        rows = postgres_service.execute(
            """
            SELECT id, name, owner_id, assigned_officer_id, assigned_middleman_ids, device_ids, created_at, updated_at
            FROM farms
            WHERE assigned_officer_id = %s
            ORDER BY created_at ASC;
            """,
            (officer_id,),
            fetchall=True,
        ) or []
        return [self._to_model(dict(row)) for row in rows]

    def get_farms_assigned_to_middleman(self, middleman_id: str) -> List[Farm]:
        rows = postgres_service.execute(
            """
            SELECT id, name, owner_id, assigned_officer_id, assigned_middleman_ids, device_ids, created_at, updated_at
            FROM farms
            WHERE assigned_middleman_ids @> %s::jsonb
            ORDER BY created_at ASC;
            """,
            (json.dumps([middleman_id]),),
            fetchall=True,
        ) or []
        return [self._to_model(dict(row)) for row in rows]

    def update(self, farm_id: str, update_data: Dict[str, Any]) -> Optional[Farm]:
        if not update_data:
            return self.get_by_id(farm_id)

        field_map = {
            "name": "name",
            "assigned_officer_id": "assigned_officer_id",
            "assigned_middleman_ids": "assigned_middleman_ids",
            "device_ids": "device_ids",
        }

        clauses = []
        params = []
        for key, value in update_data.items():
            column = field_map.get(key)
            if not column:
                continue
            
            if column in {"device_ids", "assigned_middleman_ids"}:
                clauses.append(f"{column} = %s::jsonb")
                params.append(json.dumps(value or []))
            else:
                clauses.append(f"{column} = %s")
                params.append(value)

        clauses.append("updated_at = %s")
        params.append(datetime.utcnow())

        if not clauses:
            return self.get_by_id(farm_id)

        params.append(farm_id)
        postgres_service.execute(
            f"""
            UPDATE farms
            SET {", ".join(clauses)}
            WHERE id = %s;
            """,
            tuple(params),
        )
        return self.get_by_id(farm_id)

    def delete(self, farm_id: str) -> None:
        postgres_service.execute(
            "DELETE FROM farms WHERE id = %s;",
            (farm_id,),
        )

    def _to_model(self, row: dict) -> Farm:
        device_ids = row.get("device_ids") or []
        middleman_ids = row.get("assigned_middleman_ids") or []
        
        if isinstance(device_ids, str):
            device_ids = json.loads(device_ids)
        if isinstance(middleman_ids, str):
            middleman_ids = json.loads(middleman_ids)
            
        row["device_ids"] = device_ids
        row["assigned_middleman_ids"] = middleman_ids
        
        return Farm(**row)


farm_repository = FarmRepository()
