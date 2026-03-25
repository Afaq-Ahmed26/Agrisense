#!/usr/bin/env python3
"""
Quick script to check if backend is using real Firebase or mock.
"""

import sys
sys.path.insert(0, '/home/afaq-ahmed/Desktop/Agriscense/backend')

from app.services.firebase_service import firebase_service

print("\n" + "="*60)
print(" Firebase Service Status Check")
print("="*60 + "\n")

print(f"Is Mock Service: {firebase_service.is_mock}")
print(f"Database Client: {type(firebase_service.db).__name__}")

if firebase_service.is_mock:
    print("\n⚠️  WARNING: Using MOCK Firebase (data not persisted)")
    print("   Check backend/.env file and firebase-credentials.json")
else:
    print("\n✅ Using REAL Firebase (data will be persisted)")
    print(f"   Project ID: {firebase_service.db._database.database}")

print("\n" + "="*60 + "\n")
