from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from typing import List, Optional, Dict, Any
from app.middleware.auth import JWTBearer
from app.models.farm import Farm, FarmCreate, FarmUpdate
from app.repositories.farm_repository import farm_repository
from app.services.user_service import get_user
from app.services.activity_log_service import log_activity
from app.models.user import User
from app.dependencies import normalize_role, get_current_user, ensure_device_access
import uuid
import asyncio
from datetime import datetime

router = APIRouter()
security = JWTBearer()

async def is_farm_owner_or_admin(request: Request, farm_id: str):
    """Helper to check if the acting user is the farm owner or an admin."""
    user_payload = request.state.user
    acting_user_uid = user_payload.get('user_id') or user_payload.get('uid') or user_payload.get('sub')

    farm = await asyncio.to_thread(farm_repository.get_by_id, farm_id)
    if not farm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found.")

    acting_user = await get_user(acting_user_uid)
    if not acting_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acting user not found.")

    if acting_user.role == 'admin':
        return farm
    
    if acting_user.role == 'farmer' and farm.owner_id == acting_user_uid:
        return farm

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to perform this action on this farm."
    )

# --- Farm Management Routes ---

@router.post("/", response_model=Farm)
async def create_farm(farm_data: FarmCreate, request: Request, token: str = Depends(security)):
    """
    Create a new farm in PostgreSQL. Only farmers can create farms.
    """
    user_payload = request.state.user
    farmer_id = user_payload.get('user_id') or user_payload.get('uid') or user_payload.get('sub')

    if not farmer_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate user credentials.")
    
    farmer_user = await get_user(farmer_id)
    if not farmer_user or normalize_role(farmer_user.role) != "farmer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only farmers can create farms.")

    new_farm = Farm(
        id=str(uuid.uuid4()),
        name=farm_data.name,
        owner_id=farmer_id,
        assigned_officer_id=None,
        assigned_middleman_ids=farm_data.assigned_middleman_ids or [],
        device_ids=farm_data.device_ids or [],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    created_farm = await asyncio.to_thread(farm_repository.create, new_farm)

    await log_activity(
        user_id=farmer_id,
        action="Farm Created",
        details={"farm_id": created_farm.id, "farm_name": created_farm.name}
    )
    
    return created_farm


@router.get("/", response_model=List[Farm])
async def get_farms(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Get farms from PostgreSQL.
    """
    acting_user_uid = current_user.id
    role = normalize_role(current_user.role)

    if role == "admin":
        return await asyncio.to_thread(farm_repository.get_farms_by_owner, None) 
    elif role == "farmer":
        farms = await asyncio.to_thread(farm_repository.get_farms_by_owner, acting_user_uid)
        if not farms and current_user.assigned_device_ids:
            # Synthesize a virtual farm if farmer has devices but no farms
            virtual_farm = Farm(
                id=f"virtual-farm-{acting_user_uid}",
                name=f"{current_user.username}'s Farm",
                owner_id=acting_user_uid,
                assigned_officer_id=None,
                assigned_middleman_ids=[],
                device_ids=current_user.assigned_device_ids,
                created_at=current_user.created_at,
                updated_at=current_user.created_at
            )
            return [virtual_farm]
        return farms
    elif role == "officer":
        return await asyncio.to_thread(farm_repository.get_farms_assigned_to_officer, acting_user_uid)
    elif role == "middleman":
        return await asyncio.to_thread(farm_repository.get_farms_assigned_to_middleman, acting_user_uid)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unknown user role.")

@router.get("/{farm_id}", response_model=Farm)
async def get_farm(farm_id: str, current_user: User = Depends(get_current_user)):
    """
    Get a specific farm from PostgreSQL.
    """
    # Authorization check
    ensure_device_access(current_user, farm_id)
    
    farm = await asyncio.to_thread(farm_repository.get_by_id, farm_id)
    if not farm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found.")

    return farm


@router.put("/{farm_id}/assign-officer", response_model=Farm)
async def assign_officer_to_farm(
    farm_id: str,
    assignment_data: Dict[str, Optional[str]],
    request: Request,
    token: str = Depends(security)
):
    """
    Assign an officer to a farm in PostgreSQL.
    """
    user_payload = request.state.user
    acting_user_uid = user_payload.get('user_id') or user_payload.get('uid') or user_payload.get('sub')
    
    farm = await is_farm_owner_or_admin(request, farm_id)
    
    officer_id = assignment_data.get("officer_id")

    if officer_id:
        officer_user = await get_user(officer_id)
        if not officer_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Officer not found.")
        if normalize_role(officer_user.role) != "officer":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided user ID is not an officer.")

    update_data = {"assigned_officer_id": officer_id}
    updated_farm = await asyncio.to_thread(farm_repository.update, farm_id, update_data)

    if not updated_farm:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update farm.")

    action = "Officer Assigned" if officer_id else "Officer Unassigned"
    await log_activity(
        user_id=acting_user_uid,
        action=action,
        details={"farm_id": farm_id, "farm_name": updated_farm.name, "officer_id": officer_id}
    )

    return updated_farm


@router.patch("/{farm_id}", response_model=Farm)
async def update_farm(farm_id: str, farm_update: FarmUpdate, request: Request, token: str = Depends(security)):
    """
    Update farm details in PostgreSQL.
    """
    user_payload = request.state.user
    acting_user_uid = user_payload.get('user_id') or user_payload.get('uid') or user_payload.get('sub')

    farm = await is_farm_owner_or_admin(request, farm_id)

    update_data = farm_update.model_dump(exclude_unset=True, exclude={'assigned_officer_id'})
    
    if not update_data:
        return farm

    if 'device_ids' in update_data and update_data['device_ids'] is not None:
        cleaned_device_ids = [str(dev_id).strip() for dev_id in update_data['device_ids'] if isinstance(dev_id, str) and str(dev_id).strip()]
        update_data['device_ids'] = list(set(cleaned_device_ids))

    updated_farm = await asyncio.to_thread(farm_repository.update, farm_id, update_data)

    if not updated_farm:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update farm.")

    await log_activity(
        user_id=acting_user_uid,
        action="Farm Updated",
        details={"farm_id": farm_id, "farm_name": updated_farm.name, "update_data": update_data}
    )

    return updated_farm


@router.delete("/{farm_id}")
async def delete_farm(farm_id: str, request: Request, token: str = Depends(security)):
    """
    Delete a farm from PostgreSQL.
    """
    user_payload = request.state.user
    acting_user_uid = user_payload.get('user_id') or user_payload.get('uid') or user_payload.get('sub')

    farm = await is_farm_owner_or_admin(request, farm_id)
    
    await asyncio.to_thread(farm_repository.delete, farm_id)

    await log_activity(
        user_id=acting_user_uid,
        action="Farm Deleted",
        details={"farm_id": farm_id, "farm_name": farm.name}
    )

    return {"message": "Farm deleted successfully."}
