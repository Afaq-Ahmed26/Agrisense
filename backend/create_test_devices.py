import os
from dotenv import load_dotenv
import requests
import asyncio
from typing import Dict, Any

# Load environment variables from .env file
load_dotenv()

# Assuming the backend is running on http://localhost:8000
BASE_URL = "http://localhost:8000"

# --- Admin User Credentials for obtaining a JWT token ---
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "afaqahmad16007@gmail.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "afaqahmad16007@gmail.com") # Replace with actual admin password if different
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY") # Read from .env

async def get_admin_token() -> str:
    """
    Authenticates as an admin user with Firebase to get an ID token.
    The backend is configured to accept Firebase ID tokens as JWTs.
    """
    if not FIREBASE_API_KEY:
        print("ERROR: FIREBASE_API_KEY not found in environment variables.")
        raise Exception("FIREBASE_API_KEY not set.")

    # Sign in with Email/Password to Firebase to get an ID Token
    firebase_signin_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    firebase_login_payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "returnSecureToken": True
    }
    
    print(f"Attempting to get Firebase ID token for {ADMIN_EMAIL}...")
    try:
        response = requests.post(firebase_signin_url, json=firebase_login_payload)
        if response.status_code != 200:
            print(f"ERROR: Firebase sign-in failed with status {response.status_code}")
            print(f"Response: {response.text}")
            raise Exception(f"Firebase sign-in failed: {response.text}")
            
        token = response.json().get("idToken")
        if not token:
            raise Exception("Failed to retrieve Firebase ID token.")
            
        print("Successfully obtained Firebase ID token.")
        return token
    except requests.exceptions.RequestException as e:
        print(f"Error signing in to Firebase: {e}")
        raise

async def create_test_device(device_data: Dict[str, Any], token: str) -> Dict[str, Any]:
    """
    Creates a single test device using the /sensors/ POST endpoint.
    """
    headers = {"Authorization": f"Bearer {token}"}
    create_device_url = f"{BASE_URL}/sensors/"
    print(f"Creating device: {device_data['name']}...")
    response = requests.post(create_device_url, json=device_data, headers=headers)
    response.raise_for_status()
    created_device = response.json()
    print(f"Successfully created device: {created_device['name']} with ID: {created_device['id']}")
    return created_device

async def main():
    admin_token = await get_admin_token()

    # Define the test devices to create
    test_devices = [
        {
            "name": "Soil Zone 1 Sensor",
            "location": "North Field",
            "owner_id": "test_owner_id", # Placeholder, ideally link to a real user
            "type": "soil_moisture_sensor",
            "zone_id": "soil_zone_1",
            "crop_type": "wheat",
            "area_size": 100.5
        },
        {
            "name": "Soil Zone 2 Sensor",
            "location": "South Field",
            "owner_id": "test_owner_id",
            "type": "soil_moisture_sensor",
            "zone_id": "soil_zone_2",
            "crop_type": "wheat",
            "area_size": 120.0
        },
        {
            "name": "Environment Station 1",
            "location": "Central Field",
            "owner_id": "test_owner_id",
            "type": "weather_station",
            "zone_id": "env_station_1",
            "crop_type": "n/a", # Environmental stations might not be crop-specific
            "area_size": 0.0 # Area size might not apply to env stations
        }
    ]

    created_devices = []
    for device_data in test_devices:
        try:
            device = await create_test_device(device_data, admin_token)
            created_devices.append(device)
        except requests.exceptions.RequestException as e:
            print(f"Error creating device {device_data['name']}: {e}")
            if e.response:
                print(f"Response content: {e.response.text}")
    
    print("\n--- All Test Devices Created ---")
    for device in created_devices:
        print(f"ID: {device['id']}, Name: {device['name']}, Zone: {device.get('zone_id', 'N/A')}")

if __name__ == "__main__":
    # Ensure a running asyncio event loop for await calls
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(main())
    loop.close()

