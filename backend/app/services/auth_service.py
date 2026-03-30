from datetime import datetime, timedelta
from typing import Optional
import requests
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.config import settings
from app.models.user import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


public_keys_cache = {}
last_fetch_time = None
CACHE_DURATION_SECONDS = 3600  # Cache for 1 hour

def verify_token(token: str) -> Optional[dict]:
    global public_keys_cache, last_fetch_time

    # 1. Check cache for public keys
    if not public_keys_cache or \
       (last_fetch_time and (datetime.now() - last_fetch_time).total_seconds() > CACHE_DURATION_SECONDS):
        try:
            public_key_url = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
            response = requests.get(public_key_url, timeout=5)  # Add a timeout for safety
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            public_keys_cache = response.json()
            last_fetch_time = datetime.now()
            print("INFO: Fetched new Firebase public keys and updated cache.")
        except requests.exceptions.RequestException as req_e:
            print(f"ERROR: Failed to fetch Firebase public keys: {req_e}")
            # If we can't fetch new keys, try with existing cache if it exists, otherwise fail
            if not public_keys_cache:
                return None
        except Exception as e:
            print(f"ERROR: Unexpected error while fetching Firebase public keys: {e}")
            if not public_keys_cache:
                return None
    
    # Rest of the verification logic remains largely the same, using public_keys_cache
    try:
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header["alg"]
        kid = unverified_header["kid"]

        key = public_keys_cache.get(kid)  # Use from cache
        if not key:
            print("ERROR: Public key not found in cache for kid.")
            return None

        # Verify the token
        payload = jwt.decode(
            token,
            key,
            algorithms=[alg],
            audience=settings.FIREBASE_PROJECT_ID,
            issuer=f"https://securetoken.google.com/{settings.FIREBASE_PROJECT_ID}"
        )
        return payload
    except JWTError as e:
        print(f"ERROR: JWT verification failed: {e.__class__.__name__}: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error during JWT verification: {e}")
        return None