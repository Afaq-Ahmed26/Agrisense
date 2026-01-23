import os
from typing import Optional
from app.config import settings
from unittest.mock import MagicMock
import json
from datetime import datetime


class MockFirestoreDB:
    """Mock Firestore database for development without Firebase"""

    def __init__(self):
        self.collections = {}

    def collection(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name)
        return self.collections[name]


class MockCollection:
    """Mock Firestore collection"""

    def __init__(self, name):
        self.name = name
        self.documents = {}

    def document(self, doc_id):
        if doc_id not in self.documents:
            self.documents[doc_id] = MockDocumentReference(self, doc_id)
        return self.documents[doc_id]

    def add(self, data):
        # Generate a mock document ID
        doc_id = f"mock_doc_{len(self.documents) + 1}"
        self.document(doc_id).set(data)
        return self.document(doc_id), doc_id


class MockDocumentReference:
    """Mock Firestore document reference"""

    def __init__(self, collection, doc_id):
        self.collection = collection
        self.doc_id = doc_id
        self.data = None

    def set(self, data):
        self.data = data

    def get(self):
        return MockDocumentSnapshot(self.doc_id, self.data if self.data is not None else {})


class MockDocumentSnapshot:
    """Mock Firestore document snapshot"""

    def __init__(self, id, data):
        self.id = id
        self._data = data

    def to_dict(self):
        return self._data

    @property
    def exists(self):
        return self._data is not None


class MockFirebaseAuth:
    """Mock Firebase Authentication for development"""

    def __init__(self):
        self.users = {}  # In-memory storage for mock users

    def get_user_by_email(self, email: str):
        # Return a mock user object
        if email in self.users:
            user_data = self.users[email]
            return MockFirebaseUser(user_data['uid'], user_data['email'], user_data.get('display_name'))
        return None

    def create_user(self, email: str, password: str, display_name: str = None):
        # Create a mock user
        uid = f"mock_uid_{len(self.users) + 1}"
        user_data = {
            'uid': uid,
            'email': email,
            'display_name': display_name,
            'password': password,  # In a real implementation, this would be hashed
            'user_metadata': MockUserMetadata()
        }
        self.users[email] = user_data
        return MockFirebaseUser(uid, email, display_name)

    def verify_id_token(self, token: str):
        # Decode and verify the token (simplified for mock)
        # In a real implementation, this would use python-jose to decode JWT
        try:
            # For mock purposes, we'll just return a simple payload
            # assuming the token contains user info in a simple format
            import base64
            # Split the token to get the payload part (second part of JWT)
            parts = token.split('.')
            if len(parts) >= 2:
                # Decode the payload (add padding if needed)
                payload = parts[1]
                # Add padding if needed
                payload += '=' * (4 - len(payload) % 4)
                decoded_payload = base64.b64decode(payload)
                payload_json = json.loads(decoded_payload)
                return payload_json
            else:
                # If not a proper JWT, return a default payload
                return {"sub": "mock_user", "role": "farmer", "exp": datetime.now().timestamp() + 3600}
        except Exception as e:
            print(f"Error decoding token: {e}")
            return {"sub": "mock_user", "role": "farmer", "exp": datetime.now().timestamp() + 3600}


class MockFirebaseUser:
    """Mock Firebase user object"""

    def __init__(self, uid, email, display_name=None):
        self.uid = uid
        self.email = email
        self.display_name = display_name
        self.user_metadata = MockUserMetadata()


class MockUserMetadata:
    """Mock user metadata"""

    def __init__(self):
        self.creation_timestamp = datetime.utcnow().timestamp() * 1000  # Firestore uses milliseconds
        self.last_sign_in_timestamp = datetime.utcnow().timestamp() * 1000


class FirebaseService:
    def __init__(self):
        # Check if Firebase credentials are available
        if settings.FIREBASE_CONFIG_PATH or settings.FIREBASE_PROJECT_ID:
            try:
                import firebase_admin
                from firebase_admin import credentials, firestore, auth

                # Initialize Firebase Admin SDK if not already initialized
                if not firebase_admin._apps:
                    if settings.FIREBASE_CONFIG_PATH:
                        cred = credentials.Certificate(settings.FIREBASE_CONFIG_PATH)
                    else:
                        # Use default credentials if available (for Google Cloud environment)
                        cred = credentials.ApplicationDefault()

                    firebase_admin.initialize_app(cred, {
                        'projectId': settings.FIREBASE_PROJECT_ID,
                    })

                self.db = firestore.client()
                self.auth = auth
                self.is_mock = False
            except Exception as e:
                print(f"Firebase initialization failed: {e}. Using mock service.")
                self.setup_mock_service()
        else:
            print("Firebase credentials not configured. Using mock service.")
            self.setup_mock_service()

    def setup_mock_service(self):
        """Set up mock Firebase services for development"""
        self.db = MockFirestoreDB()
        self.auth = MockFirebaseAuth()
        self.is_mock = True

    def get_firestore_client(self):
        return self.db

    def get_user_by_email(self, email: str):
        try:
            if self.is_mock:
                return self.auth.get_user_by_email(email)
            else:
                user = self.auth.get_user_by_email(email)
                return user
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None

    def create_firebase_user(self, email: str, password: str, display_name: str = None):
        try:
            if self.is_mock:
                return self.auth.create_user(email, password, display_name)
            else:
                user = self.auth.create_user(
                    email=email,
                    password=password,
                    display_name=display_name
                )
                return user
        except Exception as e:
            print(f"Error creating Firebase user: {e}")
            return None

    def verify_token(self, token: str):
        try:
            if self.is_mock:
                return self.auth.verify_id_token(token)
            else:
                decoded_token = self.auth.verify_id_token(token)
                return decoded_token
        except Exception as e:
            print(f"Error verifying token: {e}")
            return None


# Global instance
firebase_service = FirebaseService()