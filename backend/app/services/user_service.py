from typing import Optional, List
from datetime import datetime
import pytz
from app.models.user import User
from app.services.firebase_service import firebase_service


def get_user_from_firestore(uid: str, include_deleted: bool = False) -> Optional[User]:
    user_ref = firebase_service.db.collection('users').document(uid)
    doc = user_ref.get()
    if doc.exists:
        user_data = doc.to_dict()
        if not include_deleted and user_data.get('is_deleted', False):
            return None
        return User(**user_data)
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
