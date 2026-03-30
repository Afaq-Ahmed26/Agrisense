import os
from typing import Optional, List, Dict, Any
from app.config import settings
from unittest.mock import MagicMock
import json
from datetime import datetime
import uuid # For generating unique file names
from google.cloud.firestore_v1.base_query import FieldFilter # Import FieldFilter


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
        self.documents = {}  # Stores doc_id -> MockDocumentReference

    def document(self, doc_id):
        if doc_id not in self.documents:
            self.documents[doc_id] = MockDocumentReference(self, doc_id)
        return self.documents[doc_id]

    def add(self, data):
        # Generate a mock document ID
        doc_id = str(uuid.uuid4())
        doc_ref = self.document(doc_id)
        doc_ref.set(data)
        return doc_ref, doc_id

    def stream(self):
        # Return all documents in the collection
        for doc_ref in self.documents.values():
            yield doc_ref.get()

    def where(self, field, op, value):
        # Basic mock for filtering
        filtered_docs = []
        for doc_ref in self.documents.values():
            doc_data = doc_ref.get().to_dict()
            if doc_data and field in doc_data:
                if op == '==' and doc_data[field] == value:
                    filtered_docs.append(doc_ref)
                # Add more operators as needed for mock
        new_mock_collection = MockCollection(self.name)
        for doc_ref in filtered_docs:
            new_mock_collection.document(doc_ref.doc_id).set(doc_ref.get().to_dict())
        return new_mock_collection
    
    def order_by(self, field, direction="asc"):
        # Basic mock for ordering
        ordered_docs = sorted(self.documents.values(), key=lambda doc_ref: doc_ref.get().to_dict().get(field, None), reverse=(direction=="desc"))
        new_mock_collection = MockCollection(self.name)
        for doc_ref in ordered_docs:
            new_mock_collection.document(doc_ref.doc_id).set(doc_ref.get().to_dict())
        return new_mock_collection
    
    def limit(self, count):
        # Basic mock for limiting
        limited_docs = list(self.documents.values())[:count]
        new_mock_collection = MockCollection(self.name)
        for doc_ref in limited_docs:
            new_mock_collection.document(doc_ref.doc_id).set(doc_ref.get().to_dict())
        return new_mock_collection


class MockDocumentReference:
    """Mock Firestore document reference"""

    def __init__(self, collection, doc_id):
        self.collection = collection
        self.id = doc_id # Add id attribute
        if doc_id in collection.documents: # Check if already exists
            self.data = collection.documents[doc_id].data
        else:
            self.data = {}  # Initialize to empty dict

    def set(self, data):
        print(f"DEBUG: MockDocumentReference.set called for {self.id} with data: {data}")
        self.data = data
        self.collection.documents[self.id] = self # Ensure collection keeps reference to this instance

    def update(self, update_data: dict):
        print(f"DEBUG: MockDocumentReference.update called for {self.id} with data: {update_data}")
        self.data.update(update_data)
        self.collection.documents[self.id] = self

    def get(self):
        print(f"DEBUG: MockDocumentReference.get called for {self.id}, returning snapshot with data: {self.data}")
        return MockDocumentSnapshot(self.id, self.data) # Pass self.data directly


class MockDocumentSnapshot:
    """Mock Firestore document snapshot"""

    def __init__(self, id, data):
        self.id = id
        self._data = data
        print(f"DEBUG: MockDocumentSnapshot.__init__ for {self.id} with data: {self._data}")

    def to_dict(self):
        print(f"DEBUG: MockDocumentSnapshot.to_dict called for {self.id}, returning: {self._data}")
        return self._data

    @property
    def exists(self):
        return self._data is not None and bool(self._data)


class MockFirebaseAuth:
    """Mock Firebase Authentication for development"""

    def __init__(self):
        self.users = {}  # In-memory storage for mock users

    def get_user_by_email(self, email: str):
        # Return a mock user object
        if email in self.users:
            user_data = self.users[email]
            return MockFirebaseUser(user_data['uid'], user_data['email'], user_data.get('display_name'), user_data.get('disabled', False))
        return None

    def create_user(self, email: str, password: str, display_name: str = None):
        # Create a mock user
        uid = f"mock_uid_{len(self.users) + 1}"
        user_data = {
            'uid': uid,
            'email': email,
            'display_name': display_name,
            'password': password,  # In a real implementation, this would be hashed
            'user_metadata': MockUserMetadata(),
            'disabled': False # New: user is active by default
        }
        self.users[email] = user_data
        return MockFirebaseUser(uid, email, display_name, disabled=False)

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
                return {"sub": "mock_user", "email": "mock@example.com", "uid": "mock_uid_1", "role": "farmer", "exp": datetime.now().timestamp() + 3600}
        except Exception as e:
            print(f"Error decoding token: {e}")
            return {"sub": "mock_user", "email": "mock@example.com", "uid": "mock_uid_1", "role": "farmer", "exp": datetime.now().timestamp() + 3600}

    def get_user(self, uid: str):
        for user_data in self.users.values():
            if user_data['uid'] == uid:
                return MockFirebaseUser(user_data['uid'], user_data['email'], user_data.get('display_name'), user_data.get('disabled', False))
        return None

    def update_user(self, uid: str, **kwargs):
        for email, user_data in self.users.items():
            if user_data['uid'] == uid:
                for key, value in kwargs.items():
                    user_data[key] = value
                return MockFirebaseUser(user_data['uid'], user_data['email'], user_data.get('display_name'), user_data.get('disabled', False))
        return None

    def delete_user(self, uid: str):
        for email, user_data in list(self.users.items()):
            if user_data['uid'] == uid:
                del self.users[email]
                return True
        return False
    
    def disable_user(self, uid: str):
        for email, user_data in self.users.items():
            if user_data['uid'] == uid:
                user_data['disabled'] = True
                return MockFirebaseUser(user_data['uid'], user_data['email'], user_data.get('display_name'), disabled=True)
        return None
    
    def enable_user(self, uid: str):
        for email, user_data in self.users.items():
            if user_data['uid'] == uid:
                user_data['disabled'] = False
                return MockFirebaseUser(user_data['uid'], user_data['email'], user_data.get('display_name'), disabled=False)
        return None

    def list_users(self, page_token: Optional[str] = None, max_results: int = 1000):
        # A very basic mock list users
        mock_users = []
        for user_data in list(self.users.values())[:max_results]:
            mock_users.append(MockFirebaseUser(user_data['uid'], user_data['email'], user_data.get('display_name'), user_data.get('disabled', False)))
        return mock_users, None # Return list and no next page token for simplicity



class MockFirebaseUser:
    """Mock Firebase user object"""

    def __init__(self, uid, email, display_name=None, disabled: bool = False):
        self.uid = uid
        self.email = email
        self.display_name = display_name
        self.user_metadata = MockUserMetadata()
        self.disabled = disabled


class MockUserMetadata:
    """Mock user metadata"""

    def __init__(self):
        self.creation_timestamp = datetime.utcnow().timestamp() * 1000  # Firestore uses milliseconds
        self.last_sign_in_timestamp = datetime.utcnow().timestamp() * 1000


class FirebaseService:
    def __init__(self):
        # Check if Firebase credentials are available
        if settings.FIREBASE_CONFIG_PATH or settings.FIREBASE_ADMIN_SDK_CONFIG or settings.FIREBASE_PROJECT_ID:
            try:
                import firebase_admin
                from firebase_admin import credentials, firestore, auth

                # Initialize Firebase Admin SDK if not already initialized
                if not firebase_admin._apps:
                    if settings.FIREBASE_CONFIG_PATH:
                        cred = credentials.Certificate(settings.FIREBASE_CONFIG_PATH)
                    elif settings.FIREBASE_ADMIN_SDK_CONFIG:
                        # Parse the JSON string from environment variable
                        cred_json = json.loads(settings.FIREBASE_ADMIN_SDK_CONFIG)
                        cred = credentials.Certificate(cred_json)
                    else:
                        # Use default credentials if available (for Google Cloud environment)
                        cred = credentials.ApplicationDefault()

                    firebase_admin.initialize_app(cred, {
                        'projectId': settings.FIREBASE_PROJECT_ID if settings.FIREBASE_PROJECT_ID else cred.project_id, # Use project ID from settings or credential
                    })

                self.db = firestore.client()
                self.auth = auth
                self.is_mock = False
            except Exception as e:
                import traceback
                print(f"Firebase initialization FAILED: {e}. Using mock service.")
                traceback.print_exc() # Print full traceback
                self.setup_mock_service()
        else:
            print("Firebase credentials not configured. Using mock service.")
            self.setup_mock_service()

    def setup_mock_service(self):
        """Set up mock Firebase services for development"""
        self.db = MockFirestoreDB()
        self.auth = MockFirebaseAuth()
        self.is_mock = True
        
        # Seed default user
        admin_email = "afaqahmad16007@gmail.com"
        admin_uid = "qsmULXbieEdDtufceT4SrkbA3tH2"
        self.auth.users[admin_email] = {
            'uid': admin_uid,
            'email': admin_email,
            'display_name': "Afaq Ahmed",
            'password': "password",
            'user_metadata': MockUserMetadata(),
            'role': 'admin'
        }
        
        # Seed Firestore user profile
        self.db.collection('users').document(admin_uid).set({
            'id': admin_uid,
            'email': admin_email,
            'username': "Afaq Ahmed",
            'role': 'admin',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_deleted': False
        })

        # Seed the ESP32 device
        device_id = "esp32-b47cb8"
        self.db.collection('devices').document(device_id).set({
            'id': device_id,
            'name': "ESP32 AgriSense Node",
            'location': "Main Field",
            'owner_id': admin_uid,
            'type': "irrigation_device",
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        print(f"DEBUG: Mock Firebase seeded with user {admin_email} and device {device_id}")

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

    def get_user_by_uid(self, uid: str):
        try:
            if self.is_mock:
                return self.auth.get_user(uid)
            else:
                user = self.auth.get_user(uid)
                return user
        except Exception as e:
            print(f"Error getting user by UID: {e}")
            return None

    def update_firebase_user(self, uid: str, **kwargs):
        try:
            if self.is_mock:
                return self.auth.update_user(uid, **kwargs)
            else:
                user = self.auth.update_user(uid, **kwargs)
                return user
        except Exception as e:
            print(f"Error updating Firebase user: {e}")
            return None

    def delete_firebase_user(self, uid: str):
        try:
            if self.is_mock:
                return self.auth.delete_user(uid)
            else:
                self.auth.delete_user(uid)
                return True
        except Exception as e:
            print(f"Error deleting Firebase user: {e}")
            return False
            
    def disable_firebase_user(self, uid: str):
        try:
            if self.is_mock:
                return self.auth.disable_user(uid)
            else:
                self.auth.update_user(uid, disabled=True)
                return True
        except Exception as e:
            print(f"Error disabling Firebase user: {e}")
            return False

    def enable_firebase_user(self, uid: str):
        try:
            if self.is_mock:
                return self.auth.enable_user(uid)
            else:
                self.auth.update_user(uid, disabled=False)
                return True
        except Exception as e:
            print(f"Error enabling Firebase user: {e}")
            return False

    def list_firebase_users(self, page_token: Optional[str] = None, max_results: int = 1000):
        try:
            if self.is_mock:
                return self.auth.list_users(page_token, max_results)
            else:
                users_page = self.auth.list_users(page_token=page_token, max_results=max_results)
                return users_page.users, users_page.page_token
        except Exception as e:
            print(f"Error listing Firebase users: {e}")
            return [], None




# Global instance
firebase_service = FirebaseService()