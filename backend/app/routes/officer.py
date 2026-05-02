from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.dependencies import get_current_user, require_roles
from app.models.user import User
from app.services.user_service import get_user

router = APIRouter()

@router.get("/farmers", response_model=List[User])
async def get_managed_farmers(current_user: User = Depends(require_roles(["officer"]))):
    """
    Returns a list of farmers managed by the current officer.
    """
    if not current_user.managed_farmer_ids:
        return []
    
    managed_farmers = []
    for farmer_id in current_user.managed_farmer_ids:
        farmer = await get_user(farmer_id)
        if farmer:
            managed_farmers.append(farmer)
            
    return managed_farmers
