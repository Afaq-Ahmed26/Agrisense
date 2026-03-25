#!/usr/bin/env python3
"""
Update ESP32 device owner to afaqahmad16007@gmail.com
"""

import sys
sys.path.insert(0, '/home/afaq-ahmed/Desktop/Agriscense/backend')

from app.services.firebase_service import firebase_service
from datetime import datetime, timezone

ESP32_DEVICE_ID = "esp32-b47cb8"
NEW_OWNER = "afaqahmad16007@gmail.com"

print("\n" + "="*60)
print(" Updating ESP32 Device Owner")
print("="*60 + "\n")

db = firebase_service.db

try:
    # Update the device document
    db.collection('devices').document(ESP32_DEVICE_ID).update({
        "owner_id": NEW_OWNER,
        "location": "Demo Plant (Indoor)",
        "last_seen": datetime.now(timezone.utc),
        "is_active": True
    })
    
    print(f"✅ Device {ESP32_DEVICE_ID} updated successfully!")
    print(f"\nNew Owner: {NEW_OWNER}")
    print(f"Location: Demo Plant (Indoor)")
    print(f"Status: Active")
    
    print("\n" + "="*60)
    print(" Login to Frontend:")
    print("="*60)
    print(f"  URL: http://localhost:5173/login")
    print(f"  Email: {NEW_OWNER}")
    print(f"  Password: {NEW_OWNER}")
    print("="*60 + "\n")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
