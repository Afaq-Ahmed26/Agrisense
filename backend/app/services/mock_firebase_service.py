import json
from typing import Optional
from datetime import datetime
from unittest.mock import MagicMock


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


class MockUserMetadata:
    """Mock user metadata object"""
    
    def __init__(self):
        self.creation_timestamp = datetime.now().timestamp() * 1000  # milliseconds since epoch
        self.last_sign_in_timestamp = datetime.now().timestamp() * 1000


class MockFirebaseAuth:
    """Mock Firebase Authentication for development"""

    def __init__(self):
        self.users = {}  # In-memory storage for mock users

    def get_user_by_email(self, email: str):
        # Return a mock user object
        if email in self.users:
            user_data = self.users[email]
            if user_data.get('disabled', False): # Do not return disabled users
                return None
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
            'disabled': False # New field
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
                # Check if the user is disabled in mock auth
                for user_data in self.users.values():
                    if user_data['uid'] == payload_json.get('uid') and user_data.get('disabled', False):
                        raise Exception("User account is disabled.") # Simulate disabled user error
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

    def list_users(self, page_token: Optional[str] = None, max_results: int = 1000):
        # A very basic mock list users
        mock_users = []
        for user_data in list(self.users.values())[:max_results]:
            # Only list non-disabled users by default
            if not user_data.get('disabled', False):
                mock_users.append(MockFirebaseUser(user_data['uid'], user_data['email'], user_data.get('display_name'), user_data.get('disabled', False)))
        return mock_users, None # Return list and no next page token for simplicity


class MockFirebaseUser:
    """Mock Firebase user object"""

    def __init__(self, uid, email, display_name=None, disabled=False):
        self.uid = uid
        self.email = email
        self.display_name = display_name
        self.user_metadata = MockUserMetadata()
        self.disabled = disabled # New field