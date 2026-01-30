from datetime import datetime
from typing import Dict, Any
import joblib  # Changed from pickle to joblib
import pandas as pd
import os


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
                "predicted_at": datetime.utcnow().isoformat(),
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
            "predicted_at": datetime.utcnow().isoformat(),
            "input_data": sensor_data
        }
    
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
            "calculated_at": datetime.utcnow().isoformat(),
            "user_preferences_applied": user_preferences or {}
        }


# Global instance
ml_service = MLService()