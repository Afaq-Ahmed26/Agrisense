#!/usr/bin/env python3
"""
Test script to simulate ESP32 soil moisture data being sent to backend.
This mimics exactly what the ESP32 sends every 2 seconds.

Use this to verify:
1. Backend receives data correctly
2. Data is stored in Firebase
3. ML is NOT triggered (commented out)
"""

import requests
import time
import random

# Backend API URL
API_BASE_URL = "http://localhost:8000"

# Test device ID (same format as ESP32 generates)
DEVICE_ID = "esp32-DEMO-001"

def send_soil_moisture_reading(soil_moisture_value):
    """
    Send a single soil moisture reading to the backend.
    Mimics exactly what the ESP32 code sends.
    """
    # Correct endpoint: /sensors/{device_id}/readings (NOT /api/sensors/...)
    url = f"{API_BASE_URL}/sensors/{DEVICE_ID}/readings"
    
    # Payload matches ESP32 JSON structure (soil moisture only, others are 0)
    payload = {
        "device_id": DEVICE_ID,
        "soil_moisture": soil_moisture_value,
        "temperature": 0,      # Not testing DHT22 today - commented out in ESP32
        "humidity": 0,         # Not testing DHT22 today - commented out in ESP32
        "light_level": 0       # Not testing light sensor today - commented out in ESP32
    }
    
    print(f"\n{'='*60}")
    print(f"Sending soil moisture reading: {soil_moisture_value}%")
    print(f"URL: {url}")
    print(f"Payload: {payload}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"\nHTTP Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Data sent to backend!")
            data = response.json()
            print(f"Backend response: {data}")
            return True
        else:
            print(f"⚠️  WARNING: Backend returned error code {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to backend!")
        print("   Make sure the backend server is running:")
        print("   cd backend && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return False
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out!")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    print("\n" + "="*70)
    print(" AgriSense - ESP32 Data Flow Test (Soil Moisture Only)")
    print("="*70)
    print("\nThis script simulates ESP32 sending soil moisture data to backend.")
    print("ML prediction is COMMENTED OUT - only data storage is tested.")
    print("\nSimulating 5 readings with different moisture levels...")
    print("Press Ctrl+C to stop early.\n")
    
    # Simulate different soil moisture scenarios
    test_readings = [
        25,  # Dry - needs water
        45,  # Medium - okay
        70,  # Wet - good
        35,  # Getting dry
        60,  # After watering
    ]
    
    success_count = 0
    
    for i, moisture in enumerate(test_readings, 1):
        print(f"\n>>> Reading {i}/{len(test_readings)}")
        
        if send_soil_moisture_reading(moisture):
            success_count += 1
        
        if i < len(test_readings):
            print(f"Waiting 2 seconds (simulating ESP32 interval)...")
            time.sleep(2)
    
    print(f"\n{'='*70}")
    print(f"Test Complete: {success_count}/{len(test_readings)} readings sent successfully")
    print(f"{'='*70}\n")
    
    if success_count == len(test_readings):
        print("✅ All readings sent successfully!")
        print("\nNext steps:")
        print("1. Check Firebase Console to verify data is stored")
        print("2. Check frontend dashboard to see if values display")
        print("3. Verify NO ML predictions were triggered (commented out)")
    else:
        print("⚠️  Some readings failed. Check backend logs for details.")


if __name__ == "__main__":
    main()
