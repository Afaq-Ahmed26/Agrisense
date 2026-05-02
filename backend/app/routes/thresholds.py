import asyncio
from fastapi import APIRouter, Depends, HTTPException
from app.models.thresholds import AlertThresholds
from app.dependencies import require_roles
from app.services.activity_log_service import log_activity
from app.models.user import User
from app.repositories.threshold_repository import threshold_repository

router = APIRouter()

# Define the roles that are allowed to access these settings
AUTHORIZED_ROLES = ["admin", "officer"]

@router.get("/", response_model=AlertThresholds)
async def get_alert_thresholds(current_user: User = Depends(require_roles(AUTHORIZED_ROLES))):
    """
    Retrieve the system-wide alert thresholds from PostgreSQL.
    """
    thresholds = await asyncio.to_thread(threshold_repository.get_alert_thresholds)
    return thresholds or AlertThresholds()

@router.put("/", response_model=AlertThresholds)
async def update_alert_thresholds(
    thresholds: AlertThresholds,
    current_user: User = Depends(require_roles(AUTHORIZED_ROLES))
):
    """
    Update the system-wide alert thresholds in PostgreSQL.
    """
    old_thresholds = await asyncio.to_thread(threshold_repository.get_alert_thresholds)
    old_thresholds = old_thresholds or AlertThresholds()
    
    await asyncio.to_thread(threshold_repository.upsert_alert_thresholds, thresholds)

    # Log the activity
    changes = {k: {"old": getattr(old_thresholds, k), "new": getattr(thresholds, k)} for k in thresholds.model_dump().keys() if getattr(old_thresholds, k) != getattr(thresholds, k)}
    if changes:
        await log_activity(
            user_id=current_user.id,
            action="Alert Thresholds Update",
            details={"changes": changes}
        )

    return thresholds

@router.get("/defaults", response_model=AlertThresholds)
async def get_default_thresholds(current_user: User = Depends(require_roles(AUTHORIZED_ROLES))):
    """
    Retrieve the default alert thresholds.
    """
    return AlertThresholds()
