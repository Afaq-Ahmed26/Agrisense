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


def verify_token(token: str) -> Optional[dict]:
    try:
        # Get the public key from Google
        public_key_url = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
        response = requests.get(public_key_url)
        public_keys = response.json()

        # Get the unverified header from the token
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header["alg"]
        kid = unverified_header["kid"]

        # Find the correct key
        key = public_keys.get(kid)
        if not key:
            print("ERROR: Public key not found for kid.")
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
        print(f"ERROR: JWT verification failed: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error during JWT verification: {e}")
        return None