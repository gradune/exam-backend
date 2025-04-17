from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from utils.auth import decode_token

#  it just extracts the token from incoming requests, 
# expects a token to be sent in the Authorization header in the format: Authorization: Bearer <access_token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)

    userId: int = payload.get("id")
    if userId is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Token is invalid")
    if isinstance(payload, dict) and "error" in payload:
        if payload["error"] == "expired":
            raise HTTPException(status_code=401, detail="Token has expired")
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    return payload
