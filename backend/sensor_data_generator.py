import asyncio
import requests
import random
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any, List

# Load environment variables from .env file
load_dotenv()

BASE_URL = "http://localhost:8000"

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

SENSOR_READING_INTERVAL_SECONDS = 5 * 60 # 5 minutes

async def get_admin_token() -> str:
    """
    Authenticates as an admin user with Firebase, gets an ID token,
    then uses that ID token to get a backend JWT token.
    """
    if not FIREBASE_API_KEY:
        raise Exception("FIREBASE_API_KEY not set. Please add it to your .env file in the backend directory.")
    if ADMIN_EMAIL == "admin@example.com" and ADMIN_PASSWORD == "admin":
        print("WARNING: Using default admin credentials. Ensure admin@example.com is registered in Firebase Auth and has password 'admin'.")

    # 1. Sign in with Email/Password to Firebase to get an ID Token
    firebase_signin_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    firebase_login_payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "returnSecureToken": True
    }
    print("Attempting to get Firebase ID token...")
    try:
        response = requests.post(firebase_signin_url, json=firebase_login_payload)
        response.raise_for_status()
        firebase_id_token = response.json().get("idToken")
        if not firebase_id_token:
            raise Exception("Failed to retrieve Firebase ID token.")
        print("Successfully obtained Firebase ID token.")
    except requests.exceptions.RequestException as e:
        print(f"Error signing in with email/password to get ID token from Firebase: {e}")
        if e.response:
            print(f"Firebase response: {e.response.text}")
        raise

    # 2. Use Firebase ID Token to get the backend's JWT token
    login_url = f"{BASE_URL}/auth/login"
    backend_login_payload = {
        "id_token": firebase_id_token
    }
    print("Attempting to get backend JWT token...")
    try:
        response = requests.post(login_url, json=backend_login_payload)
        response.raise_for_status() # Raise an exception for HTTP errors
        token = response.json().get("access_token")
        if not token:
            raise Exception("Failed to retrieve backend access token.")
        print(f"Successfully obtained backend JWT token.")
        return token
    except requests.exceptions.RequestException as e:
        print(f"Error getting backend JWT token from /auth/login: {e}")
        if e.response:
            print(f"Backend response: {e.response.text}")
        raise

async def get_all_devices(token: str) -> List[Dict[str, Any]]:
    """
    Fetches all registered devices from the backend.
    """
    headers = {"Authorization": f"Bearer {token}"}
    devices_url = f"{BASE_URL}/sensors/"
    print("Fetching devices...")
    response = requests.get(devices_url, headers=headers)
    response.raise_for_status()
    devices = response.json()
    print(f"Found {len(devices)} devices.")
    return devices

async def generate_and_send_reading(device: Dict[str, Any], token: str):
    """
    Generates random sensor data for a given device and sends it to the backend.
    """
    headers = {"Authorization": f"Bearer {token}"}
    
    # Generate random sensor data within specified ranges
    soil_moisture = round(random.uniform(20.0, 60.0), 2)
    temperature = round(random.uniform(18.0, 40.0), 2)
    humidity = round(random.uniform(40.0, 80.0), 2)
    light_level = round(random.uniform(300.0, 1200.0), 2)
    
    reading_payload = {
        "device_id": device["id"],
        "soil_moisture": soil_moisture,
        "temperature": temperature,
        "humidity": humidity,
        "light_level": light_level,
        "timestamp": datetime.utcnow().isoformat() + "Z" # ISO 8601 format with Z for UTC
    }
    
    send_reading_url = f"{BASE_URL}/sensors/{device['id']}/readings"
    
    print(f"Sending reading for device {device['name']} (ID: {device['id']}): {reading_payload}")
    try:
        response = requests.post(send_reading_url, json=reading_payload, headers=headers)
        response.raise_for_status()
        print(f"Successfully sent reading for device {device['name']}.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending reading for device {device['name']}: {e}")
        if e.response:
            print(f"Response content: {e.response.text}")

async def main():
    token = await get_admin_token()
    devices = await get_all_devices(token)

    if not devices:
        print("No devices found. Please create some test devices first using create_test_devices.py.")
        return

    while True:
        print(f"\n--- Generating and sending sensor readings (Timestamp: {datetime.utcnow().isoformat()}Z) ---")
        tasks = [generate_and_send_reading(device, token) for device in devices]
        await asyncio.gather(*tasks)
        print(f"Waiting for {SENSOR_READING_INTERVAL_SECONDS} seconds before next batch...")
        await asyncio.sleep(SENSOR_READING_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        # Ensure a running asyncio event loop for await calls
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    print("Starting sensor data generator...")
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nSensor data generator stopped by user.")
    finally:
        loop.close()