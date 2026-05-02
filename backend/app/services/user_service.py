import asyncio
import time
from typing import Optional, List
from datetime import datetime
from app.models.user import User
from app.repositories.user_repository import user_repository

# User cache to reduce DB reads
_user_cache = {}
_user_cache_time = {}
USER_CACHE_EXPIRY = 3600  # 1 hour in seconds


def invalidate_user_cache(uid: str) -> None:
    _user_cache.pop(uid, None)
    _user_cache_time.pop(uid, None)


async def get_user_from_postgres(uid: str):
    """Fetch user profile from PostgreSQL by Firebase UID"""
    from app.repositories.user_repository import user_repository
    user = await asyncio.to_thread(user_repository.get_by_id, uid)
    return user


async def get_user(uid: str, include_deleted: bool = False) -> Optional[User]:
    now = time.time()
    
    # Return from cache if fresh
    if uid in _user_cache and (now - _user_cache_time.get(uid, 0)) < USER_CACHE_EXPIRY:
        cached_user = _user_cache[uid]
        if not include_deleted and cached_user.is_deleted:
            return None
        return cached_user

    # Always use user_repository (PostgreSQL)
    user = await asyncio.to_thread(user_repository.get_by_id, uid, include_deleted)
    if user:
        _user_cache[uid] = user
        _user_cache_time[uid] = now
        return user

    return None

async def create_user(user: User):
    # Always use user_repository (PostgreSQL)
    await asyncio.to_thread(user_repository.create, user)
    _user_cache[user.id] = user
    _user_cache_time[user.id] = time.time()

async def update_user(uid: str, update_data: dict):
    # Always use user_repository (PostgreSQL)
    await asyncio.to_thread(user_repository.update, uid, update_data)
    invalidate_user_cache(uid)

async def get_all_users(skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[User]:
    # Always use user_repository (PostgreSQL)
    return await asyncio.to_thread(user_repository.get_all, skip, limit, include_deleted)


async def get_deleted_users(skip: int = 0, limit: int = 100) -> List[User]:
    # Always use user_repository (PostgreSQL)
    return await asyncio.to_thread(user_repository.get_deleted, skip, limit)
