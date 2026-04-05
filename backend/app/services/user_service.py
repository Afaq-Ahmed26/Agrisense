import asyncio
from typing import Optional, List
from datetime import datetime
import pytz
from app.models.user import User
from app.services.firebase_service import firebase_service


async def get_user_from_firestore(uid: str, include_deleted: bool = False) -> Optional[User]:
    print(f"DEBUG: get_user_from_firestore - trying to fetch user with UID: {uid}")
    user_ref = firebase_service.db.collection('users').document(uid)
    
    # Use to_thread for blocking get()
    doc = await asyncio.to_thread(user_ref.get)
    
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

async def create_user_in_firestore(user: User):
    user_ref = firebase_service.db.collection('users').document(user.id)
    # Use to_thread for blocking set()
    await asyncio.to_thread(user_ref.set, user.model_dump(by_alias=True))

async def update_user_in_firestore(uid: str, update_data: dict):
    user_ref = firebase_service.db.collection('users').document(uid)
    # Use to_thread for blocking update()
    await asyncio.to_thread(user_ref.update, update_data)

async def get_all_users_from_firestore(skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[User]:
    users_ref = firebase_service.db.collection('users')
    query = users_ref.order_by('created_at')

    if not include_deleted:
        query = query.where('is_deleted', '==', False)

    # Use to_thread for blocking stream()
    docs = await asyncio.to_thread(lambda: [doc for doc in query.stream()])

    all_users = []
    for doc in docs:
        user_data = doc.to_dict()
        user_data['id'] = doc.id # Add the document ID
        all_users.append(User(**user_data))

    return all_users[skip : skip + limit]
