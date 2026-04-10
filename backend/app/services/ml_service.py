from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import joblib  # Changed from pickle to joblib
import pandas as pd
import os
import random
from app.services.sensor_service import sensor_service


class MLService:
    """
    ML Service that loads a pre-trained model to make irrigation predictions.
    """
    
    def __init__(self):
        """
        Initializes the MLService by loading the trained model.
        The model is loaded using joblib from the /model directory.
        """
        # Construct the absolute path to the new model file in the /model directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, '..', '..', '..', 'model', 'irrigation_model.pkl')
        
        try:
            self.model = joblib.load(model_path)
            print(f"Successfully loaded model from {model_path}")
        except FileNotFoundError:
            print(f"Error: Model file not found at {model_path}")
            self.model = None
        except Exception as e:
            print(f"An error occurred while loading the model: {e}")
            self.model = None

    async def predict_irrigation_need(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict irrigation valve duration based on sensor data using the loaded ML model.
        """
        if self.model is None:
            return {
                "error": "The irrigation prediction model could not be loaded.",
                "predicted_valve_duration_s": None,
                "predicted_at": datetime.now(timezone.utc).isoformat(),
                "input_data": sensor_data,
            }

        # The model was trained with specific feature names. We must match them exactly.
        # These are the columns from the notebook:
        # ['Soil Moisture (%)', 'Temperature (°C)', 'Humidity (%)', 'Light Level (lx)']
        
        # Map API input keys to the required model feature names
        input_data_for_model = {
            'Soil Moisture (%)': sensor_data.get('soil_moisture'),
            'Temperature (°C)': sensor_data.get('temperature'),
            'Humidity (%)': sensor_data.get('humidity'),
            'Light Level (lx)': sensor_data.get('light_level')
        }

        # Check if all required data is present
        if any(value is None for value in input_data_for_model.values()):
            return {
                "error": "Missing one or more required sensor data fields: soil_moisture, temperature, humidity, light_level.",
                "predicted_valve_duration_s": None,
                "input_data": sensor_data
            }
        
        try:
            # Create a DataFrame with the exact feature names the model was trained on
            input_df = pd.DataFrame([input_data_for_model])
            
            # Get prediction from the model
            predicted_duration = self.model.predict(input_df)[0]
            
            # The model predicts the valve duration in seconds.
            # We can add a simple floor to prevent negative predictions if the model were to do that.
            predicted_duration = max(0, predicted_duration)

        except Exception as e:
            return {
                "error": f"Failed to get prediction: {e}",
                "predicted_valve_duration_s": None,
                "input_data": sensor_data
            }

        return {
            "predicted_valve_duration_s": round(predicted_duration, 2),
            "unit": "seconds",
            "predicted_at": datetime.now(timezone.utc).isoformat(),
            "input_data": sensor_data
        }
    
    async def predict_future_irrigation_needs(self, device_id: str, hours_ahead: int = 48) -> List[Dict[str, Any]]:
        """
        Predict irrigation needs for future hours based on simulated sensor data.
        """
        future_predictions = []
        current_time = datetime.now(timezone.utc)

        # Get the latest actual sensor reading as a starting point
        latest_actual_reading = await sensor_service.get_latest_sensor_reading(device_id)

        if not latest_actual_reading:
            print(f"WARNING: No latest sensor reading found for device {device_id}. Cannot predict future.")
            return []

        # Initialize simulated sensor values with the latest actual reading (with defaults)
        simulated_soil_moisture = latest_actual_reading.soil_moisture if latest_actual_reading.soil_moisture is not None else 30.0
        simulated_temperature = latest_actual_reading.temperature if latest_actual_reading.temperature is not None else 25.0
        simulated_humidity = latest_actual_reading.humidity if latest_actual_reading.humidity is not None else 50.0
        simulated_light_level = latest_actual_reading.light_level if latest_actual_reading.light_level is not None else 500.0

        for i in range(1, hours_ahead + 1):
            future_time = current_time + timedelta(hours=i)

            # Simple simulation: random walk with bounds
            # Keep values within reasonable ranges (e.g., soil moisture 0-100, temp -10-50, humidity 0-100, light 0-2000)
            simulated_soil_moisture = max(0.0, min(100.0, simulated_soil_moisture + random.uniform(-2.0, 2.0)))
            simulated_temperature = max(-10.0, min(50.0, simulated_temperature + random.uniform(-1.0, 1.0)))
            simulated_humidity = max(0.0, min(100.0, simulated_humidity + random.uniform(-1.0, 1.0)))
            
            # Light level can vary more significantly with day/night cycles, but for simplicity, a random walk for now
            # A more advanced simulation would consider time of day.
            simulated_light_level = max(0.0, min(2000.0, simulated_light_level + random.uniform(-50.0, 50.0)))


            simulated_sensor_data = {
                'soil_moisture': simulated_soil_moisture,
                'temperature': simulated_temperature,
                'humidity': simulated_humidity,
                'light_level': simulated_light_level
            }

            prediction_result = await self.predict_irrigation_need(simulated_sensor_data)
            
            future_predictions.append({
                "predicted_at": future_time.isoformat(),
                "predicted_valve_duration_s": prediction_result["predicted_valve_duration_s"],
                "input_data": simulated_sensor_data
            })
        
        return future_predictions
    
    async def get_optimal_irrigation_schedule(self, device_id: str, user_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get optimal irrigation schedule based on historical data and predictions.
        This is a placeholder implementation.
        """
        # This part remains a placeholder
        optimal_times = [
            {"day": "monday", "time": "06:00"},
            {"day": "wednesday", "time": "06:00"},
            {"day": "friday", "time": "06:00"}
        ]
        
        
        return {
            "device_id": device_id,
            "optimal_schedule": optimal_times,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
            "user_preferences_applied": user_preferences or {}
        }


# Global instance
ml_service = MLService()