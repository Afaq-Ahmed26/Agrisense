import os
import sys
from datetime import datetime

# Add the current directory to sys.path to import app modules
sys.path.append(os.path.dirname(__file__))

from app.services.firebase_service import firebase_service
from app.services.sensor_service import sensor_service
from app.models.sensor import DeviceCreate

async def register_device():
    print("Connecting to Firebase...")
    db = firebase_service.db
    auth = firebase_service.auth

    target_email = "afaqahmad16007@gmail.com"
    device_id = "esp32-b47cb8"

    print(f"Looking for user: {target_email}")
    try:
        user = auth.get_user_by_email(target_email)
        user_id = user.uid
        print(f"Found user {target_email} with UID: {user_id}")
    except Exception as e:
        print(f"Error finding user: {e}")
        return

    print(f"Checking if device {device_id} already exists...")
    device_ref = db.collection('devices').document(device_id)
    doc = device_ref.get()

    if doc.exists:
        print(f"Device {device_id} already exists. Updating owner to {user_id}...")
        device_ref.update({
            "owner_id": user_id,
            "updated_at": datetime.utcnow()
        })
        print("Device owner updated successfully.")
    else:
        print(f"Creating new device {device_id} for owner {user_id}...")
        new_device = {
            "id": device_id,
            "name": "ESP32 AgriSense Node",
            "location": "Main Field",
            "owner_id": user_id,
            "type": "irrigation_device",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        db.collection('devices').document(device_id).set(new_device)
        print("Device created successfully.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(register_device())
