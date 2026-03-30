import os
import asyncio
import uvicorn
from app.main import app

if __name__ == "__main__":
    # ONLY initialize simulator if an environment variable is set
    # This prevents accidental "garbage" data generation in your real Firestore
    if os.getenv("USE_SIMULATOR") == "true":
        from app.services.sensor_simulation import sensor_simulator
        async def initialize_simulator():
            await sensor_simulator.initialize_devices(2)
            print(f"📡 Simulator Active: {len(sensor_simulator.devices)} mock devices initialized.")
        asyncio.run(initialize_simulator())
    else:
        print("🚀 Starting Production Backend (No Simulator)")
    
    # Start the Uvicorn server
    uvicorn.run(app, host="0.0.0.0", port=8000)