from fastapi import APIRouter, Depends, HTTPException, status, Body
from app.middleware.auth import JWTBearer
from app.services.ml_service import ml_service
from app.models.ml import MLPredictionInput # Import MLPredictionInput


router = APIRouter()
security = JWTBearer()


@router.post("/predict", summary="Get ML prediction for irrigation needs")
async def get_ml_prediction(
    data: MLPredictionInput = Body(...),
    token: str = Depends(security)
):
    """
    Get ML-based prediction for irrigation needs based on sensor data.
    """
    prediction = await ml_service.predict_irrigation_need(data.model_dump())
    if prediction.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=prediction["error"])
    return prediction


@router.get("/future_predictions/{device_id}", summary="Get future ML predictions for irrigation needs")
async def get_future_ml_predictions(
    device_id: str,
    hours_ahead: int = 48,
    token: str = Depends(security)
):
    """
    Get ML-based predictions for irrigation needs for future hours based on simulated sensor data.
    """
    if not (1 <= hours_ahead <= 168):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="hours_ahead must be between 1 and 168 (1 week)."
        )

    predictions = await ml_service.predict_future_irrigation_needs(device_id, hours_ahead)
    return predictions


# @router.post("/schedule/optimize", summary="Get optimized irrigation schedule")
# async def get_optimized_schedule(
#     device_id: str,
#     user_preferences: dict = {},
#     token: str = Depends(security)
# ):
#     """
#     Get an optimized irrigation schedule based on historical data and ML predictions.
#     This endpoint serves as a placeholder for the future ML model integration.
#     """
#     schedule = await ml_service.get_optimal_irrigation_schedule(device_id, user_preferences)
    
#     return schedule


@router.get("/status", summary="Check ML service status")
async def ml_service_status(token: str = Depends(security)):
    """
    Check the status of the ML service.
    """
    status = ml_service.get_status()
    return {
        "status": "operational" if status["model_loaded"] else "degraded",
        "service": "ml_service",
        "message": "ML service is ready for predictions" if status["model_loaded"] else "ML model is not loaded",
        "model_loaded": status["model_loaded"],
        "model_path": status["model_path"],
    }
