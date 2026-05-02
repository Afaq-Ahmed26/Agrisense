"""
Routes for managing middleman/officer assignments and relationships.
"""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
from app.middleware.auth import JWTBearer
from app.models.user import User
from app.services.user_service import get_user
from app.services.middleman_service import (
    assign_middleman_to_farmer,
    revoke_middleman_access,
    get_farmers_for_middleman,
    get_middlemen_for_farmer,
    get_farms_for_middleman,
)
from app.services.activity_log_service import log_activity

router = APIRouter()
security = JWTBearer()


@router.post("/farmers/{farmer_id}/middleman/{middleman_id}")
async def assign_middleman(
    farmer_id: str,
    middleman_id: str,
    request: Request,
    token: str = Depends(security)
):
    """
    Assign a middleman to manage a farmer's farms.
    Only admin can perform this operation.
    
    Args:
        farmer_id: ID of the farmer
        middleman_id: ID of the middleman/officer to assign
    
    Returns:
        Success message with assigned middleman details
    """
    user_payload = request.state.user
    acting_user_id = user_payload.get('uid') or user_payload.get('sub') or user_payload.get('user_id')
    
    # Only admins can assign middlemen
    acting_user = await get_user(acting_user_id)
    if not acting_user or acting_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Only admins can assign middlemen to farmers"
        )
    
    # Perform assignment
    success = await assign_middleman_to_farmer(farmer_id, middleman_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to assign middleman. Please verify both users exist and middleman has officer/middleman role."
        )
    
    # Log activity
    await log_activity(
        user_id=acting_user_id,
        action="Middleman Assignment",
        details={"farmer_id": farmer_id, "middleman_id": middleman_id}
    )
    
    # Fetch updated middleman to return
    middleman = await get_user(middleman_id)
    
    return {
        "message": f"Middleman {middleman.username} assigned to farmer",
        "middleman": middleman,
        "farmer_id": farmer_id
    }


@router.delete("/farmers/{farmer_id}/middleman/{middleman_id}")
async def revoke_middleman(
    farmer_id: str,
    middleman_id: str,
    request: Request,
    token: str = Depends(security)
):
    """
    Revoke a middleman's access to a farmer's farms.
    Either the farmer or admin can perform this operation.
    
    Args:
        farmer_id: ID of the farmer
        middleman_id: ID of the middleman/officer to revoke
    
    Returns:
        Success message
    """
    user_payload = request.state.user
    acting_user_id = user_payload.get('uid') or user_payload.get('sub') or user_payload.get('user_id')
    
    # Check authorization: farmer or admin
    acting_user = await get_user(acting_user_id)
    if not acting_user:
        raise HTTPException(status_code=404, detail="Acting user not found")
    
    is_farmer = acting_user_id == farmer_id
    is_admin = acting_user.role == 'admin'
    
    if not (is_farmer or is_admin):
        raise HTTPException(
            status_code=403,
            detail="Only the farmer or admin can revoke middleman access"
        )
    
    # Perform revocation
    success = await revoke_middleman_access(farmer_id, middleman_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to revoke middleman access"
        )
    
    # Log activity
    await log_activity(
        user_id=acting_user_id,
        action="Middleman Revocation",
        details={"farmer_id": farmer_id, "middleman_id": middleman_id}
    )
    
    return {"message": f"Middleman {middleman_id} access revoked for farmer {farmer_id}"}


@router.get("/middleman/{middleman_id}/farmers", response_model=List[User])
async def get_farmers_for_middleman_route(
    middleman_id: str,
    request: Request,
    token: str = Depends(security)
):
    """
    Get all farmers assigned to a middleman.
    Middleman can only view their own farmers, admins can view any middleman's farmers.
    
    Args:
        middleman_id: ID of the middleman
    
    Returns:
        List of User objects (farmers)
    """
    user_payload = request.state.user
    acting_user_id = user_payload.get('uid') or user_payload.get('sub') or user_payload.get('user_id')
    
    # Check authorization: middleman viewing self or admin
    acting_user = await get_user(acting_user_id)
    if not acting_user:
        raise HTTPException(status_code=404, detail="Acting user not found")
    
    can_view = acting_user_id == middleman_id or acting_user.role == 'admin'
    if not can_view:
        raise HTTPException(
            status_code=403,
            detail="Cannot view farmers assigned to other middlemen"
        )
    
    farmers = await get_farmers_for_middleman(middleman_id)
    return farmers


@router.get("/farmer/{farmer_id}/middlemen", response_model=List[User])
async def get_middlemen_for_farmer_route(
    farmer_id: str,
    request: Request,
    token: str = Depends(security)
):
    """
    Get all middlemen assigned to a farmer's farms.
    Farmer can view their own middlemen, admins can view any farmer's middlemen.
    
    Args:
        farmer_id: ID of the farmer
    
    Returns:
        List of User objects (middlemen)
    """
    user_payload = request.state.user
    acting_user_id = user_payload.get('uid') or user_payload.get('sub') or user_payload.get('user_id')
    
    # Check authorization: farmer viewing self or admin
    acting_user = await get_user(acting_user_id)
    if not acting_user:
        raise HTTPException(status_code=404, detail="Acting user not found")
    
    can_view = acting_user_id == farmer_id or acting_user.role == 'admin'
    if not can_view:
        raise HTTPException(
            status_code=403,
            detail="Cannot view middlemen assigned to other farmers"
        )
    
    middlemen = await get_middlemen_for_farmer(farmer_id)
    return middlemen


@router.get("/middleman/{middleman_id}/farms")
async def get_farms_for_middleman_route(
    middleman_id: str,
    request: Request,
    token: str = Depends(security)
):
    """
    Get all farms that a middleman has access to.
    Middleman can only view their own farms, admins can view any middleman's farms.
    
    Args:
        middleman_id: ID of the middleman
    
    Returns:
        List of farms with farm details
    """
    user_payload = request.state.user
    acting_user_id = user_payload.get('uid') or user_payload.get('sub') or user_payload.get('user_id')
    
    # Check authorization: middleman viewing self or admin
    acting_user = await get_user(acting_user_id)
    if not acting_user:
        raise HTTPException(status_code=404, detail="Acting user not found")
    
    can_view = acting_user_id == middleman_id or acting_user.role == 'admin'
    if not can_view:
        raise HTTPException(
            status_code=403,
            detail="Cannot view farms for other middlemen"
        )
    
    farms = await get_farms_for_middleman(middleman_id)
    return farms
