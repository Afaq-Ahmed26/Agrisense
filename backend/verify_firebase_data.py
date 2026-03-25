#!/usr/bin/env python3
"""
Verify soil moisture data is being stored in Firebase Firestore.
This script queries Firebase directly to check for sensor readings.
"""

import sys
sys.path.insert(0, '/home/afaq-ahmed/Desktop/Agriscense/backend')

from app.services.firebase_service import firebase_service
from datetime import datetime

print("\n" + "="*70)
print(" AgriSense - Firebase Data Verification")
print("="*70 + "\n")

db = firebase_service.db

# Check sensor_readings collection
print("Checking 'sensor_readings' collection in Firebase...")
print("-" * 70)

try:
    readings_ref = db.collection('sensor_readings')
    # Get last 10 readings ordered by timestamp
    readings_docs = readings_ref.order_by('timestamp', direction='DESCENDING').limit(10).get()
    
    if readings_docs:
        print(f"✅ Found {len(readings_docs)} recent sensor reading(s):\n")
        
        for i, doc in enumerate(readings_docs, 1):
            data = doc.to_dict()
            print(f"  {i}. Device: {data.get('device_id', 'N/A')}")
            print(f"     Soil Moisture: {data.get('soil_moisture', 'N/A')}%")
            print(f"     Temperature: {data.get('temperature', 'N/A')}°C")
            print(f"     Humidity: {data.get('humidity', 'N/A')}%")
            print(f"     Light Level: {data.get('light_level', 'N/A')} lx")
            
            # Convert timestamp if it exists
            ts = data.get('timestamp')
            if ts:
                if hasattr(ts, 'strftime'):
                    ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    ts_str = str(ts)
                print(f"     Timestamp: {ts_str}")
            print()
    else:
        print("⚠️  No sensor readings found in Firebase yet.")
        print("   Wait for ESP32 to send data or run test_esp32_data_flow.py")
        
except Exception as e:
    print(f"❌ Error querying Firebase: {e}")
    print("   Check your Firebase credentials and network connection.")

print("-" * 70)

# Check devices collection
print("\nChecking 'devices' collection in Firebase...")
print("-" * 70)

try:
    devices_ref = db.collection('devices')
    devices_docs = devices_ref.get()
    
    if devices_docs:
        print(f"✅ Found {len(devices_docs)} device(s):\n")
        for i, doc in enumerate(devices_docs, 1):
            data = doc.to_dict()
            print(f"  {i}. ID: {doc.id}")
            print(f"     Name: {data.get('name', 'N/A')}")
            print(f"     Location: {data.get('location', 'N/A')}")
            print(f"     Active: {data.get('is_active', 'N/A')}")
            print()
    else:
        print("ℹ️  No devices registered yet.")
        print("   Devices are auto-created when ESP32 sends first reading.")
        
except Exception as e:
    print(f"❌ Error querying Firebase: {e}")

print("-" * 70)
print("\n" + "="*70)
print(" Verification Complete")
print("="*70 + "\n")
