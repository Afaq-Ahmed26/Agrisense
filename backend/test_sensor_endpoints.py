import asyncio
import requests
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

async def get_admin_token() -> str:
    """
    Authenticates as an admin user with Firebase, gets an ID token,
    then uses that ID token to get a backend JWT token.
    """
    if not FIREBASE_API_KEY:
        raise Exception("FIREBASE_API_KEY not set. Please add it to your .env file in the backend directory.")

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

async def get_latest_reading_for_device(device_id: str, token: str):
    """
    Fetches the latest sensor reading for a specific device.
    """
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/sensors/{device_id}/latest-reading"
    print(f"Fetching latest reading for device {device_id}...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print(f"Latest Reading for {device_id}: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching latest reading for device {device_id}: {e}")
        if e.response:
            print(f"Response content: {e.response.text}")

async def get_hourly_average_for_device(device_id: str, token: str):
    """
    Fetches the hourly average sensor readings for a specific device.
    """
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/sensors/{device_id}/hourly-average"
    print(f"Fetching hourly averages for device {device_id}...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print(f"Hourly Averages for {device_id}: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching hourly averages for device {device_id}: {e}")
        if e.response:
            print(f"Response content: {e.response.text}")

async def get_daily_summary_for_device(device_id: str, token: str):
    """
    Fetches the daily summary sensor readings for a specific device.
    """
    headers = {"Authorization": f"Bearer {token}"}
    # You can specify a date here, e.g., for today
    today = datetime.utcnow().strftime("%Y-%m-%d") # Use UTC now to match backend
    url = f"{BASE_URL}/sensors/{device_id}/daily-summary?date={today}"
    print(f"Fetching daily summary for device {device_id} (Date: {today})...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print(f"Daily Summary for {device_id}: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching daily summary for device {device_id}: {e}")
        if e.response:
            print(f"Response content: {e.response.text}")

async def main():
    token = await get_admin_token()
    devices = await get_all_devices(token)

    if not devices:
        print("No devices found. Please ensure test devices are created.")
        return

    # Use the first device found for testing
    test_device_id = devices[0]['id']
    print(f"\n--- Testing endpoints for device ID: {test_device_id} ---")

    await get_latest_reading_for_device(test_device_id, token)
    await get_hourly_average_for_device(test_device_id, token)
    await get_daily_summary_for_device(test_device_id, token)
    
    print("\n--- Testing complete ---")

if __name__ == "__main__":
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    print("Starting sensor endpoint tester...")
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nSensor endpoint tester stopped.")
    finally:
        loop.close()
