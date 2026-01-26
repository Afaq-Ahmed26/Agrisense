import pytest
import pytest_asyncio # Import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import MagicMock, patch
from app.main import app # Assuming your FastAPI app instance is named 'app' in main.py
from app.services.firebase_service import firebase_service, MockFirebaseAuth, MockFirestoreDB, MockFirebaseUser
from app.models.user import UserCreate, User
from datetime import datetime, timedelta

# Mock settings for testing
TEST_ACCESS_TOKEN_EXPIRE_MINUTES = 1

@pytest.fixture(name="test_app", scope="session")
def test_app_fixture():
    # Ensure firebase_service uses mock services for the entire test session
    firebase_service.setup_mock_service()
    yield app

@pytest_asyncio.fixture(name="client")
async def client_fixture(test_app):
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_firebase_auth():
    # Directly use the MockFirebaseAuth from firebase_service for consistency
    return firebase_service.auth

@pytest.fixture
def mock_firestore_db():
    # Directly use the MockFirestoreDB from firebase_service for consistency
    return firebase_service.db

@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "password": "StrongPassword123!",
        "username": "testuser",
        "role": "farmer"
    }

@pytest.fixture
def admin_user_data():
    return {
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "username": "adminuser",
        "role": "admin"
    }

# --- Utility Functions for Mocking ---
def create_mock_firebase_user(uid, email, display_name=None, disabled=False):
    user = MockFirebaseUser(uid, email, display_name, disabled)
    user.user_metadata = MagicMock()
    user.user_metadata.creation_timestamp = datetime.utcnow().timestamp() * 1000
    user.user_metadata.last_sign_in_timestamp = datetime.utcnow().timestamp() * 1000
    return user

def create_mock_firestore_user(uid, email, username, role, is_deleted=False, deleted_at=None):
    return {
        "id": uid,
        "email": email,
        "username": username,
        "role": role,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_deleted": is_deleted,
        "deleted_at": deleted_at
    }

# --- Tests start here ---

# Test registration endpoint
@pytest.mark.asyncio
async def test_register_user(client, mock_firebase_auth, mock_firestore_db, test_user_data):
    # Mock Firebase user creation
    mock_firebase_user_obj = create_mock_firebase_user("test_uid_123", test_user_data["email"], test_user_data["username"])
    
    with patch('app.services.firebase_service.firebase_service.create_firebase_user', return_value=mock_firebase_user_obj) as mock_create_user, \
         patch('app.services.firebase_service.firebase_service.get_user_by_email', return_value=None) as mock_get_user_by_email:
        
        response = await client.post("/auth/register", json=test_user_data)
        assert response.status_code == 200
        registered_user = response.json()
        assert registered_user["email"] == test_user_data["email"]
        assert registered_user["username"] == test_user_data["username"]
        assert registered_user["role"] == test_user_data["role"]
        assert registered_user["id"] == "test_uid_123"
        assert not registered_user["is_deleted"]

        # Verify Firebase Auth user was created
        mock_create_user.assert_called_once_with(
            email=test_user_data["email"],
            password=test_user_data["password"],
            display_name=test_user_data["username"]
        )
        mock_get_user_by_email.assert_called_once_with(test_user_data["email"])
        
        # Verify Firestore user was created
        firestore_user_doc = mock_firestore_db.collection('users').document("test_uid_123").get().to_dict()
        assert firestore_user_doc['email'] == test_user_data["email"]
        assert firestore_user_doc['username'] == test_user_data["username"]
        assert firestore_user_doc['role'] == test_user_data["role"]

# Test registration with existing email
@pytest.mark.asyncio
async def test_register_existing_email(client, mock_firebase_auth, mock_firestore_db, test_user_data):
    existing_uid = "existing_uid"
    # Setup mock to simulate existing user in Firebase Auth and Firestore (initially active)
    existing_firebase_user = create_mock_firebase_user(existing_uid, test_user_data["email"], test_user_data["username"])
    mock_firestore_db.collection('users').document(existing_uid).set(
        create_mock_firestore_user(existing_uid, test_user_data["email"], test_user_data["username"], test_user_data["role"])
    )

    with patch('app.services.firebase_service.firebase_service.get_user_by_email', return_value=existing_firebase_user) as mock_get_user_by_email:
        response = await client.post("/auth/register", json=test_user_data)
        assert response.status_code == 400
        assert "Email already registered and active" in response.json()["detail"]
        mock_get_user_by_email.assert_called_once_with(test_user_data["email"])
    
    # Test re-registration of a soft-deleted user
    soft_deleted_uid = "soft_deleted_uid"
    soft_deleted_email = "deleted@example.com"
    soft_deleted_username = "deleteduser"
    soft_deleted_role = "farmer"

    soft_deleted_firebase_user = create_mock_firebase_user(soft_deleted_uid, soft_deleted_email, soft_deleted_username, disabled=True)
    soft_deleted_firestore_user = create_mock_firestore_user(soft_deleted_uid, soft_deleted_email, soft_deleted_username, soft_deleted_role, is_deleted=True)
    mock_firestore_db.collection('users').document(soft_deleted_uid).set(soft_deleted_firestore_user)

    re_register_data = {
        "email": soft_deleted_email,
        "password": "NewStrongPassword123!",
        "username": "newdeleteduser",
        "role": "farmer"
    }

    with patch('app.services.firebase_service.firebase_service.get_user_by_email', return_value=soft_deleted_firebase_user) as mock_get_user_by_email_deleted, \
         patch('app.services.firebase_service.firebase_service.get_user_by_uid', return_value=soft_deleted_firebase_user) as mock_get_user_by_uid_deleted, \
         patch('app.services.firebase_service.firebase_service.enable_firebase_user', return_value=True) as mock_enable_firebase_user, \
         patch('app.services.firebase_service.firebase_service.update_firebase_user') as mock_update_firebase_user, \
         patch('app.services.user_service.update_user_in_firestore') as mock_update_firestore:
        
        response = await client.post("/auth/register", json=re_register_data)
        assert response.status_code == 200
        reactivated_user = response.json()
        assert reactivated_user["email"] == re_register_data["email"]
        assert reactivated_user["username"] == re_register_data["username"]
        assert reactivated_user["role"] == re_register_data["role"]
        assert reactivated_user["id"] == soft_deleted_uid
        assert not reactivated_user["is_deleted"]

        mock_get_user_by_email_deleted.assert_called_once_with(re_register_data["email"])
        mock_get_user_by_uid_deleted.assert_called_once_with(soft_deleted_uid)
        mock_enable_firebase_user.assert_called_once_with(soft_deleted_uid)
        mock_update_firestore.assert_called_once_with(soft_deleted_uid, {"is_deleted": False, "deleted_at": None})
        mock_update_firebase_user.assert_called_once_with(soft_deleted_uid, display_name=re_register_data["username"])

# Test login endpoint
@pytest.mark.asyncio
async def test_login_user(client, mock_firebase_auth, mock_firestore_db, test_user_data):
    # Mock Firebase token verification
    mock_decoded_token = {
        "uid": "test_uid_123",
        "email": test_user_data["email"],
        "exp": (datetime.utcnow() + timedelta(minutes=TEST_ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()
    }
    
    with patch('app.services.firebase_service.firebase_service.verify_token', return_value=mock_decoded_token) as mock_verify_token:
        # Create a mock Firestore user for role retrieval
        firestore_user_obj = create_mock_firestore_user(
            "test_uid_123", test_user_data["email"], test_user_data["username"], test_user_data["role"]
        )
        mock_firestore_db.collection('users').document("test_uid_123").set(firestore_user_obj)
        
        response = await client.post("/auth/login", json={"id_token": "mock_firebase_id_token"})
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

        mock_verify_token.assert_called_once_with("mock_firebase_id_token")
# Test get current user endpoint (/users/me)
@pytest.mark.asyncio
async def test_get_current_user(client, mock_firebase_auth, mock_firestore_db, test_user_data):
    # Simulate a logged-in user by mocking verify_token in middleware
    mock_token_payload = {
        "uid": "current_user_uid",
        "email": "current@example.com",
        "role": "farmer",
        "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp()
    }
    # patch the middleware's verify_token directly to control the request.state.user
    with patch('app.services.firebase_service.firebase_service.verify_token', return_value=mock_token_payload):
        with patch('app.services.firebase_service.firebase_service.get_user_by_uid', return_value=create_mock_firebase_user(
            "current_user_uid", "current@example.com", "currentuser"
        )) as mock_get_user_by_uid:
            mock_firestore_db.collection('users').document("current_user_uid").set(
                create_mock_firestore_user("current_user_uid", "current@example.com", "currentuser", "farmer")
            )
            response = await client.get("/users/me", headers={"Authorization": "Bearer mock_token"})
            assert response.status_code == 200
            user_info = response.json()
            assert user_info["email"] == "current@example.com"
            assert user_info["username"] == "currentuser"
            assert user_info["role"] == "farmer"
            assert user_info["id"] == "current_user_uid"
            mock_get_user_by_uid.assert_called_once_with("current_user_uid")


# Test update user endpoint
@pytest.mark.asyncio
async def test_update_user(client, mock_firebase_auth, mock_firestore_db, test_user_data):
    user_id = "user_to_update_uid"
    
    # Simulate a logged-in user (admin)
    mock_admin_payload = {
        "uid": "admin_uid",
        "email": "admin@example.com",
        "role": "admin",
        "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp()
    }
    
    # Pre-populate mock Firebase Auth and Firestore for the user to be updated
    original_fb_user = create_mock_firebase_user(user_id, "old@example.com", "oldusername")
    
    with patch('app.services.firebase_service.firebase_service.get_user_by_uid', return_value=original_fb_user), \
         patch('app.services.firebase_service.firebase_service.get_user_by_email', return_value=original_fb_user): # Added get_user_by_email patch for safety
        original_firestore_user_data = create_mock_firestore_user(user_id, "old@example.com", "oldusername", "farmer")
        mock_firestore_db.collection('users').document(user_id).set(original_firestore_user_data)

    update_payload = {
        "email": "new@example.com",
        "username": "newusername",
        "role": "middleman"
    }

    with patch('app.services.firebase_service.firebase_service.verify_token', return_value=mock_admin_payload), \
         patch('app.services.firebase_service.firebase_service.update_firebase_user', 
               return_value=create_mock_firebase_user(user_id, update_payload["email"], update_payload["username"])) as mock_update_firebase_user, \
         patch('app.services.user_service.update_user_in_firestore') as mock_update_user_in_firestore:

        response = await client.put(f"/users/{user_id}", json=update_payload, headers={"Authorization": "Bearer mock_admin_token"})
        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["email"] == update_payload["email"]
        assert updated_user["username"] == update_payload["username"]
        assert updated_user["role"] == update_payload["role"]

        # Verify Firebase Auth update
        mock_update_firebase_user.assert_called_once_with(
            user_id, email=update_payload["email"], display_name=update_payload["username"]
        )
        # Verify Firestore update
        mock_update_user_in_firestore.assert_called_once()
        args, kwargs = mock_update_user_in_firestore.call_args
        assert args[0] == user_id
        assert kwargs['username'] == update_payload["username"]
        assert kwargs['email'] == update_payload["email"]
        assert kwargs['role'] == update_payload["role"]
        assert "updated_at" in kwargs

        # Assert the state in mock firestore
        firestore_updated_data = mock_firestore_db.collection('users').document(user_id).get().to_dict()
        assert firestore_updated_data['email'] == update_payload["email"]
        assert firestore_updated_data['username'] == update_payload["username"]
        assert firestore_updated_data['role'] == update_payload["role"]
        assert "updated_at" in firestore_updated_data


# Test delete user endpoint (hard delete Firebase, soft delete Firestore)
@pytest.mark.asyncio
async def test_delete_user(client, mock_firebase_auth, mock_firestore_db):
    user_id = "user_to_delete_uid"
    
    # Simulate a logged-in user (admin)
    mock_admin_payload = {
        "uid": "admin_uid",
        "email": "admin@example.com",
        "role": "admin",
        "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp()
    }

    # Pre-populate mock Firebase Auth and Firestore for the user to be deleted
    mock_firebase_user_obj = create_mock_firebase_user(user_id, "delete@example.com", "deleteuser")
    with patch('app.services.firebase_service.firebase_service.get_user_by_uid', return_value=mock_firebase_user_obj):
        mock_firestore_db.collection('users').document(user_id).set(
            create_mock_firestore_user(user_id, "delete@example.com", "deleteuser", "farmer")
        )

    with patch('app.services.firebase_service.firebase_service.verify_token', return_value=mock_admin_payload), \
         patch('app.services.firebase_service.firebase_service.delete_firebase_user', return_value=True) as mock_delete_firebase_user, \
         patch('app.services.user_service.update_user_in_firestore') as mock_update_user_in_firestore:

        response = await client.delete(f"/users/{user_id}", headers={"Authorization": "Bearer mock_admin_token"})
        assert response.status_code == 200
        assert "User deleted permanently from Firebase Auth and marked as deleted in Firestore." in response.json()["message"]

        # Verify Firebase Auth user was hard deleted
        mock_delete_firebase_user.assert_called_once_with(user_id)
        
        # Verify Firestore user was soft deleted
        mock_update_user_in_firestore.assert_called_once()
        args, kwargs = mock_update_user_in_firestore.call_args
        assert args[0] == user_id
        assert kwargs['is_deleted'] is True
        assert kwargs['deleted_at'] is not None

        # Assert the state in mock firestore
        firestore_user_doc = mock_firestore_db.collection('users').document(user_id).get().to_dict()
        assert firestore_user_doc['is_deleted'] is True
        assert firestore_user_doc['deleted_at'] is not None
