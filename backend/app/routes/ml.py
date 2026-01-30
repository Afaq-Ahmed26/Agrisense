from fastapi import APIRouter, Depends, HTTPException, status
from app.middleware.auth import JWTBearer
from app.services.ml_service import ml_service


router = APIRouter()
security = JWTBearer()


@router.post("/predict", summary="Get ML prediction for irrigation needs")
async def get_ml_prediction(
    soil_moisture: float, 
    temperature: float, 
    humidity: float,
    light_level: float,
    device_id: str = None,
    token: str = Depends(security)
):
    """
    Get ML-based prediction for irrigation needs based on sensor data.
    This endpoint uses a trained model to predict the optimal valve duration.
    """
    sensor_data = {
        "soil_moisture": soil_moisture,
        "temperature": temperature,
        "humidity": humidity,
        "light_level": light_level,
        "device_id": device_id
    }
    
    prediction = await ml_service.predict_irrigation_need(sensor_data)
    
    return prediction


@router.post("/schedule/optimize", summary="Get optimized irrigation schedule")
async def get_optimized_schedule(
    device_id: str,
    user_preferences: dict = {},
    token: str = Depends(security)
):
    """
    Get an optimized irrigation schedule based on historical data and ML predictions.
    This endpoint serves as a placeholder for the future ML model integration.
    """
    schedule = await ml_service.get_optimal_irrigation_schedule(device_id, user_preferences)
    
    return schedule


@router.get("/status", summary="Check ML service status")
async def ml_service_status(token: str = Depends(security)):
    """
    Check the status of the ML service.
    """
    return {
        "status": "operational",
        "service": "ml_service",
        "message": "ML service is ready for predictions"
    }