from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
from app.middleware.auth import JWTBearer
from app.services.alert_service import alert_service, Alert, AlertStatus
from app.services.activity_log_service import log_activity
from app.services.user_service import get_user_from_firestore
from datetime import datetime


router = APIRouter()
security = JWTBearer()


@router.get("/", response_model=List[Alert])
async def get_alerts(
    device_id: str = None,
    status: AlertStatus = None,
    severity: str = None,
    skip: int = 0,
    limit: int = 100,
    token: str = Depends(security)
):
    """
    Get alerts with optional filtering by device, status, and severity.
    """
    if device_id:
        alerts = await alert_service.get_device_alerts(device_id, status)
    else:
        alerts = await alert_service.get_open_alerts()
    
    # Apply additional filtering if needed
    if severity:
        alerts = [alert for alert in alerts if alert.severity.value == severity]
    
    # Apply pagination
    start_idx = skip
    end_idx = skip + limit
    paginated_alerts = alerts[start_idx:end_idx]
    
    return paginated_alerts


@router.get("/{alert_id}", response_model=Alert)
async def get_alert(alert_id: str, token: str = Depends(security)):
    """
    Get a specific alert by ID.
    """
    # In a real implementation, this would fetch from Firestore
    raise HTTPException(status_code=404, detail="Alert not found")


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, request: Request, token: str = Depends(security)):
    """
    Acknowledge an alert.
    """
    user_payload = request.state.user
    acting_user_uid = user_payload.get('uid')

    # In a real implementation, this would update the alert in Firestore
    await alert_service.acknowledge_alert(alert_id, acting_user_uid or "unknown_user")

    # Log the alert acknowledgment
    log_activity(
        user_id=acting_user_uid,
        action="Alert Acknowledged",
        details={"alert_id": alert_id}
    )
    return {"message": "Alert acknowledged", "alert_id": alert_id}


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str, request: Request, token: str = Depends(security)):
    """
    Resolve an alert.
    """
    user_payload = request.state.user
    acting_user_uid = user_payload.get('uid')

    # In a real implementation, this would update the alert in Firestore
    await alert_service.resolve_alert(alert_id, acting_user_uid or "unknown_user")
    
    # Log the alert resolution
    log_activity(
        user_id=acting_user_uid,
        action="Alert Resolved",
        details={"alert_id": alert_id}
    )
    return {"message": "Alert resolved", "alert_id": alert_id}


@router.get("/stats")
async def get_alert_statistics(token: str = Depends(security)):
    """
    Get alert statistics.
    """
    # In a real implementation, this would aggregate data from Firestore
    return {
        "total_alerts": 0,
        "open_alerts": 0,
        "acknowledged_alerts": 0,
        "resolved_alerts": 0,
        "by_severity": {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        },
        "by_type": {
            "soil_moisture_low": 0,
            "sensor_offline": 0,
            "device_error": 0,
            "irrigation_failed": 0,
            "unusual_reading": 0
        }
    }