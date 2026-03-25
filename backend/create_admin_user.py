#!/usr/bin/env python3
"""
Create admin user in Firebase Authentication.
Run this once to set up the admin account for frontend login.
"""

import requests
import json

# Firebase API Key (from .env)
FIREBASE_API_KEY = "AIzaSyCI3iqUpHuM4PKqsapOPi0D2TgsXt-f6U8"

# Admin user credentials
ADMIN_EMAIL = "admin@agrisense.com"
ADMIN_PASSWORD = "admin123"

def create_admin_user():
    """Create admin user in Firebase Auth using REST API"""
    
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "returnSecureToken": True
    }
    
    print("\n" + "="*60)
    print(" Creating Admin User in Firebase Authentication")
    print("="*60 + "\n")
    print(f"Email: {ADMIN_EMAIL}")
    print(f"Password: {ADMIN_PASSWORD}")
    print()
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ SUCCESS: Admin user created!")
            data = response.json()
            print(f"\nUser ID: {data.get('localId', 'N/A')}")
            print(f"Email: {data.get('email', 'N/A')}")
            print(f"Token: {data.get('idToken', 'N/A')[:50]}...")
            print("\n" + "="*60)
            print("You can now login to the frontend with these credentials:")
            print(f"  Email: {ADMIN_EMAIL}")
            print(f"  Password: {ADMIN_PASSWORD}")
            print("="*60 + "\n")
            return True
        else:
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', 'Unknown error')
            
            if "EMAIL_EXISTS" in error_message:
                print("⚠️  User already exists!")
                print(f"   Email: {ADMIN_EMAIL}")
                print("\nYou can still login with:")
                print(f"  Email: {ADMIN_EMAIL}")
                print(f"  Password: {ADMIN_PASSWORD}")
                print("="*60 + "\n")
            else:
                print(f"❌ ERROR: {error_message}")
                print(f"Response: {error_data}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


if __name__ == "__main__":
    create_admin_user()
