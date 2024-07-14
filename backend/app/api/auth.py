from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from ..services.auth_service import verify_google_token, get_or_create_user, create_session_token, get_user_from_token
from ..models.user import User
from pydantic import BaseModel

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class GoogleToken(BaseModel):
    token: str

@router.post("/google-login")
async def google_login(google_token: GoogleToken):
    user_data = await verify_google_token(google_token.token)
    if not user_data:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = await get_or_create_user(user_data)
    session_token = create_session_token(str(user.id))
    return {"message": "Login successful", "session_token": session_token}

@router.get("/user")
async def get_user(token: str = Depends(oauth2_scheme)):
    user = await get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"user": user}