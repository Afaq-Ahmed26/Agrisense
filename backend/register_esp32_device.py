#!/usr/bin/env python3
"""
Register the ESP32 device in Firebase Firestore.
This allows the frontend to discover and display data from the ESP32.
"""

import sys
sys.path.insert(0, '/home/afaq-ahmed/Desktop/Agriscense/backend')

from app.services.firebase_service import firebase_service
from datetime import datetime

# The ESP32 device ID from your actual hardware
# This is generated from the ESP32's chip ID
ESP32_DEVICE_ID = "esp32-b47cb8"

def register_esp32_device():
    """Register ESP32 device in Firebase Firestore devices collection"""
    
    print("\n" + "="*60)
    print(" Registering ESP32 Device in Firebase")
    print("="*60 + "\n")
    
    db = firebase_service.db
    
    if firebase_service.is_mock:
        print("⚠️  WARNING: Using mock Firebase!")
        print("   Data will not persist.")
        return False
    
    device_data = {
        "id": ESP32_DEVICE_ID,
        "name": "ESP32 Soil Moisture Sensor",
        "location": "Demo Plant (Indoor)",
        "owner_id": "afaqahmad16007@gmail.com",
        "type": "soil_moisture_sensor",
        "zone_id": "zone_1",
        "crop_type": "Potted Plant",
        "area_size": 1.0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True,
        "firmware_version": "2.0-demo",
        "last_seen": datetime.utcnow()
    }
    
    try:
        # Check if device already exists
        existing_device = db.collection('devices').document(ESP32_DEVICE_ID).get()
        
        if existing_device.exists:
            print(f"ℹ️  Device {ESP32_DEVICE_ID} already exists!")
            print("   Updating last_seen timestamp...")
            db.collection('devices').document(ESP32_DEVICE_ID).update({
                "last_seen": datetime.utcnow()
            })
        else:
            print(f"Registering new device: {ESP32_DEVICE_ID}")
            db.collection('devices').document(ESP32_DEVICE_ID).set(device_data)
            print("✅ Device registered successfully!")
        
        print("\n" + "="*60)
        print(" Device Details:")
        print("="*60)
        print(f"  Device ID: {ESP32_DEVICE_ID}")
        print(f"  Name: {device_data['name']}")
        print(f"  Location: {device_data['location']}")
        print(f"  Type: {device_data['type']}")
        print(f"  Status: {'Active' if device_data['is_active'] else 'Inactive'}")
        print("="*60)
        print("\n🎉 You can now see this device in the frontend dashboard!")
        print(f"   Go to: http://localhost:5173/dashboard")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("   Check your Firebase credentials and network connection.")
        return False


if __name__ == "__main__":
    register_esp32_device()
