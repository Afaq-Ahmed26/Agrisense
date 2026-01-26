from typing import Optional, List
from datetime import datetime
import pytz
from app.models.user import User
from app.services.firebase_service import firebase_service


def get_user_from_firestore(uid: str, include_deleted: bool = False) -> Optional[User]:
    print(f"DEBUG: get_user_from_firestore - trying to fetch user with UID: {uid}")
    user_ref = firebase_service.db.collection('users').document(uid)
    doc = user_ref.get()
    if doc.exists:
        print(f"DEBUG: get_user_from_firestore - document found for UID: {uid}")
        user_data = doc.to_dict()
        print(f"DEBUG: get_user_from_firestore - user_data from DB: {user_data}")
        if not include_deleted and user_data.get('is_deleted', False):
            print(f"DEBUG: get_user_from_firestore - user {uid} is deleted and include_deleted is False.")
            return None
        
        try:
            user_data['id'] = doc.id # Add the document ID to the data
            user = User(**user_data)
            print(f"DEBUG: get_user_from_firestore - successfully parsed user data for UID: {uid}")
            return user
        except Exception as e:
            print(f"ERROR: get_user_from_firestore - Pydantic validation error for UID {uid}: {e}")
            return None

    else:
        print(f"DEBUG: get_user_from_firestore - document NOT found for UID: {uid}")
        return None

def create_user_in_firestore(user: User):
    user_ref = firebase_service.db.collection('users').document(user.id)
    user_ref.set(user.model_dump(by_alias=True)) # Use model_dump for Pydantic v2 and by_alias=True

def update_user_in_firestore(uid: str, update_data: dict):
    user_ref = firebase_service.db.collection('users').document(uid)
    user_ref.update(update_data)

def get_all_users_from_firestore(skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[User]:
    users_ref = firebase_service.db.collection('users')
    query = users_ref.order_by('created_at')

    if not include_deleted:
        query = query.where('is_deleted', '==', False)

    docs = query.stream()

    all_users = []
    for doc in docs:
        user_data = doc.to_dict()
        all_users.append(User(**user_data))

    return all_users[skip : skip + limit]
