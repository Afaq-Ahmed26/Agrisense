import asyncio
import uvicorn
from app.main import app
from app.services.sensor_simulation import sensor_simulator


async def initialize_simulator():
    """Initialize the sensor simulator with devices"""
    await sensor_simulator.initialize_devices(5)
    print(f"Initialized {len(sensor_simulator.devices)} simulated devices")


if __name__ == "__main__":
    # Initialize the simulator
    asyncio.run(initialize_simulator())
    
    # Start the Uvicorn server
    uvicorn.run(app, host="0.0.0.0", port=8000)