from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth_service import verify_token # Import the correct verify_token
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
            user_payload = self.verify_jwt(token) # Renamed to user_payload for clarity
            
            print(f"DEBUG: JWTBearer - verified user payload: {user_payload}")
            
            if not user_payload:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid token or expired token."
                )

            if not user_payload.get("email_verified", False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Email is not verified."
                )
            
            # Attach user info to request for use in route handlers
            request.state.user = user_payload
            return token
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code."
            )

    def verify_jwt(self, jwtoken: str) -> Optional[dict]:
        try:
            # Use app.services.auth_service.verify_token for backend's JWT
            payload = verify_token(jwtoken)
            if payload:
                return payload
                
        except Exception as e:
            print(f"Backend JWT verification error: {e}")
        
        return None
