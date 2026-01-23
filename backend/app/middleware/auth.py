from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth_service import verify_token
from app.services.firebase_service import firebase_service
from typing import Optional


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme."
                )
            
            token = credentials.credentials
            user = self.verify_jwt(token)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid token or expired token."
                )
            
            # Attach user info to request for use in route handlers
            request.state.user = user
            return token
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code."
            )

    def verify_jwt(self, jwtoken: str) -> Optional[dict]:
        try:
            # First try our local JWT verification
            payload = verify_token(jwtoken)
            if payload:
                return payload
            
            # If that fails, try Firebase verification
            decoded_token = firebase_service.verify_token(jwtoken)
            if decoded_token:
                return decoded_token
                
        except Exception as e:
            print(f"Token verification error: {e}")
        
        return None