import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase
# Path adjusted to be relative to backend/ directory or absolute
cred_path = "firebase-credentials.json"
if not os.path.exists(cred_path):
    cred_path = "app/firebase-credentials.json"

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

def cleanup_alerts():
    print("Fetching all open alerts...")
    alerts_ref = db.collection('alerts')
    docs = alerts_ref.stream()
    
    count = 0
    batch = db.batch()
    batch_count = 0
    
    for doc in docs:
        batch.delete(doc.reference)
        batch_count += 1
        count += 1
        
        # Firestore batch limit is 500
        if batch_count >= 499:
            batch.commit()
            print(f"Deleted {count} alerts so far...")
            batch = db.batch()
            batch_count = 0
    
    if batch_count > 0:
        batch.commit()
    
    print(f"✅ Deleted {count} total alerts")

def cleanup_old_sensor_readings():
    print("Fetching sensor readings...")
    readings_ref = db.collection('sensor_readings')
    docs = readings_ref.stream()
    
    count = 0
    batch = db.batch()
    batch_count = 0
    
    for doc in docs:
        # Keep the last 100 readings for testing if you want, but this script deletes all
        batch.delete(doc.reference)
        batch_count += 1
        count += 1
        
        if batch_count >= 499:
            batch.commit()
            print(f"Deleted {count} readings so far...")
            batch = db.batch()
            batch_count = 0
    
    if batch_count > 0:
        batch.commit()
    
    print(f"✅ Deleted {count} total sensor readings")

if __name__ == "__main__":
    print("=== AgriSense Firestore Cleanup ===")
    try:
        cleanup_alerts()
        cleanup_old_sensor_readings()
        print("=== Cleanup Complete ===")
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
