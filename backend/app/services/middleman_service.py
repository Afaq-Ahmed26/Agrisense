import asyncio
from typing import List, Optional
from app.models.user import User
from app.models.farm import Farm
from app.services.user_service import get_user, update_user
from app.repositories.farm_repository import farm_repository


async def assign_middleman_to_farmer(farmer_id: str, middleman_id: str) -> bool:
    """
    Assign a middleman to manage a farmer's farms in PostgreSQL.
    """
    try:
        farmer = await get_user(farmer_id)
        middleman = await get_user(middleman_id)
        
        if not farmer or farmer.is_deleted:
            raise ValueError(f"Farmer {farmer_id} not found or deleted")
        if not middleman or middleman.is_deleted:
            raise ValueError(f"Middleman {middleman_id} not found or deleted")
        if middleman.role not in ['officer', 'middleman']:
            raise ValueError(f"User {middleman_id} must be an officer/middleman to manage farms")
        
        # Update User: add farmer_id to middleman's managed_farmer_ids
        if farmer_id not in (middleman.managed_farmer_ids or []):
            updated_managed = (middleman.managed_farmer_ids or []) + [farmer_id]
            await update_user(middleman_id, {'managed_farmer_ids': updated_managed})
        
        # Get all farms owned by this farmer and add middleman to each
        farms = await asyncio.to_thread(farm_repository.get_farms_by_owner, farmer_id)
        
        for farm in farms:
            assigned_middlemen = farm.assigned_middleman_ids or []
            if middleman_id not in assigned_middlemen:
                assigned_middlemen.append(middleman_id)
                await asyncio.to_thread(farm_repository.update, farm.id, {'assigned_middleman_ids': assigned_middlemen})
        
        return True
    except Exception as e:
        print(f"ERROR: Failed to assign middleman to farmer: {e}")
        return False


async def revoke_middleman_access(farmer_id: str, middleman_id: str) -> bool:
    """
    Revoke middleman's access to a farmer's farms in PostgreSQL.
    """
    try:
        middleman = await get_user(middleman_id)
        if not middleman:
            raise ValueError(f"Middleman {middleman_id} not found")
        
        # Update User: remove farmer_id from middleman's managed_farmer_ids
        managed_farmers = middleman.managed_farmer_ids or []
        if farmer_id in managed_farmers:
            managed_farmers.remove(farmer_id)
            await update_user(middleman_id, {'managed_farmer_ids': managed_farmers})
        
        # Get all farms owned by this farmer and remove middleman
        farms = await asyncio.to_thread(farm_repository.get_farms_by_owner, farmer_id)
        
        for farm in farms:
            updates = {}
            
            # Remove from assigned_middleman_ids list
            assigned_middlemen = farm.assigned_middleman_ids or []
            if middleman_id in assigned_middlemen:
                assigned_middlemen.remove(middleman_id)
                updates['assigned_middleman_ids'] = assigned_middlemen
            
            # Clear assigned_officer_id if it matches
            if farm.assigned_officer_id == middleman_id:
                updates['assigned_officer_id'] = None
                
            if updates:
                await asyncio.to_thread(farm_repository.update, farm.id, updates)
        
        return True
    except Exception as e:
        print(f"ERROR: Failed to revoke middleman access: {e}")
        return False


async def get_farmers_for_middleman(middleman_id: str) -> List[User]:
    """
    Get all farmers assigned to a middleman from PostgreSQL.
    Searches both the users table and the farms table for assignments.
    """
    try:
        farmer_ids = set()
        
        # 1. Search in middleman's profile
        middleman = await get_user(middleman_id)
        if middleman and middleman.managed_farmer_ids:
            for f_id in middleman.managed_farmer_ids:
                farmer_ids.add(f_id)
        
        # 2. Search in farms table (where this user is officer or middleman)
        from app.services.postgres_service import postgres_service
        import json
        
        # Find owners of farms where middleman_id is assigned
        rows = postgres_service.execute(
            """
            SELECT DISTINCT owner_id FROM farms 
            WHERE assigned_officer_id = %s OR assigned_middleman_ids @> %s::jsonb;
            """,
            (middleman_id, json.dumps([middleman_id])),
            fetchall=True
        ) or []
        for row in rows:
            farmer_ids.add(row['owner_id'])
        
        farmers = []
        for f_id in farmer_ids:
            farmer = await get_user(f_id)
            if farmer and not farmer.is_deleted:
                farmers.append(farmer)
        
        return farmers
    except Exception as e:
        print(f"ERROR: Failed to get farmers for middleman: {e}")
        return []


async def get_middlemen_for_farmer(farmer_id: str) -> List[User]:
    """
    Get all middlemen assigned to a farmer from PostgreSQL.
    Searches both the farms table and the users table for assignments.
    """
    try:
        middleman_ids = set()
        
        # 1. Search in farms table (both assigned_middleman_ids and assigned_officer_id)
        farms = await asyncio.to_thread(farm_repository.get_farms_by_owner, farmer_id)
        for farm in farms:
            if farm.assigned_officer_id:
                middleman_ids.add(farm.assigned_officer_id)
            for m_id in (farm.assigned_middleman_ids or []):
                middleman_ids.add(m_id)
        
        # 2. Search in users table (middlemen who have this farmer in managed_farmer_ids)
        # We need a repository method for this or use raw execute
        from app.services.postgres_service import postgres_service
        import json
        rows = postgres_service.execute(
            "SELECT id FROM users WHERE managed_farmer_ids @> %s::jsonb AND is_deleted = FALSE;",
            (json.dumps([farmer_id]),),
            fetchall=True
        ) or []
        for row in rows:
            middleman_ids.add(row['id'])
        
        middlemen = []
        for m_id in middleman_ids:
            m_user = await get_user(m_id)
            if m_user and not m_user.is_deleted:
                middlemen.append(m_user)
        
        return middlemen
    except Exception as e:
        print(f"ERROR: Failed to get middlemen for farmer: {e}")
        return []


async def has_middleman_access_to_farm(farm_id: str, middleman_id: str) -> bool:
    """
    Check if a middleman has access to a specific farm in PostgreSQL.
    """
    try:
        farm = await asyncio.to_thread(farm_repository.get_by_id, farm_id)
        if not farm:
            return False
        return middleman_id in (farm.assigned_middleman_ids or [])
    except Exception as e:
        print(f"ERROR: Failed to check middleman access: {e}")
        return False


async def get_farms_for_middleman(middleman_id: str) -> List[dict]:
    """
    Get all farms that a middleman has access to from PostgreSQL.
    """
    try:
        farms = await asyncio.to_thread(farm_repository.get_farms_assigned_to_middleman, middleman_id)
        return [f.model_dump() for f in farms]
    except Exception as e:
        print(f"ERROR: Failed to get farms for middleman: {e}")
        return []
