from ..db.mongodb import database
from ..models.user import User
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from ..config import settings
import aiohttp
import jwt
from bson import ObjectId
from datetime import datetime, timedelta

async def verify_google_token(token: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={token}') as resp:
            if resp.status != 200:
                return None
            token_info = await resp.json()
            
    if token_info.get('aud') != settings.google_client_id:
        return None

    credentials = Credentials(token)
    service = build('oauth2', 'v2', credentials=credentials)
    user_info = service.userinfo().get().execute()

    return user_info

async def get_or_create_user(user_data: dict):
    user = await database.users.find_one({"google_id": user_data["id"]})
    if not user:
        new_user = User(
            email=user_data["email"],
            name=user_data["name"],
            picture=user_data.get("picture"),
            google_id=user_data["id"]
        )
        result = await database.users.insert_one(new_user.dict(exclude={'id'}))
        new_user.id = result.inserted_id
        return new_user
    return User(**user)

def create_session_token(user_id: str):
    expiration = datetime.utcnow() + timedelta(days=1)  # Token expires in 1 day
    return jwt.encode(
        {"user_id": str(user_id), "exp": expiration},
        settings.secret_key,
        algorithm="HS256"
    )

async def get_user_from_token(token: str):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = payload.get("user_id")
        user = await database.users.find_one({"_id": ObjectId(user_id)})
        if user:
            return User(**user)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    return None