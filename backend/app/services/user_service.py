import asyncio
import time
from typing import Optional, List
from datetime import datetime
import pytz
from app.models.user import User
from app.services.firebase_service import firebase_service
from app.repositories.user_repository import user_repository

# User cache to reduce Firestore reads
_user_cache = {}
_user_cache_time = {}
USER_CACHE_EXPIRY = 3600  # 1 hour in seconds


def invalidate_user_cache(uid: str) -> None:
    _user_cache.pop(uid, None)
    _user_cache_time.pop(uid, None)


async def get_user_from_firestore(uid: str, include_deleted: bool = False) -> Optional[User]:
    now = time.time()
    
    # Return from cache if fresh
    if uid in _user_cache and (now - _user_cache_time.get(uid, 0)) < USER_CACHE_EXPIRY:
        cached_user = _user_cache[uid]
        if not include_deleted and cached_user.is_deleted:
            return None
        return cached_user

    if user_repository.is_enabled():
        user = await asyncio.to_thread(user_repository.get_by_id, uid, include_deleted)
        if user:
            _user_cache[uid] = user
            _user_cache_time[uid] = now
        return user

    print(f"DEBUG: get_user_from_firestore - trying to fetch user with UID: {uid}")
    user_ref = firebase_service.db.collection('users').document(uid)
    
    # Use to_thread for blocking get()
    doc = await asyncio.to_thread(user_ref.get)
    
    if doc.exists:
        print(f"DEBUG: get_user_from_firestore - document found for UID: {uid}")
        user_data = doc.to_dict()
        if not include_deleted and user_data.get('is_deleted', False):
            return None
        
        try:
            user_data['id'] = doc.id # Add the document ID to the data
            user = User(**user_data)
            
            # Update cache
            _user_cache[uid] = user
            _user_cache_time[uid] = now
            
            return user
        except Exception as e:
            print(f"ERROR: get_user_from_firestore - Pydantic validation error for UID {uid}: {e}")
            return None

    else:
        print(f"DEBUG: get_user_from_firestore - document NOT found for UID: {uid}")
        return None

async def create_user_in_firestore(user: User):
    if user_repository.is_enabled():
        await asyncio.to_thread(user_repository.create, user)
        _user_cache[user.id] = user
        _user_cache_time[user.id] = time.time()
        return

    user_ref = firebase_service.db.collection('users').document(user.id)
    # Use to_thread for blocking set()
    await asyncio.to_thread(user_ref.set, user.model_dump(by_alias=True))
    _user_cache[user.id] = user
    _user_cache_time[user.id] = time.time()

async def update_user_in_firestore(uid: str, update_data: dict):
    if user_repository.is_enabled():
        await asyncio.to_thread(user_repository.update, uid, update_data)
        invalidate_user_cache(uid)
        return

    user_ref = firebase_service.db.collection('users').document(uid)
    # Use to_thread for blocking update()
    await asyncio.to_thread(user_ref.update, update_data)
    invalidate_user_cache(uid)

async def get_all_users_from_firestore(skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[User]:
    if user_repository.is_enabled():
        return await asyncio.to_thread(user_repository.get_all, skip, limit, include_deleted)

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
