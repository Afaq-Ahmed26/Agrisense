import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Firebase
config_path = os.getenv('FIREBASE_CONFIG_PATH', 'firebase-credentials.json')
cred = credentials.Certificate(config_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

REAL_DEVICE_ID = "esp32-b47cb8"

def delete_collection(collection_name, batch_size=50):
    """Deletes documents in a collection, sparing the real device data."""
    print(f"\n--- Cleaning Collection: {collection_name} ---")
    collection_ref = db.collection(collection_name)
    
    # Using list_documents() to avoid high "Read" quota usage 
    # (though some metadata reads might still occur)
    docs = list(collection_ref.list_documents())
    print(f"Found {len(docs)} documents in {collection_name}")
    
    deleted_count = 0
    spared_count = 0
    
    # Process in batches
    for i in range(0, len(docs), batch_size):
        batch = db.batch()
        current_batch = docs[i:i + batch_size]
        
        for doc_ref in current_batch:
            # We need to peek at the data to see if it belongs to our real device
            # This counts as a READ, but we have no choice if we want to be selective.
            # If your quota is TRULY at 100% and blocking, this script might fail.
            try:
                doc_snapshot = doc_ref.get()
                data = doc_snapshot.to_dict()
                
                # Logic: If it has a device_id and it's NOT our real one, delete it.
                # If it's an alert/notification for our device, keep it if it's recent? 
                # For now, let's just delete everything that isn't explicitly our device's sensor readings.
                
                should_delete = True
                
                if data:
                    did = data.get('device_id') or data.get('id')
                    if did == REAL_DEVICE_ID:
                        should_delete = False
                    
                    # For sensor_readings specific check
                    if collection_name == 'sensor_readings' and data.get('device_id') == REAL_DEVICE_ID:
                        should_delete = False
                
                if should_delete:
                    batch.delete(doc_ref)
                    deleted_count += 1
                else:
                    spared_count += 1
                    
            except Exception as e:
                print(f"Error checking document {doc_ref.id}: {e}")
                # If we can't read it due to quota, we might just have to stop
                if "Quota exceeded" in str(e):
                    print("🛑 Quota exceeded error triggered. Stopping cleanup.")
                    batch.commit()
                    return
        
        batch.commit()
        print(f"Progress: {i + len(current_batch)}/{len(docs)} processed...")

    print(f"Finished {collection_name}: Deleted {deleted_count}, Spared {spared_count}")

if __name__ == "__main__":
    print("🚀 Starting AgriSense Firestore Cleanup...")
    print(f"Target: Delete all data EXCEPT for device: {REAL_DEVICE_ID}")
    
    collections_to_clean = ['sensor_readings', 'alerts', 'notifications', 'activity_logs']
    
    for coll in collections_to_clean:
        delete_collection(coll)
        
    print("\n✅ Cleanup attempt finished.")
