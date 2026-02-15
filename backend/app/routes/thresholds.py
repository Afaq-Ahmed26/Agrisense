from fastapi import APIRouter, Depends, HTTPException
from app.models.thresholds import AlertThresholds
from app.dependencies import require_roles
from app.services.firebase_service import firebase_service
from app.services.activity_log_service import log_activity
from app.models.user import User

router = APIRouter()

# Define the roles that are allowed to access these settings
AUTHORIZED_ROLES = ["admin", "officer"]

@router.get("/", response_model=AlertThresholds)
async def get_alert_thresholds(current_user: User = Depends(require_roles(AUTHORIZED_ROLES))):
    """
    Retrieve the system-wide alert thresholds.
    """
    settings_ref = firebase_service.db.collection('system_settings').document('alert_thresholds')
    doc = settings_ref.get()
    if doc.exists:
        return AlertThresholds(**doc.to_dict())
    # Return default thresholds if not set
    return AlertThresholds()

@router.put("/", response_model=AlertThresholds)
async def update_alert_thresholds(
    thresholds: AlertThresholds,
    current_user: User = Depends(require_roles(AUTHORIZED_ROLES))
):
    """
    Update the system-wide alert thresholds.
    """
    settings_ref = firebase_service.db.collection('system_settings').document('alert_thresholds')
    
    # For logging, get old thresholds
    old_thresholds_doc = settings_ref.get()
    old_thresholds = AlertThresholds(**old_thresholds_doc.to_dict()) if old_thresholds_doc.exists else AlertThresholds()

    # Set the new thresholds
    settings_ref.set(thresholds.model_dump())

    # Log the activity
    changes = {k: {"old": getattr(old_thresholds, k), "new": getattr(thresholds, k)} for k in thresholds.model_dump().keys() if getattr(old_thresholds, k) != getattr(thresholds, k)}
    if changes:
        log_activity(
            user_id=current_user.id,
            action="Alert Thresholds Update",
            details={"changes": changes}
        )

    return thresholds
