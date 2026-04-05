"""
Test script to verify Firebase configuration and connectivity
"""
import asyncio
import os
from app.services.firebase_service import firebase_service


async def test_firebase_connection():
    print("Testing Firebase connection...")

    try:
        # Get the Firestore client
        db = firebase_service.get_firestore_client()
        print("✓ Successfully connected to Firestore")

        # Test writing and reading a document
        test_doc_ref = db.collection('test').document('connection_test')
        test_data = {
            'test_field': 'connection_successful',
            'timestamp': 'SERVER_TIMESTAMP'  # Placeholder since we can't await here
        }

        # Write test data
        test_doc_ref.set(test_data)
        print("✓ Successfully wrote test data to Firestore")

        # Read test data back
        doc_snapshot = test_doc_ref.get()
        if doc_snapshot.exists:
            print("✓ Successfully read test data from Firestore")
            print(f"  Retrieved data: {doc_snapshot.to_dict()}")
        else:
            print("✗ Failed to read test data from Firestore")

        # Clean up test data
        test_doc_ref.delete()
        print("✓ Cleaned up test data")

        print("\nFirebase connection test completed successfully!")
        return True

    except Exception as e:
        print(f"✗ Error connecting to Firebase: {str(e)}")
        return False


if __name__ == "__main__":
    # Import here to avoid conflicts
    from firebase_admin import firestore

    asyncio.run(test_firebase_connection())