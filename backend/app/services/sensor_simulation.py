import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Any
from app.services.firebase_service import firebase_service
from app.models.sensor import SensorReadingCreate
from app.utils.helpers import generate_device_id


class SensorDataSimulator:
    """
    A service to simulate sensor data for testing purposes when physical hardware is not available.
    """
    
    def __init__(self):
        self.devices = []
        self.running = False
        self.simulation_task = None
    
    async def initialize_devices(self, num_devices: int = 5):
        """Initialize a set of simulated devices"""
        for i in range(num_devices):
            device_id = generate_device_id()
            device_info = {
                "id": device_id,
                "name": f"Simulated Device {i+1}",
                "location": f"Field Section {(i % 3) + 1}",
                "owner_id": f"farmer_{random.randint(1, 10)}"
            }
            self.devices.append(device_info)
    
    def generate_simulated_reading(self, device_id: str) -> Dict[str, Any]:
        """Generate a simulated sensor reading for a device"""
        # Simulate realistic sensor values with some variation
        base_soil_moisture = random.uniform(20, 80)  # Percentage
        base_temperature = random.uniform(15, 35)    # Celsius
        base_humidity = random.uniform(30, 80)       # Percentage
        base_light_level = random.uniform(100, 1500) # Lux
        
        # Add some variation based on time of day or season
        hour_factor = abs(12 - datetime.now().hour) / 6  # Factor based on time of day
        
        soil_moisture = max(0, min(100, base_soil_moisture + random.uniform(-5, 5)))
        temperature = max(-10, min(50, base_temperature + hour_factor * 2))
        humidity = max(0, min(100, base_humidity + random.uniform(-10, 10)))
        light_level = max(0, base_light_level * (1 - hour_factor * 0.5) + random.uniform(-100, 100))
        
        return {
            "device_id": device_id,
            "soil_moisture": round(soil_moisture, 2),
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2),
            "light_level": round(light_level, 2),
            "timestamp": datetime.utcnow()
        }
    
    async def simulate_single_reading(self, device_id: str):
        """Simulate a single reading for a specific device"""
        reading_data = self.generate_simulated_reading(device_id)
        
        # In a real implementation, we would save this to Firestore
        # For simulation, we'll just return the data
        return reading_data
    
    async def start_continuous_simulation(self, interval_seconds: int = 60):
        """Start continuous simulation of sensor data"""
        if self.running:
            print("Simulation already running")
            return
        
        self.running = True
        print(f"Starting continuous sensor data simulation with {len(self.devices)} devices...")
        
        while self.running:
            try:
                for device in self.devices:
                    reading_data = self.generate_simulated_reading(device["id"])
                    
                    # In a real implementation, we would save this to Firestore
                    # doc_ref = firebase_service.db.collection('sensor_readings').add(reading_data)
                    
                    print(f"Simulated reading for {device['name']}: {reading_data}")
                
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                print(f"Error in simulation: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def stop_simulation(self):
        """Stop the continuous simulation"""
        self.running = False
        if self.simulation_task:
            self.simulation_task.cancel()
            try:
                await self.simulation_task
            except asyncio.CancelledError:
                pass
        print("Simulation stopped")


# Global instance
sensor_simulator = SensorDataSimulator()